@echo off
TITLE SovereignDoc Frontend UI
echo ============================================================
echo   SovereignDoc - Launching Air-Gapped Frontend UI
echo ============================================================

set "DO_NOT_TRACK=1"
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [INFO] Installing frontend node dependencies...
    call npm install
)

echo Starting Vite Dev Server on http://127.0.0.1:5173...
npm run dev
pause
