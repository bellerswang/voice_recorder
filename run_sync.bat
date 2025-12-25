@echo off
echo Starting Voice Recorder Sync and Process...

REM Navigate to project directory
cd /d %~dp0

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM Run the sync and process script
python backend/sync_and_process.py
