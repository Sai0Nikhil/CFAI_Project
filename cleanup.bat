@echo off
echo ============================================
echo  Charite AI — Cleaning up old files...
echo ============================================
cd /d %~dp0

:: ── Old Streamlit app files ──────────────────
echo Removing old Streamlit files...
if exist app.py           del /f /q app.py
if exist core\ui.py       del /f /q core\ui.py

:: ── Old Streamlit pages folder ───────────────
if exist pages\ (
  rmdir /s /q pages
  echo   pages\ folder removed
)

:: ── Root-level duplicate hospital_graph.py ───
if exist hospital_graph.py del /f /q hospital_graph.py

:: ── Old graph preview image ──────────────────
if exist graph_preview.png del /f /q graph_preview.png

:: ── data\ CSVs (graph is hardcoded in core) ──
if exist data\ (
  rmdir /s /q data
  echo   data\ folder removed
)

:: ── lib\ — pyvis/vis-network Streamlit assets ─
if exist lib\ (
  rmdir /s /q lib
  echo   lib\ folder removed
)

:: ── Old README (replaced by SETUP.md) ────────
if exist README.md del /f /q README.md

:: ── opencode IDE junk ─────────────────────────
if exist opencode.jsonc del /f /q opencode.jsonc
if exist .opencode\ (
  rmdir /s /q .opencode
  echo   .opencode\ folder removed
)

:: ── Python cache ──────────────────────────────
echo Removing __pycache__ folders...
for /d /r . %%d in (__pycache__) do (
  if exist "%%d" rmdir /s /q "%%d"
)

:: ── pytest cache ──────────────────────────────
if exist .pytest_cache\ (
  rmdir /s /q .pytest_cache
  echo   .pytest_cache\ removed
)

echo.
echo ============================================
echo  Done! Clean project structure:
echo.
echo  core\          AI logic (keep)
echo  backend\       FastAPI server (keep)
echo  frontend\      Vite React app (keep)
echo  tests\         Unit tests (keep)
echo  start.bat      Launch both servers
echo  SETUP.md       Setup instructions
echo ============================================
pause
