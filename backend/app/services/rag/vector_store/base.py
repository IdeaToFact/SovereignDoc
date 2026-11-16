# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class VectorStore(ABC):
    """Abstract Base Class for Vector Database Providers."""

    @abstractmethod
    def add_vectors(self, vault_id: str, chunk_ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]] | None = None) -> None:
        """Store chunk IDs and their dense vector embeddings (lean index)."""
        pass

    @abstractmethod
    def search(
        self,
        vault_id: str,
        query_vector: List[float],
        top_k: int = 5,
        document_id: str | None = None
    ) -> List[Dict[str, Any]]:
        """Return top matching chunk_ids with vector similarity/distance scores, optionally scoped to a single document."""
        pass

    @abstractmethod
    def delete_document_vectors(self, vault_id: str, chunk_ids: List[str]) -> None:
        """Delete specific chunk vectors from the index."""
        pass

    @abstractmethod
    def delete_vault_collection(self, vault_id: str) -> None:
        """Delete the entire vector collection for a vault."""
        pass

    @abstractmethod
    def get_stats(self, vault_id: str) -> Dict[str, Any]:
        """Return vector index statistics (total vectors, dimension)."""
        pass
