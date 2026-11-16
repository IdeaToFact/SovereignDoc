# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Hybrid BM25 & Sequential Window Expansion Tests
"""
import tempfile
from pathlib import Path
from app.services.rag.bm25_index import BM25Index
from app.services.rag.chunker import chunker


def test_bm25_lexical_ranking():
    """Verifies SQLite/Python BM25 scores exact keyword hits."""
    tmp_dir = Path(tempfile.mkdtemp())
    index = BM25Index(tmp_dir)
    docs = [
        {"id": "c1", "text": "Customer may terminate for convenience upon sixty days prior written notice."},
        {"id": "c2", "text": "Contractor shall indemnify company against third-party patent claims."},
        {"id": "c3", "text": "Books and records must be retained for seven years."}
    ]
    index.add_chunks(docs)

    results = index.search_sparse("terminate convenience notice", top_k=2)
    assert len(results) > 0
    assert results[0]["chunk_id"] == "c1"


def test_sequential_window_expansion():
    """Verifies sequential chunker preserves previous_chunk_id and next_chunk_id pointers."""
    blocks = [
        {"text": "Article 1. Scope. Vendor provides consulting services.", "page_number": 1, "bbox": None, "section": "1", "section_title": "Scope"},
        {"text": "Article 2. Fees. Customer pays invoice in thirty days.", "page_number": 1, "bbox": None, "section": "2", "section_title": "Fees"},
        {"text": "Article 3. Warranties. Vendor warrants good workmanship.", "page_number": 2, "bbox": None, "section": "3", "section_title": "Warranties"},
        {"text": "Article 4. Remedies. Remedies are exclusive.", "page_number": 2, "bbox": None, "section": "4", "section_title": "Remedies"}
    ]
    chunks = chunker.chunk_document("doc_window_test", "vault_test", "contract.pdf", blocks)
    assert len(chunks) >= 2

    # Check pointer chaining
    for i in range(len(chunks)):
        if i > 0:
            assert chunks[i]["previous_chunk_id"] == chunks[i - 1]["id"]
        if i < len(chunks) - 1:
            assert chunks[i]["next_chunk_id"] == chunks[i + 1]["id"]


def test_bm25_document_scoping():
    """Verifies BM25 index correctly scopes sparse keyword searches to a specific document."""
    tmp_dir = Path(tempfile.mkdtemp())
    index = BM25Index(tmp_dir)
    docs = [
        {"id": "docA_p1_c1", "document_id": "docA", "text": "Licensor indemnifies Licensee against IP infringement."},
        {"id": "docB_p1_c1", "document_id": "docB", "text": "Customer shall indemnify Supplier against IP infringement and damages."},
        {"id": "docB_p1_c2", "document_id": "docB", "text": "Supplier liability is limited to twelve months of fees."}
    ]
    index.add_chunks(docs)

    # Scoped to docA: should only return docA chunk even if docB has more terms
    results_a = index.search_sparse("indemnify IP infringement", top_k=5, document_id="docA")
    assert len(results_a) == 1
    assert results_a[0]["chunk_id"] == "docA_p1_c1"

    # Scoped to docB: should only return docB chunks
    results_b = index.search_sparse("indemnify IP infringement", top_k=5, document_id="docB")
    assert len(results_b) == 1
    assert results_b[0]["chunk_id"] == "docB_p1_c1"

    # Vault-wide (document_id=None): returns both
    results_all = index.search_sparse("indemnify IP infringement", top_k=5, document_id=None)
    assert len(results_all) == 2


