@echo off
TITLE SovereignDoc Backend Server
echo ============================================================
echo   SovereignDoc - 100%% Local AI Document Intelligence
echo ============================================================
echo Starting local backend server on http://127.0.0.1:8000 ...
echo Swagger Docs: http://127.0.0.1:8000/docs
echo Press Ctrl+C to stop.
echo ============================================================

set "PYTHONPATH=%~dp0;%~dp0backend;%PYTHONPATH%"
set "ANONYMIZED_TELEMETRY=False"
set "CHROMA_TELEMETRY_IMPL=none"
set "DO_NOT_TRACK=1"
set "HF_HUB_DISABLE_TELEMETRY=1"

cd /d "%~dp0backend"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
) else (
    echo [ERROR] Virtual environment .venv not found in backend directory.
    echo Please run docs\TERMINAL_COMMANDS.md setup steps first.
    pause
)
