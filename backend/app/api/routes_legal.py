# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
API Routes for Contract Intelligence & Legal Workstation
"""
import sys
from pathlib import Path

# Ensure repository root is in sys.path so 'packages' can be imported anywhere
_repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import io
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.database import get_db
from app.db.models import (
    Vault,
    Document,
    Chunk,
    ReviewRun,
    ClauseClassification,
    RiskAuditItem,
    ObligationItem,
    ContractComparison
)

# Contract intelligence modules
from packages.contract_intelligence.enums import (
    RiskLevel,
    DetectionMethod,
    ClauseCategory,
    ObligationParty
)
from packages.contract_intelligence.plugin_sdk.registry import CapabilityRegistry
import packages.contract_intelligence.risk_rules
from packages.contract_intelligence.classifiers import clause_classifier
from packages.contract_intelligence.obligations import obligations_extractor
from packages.contract_intelligence.diff import contract_diff
from packages.contract_intelligence.exports import review_exporter

router = APIRouter(prefix="/api/vaults/{vault_id}", tags=["Contract Intelligence"])


class CompareRequest(BaseModel):
    doc_a_id: str
    doc_b_id: str


# =============================================================================
# 1. Review Runs (Audit, Classify, Risk Rules, Obligations)
# =============================================================================

@router.post("/documents/{doc_id}/review-runs")
def create_review_run(vault_id: str, doc_id: str, db: Session = Depends(get_db)):
    """
    Executes a new versioned contract analysis on the document.
    Runs clause classification, registered RiskRules, and obligations extraction.
    Creates a new ReviewRun record without destructively overwriting previous runs.
    """
    doc = db.scalar(select(Document).where(Document.id == doc_id, Document.vault_id == vault_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in vault")

    chunks = db.scalars(
        select(Chunk).where(Chunk.document_id == doc_id).order_by(Chunk.chunk_index)
    ).all()
    if not chunks:
        raise HTTPException(status_code=400, detail="Document has no indexed chunks. Please ingest document first.")

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    started_at = datetime.now(timezone.utc)

    # 1. Classify clauses into the 7 core families
    classified_map = clause_classifier.classify_chunks(chunks, doc_id)
    for category, items in classified_map.items():
        for item in items:
            cc = ClauseClassification(
                id=f"cc_{uuid.uuid4().hex[:12]}",
                document_id=doc_id,
                chunk_id=item.chunk_id,
                category=item.category.value,
                confidence=item.confidence,
                detection_method=item.detection_method.value
            )
            db.add(cc)

    # 2. Evaluate all registered RiskRules
    registered_rules = CapabilityRegistry.get_risk_rules()
    risk_findings = []
    for rule in registered_rules:
        findings = rule.evaluate(chunks, classified_map)
        risk_findings.extend(findings)

    # 3. Extract affirmative obligations
    extracted_obls = obligations_extractor.extract_obligations(chunks, doc_id)

    # 4. Create versioned ReviewRun
    review_run = ReviewRun(
        id=run_id,
        document_id=doc_id,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        classifier_version="1.1.0",
        ruleset_version="1.1.0",
        total_risks=len(risk_findings),
        total_obligations=len(extracted_obls),
        status="COMPLETED"
    )
    db.add(review_run)

    # 5. Persist RiskAuditItems linked to review_run_id
    risk_records = []
    for f in risk_findings:
        bbox_str = json.dumps(f.bbox) if f.bbox else None
        item = RiskAuditItem(
            id=f"risk_{uuid.uuid4().hex[:12]}",
            review_run_id=run_id,
            document_id=doc_id,
            rule_id=f.rule_id,
            category=f.category.value if hasattr(f.category, "value") else str(f.category),
            risk_level=f.risk_level.value if hasattr(f.risk_level, "value") else str(f.risk_level),
            issue_title=f.issue_title,
            description=f.description,
            page_number=f.page_number,
            section=f.section,
            bbox_json=bbox_str,
            verbatim_text=f.verbatim_text,
            confidence=f.confidence,
            detection_method=f.detection_method.value if hasattr(f.detection_method, "value") else str(f.detection_method)
        )
        db.add(item)
        risk_records.append(item)

    # 6. Persist ObligationItems linked to review_run_id
    obl_records = []
    for o in extracted_obls:
        bbox_str = json.dumps(o.bbox) if o.bbox else None
        item = ObligationItem(
            id=f"obl_{uuid.uuid4().hex[:12]}",
            review_run_id=run_id,
            document_id=doc_id,
            party=o.party.value if hasattr(o.party, "value") else str(o.party),
            action_required=o.action_required,
            trigger_or_condition=o.trigger_or_condition,
            deadline_or_cadence=o.deadline_or_cadence,
            page_number=o.page_number,
            section=o.section,
            bbox_json=bbox_str,
            verbatim_text=o.verbatim_text,
            confidence=o.confidence,
            detection_method=o.detection_method.value if hasattr(o.detection_method, "value") else str(o.detection_method)
        )
        db.add(item)
        obl_records.append(item)

    db.commit()
    db.refresh(review_run)

    # Synchronize Vault Knowledge Graph with new ReviewRun, RiskAuditItem, and ObligationItem nodes
    try:
        from app.services.second_brain.graph_service import knowledge_graph_service
        knowledge_graph_service.sync_vault_graph(db, vault_id)
    except Exception:
        pass

    return {
        "id": review_run.id,
        "document_id": doc_id,
        "started_at": review_run.started_at.isoformat(),
        "completed_at": review_run.completed_at.isoformat() if review_run.completed_at else None,
        "classifier_version": review_run.classifier_version,
        "ruleset_version": review_run.ruleset_version,
        "total_risks": review_run.total_risks,
        "total_obligations": review_run.total_obligations,
        "status": review_run.status,
        "risks": [
            {
                "id": r.id,
                "rule_id": r.rule_id,
                "category": r.category,
                "risk_level": r.risk_level,
                "issue_title": r.issue_title,
                "description": r.description,
                "page_number": r.page_number,
                "section": r.section,
                "bbox": json.loads(r.bbox_json) if r.bbox_json else None,
                "verbatim_text": r.verbatim_text,
                "confidence": r.confidence,
                "detection_method": r.detection_method
            }
            for r in risk_records
        ],
        "obligations": [
            {
                "id": o.id,
                "party": o.party,
                "action_required": o.action_required,
                "trigger_or_condition": o.trigger_or_condition,
                "deadline_or_cadence": o.deadline_or_cadence,
                "page_number": o.page_number,
                "section": o.section,
                "bbox": json.loads(o.bbox_json) if o.bbox_json else None,
                "verbatim_text": o.verbatim_text,
                "confidence": o.confidence,
                "detection_method": o.detection_method
            }
            for o in obl_records
        ]
    }


@router.get("/documents/{doc_id}/review-runs")
def list_review_runs(vault_id: str, doc_id: str, db: Session = Depends(get_db)):
    """
    Lists all historical review runs for a document.
    """
    runs = db.scalars(
        select(ReviewRun)
        .where(ReviewRun.document_id == doc_id)
        .order_by(desc(ReviewRun.started_at))
    ).all()

    return [
        {
            "id": r.id,
            "document_id": r.document_id,
            "started_at": r.started_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "classifier_version": r.classifier_version,
            "ruleset_version": r.ruleset_version,
            "total_risks": r.total_risks,
            "total_obligations": r.total_obligations,
            "status": r.status
        }
        for r in runs
    ]


@router.get("/documents/{doc_id}/review-runs/{run_id}")
def get_review_run(vault_id: str, doc_id: str, run_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full details, risks, and obligations for a specific review run.
    """
    run = db.scalar(select(ReviewRun).where(ReviewRun.id == run_id, ReviewRun.document_id == doc_id))
    if not run:
        raise HTTPException(status_code=404, detail="Review run not found")

    risks = db.scalars(select(RiskAuditItem).where(RiskAuditItem.review_run_id == run_id)).all()
    obligations = db.scalars(select(ObligationItem).where(ObligationItem.review_run_id == run_id)).all()

    return {
        "id": run.id,
        "document_id": run.document_id,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "classifier_version": run.classifier_version,
        "ruleset_version": run.ruleset_version,
        "total_risks": run.total_risks,
        "total_obligations": run.total_obligations,
        "status": run.status,
        "risks": [
            {
                "id": r.id,
                "rule_id": r.rule_id,
                "category": r.category,
                "risk_level": r.risk_level,
                "issue_title": r.issue_title,
                "description": r.description,
                "page_number": r.page_number,
                "section": r.section,
                "bbox": json.loads(r.bbox_json) if r.bbox_json else None,
                "verbatim_text": r.verbatim_text,
                "confidence": r.confidence,
                "detection_method": r.detection_method
            }
            for r in risks
        ],
        "obligations": [
            {
                "id": o.id,
                "party": o.party,
                "action_required": o.action_required,
                "trigger_or_condition": o.trigger_or_condition,
                "deadline_or_cadence": o.deadline_or_cadence,
                "page_number": o.page_number,
                "section": o.section,
                "bbox": json.loads(o.bbox_json) if o.bbox_json else None,
                "verbatim_text": o.verbatim_text,
                "confidence": o.confidence,
                "detection_method": o.detection_method
            }
            for o in obligations
        ]
    }


