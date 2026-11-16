# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
import re
from typing import Any, Dict, List


class StructureAwareChunker:
    """Splits structured text blocks into semantic chunks with overlap,

    protecting legal abbreviations and linking sequential chunks (previous/next).
    """

    # Protected abbreviation list to avoid splitting mid-sentence
    ABBREVIATION_PATTERN = re.compile(
        r"\b(Sec|Section|Art|Article|No|Vol|Rev|Stat|v|vs|Mr|Mrs|Ms|Dr|Prof|"
        r"Inc|Corp|Co|Ltd|LLC|LLP|Gov|Dept|U\.S|U\.K|e\.g|i\.e|et al|approx|"
        r"\d+(?:\.\d+)*)\.",
        re.IGNORECASE
    )

    def __init__(self, target_chunk_size: int = 600, overlap: int = 100):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while protecting legal & corporate abbreviations."""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        # 1. Protect abbreviations by replacing '.' with '<|PROTECTED_DOT|>'
        protected = self.ABBREVIATION_PATTERN.sub(r"\1<|PROTECTED_DOT|>", normalized)

        # 2. Split on sentence boundaries: (. ! ?) followed by whitespace or newline
        raw_parts = re.split(r"([.!?])(?:\s+|\n+)", protected)

        # Recombine delimiters with sentences
        sentences = []
        i = 0
        while i < len(raw_parts):
            part = raw_parts[i]
            if i + 1 < len(raw_parts) and raw_parts[i + 1] in [".", "!", "?"]:
                part = part + raw_parts[i + 1]
                i += 2
            else:
                i += 1

            # 3. Restore protected dots
            restored = part.replace("<|PROTECTED_DOT|>", ".").strip()
            if restored:
                sentences.append(restored)

        return sentences if sentences else [text.strip()]

    def chunk_document(
        self,
        doc_id: str,
        vault_id: str,
        doc_name: str,
        blocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        raw_chunks = []
        chunk_counter = 1

        for block in blocks:
            text = block["text"]
            page_no = block.get("page_number", 1)
            section_title = block.get("section_title") or doc_name
            article = block.get("article")
            section = block.get("section")
            subsection = block.get("subsection")
            bbox = block.get("bbox")

            # Small block: keep as single chunk
            if len(text) <= self.target_chunk_size:
                cid = f"{doc_id}_p{page_no}_c{chunk_counter}"
                raw_chunks.append({
                    "id": cid,
                    "document_id": doc_id,
                    "vault_id": vault_id,
                    "page_number": page_no,
                    "article": article,
                    "section": section,
                    "subsection": subsection,
                    "bbox_json": json.dumps(bbox) if bbox else None,
                    "bbox": bbox,
                    "section_title": section_title,
                    "text": text,
                    "char_length": len(text),
                    "token_count": max(1, len(text) // 4)
                })
                chunk_counter += 1
            else:
                # Group sentences into chunks respecting target size and overlap
                sentences = self.split_into_sentences(text)
                current_group = []
                current_len = 0

                for s in sentences:
                    current_group.append(s)
                    current_len += len(s) + 1

                    if current_len >= self.target_chunk_size:
                        chunk_text = " ".join(current_group).strip()
                        cid = f"{doc_id}_p{page_no}_c{chunk_counter}"
                        raw_chunks.append({
                            "id": cid,
                            "document_id": doc_id,
                            "vault_id": vault_id,
                            "page_number": page_no,
                            "article": article,
                            "section": section,
                            "subsection": subsection,
                            "bbox_json": json.dumps(bbox) if bbox else None,
                            "bbox": bbox,
                            "section_title": section_title,
                            "text": chunk_text,
                            "char_length": len(chunk_text),
                            "token_count": max(1, len(chunk_text) // 4)
                        })
                        chunk_counter += 1

                        # Keep last sentence for overlap if multiple sentences exist
                        if len(current_group) > 1:
                            current_group = current_group[-1:]
                            current_len = len(current_group[0])
                        else:
                            current_group = []
                            current_len = 0

                if current_group:
                    chunk_text = " ".join(current_group).strip()
                    cid = f"{doc_id}_p{page_no}_c{chunk_counter}"
                    raw_chunks.append({
                        "id": cid,
                        "document_id": doc_id,
                        "vault_id": vault_id,
                        "page_number": page_no,
                        "article": article,
                        "section": section,
                        "subsection": subsection,
                        "bbox_json": json.dumps(bbox) if bbox else None,
                        "bbox": bbox,
                        "section_title": section_title,
                        "text": chunk_text,
                        "char_length": len(chunk_text),
                        "token_count": max(1, len(chunk_text) // 4)
                    })
                    chunk_counter += 1

        # Link sequential chunks (chunk_index, previous_chunk_id, next_chunk_id)
        total_chunks = len(raw_chunks)
        for idx, chunk in enumerate(raw_chunks, start=1):
            chunk["chunk_index"] = idx
            chunk["previous_chunk_id"] = raw_chunks[idx - 2]["id"] if idx > 1 else None
            chunk["next_chunk_id"] = raw_chunks[idx]["id"] if idx < total_chunks else None
            chunk["parent_chunk_id"] = None

        return raw_chunks


chunker = StructureAwareChunker()
