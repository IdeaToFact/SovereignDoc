# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Knowledge Graph Usability, Latest-Run Tagging & Category Isolation Tests
"""
import json
from sqlalchemy.orm import Session
from app.db.models import (
    Vault,
    Document,
    Chunk,
    ReviewRun,
    ClauseClassification,
    RiskAuditItem,
    ObligationItem,
    GraphNode,
)
from app.services.second_brain.graph_service import knowledge_graph_service


def test_knowledge_graph_usability_and_grounding(in_memory_db: Session):
    """Verifies multi-run decoupling with is_latest tagging and clause category linkage."""
    db = in_memory_db

    vault = Vault(id="v_usability", name="Legal Usability Vault")
    doc = Document(
        id="doc_m62",
        vault_id="v_usability",
        filename="Master_Services_Agreement_2026.pdf",
        file_type=".pdf",
        file_size_bytes=84000,
        checksum_sha256="sha256_mock_hash",
        page_count=12,
        chunk_count=18,
    )
    chunk_audit = Chunk(
        id="chk_audit_1",
        document_id="doc_m62",
        vault_id="v_usability",
        chunk_index=0,
        page_number=4,
        section="4.1",
        section_title="4.1 Audit Rights",
        text="Customer may audit books and records upon 15 business days notice.",
        char_length=70,
        token_count=15,
    )
    cc_audit = ClauseClassification(
        id="cc_audit_1",
        document_id="doc_m62",
        chunk_id="chk_audit_1",
        category="AUDIT_AND_RECORD_RETENTION",
        confidence=0.98,
        detection_method="CLASSIFIER",
    )
    db.add_all([vault, doc, chunk_audit, cc_audit])
    db.commit()

    # Create Run 1 (Old)
    run1 = ReviewRun(
        id="run_01_old",
        document_id="doc_m62",
        total_risks=1,
        total_obligations=1,
        status="COMPLETED",
    )
    r1_risk = RiskAuditItem(
        id="risk_run1",
        review_run_id="run_01_old",
        document_id="doc_m62",
        rule_id="AUDIT_RIGHTS_SCOPE",
        category="AUDIT_AND_RECORD_RETENTION",
        risk_level="MEDIUM",
        issue_title="Unfettered Audit Access",
        description="Old audit issue.",
        verbatim_text="Customer may audit books and records upon 15 business days notice.",
        confidence=1.0,
        detection_method="RULE",
        page_number=4,
    )

    # Create Run 2 (Latest)
    run2 = ReviewRun(
        id="run_02_new",
        document_id="doc_m62",
        total_risks=1,
        total_obligations=1,
        status="COMPLETED",
    )
    r2_risk = RiskAuditItem(
        id="risk_run2",
        review_run_id="run_02_new",
        document_id="doc_m62",
        rule_id="AUDIT_RIGHTS_SCOPE",
        category="AUDIT_AND_RECORD_RETENTION",
        risk_level="HIGH",
        issue_title="Unfettered Audit Access Revised",
        description="Latest audit issue.",
        verbatim_text="Customer may audit books and records upon 15 business days notice.",
        confidence=1.0,
        detection_method="RULE",
        page_number=4,
    )
    r2_ob = ObligationItem(
        id="ob_run2",
        review_run_id="run_02_new",
        document_id="doc_m62",
        party="VENDOR",
        action_required="Provide records within 15 days",
        verbatim_text="Vendor shall provide records within 15 days.",
        deadline_or_cadence="15 business days",
        page_number=4,
        confidence=0.95,
        detection_method="HEURISTIC",
    )

    db.add_all([run1, r1_risk, run2, r2_risk, r2_ob])
    db.commit()

    # Sync graph
    knowledge_graph_service.sync_vault_graph(db, "v_usability")
    nodes = db.query(GraphNode).filter(GraphNode.vault_id == "v_usability").all()

    # Verify is_latest tagging
    node_map = {n.entity_id: n for n in nodes}
    run1_node = node_map["run_01_old"]
    run2_node = node_map["run_02_new"]

    meta_r1 = json.loads(run1_node.metadata_json or "{}")
    meta_r2 = json.loads(run2_node.metadata_json or "{}")

    assert meta_r1.get("is_latest") is False
    assert meta_r2.get("is_latest") is True

    # Verify latest risk has is_latest=True
    risk2_node = node_map["risk_run2"]
    meta_risk2 = json.loads(risk2_node.metadata_json or "{}")
    assert meta_risk2.get("is_latest") is True

    # Verify 100% grounding integrity
    integrity = knowledge_graph_service.verify_grounding_integrity(db, "v_usability")
    assert integrity["is_grounded"] is True
    assert len(integrity["ungrounded_node_ids"]) == 0

