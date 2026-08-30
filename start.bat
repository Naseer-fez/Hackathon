@echo off
setlocal enabledelayedexpansion

title BIS-SpecAI System Launcher

echo ======================================================================
echo           BIS-SpecAI - AI Recommendation ^& Procurement Engine
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
set "VENV_ACTIVATE=%ROOT_DIR%.venv\Scripts\activate.bat"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

:: Verify Virtual Environment
if exist "%VENV_ACTIVATE%" (
    echo [OK] Detected Virtual Environment: %ROOT_DIR%.venv
) else (
    echo [WARNING] .venv not found at %ROOT_DIR%.venv. Falling back to system Python.
)

echo.
echo [1/2] Launching Backend Server (FastAPI + ChromaDB + Local LLM)...
start "BIS-SpecAI Backend (Port 8000)" cmd /k "cd /d "%ROOT_DIR%" && if exist "%VENV_ACTIVATE%" (call "%VENV_ACTIVATE%") && python run_all.py"

echo [2/2] Launching Frontend UI (Vite + React)...
start "BIS-SpecAI Frontend (Port 5173)" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo ======================================================================
echo System started successfully!
echo   * Backend API:     http://127.0.0.1:8000
echo   * API Docs:        http://127.0.0.1:8000/docs
echo   * Frontend Web UI: http://127.0.0.1:5173
echo ======================================================================
echo.
echo Press any key to close this launcher window (services will keep running)...
pause >nul
