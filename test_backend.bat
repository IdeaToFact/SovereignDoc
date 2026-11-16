@echo off
TITLE SovereignDoc Automated Test Suite
echo ============================================================
echo   SovereignDoc - Running Full Automated Pytest Suite
echo ============================================================

cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv not found in backend directory.
    pause
    exit /b 1
)

:: Runs all granular domain tests by default, or accepts specific test arguments (e.g. test_backend.bat tests\test_risk_engine.py)
".venv\Scripts\python.exe" -m pytest tests %*
if errorlevel 1 (
    echo.
    echo [FAIL] One or more tests failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   All SovereignDoc Pytest Suites Passed (100% Verified)
echo ============================================================
pause
