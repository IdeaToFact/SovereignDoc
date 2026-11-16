# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Deterministic Contract Risk Rules (Core + Operational/Audit Covenant Rules)
All rules emit confidence = 1.0 and detection_method = DetectionMethod.RULE upon match.
Supports both single-chunk and stitched multi-chunk PDF section windows.
"""
import json
import re
from typing import Any, Dict, List, Optional
from packages.contract_intelligence.enums import ClauseCategory, DetectionMethod, RiskLevel
from packages.contract_intelligence.plugin_sdk.base_rules import RiskRule, RuleFinding


def _get(chunk: Any, attr: str, default: Any = None) -> Any:
    val = getattr(chunk, attr, None)
    if val is not None:
        return val
    if isinstance(chunk, dict):
        return chunk.get(attr, default)
    return default


def _get_bbox(chunk: Any) -> Optional[List[float]]:
    bbox = _get(chunk, "bbox")
    if bbox:
        return bbox
    bbox_json = _get(chunk, "bbox_json")
    if bbox_json:
        try:
            return json.loads(bbox_json)
        except Exception:
            return None
    return None


def _build_stitched_units(chunks: List[Any]) -> List[Dict[str, Any]]:
    """
    Builds evaluation units combining individual chunks plus sliding 5-chunk section windows
    so PDF sentences wrapped across visual blocks are evaluated with full context.
    """
    units: List[Dict[str, Any]] = []
    n = len(chunks)
    for i, ch in enumerate(chunks):
        raw_text = _get(ch, "text", "") or ""
        clean_text = re.sub(r"\s*\n+\s*", " ", raw_text).strip()
        if clean_text:
            units.append(
                {
                    "text": clean_text,
                    "page_number": _get(ch, "page_number", 1) or 1,
                    "section": _get(ch, "section"),
                    "bbox": _get_bbox(ch),
                }
            )

        # Build a stitched 5-chunk window within the same section
        base_sec = _get(ch, "section")
        window_parts = []
        for j in range(i, min(i + 5, n)):
            nxt = chunks[j]
            nxt_sec = _get(nxt, "section")
            if nxt_sec != base_sec and j > i:
                break
            t = (_get(nxt, "text", "") or "").strip()
            if not t or t in ("CONFIDENTIAL", "DRAFT", "PROPRIETARY"):
                continue
            window_parts.append(re.sub(r"\s*\n+\s*", " ", t))

        if len(window_parts) > 1:
            units.append(
                {
                    "text": " ".join(window_parts),
                    "page_number": _get(ch, "page_number", 1) or 1,
                    "section": base_sec,
                    "bbox": _get_bbox(ch),
                }
            )
    return units


class UncappedLiabilityRule(RiskRule):
    """
    Detects uncapped liability exposure, unlimited carve-outs, or absence of dollar/fee ceilings.
    """
    id = "UNCAPPED_LIABILITY"
    name = "Uncapped Liability Exposure"
    severity = RiskLevel.HIGH
    category = ClauseCategory.LIMITATION_OF_LIABILITY
    description = "Flags broad liability carve-outs or explicit statements of unlimited liability."

    CARVE_OUT_PATTERNS = [
        re.compile(r"\b(unlimited liability|without limitation|shall not be subject to any (cap|limitation))\b", re.IGNORECASE),
        re.compile(r"\b(shall be liable for all|no limit on|unlimited aggregate liability)\b", re.IGNORECASE),
        re.compile(r"\b(carve-?out|exceptions?)\s+to\s+liability\s+cap\b", re.IGNORECASE),
    ]

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        target_chunks = classified_clauses.get(ClauseCategory.LIMITATION_OF_LIABILITY, [])
        if not target_chunks:
            target_chunks = chunks

        seen_pages = set()
        for unit in _build_stitched_units(target_chunks):
            text = unit["text"]
            for pat in self.CARVE_OUT_PATTERNS:
                m = pat.search(text)
                if m:
                    key = (unit["page_number"], m.group(0).lower())
                    if key in seen_pages:
                        break
                    seen_pages.add(key)
                    findings.append(RuleFinding(
                        rule_id=self.id,
                        category=self.category,
                        risk_level=self.severity,
                        issue_title="Uncapped Liability or Broad Carve-out Detected",
                        description=f"Clause contains uncapped liability or broad exception: '{m.group(0)}'. This exposes the party to potentially unlimited financial recovery.",
                        page_number=unit["page_number"],
                        section=unit["section"],
                        verbatim_text=text[:300] + ("..." if len(text) > 300 else ""),
                        bbox=unit["bbox"],
                        confidence=1.0,
                        detection_method=DetectionMethod.RULE
                    ))
                    break
        return findings


class OneSidedIndemnityRule(RiskRule):
    """
    Detects unilateral or non-reciprocal indemnification duties.
    """
    id = "ONE_SIDED_INDEMNITY"
    name = "One-Sided Indemnification Duty"
    severity = RiskLevel.HIGH
    category = ClauseCategory.INDEMNIFICATION
    description = "Flags unilateral obligation where one party indemnifies the other without reciprocal protection."

    CUSTOMER_PATTERNS = [
        re.compile(
            r"\b(customer|client|company|contractor|consultant|tenant|buyer|licensee)\s+(shall|must|agrees\s+to|will)\s+(indemnify|defend|hold harmless)\b",
            re.IGNORECASE,
        ),
    ]
    RECIPROCAL_PATTERNS = [
        re.compile(r"\b(each party|parties shall mutually|both parties)\s+(shall\s+)?(indemnify|defend|hold harmless)\b", re.IGNORECASE),
    ]

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        indemnity_chunks = classified_clauses.get(ClauseCategory.INDEMNIFICATION, [])
        if not indemnity_chunks:
            indemnity_chunks = [ch for ch in chunks if "indemnif" in _get(ch, "text", "").lower()]

        has_customer_duty = False
        has_reciprocal_duty = False
        primary_unit = None

        for unit in _build_stitched_units(indemnity_chunks):
            text = unit["text"]
            if any(p.search(text) for p in self.CUSTOMER_PATTERNS):
                has_customer_duty = True
                if not primary_unit:
                    primary_unit = unit
            if any(p.search(text) for p in self.RECIPROCAL_PATTERNS):
                has_reciprocal_duty = True

        if has_customer_duty and not has_reciprocal_duty and primary_unit:
            text = primary_unit["text"]
            findings.append(RuleFinding(
                rule_id=self.id,
                category=self.category,
                risk_level=self.severity,
                issue_title="Unilateral / One-Sided Indemnification Obligation",
                description="One party is obligated to defend and indemnify the counterparty without reciprocal defense or indemnity obligations.",
                page_number=primary_unit["page_number"],
                section=primary_unit["section"],
                verbatim_text=text[:300] + ("..." if len(text) > 300 else ""),
                bbox=primary_unit["bbox"],
                confidence=1.0,
                detection_method=DetectionMethod.RULE
            ))
        return findings


class ShortNoticeRule(RiskRule):
    """
    Detects aggressive or tight notice, cure, or record-production deadlines (<= 15 days).
    Supports both numeric ('5 business days', '15 business days') and written-out parenthetical ('five (5) business days', 'fifteen (15) business days') formats.
    """
    id = "SHORT_NOTICE"
    name = "Short Notice or Production Deadline (<= 15 Days)"
    severity = RiskLevel.MEDIUM
    category = ClauseCategory.TERMINATION
    description = "Flags termination, notice, cure, or record-production deadlines of 15 days or less."

    SHORT_NOTICE_PATTERNS = [
        re.compile(
            r"\b(?:within|upon|provide|or)\s+"
            r"(?:(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen)\s*\(\s*(?:[1-9]|1[0-5])\s*\)|(?:[1-9]|1[0-5]))\s*"
            r"(?:calendar\s+|business\s+)?days?(?:\s+of\s+(?:the\s+)?request|\s+after)?\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen)\s*\(\s*(?:[1-9]|1[0-5])\s*\)|(?:[1-9]|1[0-5]))\s*"
            r"(?:calendar\s+|business\s+)?days?\s*(?:prior\s+)?written\s+notice\b",
            re.IGNORECASE,
        ),
        re.compile(r"\b(within|upon)\s+(24|48|72)\s*hours?\b", re.IGNORECASE),
    ]

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        seen_matches = set()
        for unit in _build_stitched_units(chunks):
            text = unit["text"]
            for pat in self.SHORT_NOTICE_PATTERNS:
                m = pat.search(text)
                if m:
                    matched_phrase = re.sub(r"\s+", " ", m.group(0)).strip()
                    dedup_key = (unit["page_number"], unit["section"], matched_phrase.lower())
                    if dedup_key in seen_matches:
                        break
                    seen_matches.add(dedup_key)
                    findings.append(RuleFinding(
                        rule_id=self.id,
                        category=self.category,
                        risk_level=self.severity,
                        issue_title=f"Short Turnaround / Notice Deadline: '{matched_phrase}'",
                        description=(
                            f"Agreement mandates a tight operational deadline or notice window of '{matched_phrase}'. "
                            "Short compliance windows (<= 15 days) create operational risk of inadvertent breach."
                        ),
                        page_number=unit["page_number"],
                        section=unit["section"],
                        verbatim_text=text[:300] + ("..." if len(text) > 300 else ""),
                        bbox=unit["bbox"],
                        confidence=1.0,
                        detection_method=DetectionMethod.RULE
                    ))
                    break
        return findings


class EvergreenRule(RiskRule):
    """
    Detects automatic renewal (evergreen) clauses or multi-year post-termination survival obligations.
    """
    id = "EVERGREEN"
    name = "Automatic Renewal / Long Post-Termination Survival"
    severity = RiskLevel.MEDIUM
    category = ClauseCategory.TERMINATION
    description = "Flags automatic contract renewal terms or multi-year post-termination restrictive survival periods."

    EVERGREEN_PATTERNS = [
        re.compile(r"\b(automatically\s+renew(s|ed|ing)?|auto-?renew(s|al)?)\b", re.IGNORECASE),
        re.compile(r"\b(renew\s+automatically\s+for\s+successive)\b", re.IGNORECASE),
        re.compile(r"\b(shall\s+continue\s+in\s+perpetuity|evergreen|forever\s+afterward)\b", re.IGNORECASE),
    ]

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        seen_keys = set()
        for unit in _build_stitched_units(chunks):
            text = unit["text"]
            for pat in self.EVERGREEN_PATTERNS:
                m = pat.search(text)
                if m:
                    phrase = re.sub(r"\s+", " ", m.group(0)).strip()
                    key = (unit["page_number"], phrase.lower())
                    if key in seen_keys:
                        break
                    seen_keys.add(key)
                    findings.append(RuleFinding(
                        rule_id=self.id,
                        category=self.category,
                        risk_level=self.severity,
                        issue_title=f"Perpetual or Auto-Renewing Survival Term: '{phrase}'",
                        description=f"Contract contains perpetual or automatic survival/renewal provision ('{phrase}'). Verify post-termination obligations and cancellation windows.",
                        page_number=unit["page_number"],
                        section=unit["section"],
                        verbatim_text=text[:300] + ("..." if len(text) > 300 else ""),
                        bbox=unit["bbox"],
                        confidence=1.0,
                        detection_method=DetectionMethod.RULE
                    ))
                    break
        return findings


class MissingCapRule(RiskRule):
    """
    Detects complete absence of any limitation of liability section in the document.
    """
    id = "MISSING_CAP"
    name = "Missing Limitation of Liability Cap"
    severity = RiskLevel.HIGH
    category = ClauseCategory.LIMITATION_OF_LIABILITY
    description = "Flags entire omission of limitation of liability clause."

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        liability_clauses = classified_clauses.get(ClauseCategory.LIMITATION_OF_LIABILITY, [])
        if not liability_clauses:
            has_mention = any(
                "limitation of liability" in _get(ch, "text", "").lower() or
                "liability cap" in _get(ch, "text", "").lower() or
                "aggregate liability" in _get(ch, "text", "").lower()
                for ch in chunks
            )
            if not has_mention and chunks:
                first_chunk = chunks[0]
                findings.append(RuleFinding(
                    rule_id=self.id,
                    category=self.category,
                    risk_level=self.severity,
                    issue_title="Missing Limitation of Liability Clause",
                    description="No limitation of liability or aggregate liability cap clause was identified in this contract. Without a cap, common law full exposure applies.",
                    page_number=_get(first_chunk, "page_number", 1),
                    section="Document General",
                    verbatim_text="[Clause completely absent from agreement]",
                    bbox=_get_bbox(first_chunk),
                    confidence=1.0,
                    detection_method=DetectionMethod.RULE
                ))
        return findings


class ForeignJurisdictionRule(RiskRule):
    """
    Detects non-standard or foreign court jurisdictions / offshore venues.
    """
    id = "FOREIGN_JURISDICTION"
    name = "Foreign or Non-Standard Jurisdiction"
    severity = RiskLevel.MEDIUM
    category = ClauseCategory.GOVERNING_LAW
    description = "Flags choice of law or venue outside standard domestic commercial forums."

    FOREIGN_VENUES = [
        re.compile(r"\b(england\s+and\s+wales|london|united\s+kingdom)\b", re.IGNORECASE),
        re.compile(r"\b(singapore|siac|hong\s+kong|hkiac)\b", re.IGNORECASE),
        re.compile(r"\b(cayman\s+islands|bermuda|british\s+virgin\s+islands|bvi)\b", re.IGNORECASE),
        re.compile(r"\b(switzerland|geneva|zurich|icc\s+paris)\b", re.IGNORECASE),
        re.compile(r"\b(courts?\s+located\s+in\s+india|republic\s+of\s+india)\b", re.IGNORECASE),
    ]

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        seen_keys = set()
        for unit in _build_stitched_units(chunks):
            text = unit["text"]
            for pat in self.FOREIGN_VENUES:
                m = pat.search(text)
                if m:
                    venue = re.sub(r"\s+", " ", m.group(0)).strip()
                    key = (unit["page_number"], venue.lower())
                    if key in seen_keys:
                        break
                    seen_keys.add(key)
                    findings.append(RuleFinding(
                        rule_id=self.id,
                        category=self.category,
                        risk_level=self.severity,
                        issue_title=f"Foreign or Cross-Border Venue Carve-Out: '{venue}'",
                        description=f"Agreement permits litigation or injunctive relief in a foreign or cross-border forum ('{venue}'). Cross-border enforcement creates significant cost and jurisdictional exposure.",
                        page_number=unit["page_number"],
                        section=unit["section"],
                        verbatim_text=text[:300] + ("..." if len(text) > 300 else ""),
                        bbox=unit["bbox"],
                        confidence=1.0,
                        detection_method=DetectionMethod.RULE
                    ))
                    break
        return findings


class AuditAndRecordProductionRule(RiskRule):
    """
    Detects invasive books-and-records inspection rights, customer audit pass-throughs,
    and mandatory record production / refund obligations.
    """
    id = "AUDIT_AND_RECORDS_EXPOSURE"
    name = "Invasive Books & Records Audit / Production Obligation"
    severity = RiskLevel.MEDIUM
    category = ClauseCategory.CONFIDENTIALITY
    description = "Flags clauses requiring contractor/vendor to open books & records to counterparty or third-party customers and produce financial/compliance records."

    AUDIT_PATTERNS = [
        re.compile(
            r"\b(review\s+the\s+books\s+and\s+records|permit\s+an\s+on-?site\s+audit|books\s+and\s+records\s+during\s+the\s+term)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(software\s+development,\s+legal\s+compliance\s+and\s+other\s+records|promptly\s+refund\s+to\s+Company\s+any\s+overpayments)\b",
            re.IGNORECASE,
        ),
    ]

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        seen_sections = set()
        for unit in _build_stitched_units(chunks):
            text = unit["text"]
            for pat in self.AUDIT_PATTERNS:
                m = pat.search(text)
                if m:
                    sec_key = (unit["page_number"], unit["section"] or "audit")
                    if sec_key in seen_sections:
                        break
                    seen_sections.add(sec_key)
                    findings.append(RuleFinding(
                        rule_id=self.id,
                        category=self.category,
                        risk_level=self.severity,
                        issue_title="Books & Records Inspection & Customer Audit Exposure",
                        description=(
                            f"Clause grants broad books-and-records inspection and audit rights ('{m.group(0)}'), "
                            "including third-party customer audit access, record retention, and mandatory overpayment refunds."
                        ),
                        page_number=unit["page_number"],
                        section=unit["section"],
                        verbatim_text=text[:300] + ("..." if len(text) > 300 else ""),
                        bbox=unit["bbox"],
                        confidence=1.0,
                        detection_method=DetectionMethod.RULE
                    ))
                    break
        return findings


class RestrictiveCovenantAndIPRule(RiskRule):
    """
    Detects post-termination employee/customer non-solicitation covenants (12-24+ months),
    unconditional moral rights waivers, and continuous source-code deposit mandates.
    """
    id = "RESTRICTIVE_COVENANT_AND_IP"
    name = "Post-Termination Non-Solicitation & Broad IP / Source Code Mandate"
    severity = RiskLevel.MEDIUM
    category = ClauseCategory.INTELLECTUAL_PROPERTY
    description = "Flags multi-year post-termination non-solicitation restrictions and mandatory weekly source code deposit / moral rights waiver obligations."

    RESTRICTIVE_PATTERNS = [
        re.compile(
            r"\b(Non-?Solicitation\s+Period\s+shall\s+be\s+for\s+a\s+period\s+of\s+\d+\s+months|Customer\s+Solicitation\s+Period\s+shall\s+be\s+for\s+the\s+term[^.;]{0,60}\d+\s+months)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(waive\s+all\s+moral\s+rights|place,\s+on\s+at\s+least\s+a\s+weekly\s+basis,\s+an\s+updated\s+electronic\s+copy\s+of\s+the\s+source\s+code)\b",
            re.IGNORECASE,
        ),
    ]

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        seen_keys = set()
        for unit in _build_stitched_units(chunks):
            text = unit["text"]
            for pat in self.RESTRICTIVE_PATTERNS:
                m = pat.search(text)
                if m:
                    phrase = re.sub(r"\s+", " ", m.group(0)).strip()
                    key = (unit["page_number"], unit["section"], phrase[:25].lower())
                    if key in seen_keys:
                        break
                    seen_keys.add(key)
                    findings.append(RuleFinding(
                        rule_id=self.id,
                        category=self.category,
                        risk_level=self.severity,
                        issue_title=f"Restrictive Covenant / IP Deposit Mandate (Sec. {unit['section'] or 'General'})",
                        description=(
                            f"Contract imposes binding restrictive or IP operational obligation: '{phrase}'. "
                            "Review post-termination restraint duration and continuous source-code delivery burden."
                        ),
                        page_number=unit["page_number"],
                        section=unit["section"],
                        verbatim_text=text[:300] + ("..." if len(text) > 300 else ""),
                        bbox=unit["bbox"],
                        confidence=1.0,
                        detection_method=DetectionMethod.RULE
                    ))
                    break
        return findings


class OperationalCovenantAndNoticeRule(RiskRule):
    """
    Surfaces standard/low-severity operational obligations so Reviewer obligations
    (written notice requirements, signatory authority warranties, and self-funded further assurances)
    are visible in the Risk & Obligations Matrix under LOW / STANDARD TERMS.
    """
    id = "OPERATIONAL_COVENANTS"
    name = "Operational Notice, Authority Warranty & Self-Funded Further Assurances"
    severity = RiskLevel.LOW
    category = ClauseCategory.GOVERNING_LAW
    description = "Flags standard operational duties including written notice delivery rules, authority representations, and self-funded further assurances."

    COVENANT_PATTERNS = [
        (
            "Self-Funded Further Assurances Obligation",
            re.compile(
                r"\b(parties\s+shall\s+at\s+their\s+own\s+cost\s+and\s+expense\s+execute\s+and\s+deliver\s+such\s+further\s+documents)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "Formal Written Notice & Delivery Covenant",
            re.compile(
                r"\b(Any\s+notice\s+or\s+other\s+communication\s+required\s+or\s+permitted\s+hereunder\s+shall\s+be\s+given\s+in\s+writing)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "Mutual Signatory Authority Representation & Warranty",
            re.compile(
                r"\b(Each\s+party\s+represents\s+and\s+warrants\s+to\s+the\s+other\s+that\s+the\s+execution\s+and\s+delivery\s+of\s+the\s+Agreement)\b",
                re.IGNORECASE,
            ),
        ),
    ]

    def evaluate(self, chunks: List[Any], classified_clauses: Dict[str, Any]) -> List[RuleFinding]:
        findings = []
        seen_titles = set()
        for unit in _build_stitched_units(chunks):
            text = unit["text"]
            for title, pat in self.COVENANT_PATTERNS:
                m = pat.search(text)
                if m and title not in seen_titles:
                    seen_titles.add(title)
                    phrase = re.sub(r"\s+", " ", m.group(0)).strip()
                    findings.append(RuleFinding(
                        rule_id=self.id,
                        category=self.category,
                        risk_level=self.severity,
                        issue_title=title,
                        description=(
                            f"Standard affirmative covenant detected ('{phrase}'). "
                            "Requires ongoing procedural compliance (written notice at designated address, authority warranty, or executing further instruments at party's own cost)."
                        ),
                        page_number=unit["page_number"],
                        section=unit["section"],
                        verbatim_text=text[:300] + ("..." if len(text) > 300 else ""),
                        bbox=unit["bbox"],
                        confidence=1.0,
                        detection_method=DetectionMethod.RULE
                    ))
        return findings
