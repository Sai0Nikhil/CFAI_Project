@echo off
echo ============================================
echo  Charite AI Navigator — Starting...
echo ============================================

echo.
echo [1/2] Starting FastAPI backend on port 8000...
start "FastAPI Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --reload --port 8000"

echo [2/2] Starting Vite React frontend on port 5173...
start "Vite Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo  Open http://localhost:5173 in your browser
echo ============================================
timeout /t 3
start http://localhost:5173
