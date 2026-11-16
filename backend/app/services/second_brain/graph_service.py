# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.db.models import (
    Document,
    Chunk,
    ReviewRun,
    ClauseClassification,
    RiskAuditItem,
    ObligationItem,
    NoteRecord,
    NoteLink,
    GraphNode,
    GraphEdge,
)
from packages.contract_intelligence.enums import GraphNodeType, GraphEdgeType

CURRENT_GRAPH_VERSION = "1.1.0"


def _infer_obligation_category(
    obl: ObligationItem,
    page_to_category: Optional[Dict[Tuple[str, int], str]] = None,
    section_to_category: Optional[Dict[Tuple[str, str], str]] = None,
) -> Optional[str]:
    """Deterministically map an ObligationItem to a standardized ClauseCategory."""
    text = f"{obl.action_required or ''} {obl.verbatim_text or ''}".lower()
    if any(k in text for k in ["audit", "inspect", "books and records", "record production", "examination", "monitoring"]):
        return "AUDIT_AND_RECORD_RETENTION"
    if any(k in text for k in ["confidential", "proprietary", "trade secret", "non-disclosure", "disclose"]):
        return "CONFIDENTIALITY"
    if any(k in text for k in ["terminat", "expiration", "renew", "convenience"]):
        return "TERMINATION"
    if any(k in text for k in ["indemnif", "defend", "hold harmless"]):
        return "INDEMNIFICATION"
    if any(k in text for k in ["liab", "damage", "consequential", "aggregate"]):
        return "LIMITATION_OF_LIABILITY"
    if any(k in text for k in ["pay", "invoice", "fee", "compensation", "reimburse", "late fee", "pricing"]):
        return "PAYMENT_TERMS"
    if any(k in text for k in ["insurance", "policy", "coverage", "insured", "endorsement"]):
        return "INSURANCE"
    if any(k in text for k in ["intellectual property", "work product", "patent", "copyright", "trademark", "ownership of work", "ip rights"]):
        return "INTELLECTUAL_PROPERTY"
    if any(k in text for k in ["warrant", "represent"]):
        return "REPRESENTATIONS_AND_WARRANTIES"
    if any(k in text for k in ["non-solicit", "non-compete", "restrictive covenant", "solicit"]):
        return "NON_COMPETE_AND_NON_SOLICIT"
    if any(k in text for k in ["governing law", "jurisdiction", "venue", "court", "arbitrat"]):
        return "GOVERNING_LAW"
    if any(k in text for k in ["written notice", "formal notice"]):
        return "NOTICES"
    if section_to_category and obl.section and (obl.document_id, obl.section) in section_to_category:
        return section_to_category[(obl.document_id, obl.section)]
    if page_to_category and obl.page_number and (obl.document_id, obl.page_number) in page_to_category:
        return page_to_category[(obl.document_id, obl.page_number)]
    return None


