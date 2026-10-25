"""Application configuration module."""

import os
from pathlib import Path

# Load local .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Base repository directories (derived dynamically, zero hardcoded machine paths)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TOOLS_DIR = BASE_DIR / "tools"
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
OPTIMIZATION_DIR = RESULTS_DIR / "optimization"
CACHE_DIR = BASE_DIR / "cache"
TOOLS_FILE = TOOLS_DIR / "tools.json"
DATA_QUERIES_FILE = DATA_DIR / "queries.json"

# Ollama runtime settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Application server settings
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