@router.get("/documents/{doc_id}/review-runs/{run_id}/export")
def export_review_package(vault_id: str, doc_id: str, run_id: str, db: Session = Depends(get_db)):
    """
    Generates and streams the complete contract_review.zip package for a review run.
    Contains contract_audit.md, risk_matrix.csv, and obligations.csv.
    """
    doc = db.scalar(select(Document).where(Document.id == doc_id, Document.vault_id == vault_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    run = db.scalar(select(ReviewRun).where(ReviewRun.id == run_id, ReviewRun.document_id == doc_id))
    if not run:
        raise HTTPException(status_code=404, detail="Review run not found")

    risks = db.scalars(select(RiskAuditItem).where(RiskAuditItem.review_run_id == run_id)).all()
    obligations = db.scalars(select(ObligationItem).where(ObligationItem.review_run_id == run_id)).all()

    zip_bytes = review_exporter.build_review_package_zip(
        document_filename=doc.filename,
        review_run_id=run.id,
        ruleset_version=run.ruleset_version,
        risks=risks,
        obligations=obligations
    )

    clean_filename = f"{doc.filename.rsplit('.', 1)[0]}_review_{run.id}.zip"
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{clean_filename}"'
        }
    )


# =============================================================================
# 2. Redline Comparison (Document A vs. Document B)
# =============================================================================

