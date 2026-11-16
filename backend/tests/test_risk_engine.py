# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Deterministic Risk Engine & Heuristic Rules Tests
"""
from packages.contract_intelligence.plugin_sdk.registry import CapabilityRegistry
import packages.contract_intelligence.risk_rules  # Registers rules
from packages.contract_intelligence.enums import RiskLevel, DetectionMethod


def test_registered_risk_rules():
    """Verifies all built-in deterministic risk rules are registered in CapabilityRegistry."""
    rules = CapabilityRegistry.get_risk_rules()
    assert len(rules) >= 6

    rule_ids = [r.id for r in rules]
    assert "UNCAPPED_LIABILITY" in rule_ids or "MISSING_CAP" in rule_ids
    assert "SHORT_NOTICE" in rule_ids
    assert "ONE_SIDED_INDEMNITY" in rule_ids


def test_short_turnaround_rule():
    """Verifies ShortTurnaroundRule flags aggressive notice/cure windows (< 15 days)."""
    rules = {r.id: r for r in CapabilityRegistry.get_risk_rules()}
    short_rule = rules.get("SHORT_NOTICE")
    assert short_rule is not None

    chunks = [
        {
            "id": "chk_turnaround",
            "document_id": "doc_1",
            "text": "Contractor must cure any material breach within three (3) calendar days of notice.",
            "page_number": 1,
            "section": "12.1"
        }
    ]

    findings = short_rule.evaluate(chunks, classified_clauses=[])
    assert len(findings) >= 1
    f = findings[0]
    assert f.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)
    assert f.detection_method == DetectionMethod.RULE
    assert f.confidence == 1.0

