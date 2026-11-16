# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from fastapi.responses import FileResponse
import hashlib
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Vault, Document, Chunk, IngestionJob
from app.models.schemas import (
    DocumentResponse,
    IngestionJobResponse,
    HybridQueryRequest,
    HybridQueryResponse
)
from app.services.storage_manager import storage_manager
from app.services.rag.document_parser import document_parser
from app.services.rag.chunker import chunker
from app.services.rag.embedding_service import embedding_service
from app.services.rag.bm25_index import BM25Index
from app.services.rag.vector_store import vector_store
from app.services.rag.hybrid_retriever import hybrid_retriever

router = APIRouter(prefix="/api/vaults/{vault_id}", tags=["Documents & Hybrid RAG"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/documents/upload", response_model=IngestionJobResponse)
async def upload_document(
    vault_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload document, compute SHA-256 for deduplication, parse, chunk, embed, and index."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    content = await file.read()
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Cannot upload empty file")

    # Cryptographic SHA-256 Checksum
    checksum = hashlib.sha256(content).hexdigest()

    # 1. Deduplication check in this vault
    existing_doc = (
        db.query(Document)
        .filter(Document.vault_id == vault_id, Document.checksum_sha256 == checksum)
        .first()
    )
    if existing_doc:
        existing_job = (
            db.query(IngestionJob)
            .filter(IngestionJob.document_id == existing_doc.id)
            .order_by(IngestionJob.created_at.desc())
            .first()
        )
        if existing_job:
            return IngestionJobResponse(
                id=existing_job.id,
                vault_id=existing_job.vault_id,
                document_id=existing_doc.id,
                filename=existing_doc.filename,
                status="READY",
                error_message="Duplicate file detected. Document already indexed in vault.",
                progress_pct=100,
                processing_time_ms=existing_job.processing_time_ms,
                chunks_generated=existing_doc.chunk_count,
                embeddings_generated=existing_doc.chunk_count,
                created_at=existing_job.created_at,
                completed_at=existing_job.completed_at or utc_now()
            )

    # 2. Save physical file to vault directory
    vault_path = storage_manager.get_vault_path(vault_id)
    raw_filename = file.filename or "uploaded_file"
    safe_filename = Path(raw_filename).name
    doc_id = str(uuid.uuid4())
    saved_file_path = vault_path / f"{doc_id}_{safe_filename}"
    with open(saved_file_path, "wb") as f:
        f.write(content)

    # 3. Create Document and IngestionJob in SQLite
    doc_record = Document(
        id=doc_id,
        vault_id=vault_id,
        filename=safe_filename,
        file_type=Path(safe_filename).suffix.lower(),
        file_size_bytes=file_size,
        file_path=str(saved_file_path),
        checksum_sha256=checksum,
        page_count=1,
        chunk_count=0
    )
    db.add(doc_record)

    job_id = str(uuid.uuid4())
    job = IngestionJob(
        id=job_id,
        vault_id=vault_id,
        document_id=doc_id,
        filename=safe_filename,
        status="PROCESSING",
        progress_pct=10
    )
    db.add(job)
    db.commit()

    # 4. Ingestion Processing
    start_time = time.time()
    try:
        # A. Parse document
        blocks = document_parser.parse_file(saved_file_path)
        page_numbers = [b.get("page_number", 1) for b in blocks]
        max_page = max(page_numbers) if page_numbers else 1
        doc_record.page_count = max_page
        job.progress_pct = 30
        db.commit()

        # B. Chunk document with sequential links and abbreviation protection
        raw_chunks = chunker.chunk_document(doc_id, vault_id, safe_filename, blocks)
        job.chunks_generated = len(raw_chunks)
        job.progress_pct = 50
        db.commit()

        # C. Store Chunks in SQLite (Single Source of Truth)
        chunk_entities = []
        for c in raw_chunks:
            chunk_entities.append(Chunk(
                id=c["id"],
                document_id=doc_id,
                vault_id=vault_id,
                chunk_index=c["chunk_index"],
                previous_chunk_id=c["previous_chunk_id"],
                next_chunk_id=c["next_chunk_id"],
                parent_chunk_id=c.get("parent_chunk_id"),
                page_number=c["page_number"],
                article=c.get("article"),
                section=c.get("section"),
                subsection=c.get("subsection"),
                bbox_json=c.get("bbox_json"),
                section_title=c.get("section_title"),
                text=c["text"],
                char_length=c["char_length"],
                token_count=c["token_count"]
            ))
        db.bulk_save_objects(chunk_entities)
        doc_record.chunk_count = len(chunk_entities)
        job.progress_pct = 70
        db.commit()

        # D. Embed Chunks (100% Local FastEmbed ONNX)
        chunk_texts = [c["text"] for c in raw_chunks]
        chunk_ids = [c["id"] for c in raw_chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)
        job.embeddings_generated = len(embeddings)
        job.progress_pct = 85
        db.commit()

        # E. Index in ChromaVectorStore (IDs + Embeddings only)
        vector_store.add_vectors(
            vault_id=vault_id,
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            metadatas=[{"document_id": doc_id} for _ in chunk_ids]
        )

        # F. Index in BM25 Sparse Index
        bm25 = BM25Index(vault_path)
        bm25.add_chunks(raw_chunks)

        # G. Complete Job
        elapsed_ms = int((time.time() - start_time) * 1000)
        job.status = "READY"
        job.progress_pct = 100
        job.processing_time_ms = elapsed_ms
        job.completed_at = utc_now()
        db.commit()

        # H. Synchronize Vault Knowledge Graph nodes & edges
        try:
            from app.services.second_brain.graph_service import knowledge_graph_service
            knowledge_graph_service.sync_vault_graph(db, vault_id)
        except Exception:
            pass

    except Exception as e:
        db.rollback()
        job.status = "FAILED"
        job.error_message = str(e)
        job.completed_at = utc_now()
        db.commit()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return IngestionJobResponse(
        id=job.id,
        vault_id=job.vault_id,
        document_id=job.document_id,
        filename=job.filename,
        status=job.status,
        error_message=job.error_message,
        progress_pct=job.progress_pct,
        processing_time_ms=job.processing_time_ms,
        chunks_generated=job.chunks_generated,
        embeddings_generated=job.embeddings_generated,
        created_at=job.created_at,
        completed_at=job.completed_at
    )


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
def get_job_status(vault_id: str, job_id: str, db: Session = Depends(get_db)):
    """Poll ingestion job status and telemetry metrics."""
    job = (
        db.query(IngestionJob)
        .filter(IngestionJob.id == job_id, IngestionJob.vault_id == vault_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(vault_id: str, db: Session = Depends(get_db)):
    """List all documents in a vault."""
    docs = (
        db.query(Document)
        .filter(Document.vault_id == vault_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return docs


@router.delete("/documents/{doc_id}")
def delete_document(vault_id: str, doc_id: str, db: Session = Depends(get_db)):
    """Delete document, drop its chunks from SQLite, vectors from Chroma, and terms from BM25."""
    doc = db.query(Document).filter(Document.id == doc_id, Document.vault_id == vault_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_ids = [c.id for c in db.query(Chunk.id).filter(Chunk.document_id == doc_id).all()]
    vector_store.delete_document_vectors(vault_id, chunk_ids)

    vault_path = storage_manager.get_vault_path(vault_id)
    bm25 = BM25Index(vault_path)
    bm25.remove_document_chunks(doc_id)

    saved_file = vault_path / f"{doc_id}_{doc.filename}"
    if saved_file.exists():
        saved_file.unlink()

    db.delete(doc)
    db.commit()

    try:
        from app.services.second_brain.graph_service import knowledge_graph_service
        knowledge_graph_service.sync_vault_graph(db, vault_id)
    except Exception:
        pass

    return {"status": "success", "message": f"Document '{doc.filename}' deleted"}


@router.post("/query", response_model=HybridQueryResponse)
def query_vault(
    vault_id: str,
    req: HybridQueryRequest,
    db: Session = Depends(get_db)
):
    """Execute two-stage hybrid search with RRF fusion, SQLite hydration, and Cross-Encoder reranking."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    vault_path = storage_manager.get_vault_path(vault_id)
    bm25 = BM25Index(vault_path)

    results = hybrid_retriever.search(
        vault_id=vault_id,
        bm25_index=bm25,
        db_session=db,
        query=req.query,
        document_id=req.document_id,
        top_k=req.top_k,
        mode=req.mode,
        enable_reranker=req.enable_reranker,
        expand_window=req.expand_window
    )

    reranked = req.enable_reranker and len(results) > 1 and req.mode != "keyword_only"

    return HybridQueryResponse(
        query=req.query,
        vault_id=vault_id,
        mode=req.mode,
        reranked=reranked,
        results=results
    )


@router.get("/documents/{doc_id}/file")
def get_document_file(vault_id: str, doc_id: str, db: Session = Depends(get_db)):
    """Stream raw physical document for PDF.js canvas viewer."""
    doc = db.query(Document).filter(Document.id == doc_id, Document.vault_id == vault_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = None
    if doc.file_path and Path(doc.file_path).exists():
        file_path = Path(doc.file_path)
    else:
        vault_path = storage_manager.get_vault_path(vault_id)
        fallback_path = vault_path / f"{doc.id}_{doc.filename}"
        if fallback_path.exists():
            file_path = fallback_path

    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical document file missing on disk")

    suffix = file_path.suffix.lower()
    media_type = "application/octet-stream"
    if suffix == ".pdf":
        media_type = "application/pdf"
    elif suffix in [".txt", ".md"]:
        media_type = "text/plain; charset=utf-8"
    elif suffix == ".csv":
        media_type = "text/csv; charset=utf-8"
    elif suffix == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=doc.filename,
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'}
    )


def sync_document_chunks_metadata(db: Session, doc: Document, blocks: List[dict], page_count: int) -> None:
    """Ensure SQLite Chunk metadata (page_number, section, section_title) matches unified pagination."""
    try:
        raw_chunks = chunker.chunk_document(doc.id, doc.vault_id, doc.filename, blocks)
        existing_chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == doc.id)
            .order_by(Chunk.chunk_index.asc())
            .all()
        )
        updated = False
        if len(existing_chunks) == len(raw_chunks):
            for db_chunk, new_c in zip(existing_chunks, raw_chunks):
                if (
                    db_chunk.page_number != new_c["page_number"]
                    or db_chunk.section != new_c.get("section")
                    or db_chunk.subsection != new_c.get("subsection")
                    or db_chunk.article != new_c.get("article")
                    or db_chunk.section_title != new_c.get("section_title")
                ):
                    db_chunk.page_number = new_c["page_number"]
                    db_chunk.article = new_c.get("article")
                    db_chunk.section = new_c.get("section")
                    db_chunk.subsection = new_c.get("subsection")
                    db_chunk.section_title = new_c.get("section_title")
                    updated = True
        else:
            # Fallback alignment by text prefix if chunk count ever differed
            text_map = {c["text"][:100]: c for c in raw_chunks if c.get("text")}
            for db_chunk in existing_chunks:
                match_c = text_map.get((db_chunk.text or "")[:100])
                if match_c:
                    if (
                        db_chunk.page_number != match_c["page_number"]
                        or db_chunk.section != match_c.get("section")
                        or db_chunk.section_title != match_c.get("section_title")
                    ):
                        db_chunk.page_number = match_c["page_number"]
                        db_chunk.article = match_c.get("article")
                        db_chunk.section = match_c.get("section")
                        db_chunk.subsection = match_c.get("subsection")
                        db_chunk.section_title = match_c.get("section_title")
                        updated = True

        if doc.page_count != page_count:
            doc.page_count = page_count
            updated = True

        if updated:
            db.commit()
    except Exception:
        db.rollback()


@router.get("/documents/{doc_id}/html")
def get_document_html(vault_id: str, doc_id: str, db: Session = Depends(get_db)):
    """Return converted HTML representation of a document (for DOCX, MD, CSV, TXT)."""
    doc = db.query(Document).filter(Document.id == doc_id, Document.vault_id == vault_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = None
    if doc.file_path and Path(doc.file_path).exists():
        file_path = Path(doc.file_path)
    else:
        vault_path = storage_manager.get_vault_path(vault_id)
        fallback_path = vault_path / f"{doc.id}_{doc.filename}"
        if fallback_path.exists():
            file_path = fallback_path

    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical document file missing on disk")

    suffix = file_path.suffix.lower()
    if suffix == ".docx":
        paginated = document_parser.paginate_docx(file_path, include_html=True)
        sync_document_chunks_metadata(
            db=db,
            doc=doc,
            blocks=paginated["blocks"],
            page_count=paginated["page_count"]
        )
        return {
            "html": paginated["html"],
            "pages": paginated["pages"],
            "page_count": paginated["page_count"],
            "pagination_source": paginated["pagination_source"],
            "file_type": "docx",
            "filename": doc.filename
        }

    elif suffix in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        import html
        escaped = html.escape(text)
        rendered_html = f"<pre style='font-family: monospace; white-space: pre-wrap;'>{escaped}</pre>"
        return {
            "html": rendered_html,
            "pages": [rendered_html],
            "page_count": 1,
            "pagination_source": "VIRTUAL_LAYOUT",
            "file_type": suffix.lstrip("."),
            "filename": doc.filename
        }

    elif suffix == ".csv":
        import csv
        import html
        rows = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for r in reader:
                rows.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>")
        table_html = f"<table class='doc-csv-table'>{''.join(rows[:500])}</table>"
        return {
            "html": table_html,
            "pages": [table_html],
            "page_count": 1,
            "pagination_source": "VIRTUAL_LAYOUT",
            "file_type": "csv",
            "filename": doc.filename
        }

    return {"html": "", "pages": [""], "page_count": 1, "pagination_source": "VIRTUAL_LAYOUT", "file_type": suffix.lstrip("."), "filename": doc.filename}
