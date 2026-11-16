# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import psutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure repository root (containing 'packages') is in sys.path
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from app.db.database import Base
from app.db.models import (
    Vault,
    Document,
    Chunk,
    ReviewRun,
    ClauseClassification,
    RiskAuditItem,
    ObligationItem,
    NoteRecord,
    NoteLink,
)
from app.services.hardware_info import hardware_profiler
from app.services.rag.chunker import chunker
from app.services.rag.embedding_service import embedding_service
from app.services.rag.reranker_service import reranker_service
from app.services.second_brain.graph_service import knowledge_graph_service
from packages.contract_intelligence.classifiers import clause_classifier
from packages.contract_intelligence.obligations import obligations_extractor
from packages.contract_intelligence.plugin_sdk.registry import CapabilityRegistry
import packages.contract_intelligence.risk_rules  # noqa: F401


CLAUSE_TEMPLATES = [
    (
        "1. Confidentiality Obligations",
        "Receiving Party shall hold all Confidential Information in strict confidence for a period of five (5) years "
        "and shall not disclose such Confidential Information to any third party without prior written consent.",
    ),
    (
        "2. Indemnification",
        "Vendor shall indemnify, defend, and hold harmless Client from and against any and all third-party claims, "
        "liabilities, losses, and unlimited damages arising out of Vendor's breach or intellectual property infringement.",
    ),
    (
        "3. Limitation of Liability",
        "Notwithstanding anything to the contrary, Vendor's liability under this Agreement shall be uncapped and "
        "include consequential and incidental damages without limitation.",
    ),
    (
        "4. Term and Termination",
        "Either Party may terminate this Agreement for convenience upon fifteen (15) days prior written notice, "
        "and this Agreement shall automatically renew for successive twenty-four (24) month terms unless terminated.",
    ),
    (
        "5. Payment and Audit Rights",
        "Client shall pay all undisputed invoices within forty-five (45) days of receipt. Vendor shall maintain "
        "complete financial records and submit quarterly compliance reports within ten (10) business days.",
    ),
]


