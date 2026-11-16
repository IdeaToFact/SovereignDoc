# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from typing import List, Optional
from fastembed import TextEmbedding
from app.services.rag.model_loader import DEFAULT_EMBEDDING_MODEL, load_fastembed_model


class FastEmbedService:
    """Generates 100% local dense vector embeddings using ONNX runtime (BGE-small-en-v1.5)."""

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        allow_download: Optional[bool] = None,
    ):
        self.model_name = model_name
        self.allow_download = allow_download
        self._model = None

    @property
    def model(self):
        # Lazy initialization (fail-closed offline by default)
        if self._model is None:
            self._model = load_fastembed_model(
                TextEmbedding,
                self.model_name,
                allow_download=self.allow_download,
            )
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch embed multiple text strings into dense 384-dimensional vectors."""
        if not texts:
            return []
        embeddings_generator = self.model.embed(texts)
        return [e.tolist() for e in embeddings_generator]

    def embed_query(self, query: str) -> List[float]:
        """Embed a single search query string."""
        return self.embed_texts([query])[0]


embedding_service = FastEmbedService()
