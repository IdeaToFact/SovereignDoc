# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Core Clause Classifier Service (7 Essential Legal Types)
"""
import re
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from packages.contract_intelligence.enums import ClauseCategory, DetectionMethod

@dataclass
class ClassificationResult:
    """Represents a classified clause with provenance."""
    id: str
    document_id: str
    chunk_id: str
    category: ClauseCategory
    confidence: float
    detection_method: DetectionMethod
    page_number: int
    section: Optional[str]
    section_title: Optional[str]
    text: str
    bbox: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "category": self.category.value,
            "confidence": round(self.confidence, 3),
            "detection_method": self.detection_method.value,
            "page_number": self.page_number,
            "section": self.section,
            "section_title": self.section_title,
            "text": self.text,
            "bbox": self.bbox
        }

class ClauseClassifier:
    """
    Two-pass legal clause classifier.
    Pass 1: Regex & Section Heading Heuristics (High precision, confidence >= 0.95)
    Pass 2: Contextual Keyword Density & Proximity Scoring (confidence 0.70 - 0.90)
    """

    HEADING_PATTERNS = {
        ClauseCategory.INDEMNIFICATION: [
            re.compile(r"\b(indemnif\w*|hold harmless|defense of claims)\b", re.IGNORECASE),
        ],
        ClauseCategory.LIMITATION_OF_LIABILITY: [
            re.compile(r"\b(limitation of liability|liability cap|aggregate liability|waiver of damages|consequential damages)\b", re.IGNORECASE),
        ],
        ClauseCategory.TERMINATION: [
            re.compile(r"\b(term and termination|termination\b|early termination|cancellation for cause|cure period)\b", re.IGNORECASE),
        ],
        ClauseCategory.CONFIDENTIALITY: [
            re.compile(r"\b(confidentiality|non-disclosure|proprietary information|trade secrets)\b", re.IGNORECASE),
        ],
        ClauseCategory.INTELLECTUAL_PROPERTY: [
            re.compile(r"\b(intellectual property|ip ownership|inventions|work made for hire|license grant)\b", re.IGNORECASE),
        ],
        ClauseCategory.PAYMENT_TERMS: [
            re.compile(r"\b(payment terms?|fees and payment|invoicing|billing|taxes and fees)\b", re.IGNORECASE),
        ],
        ClauseCategory.GOVERNING_LAW: [
            re.compile(r"\b(governing law|choice of law|jurisdiction|venue|dispute resolution|arbitration)\b", re.IGNORECASE),
        ],
    }

    BODY_KEYWORD_SETS = {
        ClauseCategory.INDEMNIFICATION: [
            "indemnify", "indemnification", "indemnitee", "indemnitor", "hold harmless", "defend against", "third-party claim", "losses, damages"
        ],
        ClauseCategory.LIMITATION_OF_LIABILITY: [
            "liability", "aggregate liability", "not exceed", "consequential damages", "indirect damages", "lost profits", "disclaimer", "cap"
        ],
        ClauseCategory.TERMINATION: [
            "terminate", "termination", "material breach", "written notice", "cure period", "days notice", "survival upon termination"
        ],
        ClauseCategory.CONFIDENTIALITY: [
            "confidential", "confidentiality", "receiving party", "disclosing party", "standard of care", "non-disclosure", "marked confidential"
        ],
        ClauseCategory.INTELLECTUAL_PROPERTY: [
            "intellectual property", "patents", "copyrights", "trademarks", "trade secrets", "work made for hire", "retains all right", "license"
        ],
        ClauseCategory.PAYMENT_TERMS: [
            "invoice", "invoicing", "payment", "net 30", "due within", "late fee", "interest rate", "payable"
        ],
        ClauseCategory.GOVERNING_LAW: [
            "governed by", "laws of the state", "jurisdiction", "exclusive venue", "courts of", "dispute", "arbitration"
        ],
    }

    def classify_chunk(self, chunk: Any, document_id: str) -> Optional[ClassificationResult]:
        """
        Classifies a single chunk into one of the 7 core legal clause categories.
        """
        # Extract fields whether chunk is an ORM model or a dict
        chunk_id = getattr(chunk, "id", None) or (chunk.get("id") if isinstance(chunk, dict) else str(uuid.uuid4()))
        section_title = getattr(chunk, "section_title", None) or (chunk.get("section_title") if isinstance(chunk, dict) else "") or ""
        article = getattr(chunk, "article", None) or (chunk.get("article") if isinstance(chunk, dict) else "") or ""
        section = getattr(chunk, "section", None) or (chunk.get("section") if isinstance(chunk, dict) else "") or ""
        text = getattr(chunk, "text", None) or (chunk.get("text") if isinstance(chunk, dict) else "") or ""
        page_number = getattr(chunk, "page_number", 1) or (chunk.get("page_number", 1) if isinstance(chunk, dict) else 1)
        bbox = getattr(chunk, "bbox", None) or (chunk.get("bbox") if isinstance(chunk, dict) else None)
        
        # If bbox is a JSON string from SQLite ORM
        if bbox is None:
            bbox_json = getattr(chunk, "bbox_json", None) or (chunk.get("bbox_json") if isinstance(chunk, dict) else None)
            if bbox_json:
                import json
                try:
                    bbox = json.loads(bbox_json)
                except Exception:
                    bbox = None

        heading_corpus = f"{article} {section} {section_title}".strip()
        first_line = text.split("\n")[0] if text else ""

        # Pass 1: Heading & Explicit Clause Title Pattern Matching
        for category, patterns in self.HEADING_PATTERNS.items():
            for pat in patterns:
                if pat.search(heading_corpus) or pat.search(first_line):
                    return ClassificationResult(
                        id=f"cls_{uuid.uuid4().hex[:12]}",
                        document_id=document_id,
                        chunk_id=chunk_id,
                        category=category,
                        confidence=0.98,
                        detection_method=DetectionMethod.REGEX,
                        page_number=page_number,
                        section=section or None,
                        section_title=section_title or None,
                        text=text,
                        bbox=bbox
                    )

        # Pass 2: Keyword density scoring in body text
        text_lower = text.lower()
        best_category = None
        best_score = 0
        
        for category, keywords in self.BODY_KEYWORD_SETS.items():
            matched_count = sum(1 for kw in keywords if kw in text_lower)
            if matched_count >= 2:
                score = matched_count / len(keywords)
                if score > best_score:
                    best_score = score
                    best_category = category

        if best_category and best_score >= 0.25:
            # Calibrated confidence based on keyword density
            calibrated_conf = min(0.92, 0.70 + (best_score * 0.35))
            return ClassificationResult(
                id=f"cls_{uuid.uuid4().hex[:12]}",
                document_id=document_id,
                chunk_id=chunk_id,
                category=best_category,
                confidence=calibrated_conf,
                detection_method=DetectionMethod.CLASSIFIER,
                page_number=page_number,
                section=section or None,
                section_title=section_title or None,
                text=text,
                bbox=bbox
            )

        return None

    def classify_chunks(self, chunks: List[Any], document_id: str) -> Dict[ClauseCategory, List[ClassificationResult]]:
        """
        Classifies all chunks in a document and returns a grouped dictionary.
        """
        results: Dict[ClauseCategory, List[ClassificationResult]] = {cat: [] for cat in ClauseCategory}
        for chunk in chunks:
            res = self.classify_chunk(chunk, document_id)
            if res:
                results[res.category].append(res)
        return results

clause_classifier = ClauseClassifier()
