@echo off
title Demand Supply Dashboard

echo ==========================================
echo Demand Supply Dashboard Startup
echo ==========================================
echo.

REM Verify Python exists
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    pause
    exit /b 1
)

REM Create venv if missing
if not exist ".venv" (
    echo Creating virtual environment...
    py -m venv .venv
)

REM Activate
call .venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Verify .env exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found.
    echo Copy .env.example to .env and add MASSIVE_API_KEY.
    echo.
    pause
    exit /b 1
)

echo.
echo Starting FastAPI...
echo Dashboard URL:
echo http://127.0.0.1:8000
echo.

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause