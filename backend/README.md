# Backend Research & Evaluation Engine

## Overview
The `backend` package houses the core research system for `tool-description-optimizer`. It manages local communication with the Ollama LLM runtime, runs deterministic tool-selection evaluations, performs iterative description optimization, and exposes a decoupled REST API for the visualization layer.

## Architectural Principles
1. **Independent Usability**: The backend can run, evaluate, and optimize tool descriptions fully independently without requiring the frontend.
2. **Local & Free ($0)**: Communicates exclusively with local Ollama (`qwen2.5:3b` default) without third-party cloud API costs.
3. **Decoupled REST API**: Exposes clean endpoints under FastAPI to serve tools, evaluation runs, optimization passes, and metrics to the frontend visualization dashboard.

## Module Responsibilities
- **`app/api/`**: REST API route definitions (`routes_tools.py`, `routes_evaluation.py`, `routes_optimization.py`).
- **`app/core/`**: Configuration management (`config.py`), constants (`constants.py`), and unified logging (`logging.py`).
- **`app/services/`**:
  - `ollama_service.py`: Local LLM interaction, temperature-zero completions, and response extraction.
  - `cache_service.py`: Deterministic response caching by query and tool schema hash.
  - `evaluator_service.py`: Automated batch evaluation of tool routing against ground truth.
  - `optimizer_service.py`: Meta-prompting logic for iteratively improving tool descriptions based on misclassifications.
  - `report_service.py`: Aggregation of accuracy, confusion matrices, and run diffs.
- **`app/models/`**: Pydantic schemas for tools, queries, evaluation runs, and optimization rounds.
- **`app/utils/`**: Deterministic hashing, validation utilities, and accuracy/confusion matrix metrics.

## Running the Backend
From the repository root or backend directory:
```bash
# Set up virtual environment
py -m venv .venv
.venv\Scripts\activate

# Install requirements
pip install -r backend/requirements.txt

# Start FastAPI development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Health check endpoint:
```
GET http://127.0.0.1:8000/health
Response: {"status": "ok"}
```
