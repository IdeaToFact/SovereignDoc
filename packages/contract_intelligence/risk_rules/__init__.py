# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Built-in Deterministic Risk Rules for SovereignDoc (AGPL Community Edition)
"""
from packages.contract_intelligence.plugin_sdk.registry import CapabilityRegistry
from .rules import (
    UncappedLiabilityRule,
    OneSidedIndemnityRule,
    ShortNoticeRule,
    EvergreenRule,
    MissingCapRule,
    ForeignJurisdictionRule,
    AuditAndRecordProductionRule,
    RestrictiveCovenantAndIPRule,
    OperationalCovenantAndNoticeRule,
)

BUILT_IN_RULES = [
    UncappedLiabilityRule(),
    OneSidedIndemnityRule(),
    ShortNoticeRule(),
    EvergreenRule(),
    MissingCapRule(),
    ForeignJurisdictionRule(),
    AuditAndRecordProductionRule(),
    RestrictiveCovenantAndIPRule(),
    OperationalCovenantAndNoticeRule(),
]


def register_builtin_rules():
    """Register all built-in AGPL community risk rules into CapabilityRegistry."""
    for rule in BUILT_IN_RULES:
        CapabilityRegistry.register_risk_rule(rule)


# Automatically register built-ins on module import
register_builtin_rules()
