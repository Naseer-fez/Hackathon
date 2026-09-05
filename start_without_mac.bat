@echo off
setlocal enabledelayedexpansion

title BIS-SpecAI System Launcher (Standalone Local Mode)

echo ======================================================================
echo       BIS-SpecAI - Standalone Mode (Qwen 2.5 Local GPU Acceleration)
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

set "VENV_DIR=%ROOT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

:: Detect frontend directory (frontend or legacy\frontend fallback)
if exist "%ROOT_DIR%frontend\package.json" (
    set "FRONTEND_DIR=%ROOT_DIR%frontend"
) else if exist "%ROOT_DIR%legacy\frontend\package.json" (
    set "FRONTEND_DIR=%ROOT_DIR%legacy\frontend"
) else (
    set "FRONTEND_DIR=%ROOT_DIR%frontend"
)

:: Verify Virtual Environment
if exist "%VENV_PYTHON%" (
    echo [OK] Python Environment: %VENV_DIR%
) else (
    echo [ERROR] .venv not found at %VENV_DIR%!
    pause
    exit /b 1
)
echo [OK] Frontend Directory:  %FRONTEND_DIR%
echo.

echo [1/2] Launching Backend Server (Port 8000, Standalone Local LLM)...
start "BIS-SpecAI Backend (Port 8000) [Standalone Local]" cmd /k "set MAC_AVAILABLE=false && .venv\Scripts\python.exe run_all.py || pause"

echo [2/2] Launching Frontend UI (Port 5173)...
start "BIS-SpecAI Frontend (Port 5173)" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev || pause"

echo.
echo ======================================================================
echo All services launched in Standalone Local Mode!
echo   * Mac Reasoning Node:     DISABLED (All reasoning handled on Local GPU)
echo   * Backend API:            http://127.0.0.1:8000
echo   * Backend API Docs:       http://127.0.0.1:8000/docs
echo   * Frontend Web UI:        http://127.0.0.1:5173
echo ======================================================================
echo.
echo Press any key to close this launcher window (services keep running)...
pause >nul
