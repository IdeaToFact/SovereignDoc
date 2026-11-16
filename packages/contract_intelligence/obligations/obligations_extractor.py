# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Obligations Extractor Service
Extracts affirmative legal covenants, operational deadlines, triggers, and obligated parties.
"""
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from packages.contract_intelligence.enums import DetectionMethod, ObligationParty


@dataclass
class ExtractedObligation:
    """Represents an extracted affirmative duty with provenance."""
    id: str
    document_id: str
    party: ObligationParty
    action_required: str
    trigger_or_condition: Optional[str]
    deadline_or_cadence: Optional[str]
    page_number: int
    section: Optional[str]
    verbatim_text: str
    bbox: Optional[List[float]] = None
    confidence: float = 0.90
    detection_method: DetectionMethod = DetectionMethod.HEURISTIC

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "party": self.party.value,
            "action_required": self.action_required,
            "trigger_or_condition": self.trigger_or_condition,
            "deadline_or_cadence": self.deadline_or_cadence,
            "page_number": self.page_number,
            "section": self.section,
            "verbatim_text": self.verbatim_text,
            "bbox": self.bbox,
            "confidence": round(self.confidence, 3),
            "detection_method": self.detection_method.value,
        }


class ObligationsExtractor:
    """
    Extracts affirmative duties, conditions, notices, warranties, and deadlines from contract text chunks.
    Supports both single-chunk and multi-chunk stitched PDF paragraphs.
    """

    DUTY_PATTERN = re.compile(
        r"\b(?:The\s+)?(?P<party>"
        r"Customer|Client|Company|Tenant|Buyer|Licensee|Employer|"
        r"Vendor|Contractor|Subcontractor|Consultant|Supplier|Service\s+Provider|Landlord|Seller|Licensor|"
        r"Each\s+Party|Both\s+Parties|Either\s+Party|The\s+Parties|Parties|Each\s+person\s+signing\s+this\s+Agreement"
        r")\s+"
        r"(?:therefore\s+|also\s+|hereby\s+)?"
        r"(?P<modal>"
        r"shall|must|will\s+return|will\s+not|will\s+mutually\s+agree|"
        r"agrees\s+(?:upon\s+request\s+(?:from\s+the\s+\w+\s+)?)?to|"
        r"agrees\s+not\s+to|agrees\s+that\s+it\s+will(?:\s+not)?|"
        r"acknowledges\s+and\s+agrees\s+that|"
        r"is\s+required\s+to|covenants\s+to|"
        r"represents\s+and\s+warrants(?:\s+to\s+the\s+other)?\s+that"
        r")\s+"
        r"(?P<action>[^.;]{12,340})",
        re.IGNORECASE,
    )

    PASSIVE_NOTICE_PATTERN = re.compile(
        r"\b(?P<subject>Any\s+notice\s+or\s+other\s+communication\s+required\s+or\s+permitted\s+hereunder)\s+"
        r"(?P<modal>shall\s+be\s+given|must\s+be\s+given)\s+"
        r"(?P<action>[^.;]{10,260})",
        re.IGNORECASE,
    )

    DEADLINE_PATTERNS = [
        re.compile(
            r"\b(within\s+(?:[a-z\-]+\s*\(\d+\)|\d+)\s*(?:business\s+|calendar\s+)?(?:days?|hours?|months?|years?)"
            r"(?:\s+of\s+(?:the\s+)?request|\s+after\s+written\s+notice)?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b((?:[a-z\-]+\s*\(\d+\)|\d+)\s*(?:business\s+|calendar\s+)?days?\s+after\s+[^,.;]{3,40})\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(for\s+(?:a\s+period\s+of\s+)?\d+\s*months?\s+(?:following|after)\s+[^,.;]{3,45})\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(through\s+\d+\s*months?\s+following\s+[^,.;]{3,45})\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(on\s+at\s+least\s+a\s+weekly\s+basis|on\s+an\s+annual\s+basis|not\s+more\s+than\s+twice\s+in\s+a\s+calendar\s+year)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\b(prior\s+to\s+[^,.;\n]{3,40})\b", re.IGNORECASE),
        re.compile(r"\b(quarterly|annually|monthly|semi-annually|bi-weekly|weekly)\b", re.IGNORECASE),
        re.compile(r"\b(net\s+\d+\s*days?)\b", re.IGNORECASE),
        re.compile(r"\b(no\s+later\s+than\s+[^,.;\n]{3,40})\b", re.IGNORECASE),
        re.compile(r"\b(at\s+least\s+(?:[a-z\-]+\s*\(\d+\)|\d+)\s*days?)\b", re.IGNORECASE),
    ]

    TRIGGER_PATTERNS = [
        re.compile(r"\b(upon\s+[^,.;\n]{4,65})\b", re.IGNORECASE),
        re.compile(r"\b(in\s+the\s+event\s+of\s+[^,.;\n]{4,65})\b", re.IGNORECASE),
        re.compile(r"\b(following\s+(?:the\s+)?expiration\s+or\s+termination[^,.;\n]{0,40})\b", re.IGNORECASE),
        re.compile(r"\b(if\s+the\s+breaching\s+party\s+does\s+not\s+cure[^,.;\n]{0,50})\b", re.IGNORECASE),
        re.compile(r"\b(during\s+the\s+term\s+of\s+this\s+Agreement[^,.;\n]{0,50})\b", re.IGNORECASE),
    ]

    def _determine_party(self, party_str: str) -> ObligationParty:
        p = party_str.strip().lower()
        if any(w in p for w in ["customer", "client", "company", "tenant", "buyer", "licensee", "employer"]):
            return ObligationParty.CUSTOMER
        if any(
            w in p
            for w in [
                "vendor",
                "contractor",
                "subcontractor",
                "consultant",
                "supplier",
                "service provider",
                "landlord",
                "seller",
                "licensor",
            ]
        ):
            return ObligationParty.VENDOR
        return ObligationParty.MUTUAL

    @staticmethod
    def _extract_bbox(chunk: Any) -> Optional[List[float]]:
        bbox = getattr(chunk, "bbox", None) or (chunk.get("bbox") if isinstance(chunk, dict) else None)
        if bbox is None:
            bbox_json = getattr(chunk, "bbox_json", None) or (
                chunk.get("bbox_json") if isinstance(chunk, dict) else None
            )
            if bbox_json:
                try:
                    bbox = json.loads(bbox_json)
                except Exception:
                    bbox = None
        return bbox

    @classmethod
    def _normalize_text(cls, raw_text: str) -> str:
        """Collapses mid-sentence PDF line wraps into single spaces while preserving sentence boundaries."""
        cleaned = re.sub(r"Page\s+\d+\s+of\s*\d+|CONFIDENTIAL", " ", raw_text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*\n+\s*", " ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned.strip()

    def _extract_from_text_unit(
        self,
        unit_text: str,
        document_id: str,
        page_number: int,
        section: Optional[str],
        bbox: Optional[List[float]],
        seen_signatures: set,
    ) -> List[ExtractedObligation]:
        extracted: List[ExtractedObligation] = []
        normalized = self._normalize_text(unit_text)
        if len(normalized) < 20:
            return extracted

        sentences = re.split(r"(?<=[.;])\s+", normalized)

        for sent in sentences:
            sent_clean = sent.strip()
            if len(sent_clean) < 20:
                continue

            m = self.DUTY_PATTERN.search(sent_clean)
            party: Optional[ObligationParty] = None
            action_required: Optional[str] = None

            if m:
                party_str = m.group("party")
                modal = re.sub(r"\s+", " ", m.group("modal")).strip()
                action_raw = re.sub(r"\s+", " ", m.group("action")).strip()
                party = self._determine_party(party_str)
                action_required = f"{modal.capitalize()} {action_raw}".strip()
            else:
                pm = self.PASSIVE_NOTICE_PATTERN.search(sent_clean)
                if pm:
                    party = ObligationParty.MUTUAL
                    modal = re.sub(r"\s+", " ", pm.group("modal")).strip()
                    action_raw = re.sub(r"\s+", " ", pm.group("action")).strip()
                    action_required = f"Notice {modal} {action_raw}".strip()

            if not party or not action_required:
                continue

            # Deduplicate across overlapping chunk windows using normalized action prefix
            sig_key = re.sub(r"[^a-z0-9]", "", action_required.lower())[:36]
            if len(sig_key) < 12 or sig_key in seen_signatures:
                continue
            seen_signatures.add(sig_key)

            deadline = None
            for d_pat in self.DEADLINE_PATTERNS:
                dm = d_pat.search(sent_clean)
                if dm:
                    deadline = re.sub(r"\s+", " ", dm.group(0)).strip()
                    break

            trigger = None
            for t_pat in self.TRIGGER_PATTERNS:
                tm = t_pat.search(sent_clean)
                if tm:
                    trigger = re.sub(r"\s+", " ", tm.group(0)).strip()
                    break

            conf = 0.92 if (deadline or trigger) else 0.88

            extracted.append(
                ExtractedObligation(
                    id=f"obl_{uuid.uuid4().hex[:12]}",
                    document_id=document_id,
                    party=party,
                    action_required=action_required[:280],
                    trigger_or_condition=trigger,
                    deadline_or_cadence=deadline,
                    page_number=page_number,
                    section=section,
                    verbatim_text=sent_clean[:320],
                    bbox=bbox,
                    confidence=conf,
                    detection_method=DetectionMethod.HEURISTIC,
                )
            )

        return extracted

    def extract_from_chunk(self, chunk: Any, document_id: str) -> List[ExtractedObligation]:
        """Extracts affirmative duties from a single contract chunk."""
        text = getattr(chunk, "text", None) or (chunk.get("text") if isinstance(chunk, dict) else "") or ""
        page_number = getattr(chunk, "page_number", 1) or (chunk.get("page_number", 1) if isinstance(chunk, dict) else 1)
        section = getattr(chunk, "section", None) or (chunk.get("section") if isinstance(chunk, dict) else None)
        bbox = self._extract_bbox(chunk)
        return self._extract_from_text_unit(text, document_id, page_number, section, bbox, set())

    def extract_obligations(self, chunks: List[Any], document_id: str) -> List[ExtractedObligation]:
        """
        Extracts all affirmative obligations across all chunks of a document.
        Stitches consecutive PDF chunks within the same section/page window so sentences
        wrapped across visual PDF blocks are captured with full context and provenance.
        """
        all_obligations: List[ExtractedObligation] = []
        seen_signatures: set = set()

        # Sliding 5-chunk window within the same section (captures complete sentences even when wrapped across PDF blocks)
        n = len(chunks)
        for i in range(n):
            base_ch = chunks[i]
            base_sec = getattr(base_ch, "section", None) or (base_ch.get("section") if isinstance(base_ch, dict) else None)
            base_page = getattr(base_ch, "page_number", 1) or (
                base_ch.get("page_number", 1) if isinstance(base_ch, dict) else 1
            )
            base_bbox = self._extract_bbox(base_ch)

            window_texts = []
            for j in range(i, min(i + 5, n)):
                nxt = chunks[j]
                nxt_sec = getattr(nxt, "section", None) or (nxt.get("section") if isinstance(nxt, dict) else None)
                if nxt_sec != base_sec and j > i:
                    break
                t = getattr(nxt, "text", None) or (nxt.get("text") if isinstance(nxt, dict) else "") or ""
                if t.strip() in ("CONFIDENTIAL", "DRAFT", "PROPRIETARY"):
                    continue
                window_texts.append(t.strip())

            if window_texts:
                stitched = " ".join(window_texts)
                all_obligations.extend(
                    self._extract_from_text_unit(stitched, document_id, base_page, base_sec, base_bbox, seen_signatures)
                )

        all_obligations.sort(key=lambda o: (o.page_number, o.section or ""))
        return all_obligations


obligations_extractor = ObligationsExtractor()
