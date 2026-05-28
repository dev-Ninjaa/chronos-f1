@echo off
cd /d "%~dp0.."
echo ========================================
echo Starting Ollama and Granite Model
echo ========================================

echo Checking if Ollama is installed...
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Ollama is not installed! Installing Ollama via winget...
    winget install Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Ollama. Please install manually from https://ollama.com/
        pause
        exit /b 1
    )
    set "PATH=%LOCALAPPDATA%\Programs\Ollama;%PATH%"
)

echo Ollama found. Serving Granite model (granite3.3:2b)...
set OLLAMA_KV_CACHE_TYPE=q8_0
ollama run granite3.3:2b
pause
