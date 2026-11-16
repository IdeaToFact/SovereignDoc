# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Shared Pytest Fixtures and Global Test Configuration
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
import pymupdf

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

# Ensure isolated test data directory before any app imports to avoid ChromaDB lock conflicts
TEST_DATA_DIR = Path(tempfile.gettempdir()) / "sovereigndoc_pytest_data"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["SOVEREIGNDOC_BASE_DATA_DIR"] = str(TEST_DATA_DIR)
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:11434"
os.environ["SOVEREIGNDOC_OLLAMA_URL"] = "http://127.0.0.1:11434"

# Ensure backend and repository root are on sys.path
TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
REPO_ROOT = BACKEND_DIR.parent

for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base


@pytest.fixture(scope="session")
def client():
    """Shared FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def in_memory_db():
    """Provides a fresh isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_pdf_bytes():
    """Generates an in-memory test PDF with standard legal clause structure."""
    doc = pymupdf.open()
    page1 = doc.new_page(width=595, height=842)

    page1.insert_text(pymupdf.Point(50, 80), "MASTER SERVICES AGREEMENT", fontsize=16)
    page1.insert_text(pymupdf.Point(50, 130), "ARTICLE IV: SERVICE LEVELS & TERMINATION", fontsize=12)
    page1.insert_text(
        pymupdf.Point(50, 160),
        "Section 4.1: Customer may terminate this Agreement for convenience upon providing 30 days prior written notice. "
        "Upon termination, Vendor shall immediately refund unearned fees.",
        fontsize=10
    )
    page1.insert_text(
        pymupdf.Point(50, 220),
        "Section 4.2: The aggregate liability of Contractor under Section 4.1 shall not exceed $1,000,000 in U.S. Dollars.",
        fontsize=10
    )
    page1.insert_text(
        pymupdf.Point(50, 280),
        "Section 4.3: Contractor must provide financial, compliance, and other records within fifteen (15) business days.",
        fontsize=10
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_contract_text():
    """Provides standard synthetic multi-clause legal text for deterministic audits."""
    return (
        "MASTER SERVICES AGREEMENT\n\n"
        "SECTION 1. CONFIDENTIALITY.\n"
        "Each party agrees to maintain in strict confidence all proprietary technical and business information.\n\n"
        "SECTION 2. TERMINATION.\n"
        "Either party may terminate this Agreement without cause upon giving thirty (30) days prior written notice.\n\n"
        "SECTION 3. INDEMNIFICATION.\n"
        "Contractor shall defend, indemnify, and hold harmless Company from any third-party claims arising from negligence.\n\n"
        "SECTION 4. AUDIT RIGHTS.\n"
        "Contractor must allow Company to review books and records relating to Services within fifteen (15) business days.\n\n"
        "SECTION 5. GOVERNING LAW.\n"
        "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware.\n"
    )

