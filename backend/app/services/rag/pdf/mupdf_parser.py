# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
PyMuPDF (fitz) PDF Parser Adapter.
Licensed under GNU AGPLv3 (Artifex MuPDF). Used as the legacy / optional engine in Community Edition.
"""
from pathlib import Path
from typing import Any, Dict, List
import pymupdf

from .base import BasePDFParser


class PyMuPDFParser(BasePDFParser):
    """PDF parser implementation using PyMuPDF (fitz)."""

    def extract_page_blocks(self, file_path: Path) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        doc = pymupdf.open(str(file_path))

        for page_idx, page in enumerate(doc, start=1):
            page_blocks = page.get_text("blocks")
            for b in page_blocks:
                # b = (x0, y0, x1, y1, text, block_no, block_type)
                # block_type == 0 is text
                if len(b) > 4 and b[6] == 0:
                    raw_text = b[4].strip()
                    if not raw_text:
                        continue
                    bbox = [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]
                    blocks.append({
                        "page_number": page_idx,
                        "bbox": bbox,
                        "text": raw_text
                    })
        doc.close()
        return blocks

