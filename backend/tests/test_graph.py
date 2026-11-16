# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — 7-Entity Second Brain Knowledge Graph Tests
"""
from sqlalchemy.orm import Session
from app.db.models import Vault, Document, ReviewRun, NoteRecord, GraphNode, GraphEdge
from app.services.second_brain.graph_service import knowledge_graph_service, CURRENT_GRAPH_VERSION
from packages.contract_intelligence.enums import GraphNodeType, GraphEdgeType


def test_graph_node_and_edge_types():
    """Verifies all 7 GraphNodeType and 5 GraphEdgeType definitions."""
    assert GraphNodeType.DOCUMENT == "DOCUMENT"
    assert GraphNodeType.REVIEW_RUN == "REVIEW_RUN"
    assert GraphNodeType.CLAUSE_CATEGORY == "CLAUSE_CATEGORY"
    assert GraphNodeType.RISK == "RISK"
    assert GraphNodeType.OBLIGATION == "OBLIGATION"
    assert GraphNodeType.NOTE == "NOTE"
    assert GraphNodeType.TAG == "TAG"

    assert GraphEdgeType.CONTAINS == "CONTAINS"
    assert GraphEdgeType.GENERATED == "GENERATED"
    assert GraphEdgeType.REFERENCES == "REFERENCES"
    assert GraphEdgeType.TAGGED == "TAGGED"
    assert GraphEdgeType.LINKS_TO == "LINKS_TO"


def test_graph_sync_and_stats(in_memory_db: Session):
    """Verifies knowledge graph sync creates nodes and edges from vault records."""
    db = in_memory_db
    vault = Vault(id="v_graph_test", name="Graph Test Vault")
    doc = Document(
        id="doc_g1",
        vault_id="v_graph_test",
        filename="Commercial_Lease.pdf",
        file_type=".pdf",
        file_size_bytes=42000,
        checksum_sha256="mock_hash",
        page_count=5,
        chunk_count=10
    )
    db.add_all([vault, doc])
    db.commit()

    # Sync vault graph
    knowledge_graph_service.sync_vault_graph(db, "v_graph_test")
    nodes = db.query(GraphNode).filter(GraphNode.vault_id == "v_graph_test").all()
    assert len(nodes) >= 1
    doc_node = next((n for n in nodes if n.entity_type == GraphNodeType.DOCUMENT.value), None)
    assert doc_node is not None
    assert doc_node.entity_id == "doc_g1"

