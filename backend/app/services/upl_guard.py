# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""Zero-Latency Deterministic UPL (Unauthorized Practice of Law) Guard for Conversational Chat.

Milestone 6.1 (v1.0.0-community):
- Layer 1: LLM System Prompt Directive in routes_chat.py handles general semantic intent variations.
- Layer 2: UPLGuard provides instant deterministic pattern matching at the application layer to
  guarantee a mandatory non-legal-advice notice is appended whenever a user asks a legal-judgment question.
  (Full semantic UPL intent classification is scheduled on the v1.1 roadmap).
"""
from typing import List, Optional, Tuple

LEGAL_ADVICE_PATTERNS: List[str] = [
    "should i sign",
    "should we sign",
    "should i accept",
    "should we accept",
    "am i liable",
    "are we liable",
    "can they sue me",
    "can they sue us",
    "what should i do",
    "what should we do",
    "am i legally required",
    "are we legally required",
    "is this enforceable",
    "is it safe to sign",
    "give me legal advice",
]

UPL_NOTICE_MARKDOWN = (
    "\n\n---\n"
    "*⚖️ **Notice**: SovereignDoc provides document analysis and informational insights only "
    "and does not provide legal advice. Consult a licensed attorney regarding legal decisions.*"
)


class UPLGuard:
    """Application-layer UPL safeguard for interactive contract Q&A."""

    @classmethod
    def match_pattern(cls, query: str) -> Optional[str]:
        """Return the matched legal-advice trigger phrase if present, else None."""
        if not query:
            return None
        normalized = " ".join(query.strip().lower().split())
        for pattern in LEGAL_ADVICE_PATTERNS:
            if pattern in normalized:
                return pattern
        return None

    @classmethod
    def is_legal_advice_query(cls, query: str) -> bool:
        """Return True if the user query matches a deterministic legal-judgment pattern."""
        return cls.match_pattern(query) is not None

    @classmethod
    def apply_upl_notice(cls, answer_text: str, query: str) -> Tuple[str, bool]:
        """Deterministically append the UPL non-legal-advice notice when a legal-judgment query is detected."""
        matched = cls.match_pattern(query)
        if not matched:
            return answer_text, False
        if "does not provide legal advice" in (answer_text or "").lower():
            return answer_text, True
        return (answer_text or "").rstrip() + UPL_NOTICE_MARKDOWN, True


upl_guard = UPLGuard()

