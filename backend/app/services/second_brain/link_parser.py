# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import re
from typing import Any, Dict, List
from packages.contract_intelligence.enums import GraphNodeType


class WikiLinkParser:
    """Extracts [[WikiLinks]] and #tags from Markdown note content."""

    # Matches [[Target]] or [[Target|Alias]]
    WIKILINK_REGEX = re.compile(r"\[\[([^\[\]\n]+)\]\]")

    # Matches #tags (starts with letter, 2-36 chars, not preceded by word char or '&')
    TAG_REGEX = re.compile(r"(?:^|(?<=\s))#([a-zA-Z][a-zA-Z0-9_\-]{1,35})\b", re.MULTILINE)

    # Matches Document link syntax: Doc:Filename#Page 6 or Document:Filename#p6
    DOC_LINK_REGEX = re.compile(
        r"^(?:Doc|Document)\s*:\s*([^#|\n]+?)(?:#(?:Page|p\.?)\s*(\d+))?\s*$",
        re.IGNORECASE,
    )

    RISK_LINK_REGEX = re.compile(r"^Risk\s*:\s*([a-zA-Z0-9_\-]+)\s*$", re.IGNORECASE)
    OBLIGATION_LINK_REGEX = re.compile(r"^Obligation\s*:\s*([a-zA-Z0-9_\-]+)\s*$", re.IGNORECASE)

    @classmethod
    def extract_tags(cls, content_md: str, extra_tags: List[str] | None = None) -> List[str]:
        """Extract deduplicated lowercase #tags from markdown content (excluding code blocks)."""
        cleaned = re.sub(r"```[\s\S]*?```", "", content_md or "")
        cleaned = re.sub(r"`[^`\n]+`", "", cleaned)
        found = [m.group(1).lower() for m in cls.TAG_REGEX.finditer(cleaned)]
        if extra_tags:
            for t in extra_tags:
                t_clean = str(t).lstrip("#").strip().lower()
                if t_clean:
                    found.append(t_clean)
        # Preserve order while deduplicating
        seen = set()
        result = []
        for tag in found:
            if tag not in seen:
                seen.add(tag)
                result.append(tag)
        return result

    @classmethod
    def extract_links(cls, content_md: str) -> List[Dict[str, Any]]:
        """Extract structured [[WikiLinks]] from markdown content.

        Returns list of dicts:
          - raw_text: original inner text
          - link_type: GraphNodeType ('NOTE' | 'DOCUMENT' | 'RISK' | 'OBLIGATION')
          - target_title / target_filename / target_id / target_page
        """
        if not content_md:
            return []

        cleaned = re.sub(r"```[\s\S]*?```", "", content_md)
        links: List[Dict[str, Any]] = []
        seen_keys = set()

        for match in cls.WIKILINK_REGEX.finditer(cleaned):
            inner = match.group(1).strip()
            if not inner:
                continue

            # Split optional display alias [[Target|Display Label]]
            target_part = inner.split("|", 1)[0].strip()
            if not target_part:
                continue

            doc_m = cls.DOC_LINK_REGEX.match(target_part)
            if doc_m:
                filename = doc_m.group(1).strip()
                page = int(doc_m.group(2)) if doc_m.group(2) else None
                key = ("DOCUMENT", filename.lower(), page)
                if key not in seen_keys:
                    seen_keys.add(key)
                    links.append({
                        "link_text": inner,
                        "link_type": GraphNodeType.DOCUMENT.value,
                        "target_filename": filename,
                        "target_page": page,
                    })
                continue

            risk_m = cls.RISK_LINK_REGEX.match(target_part)
            if risk_m:
                risk_id = risk_m.group(1).strip()
                key = ("RISK", risk_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    links.append({
                        "link_text": inner,
                        "link_type": GraphNodeType.RISK.value,
                        "target_risk_id": risk_id,
                    })
                continue

            obl_m = cls.OBLIGATION_LINK_REGEX.match(target_part)
            if obl_m:
                obl_id = obl_m.group(1).strip()
                key = ("OBLIGATION", obl_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    links.append({
                        "link_text": inner,
                        "link_type": GraphNodeType.OBLIGATION.value,
                        "target_obligation_id": obl_id,
                    })
                continue

            # Default: Note-to-Note WikiLink
            key = ("NOTE", target_part.lower())
            if key not in seen_keys:
                seen_keys.add(key)
                links.append({
                    "link_text": inner,
                    "link_type": GraphNodeType.NOTE.value,
                    "target_note_title": target_part,
                })

        return links


wiki_link_parser = WikiLinkParser()

