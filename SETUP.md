# 📦 Installation & Setup

## Prerequisites

- **Python 3.11+** (3.12 recommended)
- **uv** package manager (faster than pip) - [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
- **Git** for cloning
- **Modern browser** (Chrome, Edge, Firefox)
- **Ollama** installed locally (for AI commentary) - see [OLLAMA_GRANITE.md](OLLAMA_GRANITE.md)

## Quick Start (5 Minutes)

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
