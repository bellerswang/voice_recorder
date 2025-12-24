@echo off
echo Starting Voice Recorder Monitor...

REM Configuration - REPLACE THESE WITH YOUR DETAILS
set GITHUB_USER=your_username
set GITHUB_REPO=voice_recorder
set GITHUB_PAT=your_personal_access_token

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM Run the monitor
python backend/monitor.py

pause
