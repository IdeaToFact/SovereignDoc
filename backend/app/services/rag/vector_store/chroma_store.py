# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
from typing import Any, Dict, List
import chromadb
from app.config import settings
from app.services.rag.vector_store.base import VectorStore


class ChromaVectorStore(VectorStore):
    """Concrete VectorStore implementation using local persistent ChromaDB."""

    def __init__(self, db_dir: Path = settings.base_data_dir / "db"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.db_dir))

    def _get_collection_name(self, vault_id: str) -> str:
        safe_name = f"vault_{vault_id}".replace("-", "_")
        return safe_name[:63]

    def _get_collection(self, vault_id: str):
        collection_name = self._get_collection_name(vault_id)
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_vectors(
        self,
        vault_id: str,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]] | None = None
    ) -> None:
        """Store chunk IDs and vectors (lean vector index)."""
        collection = self._get_collection(vault_id)
        dummy_docs = [""] * len(chunk_ids)
        safe_metadatas: Any = metadatas or [{"id": cid} for cid in chunk_ids]
        safe_embeddings: Any = embeddings

        collection.add(
            ids=chunk_ids,
            embeddings=safe_embeddings,
            documents=dummy_docs,
            metadatas=safe_metadatas
        )

    def search(
        self,
        vault_id: str,
        query_vector: List[float],
        top_k: int = 5,
        document_id: str | None = None
    ) -> List[Dict[str, Any]]:
        collection = self._get_collection(vault_id)
        count = collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        query_embeddings: Any = [query_vector]
        where_filter = {"document_id": document_id} if document_id else None

        try:
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=actual_k,
                where=where_filter
            )
        except Exception:
            # Fallback if metadata schema or version does not support where filter
            results = collection.query(query_embeddings=query_embeddings, n_results=actual_k)

        formatted = []
        if results["ids"] and results["ids"][0]:
            for idx in range(len(results["ids"][0])):
                cid = results["ids"][0][idx]
                distance = results["distances"][0][idx] if results["distances"] else 0.0
                formatted.append({
                    "chunk_id": cid,
                    "distance": round(float(distance), 4)
                })
        return formatted

    def delete_document_vectors(self, vault_id: str, chunk_ids: List[str]) -> None:
        collection = self._get_collection(vault_id)
        if chunk_ids:
            try:
                collection.delete(ids=chunk_ids)
            except Exception:
                pass

    def delete_vault_collection(self, vault_id: str) -> None:
        name = self._get_collection_name(vault_id)
        try:
            self.client.delete_collection(name=name)
        except Exception:
            pass

    def get_stats(self, vault_id: str) -> Dict[str, Any]:
        collection = self._get_collection(vault_id)
        return {
            "provider": "ChromaDB",
            "collection": collection.name,
            "total_vectors": collection.count()
        }


vector_store = ChromaVectorStore()
