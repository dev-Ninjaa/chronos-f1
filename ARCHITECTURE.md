# 🏗️ Project Architecture

```
chronos-f1/
│
├── 🤖 AI Intelligence Layer
│   ├── ai/
│   │   ├── graniteClient.py          # IBM Granite AI client via Ollama
│   │   ├── aiCommentary.py           # Commentary generation engine
│   │   └── __init__.py
│   │
│   ├── documents/
│   │   ├── documentProcessor.py      # Docling integration
│   │   ├── f1_regulations_sample.md  # F1 regulations database
│   │   └── __init__.py
│   │
│   └── workflows/
│       ├── langflowIntegration.py    # Langflow orchestration
│       └── __init__.py
│
├── 📊 Data Processing Layer
│   ├── manager/
│   │   ├── dataManager.py            # FastF1 data processing
│   │   └── __init__.py
│   │
│   ├── replay/
│   │   ├── replayEngine.py           # Replay state management
│   │   └── __init__.py
│   │
│   ├── models/
│   │   ├── tyreModel.py             # Bayesian tyre degradation
│   │   └── safetyCarModel.py        # Safety car simulation
│   │
│   └── utils/
│       ├── trackUtils.py            # Track geometry & DRS zones
│       └── weatherUtils.py          # Weather data formatting
│
├── 🌐 Web Application Layer
│   ├── app.py                        # Flask + SocketIO server
│   │
│   ├── templates/
│   │   └── index.html               # Main UI
│   │
│   └── static/
│       ├── css/style.css            # Dark theme styling
│       └── js/app.js                # Frontend logic
│
├── 🧪 Testing
│   └── test/
│       ├── test_ai_features.py      # AI features test suite
│       └── __init__.py
│
├── 📚 Documentation & Examples
│   ├── README.md                     # This file
│   ├── docs/
│   │   ├── PROJECT_STRUCTURE.md     # Architecture details
│   │   └── QUICK_START.md           # 3-minute guide
│   │
│   └── examples/
│       ├── aiCommentaryExample.py   # AI usage examples
│       ├── documentProcessingExample.py
│       └── workflowExample.py
│
├── ⚙️ Configuration
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment template
│   ├── .gitignore                    # Git ignore rules
│   └── start.bat                     # Windows launcher
│
└── 💾 Data & Cache
    ├── .fastf1-cache/                # FastF1 API cache
    ├── computed_data/                # Processed telemetry
    └── document_cache/               # Docling processed docs
```

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Track Canvas │  │ Leaderboard  │  │ AI Commentary│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket (25 FPS)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask + SocketIO Server                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Replay Engine (replayEngine.py)         │   │
│  │  • Playback state management                         │   │
│  │  • Frame interpolation                               │   │
│  │  • Gap calculations                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Data Manager │  │  AI Layer    │  │  Models      │
│              │  │              │  │              │
│ • FastF1 API │  │ • Granite AI │  │ • Tyre Model │
│ • Telemetry  │  │ • Docling    │  │ • Safety Car │
│ • Weather    │  │ • Langflow   │  │ • Track Geo  │
└──────────────┘  └──────────────┘  └──────────────┘
```
