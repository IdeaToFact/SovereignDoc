# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test License & Governance Guardrails for SovereignDoc.
Guarantees compliance with open-core dual-licensing:
- Core Project: GNU AGPLv3 (SPDX: AGPL-3.0-only) stewarded by Idea To Fact LLC
- Backend & Frontend Dependencies: Explicitly audited in THIRD_PARTY_NOTICES.md
  (with PyMuPDF isolated to Community Edition and flagged for Commercial substitution)
- Legal Artifacts: LICENSE, NOTICE, DISCLAIMER.md, PRIVACY.md, THIRD_PARTY_NOTICES.md,
  EDITIONS.md, TRADEMARKS.md, COMMERCIAL_TERMS_FRAMEWORK.md, CONTRIBUTING.md,
  SECURITY.md, CODE_OF_CONDUCT.md, CHANGELOG.md
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Packages that must never be silently added without explicit commercial review
PROHIBITED_NEW_COPYLEFT_PATTERNS = [
    "pytesseract",
]

# Known backend dependencies in backend/requirements.txt
ALLOWED_BACKEND_DEPENDENCIES = {
    "fastapi": "MIT",
    "uvicorn": "BSD-3-Clause",
    "httpx": "BSD-3-Clause",
    "pydantic": "MIT",
    "pydantic-settings": "MIT",
    "psutil": "BSD-3-Clause",
    "pytest": "MIT",
    "python-multipart": "Apache-2.0",
    "sqlalchemy": "MIT",
    "pymupdf": "AGPL-3.0-or-Artifex-Commercial (Community Edition only; swap for Commercial builds)",
    "pypdfium2": "BSD-3-Clause / Apache-2.0",
    "python-docx": "MIT",
    "fastembed": "Apache-2.0",
    "chromadb": "Apache-2.0",
    "rank-bm25": "Apache-2.0",
    "mammoth": "BSD-2-Clause",
}

# Known frontend dependencies in frontend/package.json
ALLOWED_FRONTEND_DEPENDENCIES = {
    "mammoth": "BSD-2-Clause",
    "pdfjs-dist": "Apache-2.0",
    "react": "MIT",
    "react-dom": "MIT",
    "@types/react": "MIT",
    "@types/react-dom": "MIT",
    "@vitejs/plugin-react": "MIT",
    "oxlint": "MIT",
    "vite": "MIT",
}


def _normalize_req_name(line: str) -> str:
    base = re.split(r"[<>=!~;\[]", line.strip(), maxsplit=1)[0]
    return base.strip().lower()


def test_backend_requirements_audited() -> None:
    req_path = ROOT / "backend" / "requirements.txt"
    assert req_path.exists(), "backend/requirements.txt must exist"

    for raw_line in req_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        dep_name = _normalize_req_name(line)
        for prohibited in PROHIBITED_NEW_COPYLEFT_PATTERNS:
            assert prohibited not in dep_name, f"Prohibited package '{dep_name}' found in requirements.txt!"
        assert (
            dep_name in ALLOWED_BACKEND_DEPENDENCIES
        ), f"Backend dependency '{dep_name}' must be reviewed and added to ALLOWED_BACKEND_DEPENDENCIES."


def test_frontend_dependencies_audited() -> None:
    pkg_path = ROOT / "frontend" / "package.json"
    assert pkg_path.exists(), "frontend/package.json must exist"

    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    all_deps = {
        **data.get("dependencies", {}),
        **data.get("devDependencies", {}),
    }
    for dep_name in all_deps:
        assert (
            dep_name in ALLOWED_FRONTEND_DEPENDENCIES
        ), f"Frontend dependency '{dep_name}' must be reviewed and added to ALLOWED_FRONTEND_DEPENDENCIES."


