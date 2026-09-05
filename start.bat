@echo off
setlocal enabledelayedexpansion

title BIS-SpecAI Unified Launcher

echo ======================================================================
echo           BIS-SpecAI - AI Recommendation ^& Procurement Engine
echo ======================================================================
echo.
echo Select Startup Mode:
echo   [1] Start WITH Mock Mac Reasoning Node (Distributed Architecture)
echo   [2] Start WITHOUT Mac Node (Standalone Local GPU / RTX 3050)
echo.
set /p MODE="Enter choice [1 or 2] (Default: 1): "

if "%MODE%"=="2" (
    echo.
    echo Launching Standalone Local Mode...
    call "%~dp0start_without_mac.bat"
) else (
    echo.
    echo Launching Distributed Mode with Mock Mac...
    call "%~dp0start_with_mac.bat"
)
