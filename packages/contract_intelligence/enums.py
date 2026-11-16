# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Contract Intelligence Typed Enums
"""
from enum import Enum

class StrEnum(str, Enum):
    """String enum helper for Python compatibility."""
    def __str__(self) -> str:
        return self.value

class RiskLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class DetectionMethod(StrEnum):
    RULE = "RULE"
    REGEX = "REGEX"
    CLASSIFIER = "CLASSIFIER"
    EMBEDDING = "EMBEDDING"
    LLM = "LLM"
    HEURISTIC = "HEURISTIC"

class ClauseCategory(StrEnum):
    INDEMNIFICATION = "INDEMNIFICATION"
    LIMITATION_OF_LIABILITY = "LIMITATION_OF_LIABILITY"
    TERMINATION = "TERMINATION"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    INTELLECTUAL_PROPERTY = "INTELLECTUAL_PROPERTY"
    PAYMENT_TERMS = "PAYMENT_TERMS"
    GOVERNING_LAW = "GOVERNING_LAW"

class ObligationParty(StrEnum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    MUTUAL = "MUTUAL"


class PaginationSource(StrEnum):
    WORD_PAGE_BREAK = "WORD_PAGE_BREAK"
    SECTION_BREAK = "SECTION_BREAK"
    VIRTUAL_LAYOUT = "VIRTUAL_LAYOUT"


class GraphNodeType(StrEnum):
    DOCUMENT = "DOCUMENT"
    REVIEW_RUN = "REVIEW_RUN"
    CLAUSE_CATEGORY = "CLAUSE_CATEGORY"
    RISK = "RISK"
    OBLIGATION = "OBLIGATION"
    NOTE = "NOTE"
    TAG = "TAG"


class GraphEdgeType(StrEnum):
    CONTAINS = "CONTAINS"         # DOCUMENT -> CLAUSE_CATEGORY
    GENERATED = "GENERATED"       # DOCUMENT -> REVIEW_RUN, REVIEW_RUN -> RISK / OBLIGATION
    REFERENCES = "REFERENCES"     # NOTE -> DOCUMENT / RISK / OBLIGATION
    TAGGED = "TAGGED"             # NOTE -> TAG
    LINKS_TO = "LINKS_TO"         # NOTE -> NOTE
