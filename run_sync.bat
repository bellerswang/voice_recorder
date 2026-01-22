@echo off
REM Navigate to project directory FIRST (before any redirections)
cd /d "%~dp0"

REM Redirect all output to log file
call :main >> logs/console.log 2>&1
exit /b

:main
echo ==================================================
echo Run generated at: %DATE% %TIME%
echo ==================================================

REM Debugging Info
echo [DEBUG] Current Directory: %CD%

REM Activate Conda Environment
echo [INFO] Activating Conda Base Environment...
call C:\Users\belle\miniconda3\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate Conda environment
    exit /b
)

echo [DEBUG] Python Path:
where python
echo [DEBUG] Python Version:
python --version

REM Check if ffmpeg is installed
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] ffmpeg is not found in PATH!
) else (
    echo [INFO] ffmpeg found.
)

REM Run the sync and process script
echo [INFO] Starting script...
python backend/sync_and_process.py
echo [INFO] Script finished.
exit /b
