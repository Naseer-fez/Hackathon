@echo off
setlocal enabledelayedexpansion

title BIS-SpecAI (Mock Mac + Backend + Frontend)

echo ======================================================================
echo           BIS-SpecAI - Mock Mac Reasoning ^& Full Stack Engine
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

set "VENV_DIR=%ROOT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

:: Detect frontend directory
if exist "%ROOT_DIR%frontend\package.json" (
    set "FRONTEND_DIR=%ROOT_DIR%frontend"
) else if exist "%ROOT_DIR%legacy\frontend\package.json" (
    set "FRONTEND_DIR=%ROOT_DIR%legacy\frontend"
) else (
    set "FRONTEND_DIR=%ROOT_DIR%legacy\frontend"
)

:: Verify Virtual Environment
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment python.exe not found at %VENV_PYTHON%!
    pause
    exit /b 1
)

echo [OK] Python Environment: %VENV_DIR%
echo [OK] Frontend Directory:  %FRONTEND_DIR%
echo.

:: 1. Launch Mock Mac Server (Port 5000)
echo [1/3] Launching Mock Mac Reasoning Node (Port 5000)...
start "BIS-SpecAI [1] Mock Mac Reasoning Node (Port 5000)" cmd /k "cd /d "%ROOT_DIR%" && .venv\Scripts\python.exe -m backend.mac_mock_server || pause"

:: 2. Launch Backend API (Port 8000) with MAC_AVAILABLE=true
echo [2/3] Launching Backend Server (Port 8000, Mac Distributed)...
start "BIS-SpecAI [2] Backend API (Port 8000)" cmd /k "cd /d "%ROOT_DIR%" && set MAC_AVAILABLE=true && .venv\Scripts\python.exe run_all.py || pause"

:: 3. Launch Frontend UI (Port 5173)
echo [3/3] Launching Frontend UI (Port 5173)...
start "BIS-SpecAI [3] Frontend Web UI (Port 5173)" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev || pause"

echo.
echo ======================================================================
echo All services launched in Mock Mac Distributed Mode!
echo   * Mock Mac Server:        http://127.0.0.1:5000/reason
echo   * Mock Mac Health:        http://127.0.0.1:5000/health
echo   * Backend API:            http://127.0.0.1:8000
echo   * Backend Docs:           http://127.0.0.1:8000/docs
echo   * Frontend UI:            http://127.0.0.1:5173
echo   * Direct Test Portal:     %ROOT_DIR%portal.html
echo ======================================================================
echo.
echo Press any key to close this launcher monitor (services will keep running)...
pause >nul
