@echo off
cd /d "%~dp0.."
echo ========================================
echo Starting Langflow
echo ========================================

if not exist ".venv" (
    echo Virtual environment not found. Please wait for start.bat to create it.
    timeout /t 5
)

call .\.venv\Scripts\activate
echo Starting langflow run...
langflow run
pause
