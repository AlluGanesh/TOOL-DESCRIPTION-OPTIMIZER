"""Unit tests for FastAPI endpoints under /api."""

from unittest.mock import MagicMock, patch
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.models.tool_models import ToolSelectionResult

client = TestClient(app)

def test_health_check_endpoint():
    """Verify root GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_canonical_tools_endpoint():
    """Verify GET /api/tools returns 10 canonical tool definitions."""
    response = client.get("/api/tools")
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    assert len(tools) == 10
    names = [t["name"] for t in tools]
    assert "calculator" in names
    assert "search_web" in names
    assert "search_docs" in names

def test_get_ollama_health_endpoint():
    """Verify GET /api/ollama/health endpoint."""
    with patch("backend.app.api.routes_ollama.ollama_service.health_check") as mock_health:
        mock_health.return_value = {
            "reachable": True,
            "host": "http://localhost:11434",
            "message": "Ollama daemon is reachable.",
        }
        response = client.get("/api/ollama/health")
        assert response.status_code == 200
        assert response.json()["reachable"] is True

def test_get_ollama_model_endpoint():
    """Verify GET /api/ollama/model endpoint."""
    with patch("backend.app.api.routes_ollama.ollama_service.model_available") as mock_model:
        mock_model.return_value = {
            "available": True,
            "model": "qwen2.5:3b",
            "host": "http://localhost:11434",
            "available_models": ["qwen2.5:3b"],
            "message": "Configured model 'qwen2.5:3b' is available.",
        }
        response = client.get("/api/ollama/model")
        assert response.status_code == 200
        assert response.json()["available"] is True
        assert response.json()["model"] == "qwen2.5:3b"

def test_post_tool_selection_endpoint():
    """Verify POST /api/tools/select routes query to OllamaService and returns normalized output."""
    mock_result = ToolSelectionResult(
        tool_called=True,
        tool_name="calculator",
        arguments={"expression": "25 * 16"},
        model="qwen2.5:3b",
        raw_response="",
        duration_ms=42.0,
    )
    with patch("backend.app.api.routes_tools.ollama_service.select_tool", return_value=mock_result):
        response = client.post("/api/tools/select", json={"query": "What is 25 * 16?"})
        assert response.status_code == 200
        data = response.json()
        assert data["tool_called"] is True
        assert data["tool_name"] == "calculator"
        assert data["arguments"] == {"expression": "25 * 16"}
        assert data["model"] == "qwen2.5:3b"

def test_post_evaluation_run_endpoint():
    """Verify POST /api/evaluation/run delegates to EvaluatorService."""
    from backend.app.models.evaluation_models import EvaluationMetadata, EvaluationResult

    mock_res = EvaluationResult(
        metadata=EvaluationMetadata(
            run_id="eval_test_123",
            model="qwen2.5:3b",
            split="tuning",
            runs_per_query=1,
            timestamp="2026-10-24T17:00:00",
            total_queries=35,
            tool_definition_hash="abc",
            dataset_hash="def",
        ),
        total_queries=35,
        correct_count=35,
        accuracy=1.0,
        per_tool_metrics={},
        confusion_matrix={},
        mistakes=[],
        queries=[],
    )
    with patch("backend.app.api.routes_evaluation.evaluator_service.evaluate", return_value=mock_res):
        response = client.post("/api/evaluation/run", json={"split": "tuning", "runs_per_query": 1})
        assert response.status_code == 200
        assert response.json()["accuracy"] == 1.0
