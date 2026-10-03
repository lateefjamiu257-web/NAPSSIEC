@echo off
title NAPSS Independent Electoral Commission (NAPSSIEC) - Public Online Voting Server
echo =====================================================================
echo    NAPSS INDEPENDENT ELECTORAL COMMISSION (NAPSSIEC)
echo    Department of Political Science - Public Multi-Device E-Voting
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/2] Checking dependencies...
pip install fastapi uvicorn[standard] jinja2 python-multipart aiosqlite pydantic >nul 2>&1

echo [2/2] Launching Public E-Voting Server with Global Tunnel...
echo.
python run_public.py
pause
