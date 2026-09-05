@echo off
setlocal enabledelayedexpansion

title Download Qwen2.5-3B-Instruct GGUF

echo ======================================================================
echo    Downloading Qwen2.5-3B-Instruct-Q4_K_M.gguf (~2.0 GB)
echo    Destination: D:\CODE\Hackathon\llm\
echo ======================================================================
echo.

set "ROOT_DIR=%~dp0"
set "TARGET_DIR=%ROOT_DIR%llm"
set "TARGET_FILE=%TARGET_DIR%\Qwen2.5-3B-Instruct-Q4_K_M.gguf"
set "MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

if exist "%TARGET_FILE%" (
    echo [INFO] Model file already exists at:
    echo        %TARGET_FILE%
    echo.
    set /p RE_DOWNLOAD="Do you want to re-download and overwrite it? (y/N): "
    if /i not "!RE_DOWNLOAD!"=="y" (
        echo Download cancelled.
        pause
        exit /b 0
    )
)

echo.
echo Starting download with curl... Please keep this window open until complete.
echo.

curl.exe -L --progress-bar -o "%TARGET_FILE%" "%MODEL_URL%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ======================================================================
    echo [SUCCESS] Download completed successfully!
    echo Saved to: %TARGET_FILE%
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo [ERROR] Download failed or was interrupted.
    echo You can also download it directly via your browser at:
    echo %MODEL_URL%
    echo and save it to: %TARGET_FILE%
    echo ======================================================================
)

echo.
pause
