# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
SovereignDoc — System Health & Hardware Profiler Tests
"""
from fastapi.testclient import TestClient


def test_system_health(client: TestClient):
    """Verifies system health status and local airgap flag."""
    res = client.get("/api/system/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health = res.json()
    assert health["app"] == "SovereignDoc"
    assert "version" in health
    assert health["airgap_status"] == "LOCAL_ONLY"
    assert health["external_endpoints_configured"] is False
    assert health["llm_provider"] == "ollama"


def test_hardware_profiler(client: TestClient):
    """Verifies hardware capabilities and compute tier profiling."""
    res = client.get("/api/system/hardware")
    assert res.status_code == 200, f"Hardware check failed: {res.text}"
    hw = res.json()
    assert "os" in hw
    assert "cpu" in hw
    assert "ram" in hw
    assert "accelerator" in hw
    assert "capability_profile" in hw
    assert hw["ram"]["total_gb"] > 0
    assert hw["cpu"]["physical_cores"] > 0


def test_system_capabilities(client: TestClient):
    """Verifies system feature flags and format support."""
    res = client.get("/api/system/capabilities")
    assert res.status_code == 200, f"Capabilities check failed: {res.text}"
    caps = res.json()
    assert caps["pdf_support"] is True
    assert caps["airgap"] is True


def test_model_discovery(client: TestClient):
    """Verifies Ollama model discovery and status reporting."""
    res = client.get("/api/models")
    assert res.status_code == 200, f"Model discovery failed: {res.text}"
    data = res.json()
    assert "status" in data
    assert "models" in data
    assert isinstance(data["models"], list)

