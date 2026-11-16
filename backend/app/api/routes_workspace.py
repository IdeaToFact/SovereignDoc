# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import WorkspaceState
from app.models.schemas import WorkspaceStateRequest, WorkspaceStateResponse

router = APIRouter(prefix="/api/workspace", tags=["Workspace State & Persistence"])

CURRENT_DISCLAIMER_VERSION = "1.1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_workspace_state(state: WorkspaceState) -> WorkspaceStateResponse:
    is_accepted = state.accepted_disclaimer_version == CURRENT_DISCLAIMER_VERSION
    return WorkspaceStateResponse(
        id=state.id,
        active_vault_id=state.active_vault_id,
        active_document_id=state.active_document_id,
        active_model=state.active_model,
        active_session_id=state.active_session_id,
        sidebar_collapsed=state.sidebar_collapsed,
        current_disclaimer_version=CURRENT_DISCLAIMER_VERSION,
        accepted_disclaimer_version=state.accepted_disclaimer_version,
        disclaimer_accepted=is_accepted,
        disclaimer_accepted_at=state.disclaimer_accepted_at,
        updated_at=state.updated_at,
    )


@router.get("/state", response_model=WorkspaceStateResponse)
def get_workspace_state(db: Session = Depends(get_db)):
    """Retrieve the persisted workspace layout, active vault, active model, and versioned disclaimer state."""
    state = db.query(WorkspaceState).filter(WorkspaceState.id == "current_workspace").first()
    if not state:
        state = WorkspaceState(
            id="current_workspace",
            active_vault_id=None,
            active_document_id=None,
            active_model=None,
            active_session_id=None,
            sidebar_collapsed=False,
            accepted_disclaimer_version=None,
            disclaimer_accepted_at=None,
            updated_at=utc_now(),
        )
        db.add(state)
        db.commit()
        db.refresh(state)

    return _serialize_workspace_state(state)


@router.post("/state", response_model=WorkspaceStateResponse)
def update_workspace_state(req: WorkspaceStateRequest, db: Session = Depends(get_db)):
    """Save the active workspace layout, active vault, and active model to SQLite."""
    state = db.query(WorkspaceState).filter(WorkspaceState.id == "current_workspace").first()
    if not state:
        state = WorkspaceState(id="current_workspace")
        db.add(state)

    if req.active_vault_id is not None:
        state.active_vault_id = req.active_vault_id
    if req.active_document_id is not None:
        state.active_document_id = req.active_document_id
    if req.active_model is not None:
        state.active_model = req.active_model
    if req.active_session_id is not None:
        state.active_session_id = req.active_session_id
    if req.accepted_disclaimer_version is not None:
        state.accepted_disclaimer_version = req.accepted_disclaimer_version
        state.disclaimer_accepted_at = utc_now()
    state.sidebar_collapsed = req.sidebar_collapsed
    state.updated_at = utc_now()

    db.commit()
    db.refresh(state)

    return _serialize_workspace_state(state)


@router.post("/accept-disclaimer", response_model=WorkspaceStateResponse)
def accept_legal_disclaimer(db: Session = Depends(get_db)):
    """Record user acceptance of CURRENT_DISCLAIMER_VERSION in SQLite with UTC timestamp."""
    state = db.query(WorkspaceState).filter(WorkspaceState.id == "current_workspace").first()
    if not state:
        state = WorkspaceState(id="current_workspace")
        db.add(state)

    state.accepted_disclaimer_version = CURRENT_DISCLAIMER_VERSION
    state.disclaimer_accepted_at = utc_now()
    state.updated_at = utc_now()

    db.commit()
    db.refresh(state)

    return _serialize_workspace_state(state)