class BenchmarkService:
    """Hardware & End-to-End Document Pipeline Benchmark Suite (Milestone 6).
    Measures local CPU/CUDA/Metal throughput across ONNX embeddings, Cross-Encoder reranking,
    deterministic Contract ReviewRun, 7-Entity Knowledge Graph grounding, and a 25-page E2E contract run.
    """

    @classmethod
    def _build_25_page_synthetic_blocks(cls) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        for page_num in range(1, 26):
            sec_title, body_text = CLAUSE_TEMPLATES[(page_num - 1) % len(CLAUSE_TEMPLATES)]
            numbered_sec = f"Section {page_num}. {sec_title.split('. ', 1)[-1]}"
            blocks.append({
                "page_number": page_num,
                "article": f"Article {((page_num - 1) // 5) + 1}",
                "section": numbered_sec,
                "subsection": f"{page_num}.1",
                "section_title": numbered_sec,
                "bbox": None,
                "text": f"{numbered_sec}. {body_text} (Contract Page {page_num} of 25).",
            })
        return blocks

    @classmethod
    def run_benchmark(cls, include_llm: bool = False) -> Dict[str, Any]:
        started_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        hw_profile = hardware_profiler.get_hardware_profile()
        proc = psutil.Process(os.getpid())
        mem_before = proc.memory_info()

        # Warm up lazy ONNX models once so benchmark reflects steady-state local inference
        _ = embedding_service.embed_texts(["Warmup legal clause text."])
        _ = reranker_service.rerank("liability cap", ["Warmup candidate clause."])

        # =====================================================================
        # Stage 1: 25-Page End-to-End Document Pipeline Benchmark
        # =====================================================================
        e2e_start = time.perf_counter()

        # 1a. Parse & Chunk 25-page contract
        t0 = time.perf_counter()
        blocks_25 = cls._build_25_page_synthetic_blocks()
        raw_chunks = chunker.chunk_document(
            doc_id="bench_doc_25p",
            vault_id="bench_vault",
            doc_name="Enterprise_MSA_25Pages.docx",
            blocks=blocks_25,
        )
        parse_and_chunk_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        # 1b. FastEmbed ONNX Embeddings across all 25 pages
        t1 = time.perf_counter()
        chunk_texts = [c["text"] for c in raw_chunks]
        vectors = embedding_service.embed_texts(chunk_texts)
        embedding_ms = round((time.perf_counter() - t1) * 1000.0, 2)

        # 1c. Cross-Encoder Reranking on top 10 candidate clauses
        t2 = time.perf_counter()
        candidate_texts = chunk_texts[:10]
        rerank_scores = reranker_service.rerank(
            "What is the limitation of liability and indemnification cap?",
            candidate_texts,
        )
        rerank_ms = round((time.perf_counter() - t2) * 1000.0, 2)

        # 1d. Deterministic Contract Intelligence ReviewRun (Classify + RiskRules + Obligations)
        t3 = time.perf_counter()
        chunk_objs = [
            SimpleNamespace(
                id=c["id"],
                chunk_index=c["chunk_index"],
                text=c["text"],
                page_number=c["page_number"],
                section=c["section"],
                bbox_json=c["bbox_json"],
            )
            for c in raw_chunks
        ]
        classified_map = clause_classifier.classify_chunks(chunk_objs, "bench_doc_25p")
        risk_findings = []
        for rule in CapabilityRegistry.get_risk_rules():
            risk_findings.extend(rule.evaluate(chunk_objs, classified_map))
        extracted_obls = obligations_extractor.extract_obligations(chunk_objs, "bench_doc_25p")
        contract_review_ms = round((time.perf_counter() - t3) * 1000.0, 2)

        # 1e. 7-Entity Knowledge Graph Sync & Grounding Verification (In-Memory SQLite)
        t4 = time.perf_counter()
        mem_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=mem_engine)
        MemSession = sessionmaker(bind=mem_engine)
        db = MemSession()
        try:
            vault = Vault(id="bench_vault", name="Benchmark Vault")
            doc = Document(
                id="bench_doc_25p",
                vault_id="bench_vault",
                filename="Enterprise_MSA_25Pages.docx",
                file_type=".docx",
                file_size_bytes=64000,
                checksum_sha256="bench_sha256",
                page_count=25,
                chunk_count=len(raw_chunks),
            )
            db.add(vault)
            db.add(doc)

            for c in raw_chunks:
                db.add(
                    Chunk(
                        id=c["id"],
                        document_id="bench_doc_25p",
                        vault_id="bench_vault",
                        chunk_index=c["chunk_index"],
                        page_number=c["page_number"],
                        section=c["section"],
                        text=c["text"],
                        char_length=c["char_length"],
                        token_count=c["token_count"],
                    )
                )

            for category, items in classified_map.items():
                for item in items:
                    db.add(
                        ClauseClassification(
                            id=f"cc_{uuid.uuid4().hex[:12]}",
                            document_id="bench_doc_25p",
                            chunk_id=item.chunk_id,
                            category=item.category.value,
                            confidence=item.confidence,
                            detection_method=item.detection_method.value,
                        )
                    )

            run_id = "bench_run_1"
            db.add(
                ReviewRun(
                    id=run_id,
                    document_id="bench_doc_25p",
                    classifier_version="1.0.0",
                    ruleset_version="1.0.0",
                    total_risks=len(risk_findings),
                    total_obligations=len(extracted_obls),
                    status="COMPLETED",
                )
            )

            first_risk_id = None
            for f in risk_findings:
                rid = f"risk_{uuid.uuid4().hex[:12]}"
                if first_risk_id is None:
                    first_risk_id = rid
                db.add(
                    RiskAuditItem(
                        id=rid,
                        review_run_id=run_id,
                        document_id="bench_doc_25p",
                        rule_id=f.rule_id,
                        category=f.category.value if hasattr(f.category, "value") else str(f.category),
                        risk_level=f.risk_level.value if hasattr(f.risk_level, "value") else str(f.risk_level),
                        issue_title=f.issue_title,
                        description=f.description,
                        page_number=f.page_number,
                        section=f.section,
                        verbatim_text=f.verbatim_text,
                        confidence=f.confidence,
                        detection_method=f.detection_method.value if hasattr(f.detection_method, "value") else str(f.detection_method),
                    )
                )

            for o in extracted_obls:
                db.add(
                    ObligationItem(
                        id=f"obl_{uuid.uuid4().hex[:12]}",
                        review_run_id=run_id,
                        document_id="bench_doc_25p",
                        party=o.party.value if hasattr(o.party, "value") else str(o.party),
                        action_required=o.action_required,
                        trigger_or_condition=o.trigger_or_condition,
                        deadline_or_cadence=o.deadline_or_cadence,
                        page_number=o.page_number,
                        section=o.section,
                        verbatim_text=o.verbatim_text,
                        confidence=o.confidence,
                        detection_method=o.detection_method.value if hasattr(o.detection_method, "value") else str(o.detection_method),
                    )
                )

            note = NoteRecord(
                id="bench_note_1",
                vault_id="bench_vault",
                document_id="bench_doc_25p",
                page_number=2,
                title="Benchmark Risk Audit Note",
                content_md="Pinned finding from [[Enterprise_MSA_25Pages.docx#page=2]] #liability #audit",
                tags_json=json.dumps(["liability", "audit"]),
                current_version=1,
            )
            db.add(note)
            if first_risk_id:
                db.add(
                    NoteLink(
                        id="bench_link_1",
                        vault_id="bench_vault",
                        source_note_id="bench_note_1",
                        target_doc_id="bench_doc_25p",
                        target_risk_id=first_risk_id,
                        target_page=2,
                        link_text="Enterprise_MSA_25Pages.docx#page=2",
                        link_type="RISK",
                    )
                )
            db.commit()

            knowledge_graph_service.sync_vault_graph(db, "bench_vault")
            grounding = knowledge_graph_service.verify_grounding_integrity(db, "bench_vault")
            graph_payload = knowledge_graph_service.get_vault_graph(db, "bench_vault")
        finally:
            db.close()

        knowledge_graph_sync_ms = round((time.perf_counter() - t4) * 1000.0, 2)
        end_to_end_ms = round((time.perf_counter() - e2e_start) * 1000.0, 2)

        mem_after = proc.memory_info()

        num_chunks = max(1, len(raw_chunks))
        ms_per_chunk = round(embedding_ms / num_chunks, 2)
        chunks_per_sec = round((num_chunks / max(0.0001, embedding_ms / 1000.0)), 2)

        num_pairs = max(1, len(candidate_texts))
        ms_per_pair = round(rerank_ms / num_pairs, 2)
        pairs_per_sec = round((num_pairs / max(0.0001, rerank_ms / 1000.0)), 2)

        return {
            "benchmark_version": "1.0",
            "timestamp": started_iso,
            "end_to_end_document_benchmark": {
                "document_pages": 25,
                "chunks_processed": len(raw_chunks),
                "end_to_end_ms": end_to_end_ms,
                "stages_ms": {
                    "parse_and_chunk_ms": parse_and_chunk_ms,
                    "embedding_ms": embedding_ms,
                    "rerank_ms": rerank_ms,
                    "contract_review_ms": contract_review_ms,
                    "knowledge_graph_sync_ms": knowledge_graph_sync_ms,
                },
            },
            "components": {
                "onnx_embeddings": {
                    "model_name": embedding_service.model_name,
                    "vector_dimensions": len(vectors[0]) if vectors else 384,
                    "chunks_tested": len(raw_chunks),
                    "total_ms": embedding_ms,
                    "ms_per_chunk": ms_per_chunk,
                    "chunks_per_sec": chunks_per_sec,
                },
                "cross_encoder_reranker": {
                    "model_name": reranker_service.model_name,
                    "pairs_tested": len(rerank_scores),
                    "total_ms": rerank_ms,
                    "ms_per_pair": ms_per_pair,
                    "pairs_per_sec": pairs_per_sec,
                },
                "contract_intelligence": {
                    "clauses_tested": len(raw_chunks),
                    "risks_detected": len(risk_findings),
                    "obligations_extracted": len(extracted_obls),
                    "total_ms": contract_review_ms,
                },
                "knowledge_graph": {
                    "graph_version": graph_payload["graph_version"],
                    "total_nodes": graph_payload["stats"]["total_nodes"],
                    "total_edges": graph_payload["stats"]["total_edges"],
                    "is_grounded": grounding["is_grounded"],
                    "total_ms": knowledge_graph_sync_ms,
                },
            },
            "process_memory": {
                "rss_before_mb": round(mem_before.rss / (1024**2), 2),
                "rss_after_mb": round(mem_after.rss / (1024**2), 2),
                "vms_mb": round(mem_after.vms / (1024**2), 2),
            },
            "hardware": hw_profile,
        }


benchmark_service = BenchmarkService()

