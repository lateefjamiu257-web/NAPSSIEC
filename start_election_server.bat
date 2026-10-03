@echo off
title NAPSS Independent Electoral Commission (NAPSSIEC) - Election Server
echo =====================================================================
echo    NAPSS INDEPENDENT ELECTORAL COMMISSION (NAPSSIEC)
echo    Department of Political Science - E-Voting Platform
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [2/3] Verifying dependencies...
pip install fastapi uvicorn[standard] jinja2 python-multipart aiosqlite pydantic >nul 2>&1

echo [3/3] Launching NAPSSIEC Election Platform...
echo.
echo =====================================================================
echo    PLATFORM IS RUNNING FOR MULTI-DEVICE VOTING!
echo    - Laptop URL:               http://127.0.0.1:8000
echo    - Phones on Same Wi-Fi:     http://192.168.48.125:8000
echo    - Voter Booth (Paste Key):  http://192.168.48.125:8000/vote
echo    - Public Transparency Board:http://192.168.48.125:8000/public-board
echo    - Verify Receipt Hash:      http://192.168.48.125:8000/verify-receipt
echo    - Chairman Command Room:    http://127.0.0.1:8000/admin/login  (Pass: Chairman2026!)
echo =====================================================================
echo.
echo Opening browser...
start http://127.0.0.1:8000
echo.
echo Press CTRL+C to stop the server when election is closed.
echo.

python run.py
pause
