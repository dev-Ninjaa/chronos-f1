#!/bin/bash
cd "$(dirname "$0")/.."
echo "========================================"
echo "Starting Langflow"
echo "========================================"

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please wait for start.sh to create it."
    sleep 5
fi

source .venv/bin/activate
echo "Starting langflow run..."
langflow run
