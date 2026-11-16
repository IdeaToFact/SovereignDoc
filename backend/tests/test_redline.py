# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Contract Redline & Word Diff Engine Tests
"""
from packages.contract_intelligence.diff.contract_diff import ContractDiffEngine


def test_word_diff_insertions_and_deletions():
    """Verifies ContractDiffEngine computes token-level insertions and deletions."""
    text_v1 = "Contractor aggregate liability shall not exceed $500,000 in U.S. Dollars."
    text_v2 = "Contractor aggregate liability shall not exceed $1,000,000 in U.S. Dollars within any contract year."

    diff_result = ContractDiffEngine.compute_word_diff(text_v1, text_v2)
    assert "tokens" in diff_result
    tokens = diff_result["tokens"]
    assert len(tokens) > 0

    types = [t["type"] for t in tokens]
    assert "eq" in types
    assert "del" in types  # "$500,000" replaced/deleted
    assert "ins" in types  # "$1,000,000" and "within any contract year" inserted
    assert diff_result["additions"] > 0
    assert diff_result["deletions"] > 0

