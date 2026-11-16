# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ModelListResponse,
    SelectModelRequest,
    TestPromptRequest,
    TestPromptResponse,
)
from app.services.llm.provider_factory import get_model_registry

router = APIRouter(prefix="/api/models", tags=["Model Management"])


@router.get("", response_model=ModelListResponse)
async def list_models():
    """Discover installed models from the local provider with compatibility evaluation."""
    registry = get_model_registry()
    health_data = await registry.provider.get_health()
    evaluated_models = await registry.get_evaluated_models()

    return ModelListResponse(
        provider=registry.provider.provider_name,
        status=health_data["status"],
        active_model=registry.get_active_model(),
        models=evaluated_models
    )


@router.post("/select")
async def select_model(req: SelectModelRequest):
    """Switch active model for subsequent operations."""
    registry = get_model_registry()
    models = await registry.get_evaluated_models()
    available_names = [m["name"] for m in models]

    if req.model_name not in available_names:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{req.model_name}' not found in local provider registry."
        )

    registry.set_active_model(req.model_name)
    return {"status": "success", "active_model": req.model_name}


@router.post("/test", response_model=TestPromptResponse)
async def test_inference(req: TestPromptRequest):
    """Execute immediate test inference to verify local token generation."""
    registry = get_model_registry()
    active_model = registry.get_active_model()

    if not active_model:
        raise HTTPException(
            status_code=400,
            detail="No active model selected or available in local provider."
        )

    try:
        res = await registry.provider.generate(model_name=active_model, prompt=req.prompt)
        return TestPromptResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
