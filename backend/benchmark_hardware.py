# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

r"""Standalone CLI Hardware & 25-Page End-to-End Document Benchmark Utility (Milestone 6).

Usage:
    .\backend\.venv\Scripts\python.exe backend/benchmark_hardware.py
"""
import json
import sys
from pathlib import Path

# Ensure repo root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent
for p in (str(REPO_ROOT), str(BACKEND_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.benchmark_service import benchmark_service  # noqa: E402


def main() -> int:
    print("=" * 72)
    print("  SovereignDoc Local Hardware & 25-Page E2E Pipeline Benchmark")
    print("=" * 72)

    res = benchmark_service.run_benchmark()
    hw = res["hardware"]
    e2e = res["end_to_end_document_benchmark"]
    comp = res["components"]
    mem = res["process_memory"]

    print(f"  OS / Architecture   : {hw['os']} ({hw['architecture']})")
    print(f"  Primary Accelerator : {hw['accelerator']['primary']}")
    print(f"  CPU Cores           : {hw['cpu']['physical_cores']} Physical / {hw['cpu']['logical_cores']} Logical")
    print(f"  System RAM          : {hw['ram']['available_gb']} GB Free / {hw['ram']['total_gb']} GB Total")
    print(f"  Process Memory RSS  : {mem['rss_after_mb']} MB")
    print("-" * 72)
    print(f"  HEADLINE: 25-Page Contract End-to-End Benchmark : {e2e['end_to_end_ms']} ms")
    print(f"    - Parse & Structure Chunking (25 pages)       : {e2e['stages_ms']['parse_and_chunk_ms']} ms")
    print(f"    - FastEmbed ONNX Embeddings ({comp['onnx_embeddings']['chunks_per_sec']} chunks/s) : {e2e['stages_ms']['embedding_ms']} ms")
    print(f"    - Cross-Encoder Reranking ({comp['cross_encoder_reranker']['pairs_per_sec']} pairs/s)    : {e2e['stages_ms']['rerank_ms']} ms")
    print(f"    - Deterministic Contract ReviewRun            : {e2e['stages_ms']['contract_review_ms']} ms")
    print(f"    - 7-Entity Knowledge Graph Sync & Grounding   : {e2e['stages_ms']['knowledge_graph_sync_ms']} ms")
    print("-" * 72)
    print(f"  Extracted Entities  : {comp['contract_intelligence']['risks_detected']} Risks, "
          f"{comp['contract_intelligence']['obligations_extracted']} Obligations, "
          f"{comp['knowledge_graph']['total_nodes']} Graph Nodes ({comp['knowledge_graph']['total_edges']} Edges)")
    print(f"  Grounding Integrity : {'PASS (100% SQLite Grounded)' if comp['knowledge_graph']['is_grounded'] else 'FAIL'}")
    print("=" * 72)

    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())

