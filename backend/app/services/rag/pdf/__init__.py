# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
PDF Parser Adapter Module.
Supports pluggable PDF parsing engines:
- 'pdfium': Permissive Apache-2.0 / BSD-3-Clause engine (pypdfium2 / Chrome PDFium).
            Default for both Commercial and Community editions.
- 'mupdf':  GNU AGPLv3 engine (PyMuPDF / Artifex).
"""
import os
from typing import Optional
from .base import BasePDFParser
from .pdfium_parser import PDFiumParser


def is_commercial_edition() -> bool:
    """Check if SovereignDoc is running in Commercial Pro or Enterprise mode."""
    edition = os.getenv("SOVEREIGNDOC_EDITION", "").strip().lower()
    if edition in {"pro", "enterprise", "commercial"}:
        return True
    return os.getenv("SOVEREIGNDOC_COMMERCIAL_MODE", "").strip().lower() in {"1", "true", "yes"}


def get_pdf_parser(engine: Optional[str] = None) -> BasePDFParser:
    """
    Return the configured PDF parser adapter.
    Defaults to 'pdfium' for clean permissive licensing across editions.
    In commercial editions, attempting to load PyMuPDF ('mupdf') raises RuntimeError.
    """
    if engine is None:
        engine = os.getenv("SOVEREIGNDOC_PDF_ENGINE", "pdfium").lower().strip()

    if is_commercial_edition():
        if engine == "mupdf":
            raise RuntimeError(
                "PyMuPDF (fitz) is copyleft GNU AGPLv3 and is strictly prohibited in Commercial Pro/Enterprise editions. "
                "Use the default clean-room 'pdfium' engine."
            )
        return PDFiumParser()

    if engine == "mupdf":
        try:
            from .mupdf_parser import PyMuPDFParser
            return PyMuPDFParser()
        except ImportError:
            return PDFiumParser()

    return PDFiumParser()


__all__ = ["BasePDFParser", "PDFiumParser", "get_pdf_parser", "is_commercial_edition"]

