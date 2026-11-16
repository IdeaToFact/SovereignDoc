# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import Vault, Document, Chunk
from app.models.schemas import VaultCreateRequest, VaultResponse
from app.services.storage_manager import storage_manager
from app.services.rag.vector_store import vector_store

router = APIRouter(prefix="/api/vaults", tags=["Vault Management"])


@router.post("", response_model=VaultResponse)
def create_vault(req: VaultCreateRequest, db: Session = Depends(get_db)):
    """Create a new isolated document vault."""
    vault_id = str(uuid.uuid4())
    vault = Vault(
        id=vault_id,
        name=req.name.strip(),
        description=req.description.strip() if req.description else None
    )
    db.add(vault)
    db.commit()
    db.refresh(vault)

    # Initialize physical directory
    storage_manager.get_vault_path(vault_id)

    return VaultResponse(
        id=vault.id,
        name=vault.name,
        description=vault.description,
        document_count=0,
        total_chunks=0,
        size_mb=0.0,
        created_at=vault.created_at,
        updated_at=vault.updated_at
    )


@router.get("", response_model=List[VaultResponse])
def list_vaults(db: Session = Depends(get_db)):
    """List all document vaults with document counts and total size."""
    vaults = db.query(Vault).all()
    res = []
    for v in vaults:
        doc_count = db.query(func.count(Document.id)).filter(Document.vault_id == v.id).scalar() or 0
        chunk_count = db.query(func.count(Chunk.id)).filter(Chunk.vault_id == v.id).scalar() or 0
        total_bytes = db.query(func.sum(Document.file_size_bytes)).filter(Document.vault_id == v.id).scalar() or 0
        size_mb = round(total_bytes / (1024 * 1024), 2)

        res.append(VaultResponse(
            id=v.id,
            name=v.name,
            description=v.description,
            document_count=doc_count,
            total_chunks=chunk_count,
            size_mb=size_mb,
            created_at=v.created_at,
            updated_at=v.updated_at
        ))
    return res


@router.get("/{vault_id}", response_model=VaultResponse)
def get_vault(vault_id: str, db: Session = Depends(get_db)):
    """Get single vault details."""
    v = db.query(Vault).filter(Vault.id == vault_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vault not found")

    doc_count = db.query(func.count(Document.id)).filter(Document.vault_id == v.id).scalar() or 0
    chunk_count = db.query(func.count(Chunk.id)).filter(Chunk.vault_id == v.id).scalar() or 0
    total_bytes = db.query(func.sum(Document.file_size_bytes)).filter(Document.vault_id == v.id).scalar() or 0
    size_mb = round(total_bytes / (1024 * 1024), 2)

    return VaultResponse(
        id=v.id,
        name=v.name,
        description=v.description,
        document_count=doc_count,
        total_chunks=chunk_count,
        size_mb=size_mb,
        created_at=v.created_at,
        updated_at=v.updated_at
    )


@router.delete("/{vault_id}")
def delete_vault(vault_id: str, db: Session = Depends(get_db)):
    """Delete vault, associated files, ChromaDB collection, and SQLite records."""
    v = db.query(Vault).filter(Vault.id == vault_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vault not found")

    # 1. Drop ChromaDB collection
    vector_store.delete_vault_collection(vault_id)

    # 2. Delete database records (cascades to documents, chunks, jobs)
    db.delete(v)
    db.commit()

    # 3. Cleanup local files
    import shutil
    vault_path = storage_manager.vaults_dir / vault_id
    if vault_path.exists():
        shutil.rmtree(vault_path, ignore_errors=True)

    return {"status": "success", "message": f"Vault '{v.name}' deleted"}