class KnowledgeGraphService:
    """Builds, persists, queries, and verifies the 7-Entity Grounded Legal Knowledge Graph in SQLite."""

    @staticmethod
    def make_node_id(vault_id: str, entity_type: GraphNodeType, entity_id: str) -> str:
        return f"{vault_id}:{entity_type.value}:{entity_id}"

    @staticmethod
    def make_edge_id(vault_id: str, source_id: str, edge_type: GraphEdgeType, target_id: str) -> str:
        return f"{vault_id}:{source_id}->{edge_type.value}->{target_id}"

    @classmethod
    def sync_vault_graph(cls, db: Session, vault_id: str) -> None:
        """Deterministically synchronize graph_nodes and graph_edges for a vault from SQLite source tables.

        Enforces the Graph Grounding Integrity axiom:
        Every GraphNode is traceable via (entity_type, entity_id) to a persisted SQLite entity.
        """
        # Clear existing cached nodes & edges for this vault and rebuild cleanly
        db.query(GraphEdge).filter(GraphEdge.vault_id == vault_id).delete(synchronize_session=False)
        db.query(GraphNode).filter(GraphNode.vault_id == vault_id).delete(synchronize_session=False)

        nodes_map: Dict[str, GraphNode] = {}
        edges_map: Dict[str, GraphEdge] = {}

        def _add_node(entity_type: GraphNodeType, entity_id: str, label: str, metadata: Dict[str, Any]) -> str:
            nid = cls.make_node_id(vault_id, entity_type, entity_id)
            if nid not in nodes_map:
                nodes_map[nid] = GraphNode(
                    id=nid,
                    vault_id=vault_id,
                    entity_type=entity_type.value,
                    entity_id=entity_id,
                    label=label[:255],
                    metadata_json=json.dumps(metadata),
                    graph_version=CURRENT_GRAPH_VERSION,
                )
            return nid

        def _add_edge(source_id: str, target_id: str, edge_type: GraphEdgeType, label: Optional[str] = None, weight: float = 1.0) -> None:
            if source_id not in nodes_map or target_id not in nodes_map:
                return
            eid = cls.make_edge_id(vault_id, source_id, edge_type, target_id)
            if eid not in edges_map:
                edges_map[eid] = GraphEdge(
                    id=eid,
                    vault_id=vault_id,
                    source_id=source_id,
                    target_id=target_id,
                    edge_type=edge_type.value,
                    label=label or edge_type.value,
                    weight=weight,
                    graph_version=CURRENT_GRAPH_VERSION,
                )

        # 1. DOCUMENT Nodes
        docs = db.query(Document).filter(Document.vault_id == vault_id).all()
        doc_ids = [d.id for d in docs]
        doc_node_ids: Dict[str, str] = {}

        for doc in docs:
            d_nid = _add_node(
                GraphNodeType.DOCUMENT,
                doc.id,
                doc.filename,
                {
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "page_count": doc.page_count,
                    "chunk_count": doc.chunk_count,
                },
            )
            doc_node_ids[doc.id] = d_nid

        # 2. CLAUSE_CATEGORY Nodes (Grouped per Document + Category)
        clause_node_ids: Dict[Tuple[str, str], str] = {}

        def _ensure_clause_category_node(doc_id: str, category: str) -> str:
            key = (doc_id, category)
            if key not in clause_node_ids:
                entity_id = f"{doc_id}:{category}"
                pretty_cat = category.replace("_", " ").title()
                c_nid = _add_node(
                    GraphNodeType.CLAUSE_CATEGORY,
                    entity_id,
                    pretty_cat,
                    {
                        "document_id": doc_id,
                        "category": category,
                        "clause_count": 1,
                    },
                )
                clause_node_ids[key] = c_nid
                if doc_id in doc_node_ids:
                    _add_edge(doc_node_ids[doc_id], c_nid, GraphEdgeType.CONTAINS, "CONTAINS")
            return clause_node_ids[key]

        page_to_category: Dict[Tuple[str, int], str] = {}
        section_to_category: Dict[Tuple[str, str], str] = {}
        if doc_ids:
            classifications = (
                db.query(ClauseClassification)
                .filter(ClauseClassification.document_id.in_(doc_ids))
                .all()
            )
            chunk_ids = [cc.chunk_id for cc in classifications if cc.chunk_id]
            if chunk_ids:
                chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
                chunk_map = {c.id: c for c in chunks}
                for cc in classifications:
                    chk = chunk_map.get(cc.chunk_id)
                    if chk:
                        page_to_category[(cc.document_id, chk.page_number)] = cc.category
                        if chk.section:
                            section_to_category[(cc.document_id, chk.section)] = cc.category
            grouped_clauses: Dict[Tuple[str, str], int] = {}
            for cc in classifications:
                key = (cc.document_id, cc.category)
                grouped_clauses[key] = grouped_clauses.get(key, 0) + 1

            for (doc_id, category), count in grouped_clauses.items():
                entity_id = f"{doc_id}:{category}"
                pretty_cat = category.replace("_", " ").title()
                c_nid = _add_node(
                    GraphNodeType.CLAUSE_CATEGORY,
                    entity_id,
                    pretty_cat,
                    {
                        "document_id": doc_id,
                        "category": category,
                        "clause_count": count,
                    },
                )
                clause_node_ids[(doc_id, category)] = c_nid
                if doc_id in doc_node_ids:
                    _add_edge(doc_node_ids[doc_id], c_nid, GraphEdgeType.CONTAINS, "CONTAINS")

        # 3. REVIEW_RUN Nodes + 4. RISK Nodes + 5. OBLIGATION Nodes
        risk_node_ids: Dict[str, str] = {}
        obligation_node_ids: Dict[str, str] = {}

        if doc_ids:
            runs = (
                db.query(ReviewRun)
                .filter(ReviewRun.document_id.in_(doc_ids))
                .order_by(ReviewRun.started_at.asc())
                .all()
            )
            # Map each document to its latest ReviewRun id
            latest_run_id_per_doc: Dict[str, str] = {}
            for r in runs:
                latest_run_id_per_doc[r.document_id] = r.id

            run_counter_per_doc: Dict[str, int] = {}
            for run in runs:
                run_idx = run_counter_per_doc.get(run.document_id, 0) + 1
                run_counter_per_doc[run.document_id] = run_idx
                is_latest_run = (run.id == latest_run_id_per_doc.get(run.document_id))
                r_nid = _add_node(
                    GraphNodeType.REVIEW_RUN,
                    run.id,
                    f"Review #{run_idx} ({run.total_risks}R / {run.total_obligations}O)",
                    {
                        "review_run_id": run.id,
                        "document_id": run.document_id,
                        "run_number": run_idx,
                        "ruleset_version": run.ruleset_version,
                        "total_risks": run.total_risks,
                        "total_obligations": run.total_obligations,
                        "is_latest": is_latest_run,
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                    },
                )
                if run.document_id in doc_node_ids:
                    _add_edge(doc_node_ids[run.document_id], r_nid, GraphEdgeType.GENERATED, f"Review #{run_idx}")

                # RiskAuditItem nodes for this ReviewRun
                risks = db.query(RiskAuditItem).filter(RiskAuditItem.review_run_id == run.id).all()
                for risk in risks:
                    c_nid = _ensure_clause_category_node(risk.document_id, risk.category)
                    rk_nid = _add_node(
                        GraphNodeType.RISK,
                        risk.id,
                        f"[{risk.risk_level}] {risk.issue_title}",
                        {
                            "risk_id": risk.id,
                            "review_run_id": run.id,
                            "document_id": risk.document_id,
                            "rule_id": risk.rule_id,
                            "category": risk.category,
                            "risk_level": risk.risk_level,
                            "issue_title": risk.issue_title,
                            "description": risk.description,
                            "confidence": risk.confidence,
                            "detection_method": risk.detection_method,
                            "page_number": risk.page_number,
                            "section": risk.section,
                            "is_latest": is_latest_run,
                            "run_number": run_idx,
                            "verbatim_text": risk.verbatim_text[:1000] if risk.verbatim_text else "",
                        },
                    )
                    risk_node_ids[risk.id] = rk_nid
                    _add_edge(r_nid, rk_nid, GraphEdgeType.GENERATED, risk.risk_level)
                    _add_edge(c_nid, rk_nid, GraphEdgeType.CONTAINS, "FLAGS")

                # ObligationItem nodes for this ReviewRun
                obligations = db.query(ObligationItem).filter(ObligationItem.review_run_id == run.id).all()
                for obl in obligations:
                    obl_cat = _infer_obligation_category(obl, page_to_category, section_to_category)
                    c_nid = None
                    if obl_cat:
                        c_nid = _ensure_clause_category_node(obl.document_id, obl_cat)
                    short_duty = (obl.action_required or "Obligation").strip()
                    if len(short_duty) > 48:
                        short_duty = short_duty[:45] + "..."
                    ob_nid = _add_node(
                        GraphNodeType.OBLIGATION,
                        obl.id,
                        f"[{obl.party}] {short_duty}",
                        {
                            "obligation_id": obl.id,
                            "review_run_id": run.id,
                            "document_id": obl.document_id,
                            "party": obl.party,
                            "category": obl_cat,
                            "deadline_or_cadence": obl.deadline_or_cadence,
                            "trigger_or_condition": obl.trigger_or_condition,
                            "page_number": obl.page_number,
                            "section": obl.section,
                            "action_required": obl.action_required,
                            "confidence": obl.confidence,
                            "detection_method": obl.detection_method,
                            "is_latest": is_latest_run,
                            "run_number": run_idx,
                            "verbatim_text": obl.verbatim_text[:1000] if obl.verbatim_text else "",
                        },
                    )
                    obligation_node_ids[obl.id] = ob_nid
                    _add_edge(r_nid, ob_nid, GraphEdgeType.GENERATED, obl.party)
                    if c_nid:
                        _add_edge(c_nid, ob_nid, GraphEdgeType.CONTAINS, "IMPOSES")

        # 6. NOTE Nodes + 7. TAG Nodes + NoteLink Edges
        notes = db.query(NoteRecord).filter(NoteRecord.vault_id == vault_id).all()
        note_node_ids: Dict[str, str] = {}
        tag_node_ids: Dict[str, str] = {}

        for note in notes:
            try:
                tags = json.loads(note.tags_json or "[]")
            except Exception:
                tags = []

            n_nid = _add_node(
                GraphNodeType.NOTE,
                note.id,
                note.title,
                {
                    "note_id": note.id,
                    "document_id": note.document_id,
                    "page_number": note.page_number,
                    "section": note.section,
                    "current_version": note.current_version,
                    "pinned": note.pinned,
                    "tags": tags,
                },
            )
            note_node_ids[note.id] = n_nid

            # Direct attachment edge: NOTE -> DOCUMENT
            if note.document_id and note.document_id in doc_node_ids:
                _add_edge(n_nid, doc_node_ids[note.document_id], GraphEdgeType.REFERENCES, "ATTACHED_TO")

            # Tag nodes & edges: NOTE -> TAG
            for tag in tags:
                clean_tag = str(tag).strip().lower()
                if not clean_tag:
                    continue
                if clean_tag not in tag_node_ids:
                    t_nid = _add_node(
                        GraphNodeType.TAG,
                        clean_tag,
                        f"#{clean_tag}",
                        {"tag": clean_tag},
                    )
                    tag_node_ids[clean_tag] = t_nid
                _add_edge(n_nid, tag_node_ids[clean_tag], GraphEdgeType.TAGGED, "#tag")

        # Explicit NoteLink edges (NOTE -> NOTE, NOTE -> DOCUMENT, NOTE -> RISK, NOTE -> OBLIGATION)
        note_links = db.query(NoteLink).filter(NoteLink.vault_id == vault_id).all()
        for nl in note_links:
            src_nid = note_node_ids.get(nl.source_note_id)
            if not src_nid:
                continue
            if nl.target_note_id and nl.target_note_id in note_node_ids:
                _add_edge(src_nid, note_node_ids[nl.target_note_id], GraphEdgeType.LINKS_TO, "LINKS_TO")
            if nl.target_doc_id and nl.target_doc_id in doc_node_ids:
                page_lbl = f"Page {nl.target_page}" if nl.target_page else "REFERENCES"
                _add_edge(src_nid, doc_node_ids[nl.target_doc_id], GraphEdgeType.REFERENCES, page_lbl)
            if nl.target_risk_id and nl.target_risk_id in risk_node_ids:
                _add_edge(src_nid, risk_node_ids[nl.target_risk_id], GraphEdgeType.REFERENCES, "PINNED_RISK")
            if nl.target_obligation_id and nl.target_obligation_id in obligation_node_ids:
                _add_edge(src_nid, obligation_node_ids[nl.target_obligation_id], GraphEdgeType.REFERENCES, "PINNED_DUTY")

        if nodes_map:
            db.bulk_save_objects(list(nodes_map.values()))
        if edges_map:
            db.bulk_save_objects(list(edges_map.values()))
        db.commit()

    @classmethod
    def verify_grounding_integrity(cls, db: Session, vault_id: str) -> Dict[str, Any]:
        """Verify that every GraphNode in SQLite is traceable via (entity_type, entity_id)

        to a live persisted SQLite record.
        """
        nodes = db.query(GraphNode).filter(GraphNode.vault_id == vault_id).all()

        valid_doc_ids = {r[0] for r in db.query(Document.id).filter(Document.vault_id == vault_id).all()}
        valid_run_ids = (
            {r[0] for r in db.query(ReviewRun.id).filter(ReviewRun.document_id.in_(valid_doc_ids)).all()}
            if valid_doc_ids else set()
        )
        valid_clause_ids = set()
        if valid_doc_ids:
            for r in db.query(ClauseClassification.document_id, ClauseClassification.category).filter(ClauseClassification.document_id.in_(valid_doc_ids)).all():
                valid_clause_ids.add(f"{r[0]}:{r[1]}")
            for r in db.query(RiskAuditItem.document_id, RiskAuditItem.category).filter(RiskAuditItem.document_id.in_(valid_doc_ids)).all():
                valid_clause_ids.add(f"{r[0]}:{r[1]}")
            for ob in db.query(ObligationItem).filter(ObligationItem.document_id.in_(valid_doc_ids)).all():
                c = _infer_obligation_category(ob)
                if c:
                    valid_clause_ids.add(f"{ob.document_id}:{c}")
        valid_risk_ids = (
            {r[0] for r in db.query(RiskAuditItem.id).filter(RiskAuditItem.document_id.in_(valid_doc_ids)).all()}
            if valid_doc_ids else set()
        )
        valid_obl_ids = (
            {r[0] for r in db.query(ObligationItem.id).filter(ObligationItem.document_id.in_(valid_doc_ids)).all()}
            if valid_doc_ids else set()
        )
        notes = db.query(NoteRecord).filter(NoteRecord.vault_id == vault_id).all()
        valid_note_ids = {n.id for n in notes}
        valid_tags = set()
        for n in notes:
            try:
                for t in json.loads(n.tags_json or "[]"):
                    valid_tags.add(str(t).strip().lower())
            except Exception:
                pass

        ungrounded: List[str] = []
        for gn in nodes:
            etype = gn.entity_type
            eid = gn.entity_id
            if etype == GraphNodeType.DOCUMENT.value and eid not in valid_doc_ids:
                ungrounded.append(gn.id)
            elif etype == GraphNodeType.REVIEW_RUN.value and eid not in valid_run_ids:
                ungrounded.append(gn.id)
            elif etype == GraphNodeType.CLAUSE_CATEGORY.value and eid not in valid_clause_ids:
                ungrounded.append(gn.id)
            elif etype == GraphNodeType.RISK.value and eid not in valid_risk_ids:
                ungrounded.append(gn.id)
            elif etype == GraphNodeType.OBLIGATION.value and eid not in valid_obl_ids:
                ungrounded.append(gn.id)
            elif etype == GraphNodeType.NOTE.value and eid not in valid_note_ids:
                ungrounded.append(gn.id)
            elif etype == GraphNodeType.TAG.value and eid not in valid_tags:
                ungrounded.append(gn.id)

        return {
            "is_grounded": len(ungrounded) == 0,
            "checked_nodes": len(nodes),
            "ungrounded_node_ids": ungrounded,
        }

    @classmethod
    def get_vault_graph(cls, db: Session, vault_id: str, query: Optional[str] = None) -> Dict[str, Any]:
        """Return persisted Knowledge Graph for the vault, auto-syncing if version changed or uninitialized."""
        existing_nodes = db.query(GraphNode).filter(GraphNode.vault_id == vault_id).all()
        doc_count_db = db.query(Document).filter(Document.vault_id == vault_id).count()
        note_count_db = db.query(NoteRecord).filter(NoteRecord.vault_id == vault_id).count()

        needs_sync = False
        if not existing_nodes and (doc_count_db > 0 or note_count_db > 0):
            needs_sync = True
        elif any(n.graph_version != CURRENT_GRAPH_VERSION for n in existing_nodes):
            needs_sync = True
        else:
            integrity = cls.verify_grounding_integrity(db, vault_id)
            if not integrity["is_grounded"]:
                needs_sync = True

        if needs_sync:
            cls.sync_vault_graph(db, vault_id)
            existing_nodes = db.query(GraphNode).filter(GraphNode.vault_id == vault_id).all()

        existing_edges = db.query(GraphEdge).filter(GraphEdge.vault_id == vault_id).all()

        counts = {
            GraphNodeType.DOCUMENT.value: 0,
            GraphNodeType.REVIEW_RUN.value: 0,
            GraphNodeType.CLAUSE_CATEGORY.value: 0,
            GraphNodeType.RISK.value: 0,
            GraphNodeType.OBLIGATION.value: 0,
            GraphNodeType.NOTE.value: 0,
            GraphNodeType.TAG.value: 0,
        }

        node_items = []
        matched_node_ids = []
        q_lower = query.strip().lower() if query and query.strip() else None

        for gn in existing_nodes:
            counts[gn.entity_type] = counts.get(gn.entity_type, 0) + 1
            try:
                meta = json.loads(gn.metadata_json or "{}")
            except Exception:
                meta = {}

            if q_lower:
                searchable = " ".join([
                    gn.label,
                    gn.entity_type,
                    str(meta.get("category", "")),
                    str(meta.get("risk_level", "")),
                    str(meta.get("party", "")),
                    str(meta.get("rule_id", "")),
                    str(meta.get("verbatim_text", "")),
                    " ".join(meta.get("tags", [])) if isinstance(meta.get("tags"), list) else "",
                ]).lower()
                if q_lower in searchable:
                    matched_node_ids.append(gn.id)

            node_items.append({
                "id": gn.id,
                "vault_id": gn.vault_id,
                "entity_type": gn.entity_type,
                "entity_id": gn.entity_id,
                "label": gn.label,
                "metadata": meta,
                "node_embedding": getattr(gn, "node_embedding", None),
                "graph_version": gn.graph_version,
            })

        edge_items = []
        for ge in existing_edges:
            try:
                edge_meta = json.loads(getattr(ge, "metadata_json", "{}") or "{}")
            except Exception:
                edge_meta = {}
            edge_items.append({
                "id": ge.id,
                "vault_id": ge.vault_id,
                "source_id": ge.source_id,
                "target_id": ge.target_id,
                "edge_type": ge.edge_type,
                "label": ge.label,
                "weight": ge.weight,
                "metadata": edge_meta,
                "graph_version": ge.graph_version,
            })

        return {
            "vault_id": vault_id,
            "graph_version": CURRENT_GRAPH_VERSION,
            "stats": {
                "documents": counts.get(GraphNodeType.DOCUMENT.value, 0),
                "review_runs": counts.get(GraphNodeType.REVIEW_RUN.value, 0),
                "clause_categories": counts.get(GraphNodeType.CLAUSE_CATEGORY.value, 0),
                "risks": counts.get(GraphNodeType.RISK.value, 0),
                "obligations": counts.get(GraphNodeType.OBLIGATION.value, 0),
                "notes": counts.get(GraphNodeType.NOTE.value, 0),
                "tags": counts.get(GraphNodeType.TAG.value, 0),
                "total_nodes": len(node_items),
                "total_edges": len(edge_items),
            },
            "matched_node_ids": matched_node_ids,
            "nodes": node_items,
            "edges": edge_items,
        }

    @classmethod
    def get_vault_stats(cls, db: Session, vault_id: str) -> Dict[str, Any]:
        """Return lightweight vault knowledge graph statistics without transferring full node/edge arrays."""
        graph_data = cls.get_vault_graph(db=db, vault_id=vault_id)
        return {
            "vault_id": vault_id,
            "graph_version": graph_data["graph_version"],
            "stats": graph_data["stats"],
        }


knowledge_graph_service = KnowledgeGraphService()

