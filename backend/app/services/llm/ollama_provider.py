# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
import time
import httpx
from typing import Any, AsyncGenerator, Dict, List
from app.config import settings
from app.services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Async client implementation for local Ollama instances."""

    def __init__(self, base_url: str = settings.ollama_url):
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def get_health(self) -> Dict[str, Any]:
        """Check Ollama service status and availability."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                if res.status_code == 200:
                    models = await self.get_models()
                    status = "ONLINE_READY" if len(models) > 0 else "ONLINE_NO_MODELS"
                    return {"status": status, "version": res.json().get("version")}
        except Exception:
            pass
        return {"status": "OFFLINE", "version": None}

    async def get_models(self) -> List[Dict[str, Any]]:
        """Retrieve all installed models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    raw_models = res.json().get("models", [])
                    formatted = []
                    for m in raw_models:
                        size_gb = round(m.get("size", 0) / (1024**3), 2)
                        details = m.get("details", {})
                        formatted.append({
                            "name": m.get("name"),
                            "size_gb": size_gb,
                            "modified_at": m.get("modified_at", ""),
                            "family": details.get("family", "unknown")
                        })
                    return formatted
        except Exception:
            pass
        return []

    async def generate(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Execute a local completion call via Ollama /api/generate."""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(f"{self.base_url}/api/generate", json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Ollama generation failed ({res.status_code}): {res.text}")

            data = res.json()
            total_time = time.time() - start_time
            eval_count = data.get("eval_count", 0)
            eval_duration_sec = (
                data.get("eval_duration", 0) / 1e9
                if data.get("eval_duration")
                else total_time
            )
            tps = round(eval_count / eval_duration_sec, 2) if eval_duration_sec > 0 else 0.0

            return {
                "model": model_name,
                "response": data.get("response", ""),
                "tokens_generated": eval_count,
                "eval_duration_seconds": round(eval_duration_sec, 2),
                "tokens_per_second": tps
            }

    async def generate_stream(self, model_name: str, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream completion tokens from Ollama /api/generate."""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                if response.status_code != 200:
                    error_bytes = await response.aread()
                    raise RuntimeError(f"Ollama stream failed ({response.status_code}): {error_bytes.decode('utf-8', errors='ignore')}")

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        yield chunk
                    except json.JSONDecodeError:
                        continue
