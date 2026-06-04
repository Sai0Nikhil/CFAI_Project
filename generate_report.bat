@echo off
echo ============================================
echo  Hospital AI Navigator - Report Generator
echo ============================================
echo.
echo Step 1: Installing docx npm package...
call npm install docx --prefix "%~dp0" 2>nul
if errorlevel 1 (
    echo Trying global install...
    call npm install -g docx
)
echo.
echo Step 2: Generating Project Report...
cd /d "%~dp0"
node generate_report.js
echo.
echo ============================================
echo  Done! Check C:\CFAI_Project\ for:
echo  - Hospital_AI_Navigator_Report.docx
echo ============================================
echo.
pause
