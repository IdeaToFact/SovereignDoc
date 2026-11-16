# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List


class LLMProvider(ABC):
    """Abstract Base Class for LLM runtime providers (Ollama, LM Studio, vLLM, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'ollama', 'lm_studio', 'vllm')."""
        pass

    @abstractmethod
    async def get_health(self) -> Dict[str, Any]:
        """Returns provider status (ONLINE_READY, ONLINE_NO_MODELS, OFFLINE)."""
        pass

    @abstractmethod
    async def get_models(self) -> List[Dict[str, Any]]:
        """Returns list of raw discovered models from the local provider."""
        pass

    @abstractmethod
    async def generate(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Executes a local inference completion call."""
        pass

    async def generate_stream(self, model_name: str, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Yields streaming token objects from the local provider."""
        res = await self.generate(model_name, prompt)
        yield {"response": res.get("response", ""), "done": True, "eval_count": res.get("tokens_generated", 0)}
