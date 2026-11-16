# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import os
from typing import List, Optional
from fastembed.rerank.cross_encoder import TextCrossEncoder
from app.services.rag.model_loader import get_default_reranker_model, load_fastembed_model


class CrossEncoderRerankerService:
    """Local Cross-Encoder reranker using ONNX runtime.
    
    Default model: 'Xenova/ms-marco-MiniLM-L-6-v2' (lightweight 80MB default for Community Edition).
    Commercial deployments can configure 'BAAI/bge-reranker-base' (MIT) or 
    'jinaai/jina-reranker-v1-tiny-en' (Apache-2.0) via SOVEREIGNDOC_RERANKER_MODEL to align with
    commercial data terms.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        allow_download: Optional[bool] = None,
    ):
        if model_name is None:
            model_name = get_default_reranker_model()
        self.model_name = model_name
        self.allow_download = allow_download
        self._model = None

    @property
    def model(self):
        # Lazy initialization (fail-closed offline by default)
        if self._model is None:
            self._model = load_fastembed_model(
                TextCrossEncoder,
                self.model_name,
                allow_download=self.allow_download,
            )
        return self._model

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        """Calculate cross-encoder scores for (query, document) pairs."""
        if not documents:
            return []
        scores = list(self.model.rerank(query, documents))
        return [round(float(s), 4) for s in scores]


reranker_service = CrossEncoderRerankerService()
