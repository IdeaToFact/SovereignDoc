# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from app.services.llm.base import LLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.model_registry import ModelRegistry

# Default global instance initialized with OllamaProvider
_default_provider = OllamaProvider()
model_registry = ModelRegistry(provider=_default_provider)


def get_model_registry() -> ModelRegistry:
    """Return the active model registry singleton."""
    return model_registry


def get_llm_provider() -> LLMProvider:
    """Return the active LLM provider singleton."""
    return model_registry.provider
