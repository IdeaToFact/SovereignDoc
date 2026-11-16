# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Capability Registry for SovereignDoc Plugin SDK
"""
from typing import Dict, Any, Type, List, Optional
import logging

logger = logging.getLogger("sovereigndoc.plugin_sdk")

class CapabilityRegistry:
    """
    Central registry mapping capability names and extension points to their implementations.
    Enables AGPL core to remain clean while allowing commercial plugins to plug in.
    """
    _capabilities: Dict[str, Any] = {}
    _risk_rules: Dict[str, Any] = {}

    @classmethod
    def register(cls, capability_name: str, implementation: Any) -> None:
        """Register a generic capability implementation."""
        logger.info(f"Registering capability: '{capability_name}' -> {implementation}")
        cls._capabilities[capability_name] = implementation

    @classmethod
    def get(cls, capability_name: str, default: Any = None) -> Any:
        """Retrieve a registered capability."""
        return cls._capabilities.get(capability_name, default)

    @classmethod
    def list_capabilities(cls) -> List[str]:
        """List all currently registered capabilities."""
        return list(cls._capabilities.keys())

    @classmethod
    def register_risk_rule(cls, rule_instance: Any) -> None:
        """Register a RiskRule instance into the registry."""
        rule_id = getattr(rule_instance, "id", None)
        if not rule_id:
            raise ValueError(f"Cannot register RiskRule without 'id' attribute: {rule_instance}")
        cls._risk_rules[rule_id] = rule_instance
        logger.info(f"Registered RiskRule: [{rule_id}] {getattr(rule_instance, 'name', '')}")

    @classmethod
    def get_risk_rules(cls) -> List[Any]:
        """Get all registered RiskRule instances."""
        return list(cls._risk_rules.values())

    @classmethod
    def get_risk_rule(cls, rule_id: str) -> Optional[Any]:
        """Get a specific RiskRule by ID."""
        return cls._risk_rules.get(rule_id)

    @classmethod
    def clear(cls) -> None:
        """Reset registry (useful for unit testing)."""
        cls._capabilities.clear()
        cls._risk_rules.clear()
