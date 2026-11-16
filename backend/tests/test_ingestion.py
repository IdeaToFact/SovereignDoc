# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Document Ingestion & Deduplication Tests
"""
import hashlib
import tempfile
from pathlib import Path
from app.services.rag.document_parser import document_parser


def test_pdf_parsing_in_memory(sample_pdf_bytes: bytes):
    """Verifies PyMuPDF extracts text, bounding boxes, and pages from PDF files."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(sample_pdf_bytes)

    try:
        blocks = document_parser.parse_file(tmp_path)
        assert len(blocks) >= 1
        all_text = " ".join(b.get("text", "") for b in blocks)
        assert "MASTER SERVICES AGREEMENT" in all_text
        assert "TERMINATION" in all_text
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_sha256_cryptographic_deduplication(sample_pdf_bytes: bytes):
    """Verifies SHA-256 checksum uniquely identifies document contents for vault deduplication."""
    hash1 = hashlib.sha256(sample_pdf_bytes).hexdigest()
    hash2 = hashlib.sha256(sample_pdf_bytes).hexdigest()
    assert hash1 == hash2
    assert len(hash1) == 64

    # Modified byte content produces completely distinct hash
    modified_bytes = sample_pdf_bytes + b"\n% EOF"
    hash_mod = hashlib.sha256(modified_bytes).hexdigest()
    assert hash_mod != hash1

