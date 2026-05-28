# 🦙 Ollama and IBM Granite Setup

Chronos F1 uses **IBM Granite** via **local Ollama** for AI commentary generation.

## Why Local Ollama?
- ✅ Free, completely offline, and private
- ✅ Fast response times locally
- ✅ Easy model switching via `.env`
- ✅ Full alignment with IBM's AI ecosystem using Granite models

## Installing Ollama
1. Visit the [Ollama website](https://ollama.com/)
2. Download and install the version for your operating system (Windows, macOS, or Linux)
3. Verify installation by opening a terminal and running:
   ```bash
   ollama --version
   ```

## Installing the Granite Model
By default, the project is configured to use `granite3.3:2b` or `granite3.3:1b`. You can pull the required model using Ollama:
```bash
ollama run granite3.3:2b
```
*(Or use whichever Granite model variant you prefer)*

## Changing the Project Level Model Name
If you want to use a different model, you can change it in the project's `.env` file.

1. Ensure you have copied `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and edit the `OLLAMA_MODEL` variable:
   ```env
   # Example: Using the 1b model instead of 2b
   OLLAMA_MODEL=granite3.3:1b
   ```
3. Make sure you have pulled that specific model using `ollama pull granite3.3:1b`.
