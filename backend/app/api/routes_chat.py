# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Vault, Document, Chunk, ChatSession, ChatMessage
from app.models.schemas import (
    ChatStreamRequest,
    EvidenceObject,
    ChatSessionResponse,
    ChatSessionCreateRequest,
    ChatMessageResponse
)
from app.services.storage_manager import storage_manager
from app.services.rag.bm25_index import BM25Index
from app.services.rag.hybrid_retriever import hybrid_retriever
from app.services.llm.provider_factory import get_llm_provider, get_model_registry
from app.services.upl_guard import upl_guard, UPL_NOTICE_MARKDOWN

router = APIRouter(prefix="/api/vaults/{vault_id}", tags=["Grounded Chat & Evidence Engine"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_confidence(score: float, is_reranked: bool) -> float:
    """Normalize raw retriever/reranker score into a calibrated 0.45 - 0.98 confidence metric."""
    if is_reranked:
        # Cross-encoder (ms-marco-MiniLM-L-6-v2) logits typically span [-10.0, +2.0]
        # Map onto a realistic non-linear curve so high-relevance chunks score 80-98%
        norm = (score - (-10.0)) / (2.0 - (-10.0))
        norm = min(max(norm, 0.0), 1.0)
        val = 0.45 + 0.53 * (norm ** 0.8)
        return round(min(max(val, 0.45), 0.98), 2)
    else:
        # RRF scores typically range from 0.01 to 0.04
        val = min(max(score * 30.0, 0.50), 0.95)
        return round(val, 2)


def build_system_prompt(recipe: Optional[str]) -> str:
    base = (
        "You are SovereignDoc, a 100% air-gapped legal and document intelligence second brain.\n"
        "You have zero internet access. Answer ONLY based on the provided document excerpts below.\n"
        "Strict Grounding Rules:\n"
        "1. Every factual claim, finding, or quote MUST cite its source using tags like [Page X, Section Y].\n"
        "2. Do NOT extrapolate or assume terms not in the text.\n"
        "3. If the provided excerpts do not contain the answer, explicitly state: 'The provided document does not contain this information.'\n"
        "4. System Directive (UPL Protection): SovereignDoc is an automated contract intelligence tool and not a licensed attorney. "
        "If asked for legal advice (e.g., 'Should I sign?', 'Am I liable?'), analyze the text factually, state the risks based on document evidence, "
        "and append: 'Note: This analysis is informational and does not constitute formal legal counsel.'\n"
    )
    if recipe == "obligations":
        base += "\nFocus specifically on affirmative duties, required notices, deadlines, and operational obligations."
    elif recipe == "liability":
        base += "\nFocus specifically on indemnification covenants, liability caps, carve-outs, warranties, and clawbacks."
    elif recipe == "termination":
        base += "\nFocus specifically on termination for cause/convenience, cure periods, notice requirements, and post-termination survival."
    elif recipe == "executive":
        base += "\nProvide a clear, high-level executive briefing with concise bullet points and direct clause citations."
    return base


def _clean_section_label(sec: Optional[str]) -> Optional[str]:
    if not sec:
        return None
    cleaned = re.sub(r"^(?:Section|Sec\.?|§)\s*", "", str(sec), flags=re.IGNORECASE).strip()
    return cleaned or None


def format_grounded_prompt(system_prompt: str, evidence: List[EvidenceObject], user_query: str) -> str:
    evidence_blocks = []
    for i, ev in enumerate(evidence, 1):
        clean_sec = _clean_section_label(ev.section)
        clause_tag = f"Section {clean_sec}" if clean_sec else (ev.article or "General Clause")
        context_body = ev.surrounding_context if ev.surrounding_context else ev.evidence_text
        block = f"[Source {i} | Doc: {ev.filename} | Page: {ev.page_number} | {clause_tag}]\n{context_body.strip()}"
        evidence_blocks.append(block)

    joined_evidence = "\n\n".join(evidence_blocks) if evidence_blocks else "NO SOURCES RETRIEVED."

    prompt = (
        f"{system_prompt}\n\n"
        f"--- PROVIDED EVIDENCE SOURCES ---\n"
        f"{joined_evidence}\n"
        f"--- END EVIDENCE SOURCES ---\n\n"
        f"USER INQUIRY: {user_query}\n\n"
        f"ASSISTANT GROUNDED ANSWER:"
    )
    return prompt


@router.post("/chat/stream")
async def stream_chat(
    vault_id: str,
    req: ChatStreamRequest,
    db: Session = Depends(get_db)
):
    """Execute grounded hybrid search and stream response tokens and EvidenceObjects via Server-Sent Events (SSE)."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    # 1. Resolve or create chat session
    session_id = req.session_id
    if not session_id:
        new_session = ChatSession(
            id=str(uuid.uuid4()),
            vault_id=vault_id,
            document_id=req.document_id,
            title=req.query[:40] + ("..." if len(req.query) > 40 else "")
        )
        db.add(new_session)
        db.commit()
        session_id = new_session.id
    else:
        existing_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.vault_id == vault_id).first()
        if not existing_session:
            raise HTTPException(status_code=404, detail="Chat session not found")

    # 2. Execute Hybrid Retrieval with Document-Level Pre-Filtering
    t0_retrieval = time.time()
    vault_path = storage_manager.get_vault_path(vault_id)
    bm25 = BM25Index(vault_path)

    raw_results = hybrid_retriever.search(
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

    retrieval_ms = int((time.time() - t0_retrieval) * 1000)
    is_reranked = req.enable_reranker and len(raw_results) > 1 and req.mode != "keyword_only"

    # 3. Convert results to rich EvidenceObjects
    evidence_list: List[EvidenceObject] = []
    for r in raw_results:
        confidence = normalize_confidence(r.score, is_reranked)
        clean_sec = _clean_section_label(r.section)
        ev_title = r.section_title or (f"Section {clean_sec}" if clean_sec else (r.article or f"Page {r.page_number} Excerpt"))
        evidence_list.append(
            EvidenceObject(
                citation_id=f"cit_{r.chunk_id}",
                document_id=r.document_id,
                filename=r.document_name,
                page_number=r.page_number,
                bbox=r.bbox,
                article=r.article,
                section=clean_sec,
                subsection=r.subsection,
                clause_title=ev_title,
                evidence_text=r.snippet,
                surrounding_context=r.expanded_context,
                confidence=confidence,
                rerank_score=round(r.score, 4)
            )
        )

    # 4. Resolve Model & Prompt
    model_name = req.model_name or get_model_registry().active_model
    system_prompt = build_system_prompt(req.recipe)
    full_prompt = format_grounded_prompt(system_prompt, evidence_list, req.query)

    provider = get_llm_provider()

    async def sse_generator() -> AsyncGenerator[str, None]:
        # Event 1: retrieval_done
        yield f"event: retrieval_done\ndata: {json.dumps({'evidence_count': len(evidence_list), 'retrieval_time_ms': retrieval_ms})}\n\n"

        accumulated_text = ""
        total_tokens = 0
        eval_duration = 0.0
        t0_stream = time.time()

        try:
            # Check provider health
            health = await provider.get_health()
            if health.get("status") == "OFFLINE" or not model_name:
                # Fallback response explaining offline status
                fallback_resp = (
                    "**[Offline Advisory]** Local inference service is currently offline or no model is selected.\n\n"
                    "However, your documents are securely indexed and retrieved locally! "
                    "You can inspect the verified evidence sources in the pane below."
                )
                accumulated_text = fallback_resp
                for word in fallback_resp.split(" "):
                    yield f"event: token\ndata: {json.dumps({'text': word + ' '})}\n\n"
            else:
                async for chunk in provider.generate_stream(model_name, full_prompt):
                    token = chunk.get("response", "")
                    if token:
                        accumulated_text += token
                        yield f"event: token\ndata: {json.dumps({'text': token})}\n\n"
                    if chunk.get("done"):
                        total_tokens = chunk.get("eval_count", 0)
                        if chunk.get("eval_duration"):
                            eval_duration = chunk["eval_duration"] / 1e9

        except Exception as e:
            err_msg = f"\n\n*(Inference notice: {str(e)})*"
            accumulated_text += err_msg
            yield f"event: token\ndata: {json.dumps({'text': err_msg})}\n\n"

        # Milestone 6.1 Layer 2: Deterministic application-layer UPL safeguard
        if upl_guard.is_legal_advice_query(req.query) and "does not provide legal advice" not in accumulated_text.lower():
            accumulated_text = accumulated_text.rstrip() + UPL_NOTICE_MARKDOWN
            yield f"event: token\ndata: {json.dumps({'text': UPL_NOTICE_MARKDOWN})}\n\n"

        total_elapsed = time.time() - t0_stream
        if total_tokens == 0:
            total_tokens = len(accumulated_text.split())
        tps = round(total_tokens / total_elapsed, 2) if total_elapsed > 0 else 0.0

        # Persist messages in SQLite
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=req.query,
            created_at=utc_now()
        )
        asst_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=accumulated_text,
            evidence_json=json.dumps([ev.model_dump() for ev in evidence_list]),
            tokens_generated=total_tokens,
            tokens_per_second=tps,
            created_at=utc_now()
        )
        db.add(user_msg)
        db.add(asst_msg)
        db.commit()

        # Event 2: evidence
        evidence_payload = {"evidence": [ev.model_dump() for ev in evidence_list]}
        yield f"event: evidence\ndata: {json.dumps(evidence_payload)}\n\n"

        # Event 3: done
        done_payload = {
            "session_id": session_id,
            "message_id": asst_msg.id,
            "tokens_generated": total_tokens,
            "tokens_per_second": tps,
            "eval_duration_sec": round(total_elapsed, 2)
        }
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


def _serialize_session(s: ChatSession, db: Session) -> ChatSessionResponse:
    msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
    doc_filename = None
    if s.document_id:
        doc = db.query(Document).filter(Document.id == s.document_id).first()
        if doc:
            doc_filename = doc.filename
    return ChatSessionResponse(
        id=s.id,
        vault_id=s.vault_id,
        document_id=s.document_id,
        document_filename=doc_filename,
        title=s.title,
        message_count=msg_count,
        created_at=s.created_at,
        updated_at=s.updated_at
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_sessions(vault_id: str, document_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List chat sessions for the vault, optionally filtered by document_id."""
    query = db.query(ChatSession).filter(ChatSession.vault_id == vault_id)
    if document_id:
        query = query.filter(ChatSession.document_id == document_id)
    sessions = query.order_by(ChatSession.updated_at.desc()).all()
    return [_serialize_session(s, db) for s in sessions]


@router.get("/documents/{document_id}/sessions", response_model=List[ChatSessionResponse])
def list_document_sessions(vault_id: str, document_id: str, db: Session = Depends(get_db)):
    """Clean RESTful endpoint returning sessions scoped specifically to a document."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.vault_id == vault_id, ChatSession.document_id == document_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [_serialize_session(s, db) for s in sessions]


@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(vault_id: str, req: ChatSessionCreateRequest, db: Session = Depends(get_db)):
    """Create a new chat session for a vault, optionally associated with a document."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    session = ChatSession(
        id=str(uuid.uuid4()),
        vault_id=vault_id,
        document_id=req.document_id,
        title=req.title or "New Analysis"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _serialize_session(session, db)


@router.post("/documents/{document_id}/sessions", response_model=ChatSessionResponse)
def create_document_session(vault_id: str, document_id: str, req: ChatSessionCreateRequest, db: Session = Depends(get_db)):
    """RESTful endpoint to create a chat session directly linked to a document."""
    req.document_id = document_id
    return create_session(vault_id, req, db)


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(vault_id: str, session_id: str, db: Session = Depends(get_db)):
    """Retrieve full chronological conversation history with evidence objects for a session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.vault_id == vault_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    output = []
    for m in messages:
        evidence = []
        if m.evidence_json:
            try:
                raw_ev = json.loads(m.evidence_json)
                for item in raw_ev:
                    ev_obj = EvidenceObject(**item)
                    # Hydrate live page_number, section, and clause_title from SQLite Chunk (Single Source of Truth)
                    cid = ev_obj.citation_id[4:] if ev_obj.citation_id and ev_obj.citation_id.startswith("cit_") else None
                    ch = db.query(Chunk).filter(Chunk.id == cid).first() if cid else None
                    if not ch and ev_obj.document_id and ev_obj.evidence_text:
                        ch = (
                            db.query(Chunk)
                            .filter(
                                Chunk.document_id == ev_obj.document_id,
                                Chunk.text.startswith(ev_obj.evidence_text[:80])
                            )
                            .first()
                        )
                    if ch:
                        clean_sec = _clean_section_label(ch.section)
                        ev_obj.page_number = ch.page_number
                        ev_obj.article = ch.article
                        ev_obj.section = clean_sec
                        ev_obj.subsection = ch.subsection
                        ev_obj.clause_title = ch.section_title or (
                            f"Section {clean_sec}" if clean_sec else (ch.article or f"Page {ch.page_number} Excerpt")
                        )
                    else:
                        ev_obj.section = _clean_section_label(ev_obj.section)
                    evidence.append(ev_obj)
            except Exception:
                pass
        output.append(
            ChatMessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                evidence=evidence,
                tokens_generated=m.tokens_generated,
                tokens_per_second=m.tokens_per_second,
                created_at=m.created_at
            )
        )
    return output


@router.delete("/sessions/{session_id}")
def delete_session(vault_id: str, session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and all its messages."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.vault_id == vault_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    db.delete(session)
    db.commit()
    return {"status": "success", "message": f"Chat session '{session_id}' deleted."}
