# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from rank_bm25 import BM25Okapi


class BM25Index:
    """In-memory BM25 sparse keyword search index with local vault persistence."""

    def __init__(self, vault_dir: Path):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.vault_dir / "bm25_index.json"
        self.chunks: List[Dict[str, Any]] = []
        self.bm25: BM25Okapi | None = None
        self._load()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple lowercase alphanumeric tokenizer."""
        return re.findall(r"\b\w+\b", text.lower())

    def _load(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                corpus = [self._tokenize(c["text"]) for c in self.chunks]
                if corpus:
                    self.bm25 = BM25Okapi(corpus)
            except Exception:
                self.chunks = []
                self.bm25 = None

    def save(self):
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        """Add new chunks (id and text) and re-index."""
        # Store only id and text to keep index lightweight
        for c in new_chunks:
            self.chunks.append({
                "chunk_id": c["id"],
                "document_id": c.get("document_id"),
                "text": c["text"]
            })
        corpus = [self._tokenize(c["text"]) for c in self.chunks]
        if corpus:
            self.bm25 = BM25Okapi(corpus)
        self.save()

    def remove_document_chunks(self, document_id: str):
        """Remove chunks belonging to a document and rebuild index."""
        self.chunks = [c for c in self.chunks if c.get("document_id") != document_id]
        corpus = [self._tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(corpus) if corpus else None
        self.save()

    def search_sparse(
        self,
        query: str,
        top_k: int = 5,
        document_id: str | None = None
    ) -> List[Dict[str, Any]]:
        """Search query against BM25 corpus, optionally scoped to a single document."""
        if not self.bm25 or not self.chunks:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)

        # Determine candidate indices (optionally scoped to document_id)
        candidate_indices = range(len(scores))
        if document_id:
            candidate_indices = [
                i for i in candidate_indices
                if self.chunks[i].get("document_id") == document_id
                or str(self.chunks[i].get("chunk_id", "")).startswith(f"{document_id}_")
            ]
            if not candidate_indices:
                return []

        top_indices = sorted(candidate_indices, key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "chunk_id": self.chunks[idx]["chunk_id"],
                    "bm25_score": round(float(scores[idx]), 4)
                })
        return results
