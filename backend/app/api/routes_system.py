# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from fastapi import APIRouter
from app.config import settings
from app.models.schemas import HardwareProfileResponse, SystemCapabilitiesResponse
from app.services.hardware_info import hardware_profiler
from app.services.airgap_verifier import airgap_verifier
from app.services.benchmark_service import benchmark_service
from app.services.llm.provider_factory import get_model_registry

router = APIRouter(prefix="/api/system", tags=["System & Health"])


@router.get("/health")
async def get_health():
    """Health and air-gap verification endpoint."""
    registry = get_model_registry()
    health_data = await registry.provider.get_health()
    return {
        "app": settings.app_name,
        "version": settings.version,
        "airgap_status": "LOCAL_ONLY",
        "external_endpoints_configured": False,
        "llm_provider": registry.provider.provider_name,
        "ollama_status": health_data["status"]
    }


@router.get("/hardware", response_model=HardwareProfileResponse)
async def get_hardware():
    """Hardware capability and accelerator profiling endpoint."""
    return hardware_profiler.get_hardware_profile()


@router.get("/capabilities", response_model=SystemCapabilitiesResponse)
async def get_capabilities():
    """High-level system capabilities discovery endpoint for frontend gating."""
    hw = hardware_profiler.get_hardware_profile()
    registry = get_model_registry()
    health_data = await registry.provider.get_health()

    return SystemCapabilitiesResponse(
        cpu=True,
        cuda=hw["accelerator"]["has_cuda"],
        metal=hw["accelerator"]["has_metal"],
        ollama=(health_data["status"] != "OFFLINE"),
        airgap=True,
        pdf_support=True,     # Milestone 2 Active
        embeddings=True       # Milestone 2 Active
    )


@router.get("/airgap-audit")
def get_airgap_audit(refresh: bool = False):
    """Run or retrieve cached multi-layer air-gap sovereignty audit (audit_version = '1.0')."""
    return airgap_verifier.get_audit_report(refresh=refresh)


@router.post("/benchmark")
def run_hardware_benchmark():
    """Execute 25-page End-to-End Document & local hardware throughput benchmark."""
    return benchmark_service.run_benchmark()
