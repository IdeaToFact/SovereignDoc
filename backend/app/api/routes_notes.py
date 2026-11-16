# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    Vault,
    Document,
    RiskAuditItem,
    ObligationItem,
    NoteRecord,
    NoteVersion,
    NoteLink,
)
from app.models.schemas import (
    NoteCreateRequest,
    NoteUpdateRequest,
    NoteResponse,
    NoteVersionResponse,
    NoteLinkItemResponse,
    QuickCaptureRequest,
    KnowledgeGraphResponse,
)
from app.services.second_brain.link_parser import wiki_link_parser
from app.services.second_brain.graph_service import knowledge_graph_service
from packages.contract_intelligence.enums import GraphNodeType

router = APIRouter(prefix="/api/vaults/{vault_id}", tags=["Second Brain & Knowledge Graph"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sync_note_links_and_backlinks(
    db: Session,
    vault_id: str,
    note: NoteRecord,
    pinned_risk_id: Optional[str] = None,
    pinned_obligation_id: Optional[str] = None,
    pinned_doc_id: Optional[str] = None,
    pinned_page: Optional[int] = None,
) -> None:
    """Parse [[WikiLinks]] from note.content_md and rebuild outgoing NoteLink rows."""
    # Preserve existing pinned RISK / OBLIGATION links from previous quick-captures on this note
    existing_pinned = (
        db.query(NoteLink)
        .filter(
            NoteLink.source_note_id == note.id,
            NoteLink.link_type.in_([GraphNodeType.RISK.value, GraphNodeType.OBLIGATION.value]),
        )
        .all()
    )
    preserved_risk_ids = {nl.target_risk_id for nl in existing_pinned if nl.target_risk_id}
    preserved_obl_ids = {nl.target_obligation_id for nl in existing_pinned if nl.target_obligation_id}

    if pinned_risk_id:
        preserved_risk_ids.add(pinned_risk_id)
    if pinned_obligation_id:
        preserved_obl_ids.add(pinned_obligation_id)

    # Clear current outgoing links for this note and rebuild
    db.query(NoteLink).filter(NoteLink.source_note_id == note.id).delete(synchronize_session=False)

    parsed_links = wiki_link_parser.extract_links(note.content_md or "")
    new_links: List[NoteLink] = []

    for pl in parsed_links:
        ltype = pl["link_type"]
        if ltype == GraphNodeType.DOCUMENT.value:
            fname = pl.get("target_filename", "")
            doc = (
                db.query(Document)
                .filter(
                    Document.vault_id == vault_id,
                    func.lower(Document.filename) == fname.lower(),
                )
                .first()
            )
            if not doc:
                # Partial match fallback
                doc = (
                    db.query(Document)
                    .filter(
                        Document.vault_id == vault_id,
                        Document.filename.ilike(f"%{fname}%"),
                    )
                    .first()
                )
            new_links.append(
                NoteLink(
                    id=str(uuid.uuid4()),
                    vault_id=vault_id,
                    source_note_id=note.id,
                    target_doc_id=doc.id if doc else None,
                    target_page=pl.get("target_page"),
                    link_text=pl["link_text"][:255],
                    link_type=GraphNodeType.DOCUMENT.value,
                )
            )
        elif ltype == GraphNodeType.RISK.value:
            rid = pl.get("target_risk_id")
            if rid:
                preserved_risk_ids.add(rid)
        elif ltype == GraphNodeType.OBLIGATION.value:
            oid = pl.get("target_obligation_id")
            if oid:
                preserved_obl_ids.add(oid)
        else:
            # Note-to-Note link
            target_title = pl.get("target_note_title", "")
            target_note = (
                db.query(NoteRecord)
                .filter(
                    NoteRecord.vault_id == vault_id,
                    NoteRecord.id != note.id,
                    func.lower(NoteRecord.title) == target_title.lower(),
                )
                .first()
            )
            new_links.append(
                NoteLink(
                    id=str(uuid.uuid4()),
                    vault_id=vault_id,
                    source_note_id=note.id,
                    target_note_id=target_note.id if target_note else None,
                    link_text=pl["link_text"][:255],
                    link_type=GraphNodeType.NOTE.value,
                )
            )

    # Add preserved/pinned RISK links
    for rid in preserved_risk_ids:
        risk_obj = db.query(RiskAuditItem).filter(RiskAuditItem.id == rid).first()
        if risk_obj:
            new_links.append(
                NoteLink(
                    id=str(uuid.uuid4()),
                    vault_id=vault_id,
                    source_note_id=note.id,
                    target_doc_id=risk_obj.document_id,
                    target_risk_id=risk_obj.id,
                    target_page=risk_obj.page_number,
                    link_text=f"Risk: {risk_obj.issue_title}"[:255],
                    link_type=GraphNodeType.RISK.value,
                )
            )

    # Add preserved/pinned OBLIGATION links
    for oid in preserved_obl_ids:
        obl_obj = db.query(ObligationItem).filter(ObligationItem.id == oid).first()
        if obl_obj:
            new_links.append(
                NoteLink(
                    id=str(uuid.uuid4()),
                    vault_id=vault_id,
                    source_note_id=note.id,
                    target_doc_id=obl_obj.document_id,
                    target_obligation_id=obl_obj.id,
                    target_page=obl_obj.page_number,
                    link_text=f"Obligation: {obl_obj.action_required[:80]}"[:255],
                    link_type=GraphNodeType.OBLIGATION.value,
                )
            )

    # If pinned_doc_id was explicitly provided and not already covered by a DOCUMENT link
    if pinned_doc_id and not any(nl.target_doc_id == pinned_doc_id and nl.link_type == GraphNodeType.DOCUMENT.value for nl in new_links):
        doc_obj = db.query(Document).filter(Document.id == pinned_doc_id).first()
        if doc_obj:
            new_links.append(
                NoteLink(
                    id=str(uuid.uuid4()),
                    vault_id=vault_id,
                    source_note_id=note.id,
                    target_doc_id=doc_obj.id,
                    target_page=pinned_page,
                    link_text=f"Doc:{doc_obj.filename}" + (f"#Page {pinned_page}" if pinned_page else ""),
                    link_type=GraphNodeType.DOCUMENT.value,
                )
            )

    if new_links:
        db.bulk_save_objects(new_links)

    # Resolve any previously unresolved incoming [[Note Title]] links from other notes in this vault
    unresolved = (
        db.query(NoteLink)
        .filter(
            NoteLink.vault_id == vault_id,
            NoteLink.link_type == GraphNodeType.NOTE.value,
            NoteLink.target_note_id.is_(None),
        )
        .all()
    )
    for ul in unresolved:
        raw_target = ul.link_text.split("|", 1)[0].strip()
        if raw_target.lower() == note.title.lower() and ul.source_note_id != note.id:
            ul.target_note_id = note.id


def _serialize_link_item(nl: NoteLink, db: Session) -> NoteLinkItemResponse:
    src_note = db.query(NoteRecord).filter(NoteRecord.id == nl.source_note_id).first()
    tgt_note = db.query(NoteRecord).filter(NoteRecord.id == nl.target_note_id).first() if nl.target_note_id else None
    tgt_doc = db.query(Document).filter(Document.id == nl.target_doc_id).first() if nl.target_doc_id else None
    return NoteLinkItemResponse(
        id=nl.id,
        source_note_id=nl.source_note_id,
        source_note_title=src_note.title if src_note else None,
        target_note_id=nl.target_note_id,
        target_note_title=tgt_note.title if tgt_note else None,
        target_doc_id=nl.target_doc_id,
        target_doc_filename=tgt_doc.filename if tgt_doc else None,
        target_risk_id=nl.target_risk_id,
        target_obligation_id=nl.target_obligation_id,
        target_page=nl.target_page,
        link_text=nl.link_text,
        link_type=nl.link_type,
        created_at=nl.created_at,
    )


def _serialize_note(note: NoteRecord, db: Session, include_links: bool = True) -> NoteResponse:
    try:
        tags = json.loads(note.tags_json or "[]")
    except Exception:
        tags = []

    doc_filename = None
    if note.document_id:
        doc = db.query(Document).filter(Document.id == note.document_id).first()
        if doc:
            doc_filename = doc.filename

    links_out_rows = db.query(NoteLink).filter(NoteLink.source_note_id == note.id).all()
    backlink_rows = db.query(NoteLink).filter(NoteLink.target_note_id == note.id).all()

    return NoteResponse(
        id=note.id,
        vault_id=note.vault_id,
        document_id=note.document_id,
        document_filename=doc_filename,
        page_number=note.page_number,
        section=note.section,
        title=note.title,
        content_md=note.content_md,
        tags=tags,
        current_version=note.current_version,
        pinned=note.pinned,
        outgoing_links_count=len(links_out_rows),
        backlinks_count=len(backlink_rows),
        links_out=[_serialize_link_item(nl, db) for nl in links_out_rows] if include_links else [],
        backlinks=[_serialize_link_item(nl, db) for nl in backlink_rows] if include_links else [],
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


# =============================================================================
# 1. Notes CRUD & Local Search
# =============================================================================

@router.get("/notes", response_model=List[NoteResponse])
def list_notes(
    vault_id: str,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    document_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List and search local Markdown notes in a vault."""
    query = db.query(NoteRecord).filter(NoteRecord.vault_id == vault_id)
    if document_id:
        query = query.filter(NoteRecord.document_id == document_id)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            (NoteRecord.title.ilike(term))
            | (NoteRecord.content_md.ilike(term))
            | (NoteRecord.tags_json.ilike(term))
        )

    notes = query.order_by(NoteRecord.pinned.desc(), NoteRecord.updated_at.desc()).all()

    if tag and tag.strip():
        clean_tag = tag.strip().lstrip("#").lower()
        filtered = []
        for n in notes:
            try:
                ntags = [t.lower() for t in json.loads(n.tags_json or "[]")]
            except Exception:
                ntags = []
            if clean_tag in ntags:
                filtered.append(n)
        notes = filtered

    return [_serialize_note(n, db, include_links=True) for n in notes]


@router.post("/notes", response_model=NoteResponse)
def create_note(vault_id: str, req: NoteCreateRequest, db: Session = Depends(get_db)):
    """Create a new Markdown note (v1), extract #tags and [[WikiLinks]], and update Knowledge Graph."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    tags = wiki_link_parser.extract_tags(req.content_md)
    note_id = str(uuid.uuid4())
    now = utc_now()

    note = NoteRecord(
        id=note_id,
        vault_id=vault_id,
        document_id=req.document_id,
        page_number=req.page_number,
        section=req.section,
        title=req.title.strip(),
        content_md=req.content_md,
        tags_json=json.dumps(tags),
        current_version=1,
        pinned=req.pinned,
        created_at=now,
        updated_at=now,
    )
    db.add(note)
    db.flush()

    v1 = NoteVersion(
        id=str(uuid.uuid4()),
        note_id=note.id,
        version_number=1,
        title=note.title,
        content_md=note.content_md,
        summary=req.summary or "Initial note creation (v1)",
        created_at=now,
    )
    db.add(v1)

    _sync_note_links_and_backlinks(
        db=db,
        vault_id=vault_id,
        note=note,
        pinned_doc_id=req.document_id,
        pinned_page=req.page_number,
    )
    db.commit()

    knowledge_graph_service.sync_vault_graph(db, vault_id)
    db.refresh(note)
    return _serialize_note(note, db, include_links=True)


@router.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(vault_id: str, note_id: str, db: Session = Depends(get_db)):
    """Retrieve a single note with outgoing links and incoming bi-directional backlinks."""
    note = (
        db.query(NoteRecord)
        .filter(NoteRecord.id == note_id, NoteRecord.vault_id == vault_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _serialize_note(note, db, include_links=True)


@router.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    vault_id: str,
    note_id: str,
    req: NoteUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update a note, snapshot a new NoteVersion (vN+1) if content/title changed, and sync Knowledge Graph."""
    note = (
        db.query(NoteRecord)
        .filter(NoteRecord.id == note_id, NoteRecord.vault_id == vault_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    content_changed = False
    if req.title is not None and req.title.strip() != note.title:
        note.title = req.title.strip()
        content_changed = True
    if req.content_md is not None and req.content_md != note.content_md:
        note.content_md = req.content_md
        content_changed = True
    if req.document_id is not None:
        note.document_id = req.document_id or None
    if req.page_number is not None:
        note.page_number = req.page_number
    if req.section is not None:
        note.section = req.section
    if req.pinned is not None:
        note.pinned = req.pinned

    tags = wiki_link_parser.extract_tags(note.content_md)
    note.tags_json = json.dumps(tags)
    note.updated_at = utc_now()

    if content_changed:
        note.current_version += 1
        ver = NoteVersion(
            id=str(uuid.uuid4()),
            note_id=note.id,
            version_number=note.current_version,
            title=note.title,
            content_md=note.content_md,
            summary=req.summary or f"Updated note (v{note.current_version})",
            created_at=utc_now(),
        )
        db.add(ver)

    _sync_note_links_and_backlinks(
        db=db,
        vault_id=vault_id,
        note=note,
        pinned_doc_id=note.document_id,
        pinned_page=note.page_number,
    )
    db.commit()

    knowledge_graph_service.sync_vault_graph(db, vault_id)
    db.refresh(note)
    return _serialize_note(note, db, include_links=True)


@router.delete("/notes/{note_id}")
def delete_note(vault_id: str, note_id: str, db: Session = Depends(get_db)):
    """Delete a note, cascade delete its versions and outgoing links, and update Knowledge Graph."""
    note = (
        db.query(NoteRecord)
        .filter(NoteRecord.id == note_id, NoteRecord.vault_id == vault_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.query(NoteLink).filter(NoteLink.source_note_id == note_id).delete(synchronize_session=False)
    db.query(NoteLink).filter(NoteLink.target_note_id == note_id).update(
        {"target_note_id": None}, synchronize_session=False
    )
    db.delete(note)
    db.commit()

    knowledge_graph_service.sync_vault_graph(db, vault_id)
    return {"status": "success", "message": f"Note '{note.title}' deleted."}


# =============================================================================
# 2. Note Version History & Non-Destructive Restore
# =============================================================================

@router.get("/notes/{note_id}/versions", response_model=List[NoteVersionResponse])
def list_note_versions(vault_id: str, note_id: str, db: Session = Depends(get_db)):
    """Return full chronological version history (v1..vN) for a note."""
    note = (
        db.query(NoteRecord)
        .filter(NoteRecord.id == note_id, NoteRecord.vault_id == vault_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    versions = (
        db.query(NoteVersion)
        .filter(NoteVersion.note_id == note_id)
        .order_by(NoteVersion.version_number.desc())
        .all()
    )
    return versions


@router.post("/notes/{note_id}/versions/{version_id}/restore", response_model=NoteResponse)
def restore_note_version(
    vault_id: str,
    note_id: str,
    version_id: str,
    db: Session = Depends(get_db),
):
    """Non-destructively restore a prior NoteVersion as a new latest version (vN+1)."""
    note = (
        db.query(NoteRecord)
        .filter(NoteRecord.id == note_id, NoteRecord.vault_id == vault_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    target_ver = (
        db.query(NoteVersion)
        .filter(NoteVersion.id == version_id, NoteVersion.note_id == note_id)
        .first()
    )
    if not target_ver:
        raise HTTPException(status_code=404, detail="Note version not found")

    note.current_version += 1
    note.title = target_ver.title
    note.content_md = target_ver.content_md
    tags = wiki_link_parser.extract_tags(note.content_md)
    note.tags_json = json.dumps(tags)
    note.updated_at = utc_now()

    restored_ver = NoteVersion(
        id=str(uuid.uuid4()),
        note_id=note.id,
        version_number=note.current_version,
        title=note.title,
        content_md=note.content_md,
        summary=f"Restored from v{target_ver.version_number}",
        created_at=utc_now(),
    )
    db.add(restored_ver)

    _sync_note_links_and_backlinks(
        db=db,
        vault_id=vault_id,
        note=note,
        pinned_doc_id=note.document_id,
        pinned_page=note.page_number,
    )
    db.commit()

    knowledge_graph_service.sync_vault_graph(db, vault_id)
    db.refresh(note)
    return _serialize_note(note, db, include_links=True)


# =============================================================================
# 3. One-Click Citation Pinning (📌 Save to Note from Chat, Risk & Obligation)
# =============================================================================

@router.post("/notes/quick-capture", response_model=NoteResponse)
def quick_capture_to_note(
    vault_id: str,
    req: QuickCaptureRequest,
    db: Session = Depends(get_db),
):
    """Pin a Grounded Chat Evidence card, RiskAuditItem, or ObligationItem directly into a Second Brain note."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    doc_filename = req.filename
    if req.document_id and not doc_filename:
        doc = db.query(Document).filter(Document.id == req.document_id).first()
        if doc:
            doc_filename = doc.filename
    doc_filename = doc_filename or "Contract Document"

    page_num = req.page_number or 1
    sec_label = f", Section {req.section}" if req.section else ""

    # Format structured Markdown block with grounded [[WikiLinks]]
    header_badge = "📌 Grounded Evidence"
    entity_wikilink = f"[[Doc:{doc_filename}#Page {page_num}]]"
    auto_tags = list(req.tags or [])

    if req.source_type == "RISK":
        lvl = (req.risk_level or "HIGH").upper()
        header_badge = f"⚠️ [{lvl} RISK] {req.clause_title or req.rule_id or 'Contract Exposure'}"
        if req.risk_id:
            entity_wikilink += f" • [[Risk:{req.risk_id}]]"
        auto_tags.extend(["risk-audit", lvl.lower() + "-risk"])
    elif req.source_type == "OBLIGATION":
        party_lbl = (req.party or "PARTY").upper()
        deadline_lbl = f" (Deadline: {req.deadline})" if req.deadline else ""
        header_badge = f"📋 [{party_lbl} OBLIGATION]{deadline_lbl}"
        if req.obligation_id:
            entity_wikilink += f" • [[Obligation:{req.obligation_id}]]"
        auto_tags.extend(["obligation", party_lbl.lower()])
    else:
        header_badge = f"📌 {req.clause_title or f'Page {page_num}{sec_label} Evidence'}"
        auto_tags.append("grounded-evidence")

    tag_line = " ".join(f"#{t.lstrip('#').lower()}" for t in auto_tags if t)
    commentary_block = f"\n\n**Analysis / Note:** {req.commentary.strip()}" if req.commentary else ""

    captured_block = (
        f"### {header_badge}\n"
        f"- **Source:** {entity_wikilink} (Page {page_num}{sec_label})\n\n"
        f"> {req.verbatim_text.strip()}"
        f"{commentary_block}\n\n"
        f"{tag_line}\n"
    )

    # Resolve target note: explicit note_id -> existing note for this document -> create new note
    target_note = None
    if req.note_id:
        target_note = (
            db.query(NoteRecord)
            .filter(NoteRecord.id == req.note_id, NoteRecord.vault_id == vault_id)
            .first()
        )
    if not target_note and req.document_id:
        target_note = (
            db.query(NoteRecord)
            .filter(
                NoteRecord.vault_id == vault_id,
                NoteRecord.document_id == req.document_id,
            )
            .order_by(NoteRecord.updated_at.desc())
            .first()
        )

    now = utc_now()
    if target_note:
        target_note.content_md = (target_note.content_md.rstrip() + "\n\n---\n\n" + captured_block).strip()
        target_note.current_version += 1
        target_note.updated_at = now
        merged_tags = wiki_link_parser.extract_tags(target_note.content_md, auto_tags)
        target_note.tags_json = json.dumps(merged_tags)

        ver = NoteVersion(
            id=str(uuid.uuid4()),
            note_id=target_note.id,
            version_number=target_note.current_version,
            title=target_note.title,
            content_md=target_note.content_md,
            summary=f"Pinned {req.source_type.lower()} citation from Page {page_num}",
            created_at=now,
        )
        db.add(ver)
    else:
        default_title = req.note_title or f"Research Notes — {doc_filename}"
        initial_md = f"# {default_title}\n\n{captured_block}"
        merged_tags = wiki_link_parser.extract_tags(initial_md, auto_tags)
        target_note = NoteRecord(
            id=str(uuid.uuid4()),
            vault_id=vault_id,
            document_id=req.document_id,
            page_number=page_num,
            section=req.section,
            title=default_title[:255],
            content_md=initial_md,
            tags_json=json.dumps(merged_tags),
            current_version=1,
            pinned=True,
            created_at=now,
            updated_at=now,
        )
        db.add(target_note)
        db.flush()

        ver = NoteVersion(
            id=str(uuid.uuid4()),
            note_id=target_note.id,
            version_number=1,
            title=target_note.title,
            content_md=target_note.content_md,
            summary=f"Created via Quick Capture ({req.source_type.lower()} on Page {page_num})",
            created_at=now,
        )
        db.add(ver)

    _sync_note_links_and_backlinks(
        db=db,
        vault_id=vault_id,
        note=target_note,
        pinned_risk_id=req.risk_id,
        pinned_obligation_id=req.obligation_id,
        pinned_doc_id=req.document_id,
        pinned_page=page_num,
    )
    db.commit()

    knowledge_graph_service.sync_vault_graph(db, vault_id)
    db.refresh(target_note)
    return _serialize_note(target_note, db, include_links=True)


# =============================================================================
# 4. 7-Entity Knowledge Graph, Statistics & Graph Search
# =============================================================================

@router.get("/graph", response_model=KnowledgeGraphResponse)
def get_vault_knowledge_graph(
    vault_id: str,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return persisted 7-entity Knowledge Graph (nodes, edges, stats, and optional ?q= search matches)."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    payload = knowledge_graph_service.get_vault_graph(db=db, vault_id=vault_id, query=q)
    return KnowledgeGraphResponse(**payload)


@router.post("/graph/sync", response_model=KnowledgeGraphResponse)
def sync_vault_knowledge_graph(vault_id: str, db: Session = Depends(get_db)):
    """Force a deterministic rebuild of the vault's graph_nodes and graph_edges in SQLite."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    knowledge_graph_service.sync_vault_graph(db=db, vault_id=vault_id)
    payload = knowledge_graph_service.get_vault_graph(db=db, vault_id=vault_id)
    return KnowledgeGraphResponse(**payload)


@router.get("/graph/stats")
def get_vault_knowledge_graph_stats(vault_id: str, db: Session = Depends(get_db)):
    """Return lightweight Vault Statistics (documents, review_runs, risks, obligations, notes, tags, edges)."""
    vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    return knowledge_graph_service.get_vault_stats(db=db, vault_id=vault_id)

