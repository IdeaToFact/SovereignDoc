# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any, Dict, List, Optional
from app.services.hardware_info import hardware_profiler
from app.services.llm.base import LLMProvider


class ModelRegistry:
    """Manages model discovery, active selection, and capability evaluation."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.active_model: Optional[str] = None

    async def get_evaluated_models(self) -> List[Dict[str, Any]]:
        raw_models = await self.provider.get_models()
        hw_profile = hardware_profiler.get_hardware_profile()
        eff_mem = hw_profile["capability_profile"]["effective_memory_gb"]

        evaluated = []
        for m in raw_models:
            size_gb = m["size_gb"]
            # Compatibility scoring based on hardware memory footprint
            compatible = size_gb <= (eff_mem * 1.2)
            recommended = compatible and (size_gb <= eff_mem * 0.85)

            if size_gb <= eff_mem * 0.5:
                perf_class = "⚡ Excellent (Ultra-Fast)"
            elif compatible:
                perf_class = "🟢 Good (Balanced)"
            else:
                perf_class = "⚠️ Slow (Memory Pressure)"

            m_meta = {
                **m,
                "compatible": compatible,
                "recommended": recommended,
                "performance_class": perf_class
            }
            evaluated.append(m_meta)

        # Set default active model if unassigned
        if evaluated and not self.active_model:
            # Pick first recommended model, or fallback to first available
            recommended_models = [m["name"] for m in evaluated if m["recommended"]]
            self.active_model = recommended_models[0] if recommended_models else evaluated[0]["name"]

        return evaluated

    def set_active_model(self, model_name: str) -> None:
        self.active_model = model_name

    def get_active_model(self) -> Optional[str]:
        return self.active_model
