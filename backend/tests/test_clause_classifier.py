# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Legal Clause Classifier Tests
"""
from packages.contract_intelligence.classifiers.clause_classifier import ClauseClassifier
from packages.contract_intelligence.enums import ClauseCategory, DetectionMethod


def test_clause_classification_families():
    """Verifies ClauseClassifier identifies standard legal clause families."""
    classifier = ClauseClassifier()

    chunks = [
        {
            "id": "chk_1",
            "document_id": "doc_test",
            "text": "SECTION 1. CONFIDENTIALITY. Each party agrees not to disclose proprietary trade secrets.",
            "page_number": 1,
            "section": "1",
            "section_title": "CONFIDENTIALITY"
        },
        {
            "id": "chk_2",
            "document_id": "doc_test",
            "text": "SECTION 2. TERMINATION. Either party may terminate this agreement on 30 days written notice.",
            "page_number": 1,
            "section": "2",
            "section_title": "TERMINATION"
        },
        {
            "id": "chk_3",
            "document_id": "doc_test",
            "text": "SECTION 3. INDEMNIFICATION. Contractor shall indemnify and hold harmless the Company.",
            "page_number": 2,
            "section": "3",
            "section_title": "INDEMNIFICATION"
        }
    ]

    results_by_cat = classifier.classify_chunks(chunks, document_id="doc_test")
    assert len(results_by_cat) >= 1

    categories = list(results_by_cat.keys())
    assert ClauseCategory.CONFIDENTIALITY in categories or ClauseCategory.TERMINATION in categories or ClauseCategory.INDEMNIFICATION in categories

