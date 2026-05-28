@echo off
cd /d "%~dp0.."
echo ========================================
echo Chronos F1 - Web-based Race Replay
echo ========================================
echo.

echo Checking for uv...
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo uv not found. Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
)

echo Creating virtual environment...
if not exist .venv (
    uv venv
)

echo Activating virtual environment...
call .\.venv\Scripts\activate

echo Installing dependencies...
uv pip install -r requirements.txt

echo Starting server...
echo Open your browser to: http://localhost:5000
echo Press Ctrl+C to stop the server
python app.py
pause
