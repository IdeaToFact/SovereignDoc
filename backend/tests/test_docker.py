# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — Docker Deployment & Air-Gap Environment Tests
"""
import os
from app.config import settings


def test_airgap_environment_flags():
    """Verifies privacy, telemetry prevention, and offline settings."""
    assert os.environ.get("ANONYMIZED_TELEMETRY") == "False"
    assert os.environ.get("HF_HUB_DISABLE_TELEMETRY") == "1"
    assert os.environ.get("CHROMA_TELEMETRY_IMPL") == "none"


def test_cors_strictly_local():
    """Verifies CORS origins allow only local workstation access."""
    from app.main import app
    cors_middleware = next(
        (m for m in app.user_middleware if "CORSMiddleware" in str(m.cls)),
        None
    )
    assert cors_middleware is not None
    allow_origins = cors_middleware.kwargs.get("allow_origins", [])
    for origin in allow_origins:
        # All permitted origins must be local loopback
        assert "localhost" in origin or "127.0.0.1" in origin


def test_ollama_byoo_url_format():
    """Verifies Ollama BYOO URL points to loopback or host.docker.internal."""
    url = settings.ollama_url
    assert "127.0.0.1" in url or "localhost" in url or "host.docker.internal" in url

