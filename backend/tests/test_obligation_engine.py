# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Affirmative Obligations & SLA Extractor Tests
"""
from packages.contract_intelligence.obligations.obligations_extractor import ObligationsExtractor
from packages.contract_intelligence.enums import ObligationParty


def test_obligation_duty_and_deadline_extraction():
    """Verifies ObligationsExtractor detects covenants, deadlines, and obligated parties."""
    extractor = ObligationsExtractor()

    chunks = [
        {
            "id": "chk_duty_1",
            "document_id": "doc_sla",
            "text": "Contractor must deliver quarterly financial audit reports within fifteen (15) business days.",
            "page_number": 3,
            "section": "7.2"
        },
        {
            "id": "chk_duty_2",
            "document_id": "doc_sla",
            "text": "Both parties agree to promptly notify each other in writing upon becoming aware of any security incident.",
            "page_number": 4,
            "section": "8.1"
        }
    ]

    obligations = extractor.extract_obligations(chunks, document_id="doc_sla")
    assert len(obligations) >= 1

    # Check vendor duty with 15-day deadline
    v_duty = obligations[0]
    assert v_duty.party == ObligationParty.VENDOR
    assert "15" in (v_duty.deadline_or_cadence or "")

