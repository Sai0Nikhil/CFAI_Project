@echo off
echo ============================================================
echo  Hospital AI Navigator - Report + Poster Generator
echo ============================================================
echo.

echo [1/2] Generating Project Report (DOCX)...
python "%~dp0generate_report_py.py"
if errorlevel 1 (
    echo ERROR: Report generation failed. Check python is in PATH.
    pause
    exit /b 1
)

echo.
echo [2/2] Generating Poster (PDF)...
python "%~dp0generate_poster.py"
if errorlevel 1 (
    echo ERROR: Poster generation failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  DONE! Files saved to C:\CFAI_Project\
echo   - Hospital_AI_Navigator_Report.docx
echo   - Hospital_AI_Navigator_Poster.pdf
echo ============================================================
echo.
echo Opening files...
start "" "C:\CFAI_Project\Hospital_AI_Navigator_Report.docx"
start "" "C:\CFAI_Project\Hospital_AI_Navigator_Poster.pdf"
pause
