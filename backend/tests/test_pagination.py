# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Synthetic Pagination & Header Alignment Tests
"""
import tempfile
from pathlib import Path
import docx
from docx.oxml import OxmlElement
from app.services.rag.document_parser import document_parser
from packages.contract_intelligence.enums import PaginationSource


def test_pagination_source_enum():
    """Verifies standard pagination source types."""
    assert PaginationSource.WORD_PAGE_BREAK == "WORD_PAGE_BREAK"
    assert PaginationSource.SECTION_BREAK == "SECTION_BREAK"
    assert PaginationSource.VIRTUAL_LAYOUT == "VIRTUAL_LAYOUT"


def test_docx_synthetic_pagination():
    """Verifies DocumentParser synthetic pagination for DOCX files."""
    doc = docx.Document()

    # Generate 5 paragraphs separated by lastRenderedPageBreak
    for i in range(1, 6):
        p = doc.add_paragraph(f"{i}. Clause {i}. Text of section {i} for pagination validation.")
        if i > 1:
            r = p._element.xpath("./w:r")[0]
            r.insert(0, OxmlElement("w:lastRenderedPageBreak"))

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        doc.save(str(tmp_path))
        res = document_parser.paginate_docx(tmp_path, include_html=True)
        assert res["pagination_source"] == "WORD_PAGE_BREAK"
        assert len(res["pages"]) >= 5
        assert len(res["blocks"]) >= 5
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

