# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import os
import sys
from pathlib import Path

# Ensure repository root (containing 'packages') is in sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes_models import router as models_router
from app.api.routes_system import router as system_router
from app.api.routes_vaults import router as vaults_router
from app.api.routes_documents import router as documents_router
from app.api.routes_chat import router as chat_router
from app.api.routes_workspace import router as workspace_router
from app.api.routes_legal import router as legal_router
from app.api.routes_notes import router as notes_router
from app.config import settings
from app.db.database import init_db
from app.services.storage_manager import storage_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure local directory structures exist (.sovereigndoc)
    storage_manager.initialize_dirs()
    # Initialize SQLite database tables
    init_db()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="100% Local AI Document Intelligence & Second Brain Backend",
    lifespan=lifespan
)

# Strictly limit CORS to local origins for air-gap protection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(models_router)
app.include_router(vaults_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(workspace_router)
app.include_router(legal_router)
app.include_router(notes_router)


# Determine static frontend distribution directory
_env_static = os.environ.get("SOVEREIGNDOC_STATIC_DIR")
_static_candidates = [
    Path(_env_static) if _env_static else None,
    _repo_root / "frontend" / "dist",
    Path("/app/frontend/dist"),
]
_static_dir = next((p for p in _static_candidates if p and p.is_dir() and (p / "index.html").is_file()), None)

if _static_dir:
    _assets_dir = _static_dir / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(_static_dir / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API routes that 404 to return JSON rather than SPA index.html
        if full_path == "api" or full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_path = _static_dir / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_static_dir / "index.html"))
else:
    @app.get("/")
    async def root_redirect():
        return {
            "app": settings.app_name,
            "status": "running",
            "airgap_mode": "strict_local",
            "docs": f"http://{settings.host}:{settings.port}/docs"
        }
