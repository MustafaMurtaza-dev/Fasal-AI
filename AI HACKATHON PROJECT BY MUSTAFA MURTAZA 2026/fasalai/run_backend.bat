@echo off
echo ============================
echo  FasalAI Backend Starting
echo ============================
cd /d "%~dp0backend"
if not exist ".env" (
    echo [!] No .env file found. Copy .env.example to .env and add your API keys.
    pause
    exit /b 1
)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
