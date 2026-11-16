@echo off
TITLE SovereignDoc Full App Launcher
echo ====================================================================
echo   SovereignDoc: 100%% Local AI Document Intelligence & Second Brain
echo ====================================================================
echo.
echo   Running Sovereign Preflight Verification...
echo   ------------------------------------------------------------------

set "ANONYMIZED_TELEMETRY=False"
set "CHROMA_TELEMETRY_IMPL=none"
set "DO_NOT_TRACK=1"
set "HF_HUB_DISABLE_TELEMETRY=1"

if exist "%~dp0backend\.venv\Scripts\python.exe" (
    echo   [PASS] Python Runtime ^(.venv^)
) else (
    echo   [FAIL] Python Virtual Environment not found in backend\.venv
    echo          Please follow setup steps in docs\TERMINAL_COMMANDS.md
    pause
    exit /b 1
)

where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   [PASS] Node.js Runtime
) else (
    echo   [WARN] Node.js not found in PATH
)

where ollama >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   [PASS] Ollama Local CLI Detected
) else (
    echo   [INFO] Ollama CLI not in PATH ^(Optional for deterministic audit/graph^)
)

echo   [PASS] Telemetry Disabled ^(ANONYMIZED_TELEMETRY=False, DO_NOT_TRACK=1^)
echo   [PASS] Localhost Binding ^(127.0.0.1:8000 / 127.0.0.1:5173^)
echo   [PASS] ChromaDB ^& SQLite Local Storage ^(~/.sovereigndoc^)
echo   ------------------------------------------------------------------
echo.
echo [1/2] Starting SovereignDoc Backend on http://127.0.0.1:8000...
start "SovereignDoc Backend" cmd /c "%~dp0run_backend.bat"

timeout /t 3 /nobreak > nul

echo [2/2] Starting SovereignDoc Frontend on http://127.0.0.1:5173...
start "SovereignDoc Frontend" cmd /c "%~dp0run_frontend.bat"

timeout /t 2 /nobreak > nul

echo.
echo ====================================================================
echo   SovereignDoc is launching in 100%% Local Air-Gapped Mode!
echo   Workspace UI : http://127.0.0.1:5173
echo   Swagger API  : http://127.0.0.1:8000/docs
echo ====================================================================
start http://127.0.0.1:5173
pause
