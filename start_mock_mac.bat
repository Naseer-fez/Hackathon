@echo off
setlocal enabledelayedexpansion
set "ROOT_DIR=%~dp0"
title BIS-SpecAI Mac Reasoning Node (Cloud-Bridged Emulation)

echo ======================================================================
echo    BIS-SpecAI - Mock Mac Reasoning Server (Cloud Bridge)
echo    Port: 5000  |  Endpoint: /reason  |  Backend: OpenRouter / Gemini
echo ======================================================================
echo.

cd /d "%ROOT_DIR%"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python -m backend.mac_mock_server
) else (
    echo [ERROR] Virtual environment not found at .venv
    pause
)