def test_license_and_governance_files_exist() -> None:
    # LICENSE must be AGPLv3 full text
    license_file = ROOT / "LICENSE"
    assert license_file.exists() and license_file.stat().st_size > 30000
    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in license_file.read_text(encoding="utf-8")

    # NOTICE
    notice_text = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "SovereignDoc Community Edition" in notice_text
    assert "AGPL-3.0-only" in notice_text
    assert "Idea To Fact LLC" in notice_text

    # DISCLAIMER.md
    disclaimer_text = (ROOT / "DISCLAIMER.md").read_text(encoding="utf-8")
    assert "No Legal Advice" in disclaimer_text
    assert "GNU Affero General Public License" in disclaimer_text
    assert "AGPLV3 SECTIONS 7 OR 10" in disclaimer_text

    # PRIVACY.md
    privacy_text = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
    assert ".sovereigndoc" in privacy_text
    assert "OLLAMA_BASE_URL" in privacy_text

    # THIRD_PARTY_NOTICES.md
    tp_text = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "PyMuPDF" in tp_text
    assert "pdfjs-dist" in tp_text
    assert "python-multipart" in tp_text

    # docs/EDITIONS.md
    editions_text = (ROOT / "docs" / "EDITIONS.md").read_text(encoding="utf-8")
    assert "AGPLv3 Community Edition" in editions_text
    assert "Commercial Pro Edition" in editions_text
    assert "Commercial Enterprise Edition" in editions_text
    assert "packages/contract_intelligence/plugin_sdk/" in editions_text

    # docs/TRADEMARKS.md
    tm_text = (ROOT / "docs" / "TRADEMARKS.md").read_text(encoding="utf-8")
    assert "SovereignDoc" in tm_text
    assert "AirGap Axis" in tm_text
    assert "Idea To Fact LLC" in tm_text

    # docs/commercial/COMMERCIAL_TERMS_FRAMEWORK.md
    ct_text = (ROOT / "docs" / "commercial" / "COMMERCIAL_TERMS_FRAMEWORK.md").read_text(encoding="utf-8")
    assert "AGPLv3" in ct_text
    assert "twelve (12) months" in ct_text

    # CONTRIBUTING.md
    contrib_text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "Contributor License Agreement (CLA v1.0)" in contrib_text
    assert "Corporate CLA" in contrib_text

    # SECURITY.md
    sec_text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "Multi-Layer Zero-Egress Guard" in sec_text
    assert "Safe Harbor" in sec_text

    # CODE_OF_CONDUCT.md
    assert "Contributor Covenant" in (ROOT / "CODE_OF_CONDUCT.md").read_text(encoding="utf-8")

    # CHANGELOG.md
    assert "Keep a Changelog" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_source_files_have_spdx_headers() -> None:
    skip_dirs = {".venv", "__pycache__", ".pytest_cache", "node_modules", "dist"}
    source_files = []
    for base in [ROOT / "backend", ROOT / "packages"]:
        for path in base.rglob("*.py"):
            if not any(part in skip_dirs for part in path.parts):
                source_files.append(path)
    for path in (ROOT / "frontend" / "src").rglob("*"):
        if path.suffix in {".js", ".jsx", ".css"} and not any(part in skip_dirs for part in path.parts):
            source_files.append(path)

    assert len(source_files) >= 100
    for path in source_files:
        head = "\n".join(path.read_text(encoding="utf-8-sig").splitlines()[:6])
        assert "SPDX-License-Identifier: AGPL-3.0-only" in head, f"Missing SPDX header in {path}"
        assert "Copyright (C) 2026 Idea To Fact LLC" in head, f"Missing Copyright header in {path}"
        assert "All rights reserved" not in head, f"Unexpected 'All rights reserved' in {path}"


def test_fail_closed_offline_model_defaults() -> None:
    import os
    from app.config import settings

    assert settings.allow_model_downloads is False
    if os.environ.get("SOVEREIGNDOC_ALLOW_MODEL_DOWNLOADS", "").strip().lower() not in {"1", "true", "yes"}:
        assert os.environ.get("HF_HUB_OFFLINE") == "1"


def test_commercial_build_guardrail_prohibits_pymupdf(monkeypatch) -> None:
    """
    Guarantees clean-room commercial isolation:
    In Commercial Pro/Enterprise mode (SOVEREIGNDOC_EDITION=commercial),
    PyMuPDF (fitz) is prohibited and attempting to select 'mupdf' raises RuntimeError.
    """
    import pytest
    from app.services.rag.pdf import get_pdf_parser, is_commercial_edition
    from app.services.rag.pdf.pdfium_parser import PDFiumParser

    monkeypatch.setenv("SOVEREIGNDOC_EDITION", "commercial")
    assert is_commercial_edition() is True

    # Commercial default engine must be clean-room PDFium
    parser = get_pdf_parser()
    assert isinstance(parser, PDFiumParser)

    # In commercial edition, attempting to invoke mupdf fails closed
    with pytest.raises(RuntimeError, match="strictly prohibited in Commercial"):
        get_pdf_parser("mupdf")
