@echo off
title Sahayak Server
cd /d "%~dp0"

pip install fastapi uvicorn requests python-multipart >nul 2>nul
if errorlevel 1 (
    python -m pip install fastapi uvicorn requests python-multipart >nul 2>nul
)

if exist .env (
    for /f "tokens=2 delims==" %%a in ('findstr "SARVAM_API_KEY" .env 2^>nul') do set SARVAM_API_KEY=%%a
)

echo.
echo   Sahayak server running at http://127.0.0.1:8000
echo   Demo:  http://127.0.0.1:8000/demo
echo   Docs:  http://127.0.0.1:8000/docs
echo   Press Ctrl+C to stop.
echo.

python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
pause