@router.post("/compare")
def compare_contracts(vault_id: str, payload: CompareRequest, db: Session = Depends(get_db)):
    """
    Compares two contracts in the vault (Doc A vs Doc B), returns word-level diffs and alignment.
    """
    doc_a = db.scalar(select(Document).where(Document.id == payload.doc_a_id, Document.vault_id == vault_id))
    doc_b = db.scalar(select(Document).where(Document.id == payload.doc_b_id, Document.vault_id == vault_id))
    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both comparison documents not found in vault")

    chunks_a = db.scalars(select(Chunk).where(Chunk.document_id == payload.doc_a_id).order_by(Chunk.chunk_index)).all()
    chunks_b = db.scalars(select(Chunk).where(Chunk.document_id == payload.doc_b_id).order_by(Chunk.chunk_index)).all()

    diff_data = contract_diff.compare_documents(chunks_a, chunks_b, payload.doc_a_id, payload.doc_b_id)

    # Persist or update comparison record in SQLite
    comp_id = f"cmp_{uuid.uuid4().hex[:12]}"
    comp = ContractComparison(
        id=comp_id,
        vault_id=vault_id,
        doc_a_id=payload.doc_a_id,
        doc_b_id=payload.doc_b_id,
        status="COMPLETED",
        summary_text=diff_data["summary_text"],
        diff_json=json.dumps(diff_data)
    )
    db.add(comp)
    db.commit()

    diff_data["id"] = comp_id
    diff_data["doc_a_filename"] = doc_a.filename
    diff_data["doc_b_filename"] = doc_b.filename
    return diff_data
