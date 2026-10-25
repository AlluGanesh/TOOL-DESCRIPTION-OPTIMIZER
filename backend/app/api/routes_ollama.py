"""API routes for Ollama health and model checks."""

from fastapi import APIRouter
from backend.app.models.tool_models import OllamaHealthResponse, OllamaModelResponse
from backend.app.services.ollama_service import ollama_service

router = APIRouter(prefix="/ollama", tags=["ollama"])

@router.get("/health", response_model=OllamaHealthResponse)
def get_ollama_health():
    """Checks whether the configured local Ollama instance is reachable."""
    return ollama_service.health_check()

@router.get("/model", response_model=OllamaModelResponse)
def get_ollama_model():
    """Checks whether the configured model (default: qwen2.5:3b) is available in Ollama."""
    return ollama_service.model_available()
