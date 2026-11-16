# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Base RiskRule Abstract Base Class for Plugin SDK
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from packages.contract_intelligence.enums import RiskLevel, DetectionMethod, ClauseCategory

@dataclass
class RuleFinding:
    """Represents a discrete risk finding emitted by a RiskRule."""
    rule_id: str
    category: ClauseCategory
    risk_level: RiskLevel
    issue_title: str
    description: str
    page_number: int
    section: Optional[str]
    verbatim_text: str
    bbox: Optional[List[float]] = None
    confidence: float = 1.0
    detection_method: DetectionMethod = DetectionMethod.RULE

class RiskRule(ABC):
    """
    Abstract Base Class for contract risk rules.
    Both built-in AGPL Community rules and proprietary Pro playbook rules implement this.
    """
    id: str
    name: str
    severity: RiskLevel
    category: ClauseCategory
    description: str = ""

    @abstractmethod
    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        """
        Evaluate document chunks and classified clauses to detect legal risks.
        
        Args:
            chunks: List of document chunks with text, page_number, section, bbox metadata.
            classified_clauses: Map of category -> list of matched chunks/clauses.
            
        Returns:
            List of RuleFinding objects.
        """
        pass
