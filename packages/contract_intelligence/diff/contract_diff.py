# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Contract Redline & Word Diff Engine
Aligns clauses across two contract documents and computes token-level insertions and deletions.
"""
import difflib
import re
from typing import List, Dict, Any, Optional

class ContractDiffEngine:
    """
    Computes side-by-side synchronized word diffs and clause alignments.
    """

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        """Tokenize text into words and punctuation while preserving spacing."""
        return re.findall(r"\S+|\s+", text)

    @classmethod
    def compute_word_diff(cls, text_a: str, text_b: str) -> Dict[str, Any]:
        """
        Computes token-level word diff using SequenceMatcher.
        Returns diff tokens: list of {"type": "eq"|"ins"|"del", "text": str}.
        """
        words_a = cls._tokenize(text_a)
        words_b = cls._tokenize(text_b)

        matcher = difflib.SequenceMatcher(None, words_a, words_b)
        tokens = []
        additions = 0
        deletions = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                tokens.append({"type": "eq", "text": "".join(words_a[i1:i2])})
            elif tag == "delete":
                deleted_text = "".join(words_a[i1:i2])
                tokens.append({"type": "del", "text": deleted_text})
                deletions += len(deleted_text.split())
            elif tag == "insert":
                inserted_text = "".join(words_b[j1:j2])
                tokens.append({"type": "ins", "text": inserted_text})
                additions += len(inserted_text.split())
            elif tag == "replace":
                del_txt = "".join(words_a[i1:i2])
                ins_txt = "".join(words_b[j1:j2])
                tokens.append({"type": "del", "text": del_txt})
                tokens.append({"type": "ins", "text": ins_txt})
                deletions += len(del_txt.split())
                additions += len(ins_txt.split())

        return {
            "tokens": tokens,
            "additions": additions,
            "deletions": deletions
        }

    @classmethod
    def compare_documents(
        cls,
        doc_a_chunks: List[Any],
        doc_b_chunks: List[Any],
        doc_a_id: str,
        doc_b_id: str
    ) -> Dict[str, Any]:
        """
        Aligns clauses from Doc A and Doc B and computes clause-level diffs.
        """
        # Index Doc B chunks by section/title
        b_map: Dict[str, Any] = {}
        for ch in doc_b_chunks:
            sec = getattr(ch, "section", None) or (ch.get("section") if isinstance(ch, dict) else "") or ""
            title = getattr(ch, "section_title", None) or (ch.get("section_title") if isinstance(ch, dict) else "") or ""
            key = f"{sec}:{title}".strip(":")
            if key:
                b_map[key] = ch

        aligned_clauses = []
        total_adds = 0
        total_dels = 0
        matched_b_keys = set()

        for ch_a in doc_a_chunks:
            sec_a = getattr(ch_a, "section", None) or (ch_a.get("section") if isinstance(ch_a, dict) else "") or ""
            title_a = getattr(ch_a, "section_title", None) or (ch_a.get("section_title") if isinstance(ch_a, dict) else "") or ""
            text_a = getattr(ch_a, "text", None) or (ch_a.get("text") if isinstance(ch_a, dict) else "") or ""
            key_a = f"{sec_a}:{title_a}".strip(":")

            ch_b = b_map.get(key_a) if key_a else None
            if ch_b:
                matched_b_keys.add(key_a)
                text_b = getattr(ch_b, "text", None) or (ch_b.get("text") if isinstance(ch_b, dict) else "") or ""
                diff_res = cls.compute_word_diff(text_a, text_b)
                total_adds += diff_res["additions"]
                total_dels += diff_res["deletions"]
                status = "MODIFIED" if (diff_res["additions"] > 0 or diff_res["deletions"] > 0) else "UNCHANGED"
                aligned_clauses.append({
                    "section": sec_a or "General",
                    "title": title_a or "Standard Clause",
                    "status": status,
                    "additions": diff_res["additions"],
                    "deletions": diff_res["deletions"],
                    "tokens": diff_res["tokens"],
                    "text_a": text_a,
                    "text_b": text_b
                })
            else:
                # Clause was in Doc A but removed in Doc B
                words_count = len(text_a.split())
                total_dels += words_count
                aligned_clauses.append({
                    "section": sec_a or "General",
                    "title": title_a or "Removed Clause",
                    "status": "REMOVED",
                    "additions": 0,
                    "deletions": words_count,
                    "tokens": [{"type": "del", "text": text_a}],
                    "text_a": text_a,
                    "text_b": ""
                })

        # Find clauses in Doc B that were added
        for key_b, ch_b in b_map.items():
            if key_b not in matched_b_keys:
                sec_b = getattr(ch_b, "section", None) or (ch_b.get("section") if isinstance(ch_b, dict) else "") or ""
                title_b = getattr(ch_b, "section_title", None) or (ch_b.get("section_title") if isinstance(ch_b, dict) else "") or ""
                text_b = getattr(ch_b, "text", None) or (ch_b.get("text") if isinstance(ch_b, dict) else "") or ""
                words_count = len(text_b.split())
                total_adds += words_count
                aligned_clauses.append({
                    "section": sec_b or "General",
                    "title": title_b or "Added Clause",
                    "status": "ADDED",
                    "additions": words_count,
                    "deletions": 0,
                    "tokens": [{"type": "ins", "text": text_b}],
                    "text_a": "",
                    "text_b": text_b
                })

        summary = f"Comparison complete: {total_adds} word(s) added, {total_dels} word(s) deleted across {len(aligned_clauses)} clause section(s)."

        return {
            "doc_a_id": doc_a_id,
            "doc_b_id": doc_b_id,
            "total_additions": total_adds,
            "total_deletions": total_dels,
            "summary_text": summary,
            "clauses": aligned_clauses
        }

contract_diff = ContractDiffEngine()
