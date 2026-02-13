@echo off
echo ============================
echo  FasalAI Frontend Starting
echo ============================
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [*] Installing dependencies...
    npm install
)
npm run dev
