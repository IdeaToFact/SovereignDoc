# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Enforce strict air-gap telemetry and offline model lockdown at process startup
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_IMPL", "none")
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
if os.environ.get("SOVEREIGNDOC_ALLOW_MODEL_DOWNLOADS", "").strip().lower() not in {"1", "true", "yes"}:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")


class Settings(BaseSettings):
    app_name: str = "SovereignDoc"
    version: str = "1.1.0-community"
    debug: bool = False
    sovereign_mode: bool = True
    allow_model_downloads: bool = False

    # Server configuration (strictly localhost for air-gap protection)
    host: str = "127.0.0.1"
    port: int = 8000

    # Provider endpoints (supports both OLLAMA_BASE_URL and SOVEREIGNDOC_OLLAMA_URL)
    ollama_url: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    default_llm_provider: str = "ollama"

    # Path configuration - defaults to ~/.sovereigndoc
    base_data_dir: Path = Path.home() / ".sovereigndoc"

    model_config = SettingsConfigDict(env_prefix="SOVEREIGNDOC_")


settings = Settings()
