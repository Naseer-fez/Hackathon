@echo off
setlocal enabledelayedexpansion

title BIS-SpecAI System Launcher

echo ======================================================================
echo           BIS-SpecAI - AI Recommendation ^& Procurement Engine
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
set "VENV_DIR=%ROOT_DIR%.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

:: Verify Virtual Environment
if exist "%VENV_PYTHON%" (
    echo [OK] Using Verified Virtual Environment: %VENV_DIR%
) else (
    echo [WARNING] .venv not found at %VENV_DIR%. Falling back to system Python.
)

echo.
echo [1/2] Launching Backend Server (FastAPI + ChromaDB + Local LLM)...
start "BIS-SpecAI Backend (Port 8000)" cmd /k "cd /d %ROOT_DIR% && call .venv\Scripts\activate.bat && python run_all.py"

echo [2/2] Launching Frontend UI (Vite + React)...
start "BIS-SpecAI Frontend (Port 5173)" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo ======================================================================
echo System started successfully!
echo   * Backend API (Local):    http://127.0.0.1:8000
echo   * Backend API (Network):  http://192.168.1.9:8000
echo   * API Docs:               http://192.168.1.9:8000/docs
echo   * Frontend Web (Local):   http://127.0.0.1:5173
echo   * Frontend Web (Network): http://192.168.1.9:5173
echo ======================================================================
echo.
echo Press any key to close this launcher window (services will keep running)...
pause >nul
