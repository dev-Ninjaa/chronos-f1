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

## Installing and Running the Granite Model

We provide handy scripts in the `scripts/` folder to automatically pull and run the IBM Granite model. **Important: Always run these scripts in a separate terminal window** so they don't block the main application.

- **Windows:** Run `scripts\Granite.bat`
- **Linux/macOS:** Run `scripts/Granite.sh`

### Tips
- **What it does:** The script will automatically check if Ollama is installed, then pull and run the `granite3.3:2b` model.
- **Separate Terminal:** Keep the terminal running the script open while you use Chronos F1. If you close it, the model will stop running.
- **Manual Command:** Alternatively, you can pull the required model manually using:
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
