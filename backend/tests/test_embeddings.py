# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — FastEmbed ONNX Local Embedding Tests
"""
from pathlib import Path
import pytest

from app.services.rag.embedding_service import FastEmbedService, embedding_service


def test_embedding_generation_shape():
    """Verifies FastEmbed BGE-small-en-v1.5 generates 384-dimensional dense vectors."""
    texts = [
        "Each party agrees to maintain confidentiality of proprietary data.",
        "Customer may terminate this agreement on thirty days prior written notice."
    ]
    vectors = embedding_service.embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384
    assert isinstance(vectors[0][0], float)


def test_query_embedding():
    """Verifies single query embedding generates 384-dimensional dense vector."""
    query_vector = embedding_service.embed_query("What are the termination triggers?")
    assert len(query_vector) == 384
    assert isinstance(query_vector[0], float)


def test_embedding_fail_closed_when_model_not_cached(monkeypatch, tmp_path: Path):
    """Verifies FastEmbedService fails closed offline by default instead of downloading."""
    monkeypatch.delenv("SOVEREIGNDOC_ALLOW_MODEL_DOWNLOADS", raising=False)
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path / "empty_cache"))
    svc = FastEmbedService(model_name="BAAI/bge-small-en-v1.5")
    with pytest.raises(RuntimeError, match="fail-closed zero-egress mode"):
        _ = svc.model

