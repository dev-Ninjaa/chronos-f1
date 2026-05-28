#!/bin/bash
cd "$(dirname "$0")/.."
echo "========================================"
echo "Chronos F1 - Web-based Race Replay"
echo "========================================"
echo ""

echo "Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    uv venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
uv pip install -r requirements.txt

echo "Starting server..."
echo "Open your browser to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
python app.py
