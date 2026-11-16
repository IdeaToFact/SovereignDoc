# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Cross-Encoder Neural Reranking Tests
"""
from pathlib import Path
import pytest

from app.services.rag.reranker_service import CrossEncoderRerankerService, reranker_service


def test_cross_encoder_reranking_accuracy():
    """Verifies Cross-Encoder scores relevant contract clauses significantly higher than irrelevant ones."""
    query = "What is the liability cap under the agreement?"
    documents = [
        "Contractor aggregate liability for breach of contract shall not exceed $1,000,000.",
        "Delaware law governs all disputes without regard to conflict of laws principles.",
        "Parties may exchange written notices by certified registered mail."
    ]

    scores = reranker_service.rerank(query, documents)
    assert len(scores) == 3
    # The first document (liability cap) should have the highest semantic score
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]


def test_reranker_fail_closed_when_model_not_cached(monkeypatch, tmp_path: Path):
    """Verifies CrossEncoderRerankerService fails closed offline by default instead of downloading."""
    monkeypatch.delenv("SOVEREIGNDOC_ALLOW_MODEL_DOWNLOADS", raising=False)
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path / "empty_cache"))
    svc = CrossEncoderRerankerService(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
    with pytest.raises(RuntimeError, match="fail-closed zero-egress mode"):
        _ = svc.model

