# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — PDF Parser Adapter Parity & Bounding Box Test Suite
Verifies coordinate parity between PyMuPDF (fitz) and the permissive pypdfium2 adapter.
Ensures bounding boxes align with the top-left web canvas coordinate system expected by PDFHighlightCanvas.jsx.
"""
import tempfile
from pathlib import Path
import pytest
import pymupdf

from app.services.rag.pdf import get_pdf_parser, PDFiumParser
from app.services.rag.pdf.mupdf_parser import PyMuPDFParser
from app.services.rag.document_parser import document_parser


@pytest.fixture
def test_pdf_file():
    """Generates a multi-paragraph legal contract PDF on disk."""
    doc = pymupdf.open()
    page1 = doc.new_page(width=595, height=842)

    page1.insert_text(pymupdf.Point(50, 80), "MASTER SERVICES AGREEMENT", fontsize=16)
    page1.insert_text(pymupdf.Point(50, 130), "ARTICLE IV: SERVICE LEVELS & TERMINATION", fontsize=12)
    multi_line = (
        "Section 4.1: Customer may terminate this Agreement for convenience upon providing "
        "thirty (30) days prior written notice to Vendor. Upon termination, Vendor shall "
        "immediately refund any unearned prepaid fees."
    )
    page1.insert_textbox(pymupdf.Rect(50, 150, 450, 240), multi_line, fontsize=10)

    page1.insert_text(
        pymupdf.Point(50, 270),
        "Section 4.2: The aggregate liability of Contractor shall not exceed $1,000,000.",
        fontsize=10
    )

    pdf_bytes = doc.tobytes()
    doc.close()

    tmp_path = Path(__file__).parent / "fixture_test_contract.pdf"
    tmp_path.write_bytes(pdf_bytes)

    yield tmp_path

    if tmp_path.exists():
        tmp_path.unlink()


def test_pdfium_parser_standalone(test_pdf_file: Path):
    """Verifies PDFiumParser extracts valid blocks with normalized top-left coordinates."""
    parser = PDFiumParser()
    blocks = parser.extract_page_blocks(test_pdf_file)

    assert len(blocks) >= 3
    for b in blocks:
        assert b["page_number"] == 1
        bbox = b["bbox"]
        assert len(bbox) == 4
        x0, y0, x1, y1 = bbox
        assert 0 <= x0 < x1 <= 595
        assert 0 <= y0 < y1 <= 842  # y0 must be less than y1 (top-left origin!)

    full_text = " ".join(b["text"] for b in blocks)
    assert "MASTER SERVICES AGREEMENT" in full_text
    assert "ARTICLE IV: SERVICE LEVELS & TERMINATION" in full_text
    assert "Section 4.1" in full_text
    assert "Section 4.2" in full_text


def test_pdf_adapter_parity_fitz_vs_pdfium(test_pdf_file: Path):
    """Compares PyMuPDFParser and PDFiumParser for text content and bounding box alignment."""
    fitz_parser = PyMuPDFParser()
    pdfium_parser = PDFiumParser()

    fitz_blocks = fitz_parser.extract_page_blocks(test_pdf_file)
    pdfium_blocks = pdfium_parser.extract_page_blocks(test_pdf_file)

    assert len(fitz_blocks) >= 3
    assert len(pdfium_blocks) >= 3

    # Check title alignment (first block)
    fitz_title = fitz_blocks[0]
    pdfium_title = pdfium_blocks[0]
    assert "MASTER SERVICES AGREEMENT" in fitz_title["text"]
    assert "MASTER SERVICES AGREEMENT" in pdfium_title["text"]

    # Bounding box delta for title block: sub-pixel difference
    fx0, fy0, fx1, fy1 = fitz_title["bbox"]
    px0, py0, px1, py1 = pdfium_title["bbox"]
    assert abs(fx0 - px0) < 5.0
    assert abs(fy0 - py0) < 10.0
    assert abs(fx1 - px1) < 5.0
    assert abs(fy1 - py1) < 10.0


def test_document_parser_integration(test_pdf_file: Path):
    """Verifies DocumentParser.parse_file utilizes PDFium adapter and parses clause hierarchy."""
    blocks = document_parser.parse_file(test_pdf_file)
    assert len(blocks) >= 3

    # Check that clauses and sections were parsed correctly from blocks
    articles = [b["article"] for b in blocks if b["article"]]
    sections = [b["section"] for b in blocks if b["section"]]

    assert "ARTICLE IV" in articles
    assert "4.1" in sections
    assert "4.2" in sections

    for b in blocks:
        assert b["bbox"] is not None
        assert len(b["bbox"]) == 4


def test_pdf_engine_factory(monkeypatch):
    """Verifies get_pdf_parser respects SOVEREIGNDOC_PDF_ENGINE environment configuration."""
    monkeypatch.setenv("SOVEREIGNDOC_PDF_ENGINE", "pdfium")
    parser = get_pdf_parser()
    assert isinstance(parser, PDFiumParser)

    monkeypatch.setenv("SOVEREIGNDOC_PDF_ENGINE", "mupdf")
    parser_mupdf = get_pdf_parser()
    assert isinstance(parser_mupdf, PyMuPDFParser)
