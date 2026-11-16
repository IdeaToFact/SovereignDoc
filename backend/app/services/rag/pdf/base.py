# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Abstract Base Class for PDF Document Parsers.
Standardizes text block extraction and web-canvas coordinate normalization [x0, y0, x1, y1].
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class BasePDFParser(ABC):
    """Abstract PDF parsing engine interface."""

    @abstractmethod
    def extract_page_blocks(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract structured text blocks from a PDF file.

        Returns:
            List of dicts, each with:
            - page_number: int (1-based)
            - bbox: List[float] [x0, y0, x1, y1] normalized to top-left origin (points, 1/72 inch)
            - text: str (raw text content of the block)
        """
        pass

