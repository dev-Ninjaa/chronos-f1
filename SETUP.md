# 📦 Installation & Setup

## Prerequisites

- **Python 3.11+** (3.12 recommended)
- **uv** package manager (faster than pip) - [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
- **Git** for cloning
- **Modern browser** (Chrome, Edge, Firefox)
- **Ollama** installed locally (for AI commentary) - see [OLLAMA_GRANITE.md](OLLAMA_GRANITE.md)

## Automated Setup (Using Scripts)

For the easiest setup experience, we have provided automated scripts in the `scripts/` folder. **Important: Each script should be run in its own separate terminal** to avoid blocking other processes.

### 1. Environment Setup (`scripts/env.bat` or `scripts/env.sh`)
- **What it does:** Copies `.env.example` to `.env` if it doesn't exist, preparing your environment variables.
- **Tip:** Run this first. Then, open the `.env` file to ensure the configuration matches your setup.

### 2. Start Langflow (`scripts/langflow.bat` or `scripts/langflow.sh`)
- **What it does:** Installs Langflow and starts the Langflow server (typically on port 7860).
- **Tip:** Run this in a **separate terminal** and leave it running. It's required for workflow orchestration.

### 3. Start the Web App (`scripts/start.bat` or `scripts/start.sh`)
- **What it does:** Sets up the Python virtual environment using `uv`, installs requirements, and starts the Flask web application.
- **Tip:** Run this in a **separate terminal**. Once started, access the app at `http://127.0.0.1:5000`.

**Note:** You also need to run the IBM Granite model. See [OLLAMA_GRANITE.md](OLLAMA_GRANITE.md) for the `Granite.bat` / `Granite.sh` scripts, which should also be run in a separate terminal.

## Manual Quick Start (5 Minutes)

### Option 1: Using UV (Recommended - Faster)

```bash
# 1. Install UV (if not already installed)
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/Mac:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone the repository
git clone https://github.com/dev-Ninjaa/chronos-f1.git
cd chronos-f1

# 3. Create virtual environment with UV
uv venv

# 4. Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\activate
# Windows CMD:
.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# 5. Install dependencies with UV (much faster!)
uv pip install -r requirements.txt

# 6. Configure AI services
cp .env.example .env
# By default, it connects to local Ollama using granite3.3:2b.
# Edit .env to change models if needed.

# 7. Start the application
python app.py

# 8. Open browser
# Navigate to: http://localhost:5000
```

### Option 2: Using pip (Traditional)

```bash
# 1. Clone the repository
git clone https://github.com/dev-Ninjaa/chronos-f1.git
cd chronos-f1

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\activate
# Windows CMD:
.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies (includes Docling & Langflow)
pip install -r requirements.txt

# 5. Configure AI services
cp .env.example .env
# By default, it connects to local Ollama using granite3.3:2b.
# Edit .env to change models if needed.

# 6. Start the application
python app.py

# 7. Open browser
# Navigate to: http://localhost:5000
```
