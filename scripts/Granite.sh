#!/bin/bash
cd "$(dirname "$0")/.."
echo "========================================"
echo "Starting Ollama and Granite Model"
echo "========================================"

echo "Checking if Ollama is installed..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed! Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    if [ $? -ne 0 ]; then
        echo "Failed to install Ollama. Please install manually from https://ollama.com/"
        exit 1
    fi
fi

echo "Ollama found. Serving Granite model (granite3.3:2b)..."
export OLLAMA_KV_CACHE_TYPE=q8_0
ollama run granite3.3:2b
