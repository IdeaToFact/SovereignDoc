# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Review Package Export (.ZIP) Tests
"""
import io
import zipfile
from packages.contract_intelligence.exports.review_exporter import review_exporter


def test_review_package_export_zip_structure():
    """Verifies review package generates valid .zip with MD, CSVs, and DISCLAIMER.txt."""
    doc_info = {
        "filename": "Master_Services_Agreement.pdf",
        "checksum_sha256": "mock_sha256_checksum"
    }
    risks = [
        {
            "id": "r1",
            "rule_id": "missing_liability_cap",
            "category": "LIMITATION_OF_LIABILITY",
            "severity": "HIGH",
            "issue_title": "Missing Liability Cap",
            "issue_description": "No aggregate dollar cap found.",
            "verbatim_quote": "N/A",
            "page_number": 2,
            "section": "14",
            "confidence": 1.0,
            "detection_method": "RULE"
        }
    ]
    obligations = [
        {
            "id": "o1",
            "party": "VENDOR",
            "action_required": "Provide audit records upon request",
            "deadline_or_cadence": "15 business days",
            "verbatim_text": "Vendor shall provide records within 15 business days.",
            "page_number": 4,
            "section": "4.2",
            "confidence": 0.95,
            "detection_method": "HEURISTIC"
        }
    ]

    zip_bytes = review_exporter.build_review_package_zip(
        document_filename="Master_Services_Agreement.pdf",
        review_run_id="run_test_01",
        ruleset_version="1.0.0",
        risks=risks,
        obligations=obligations
    )
    assert len(zip_bytes) > 0

    # Inspect zip contents in-memory
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
        names = z.namelist()
        assert "contract_audit.md" in names
        assert "risk_matrix.csv" in names
        assert "obligations.csv" in names
        assert "DISCLAIMER.txt" in names

        # Verify DISCLAIMER.txt content
        disclaimer_text = z.read("DISCLAIMER.txt").decode("utf-8")
        assert "SOVEREIGNDOC LEGAL & REGULATORY DISCLAIMER" in disclaimer_text
        assert "Idea To Fact LLC" in disclaimer_text

