"""Unit tests for OllamaService with mocking (independent of live Ollama daemon)."""

from unittest.mock import MagicMock
import pytest

from backend.app.core.exceptions import OllamaConnectionError
from backend.app.services.ollama_service import OllamaService

def test_service_initialization_defaults():
    """Verify service picks up host and model defaults from config."""
    service = OllamaService()
    assert service.host == "http://localhost:11434"
    assert service.model == "qwen2.5:3b"

def test_health_check_reachable():
    """Verify health_check returns reachable=True when client.list() succeeds."""
    mock_client = MagicMock()
    mock_client.list.return_value = {"models": []}
    service = OllamaService(client=mock_client)

    res = service.health_check()
    assert res.reachable is True
    assert res.host == service.host

def test_health_check_unreachable():
    """Verify health_check gracefully returns reachable=False without throwing unhandled exceptions."""
    mock_client = MagicMock()
    mock_client.list.side_effect = ConnectionRefusedError("Connection refused")
    service = OllamaService(client=mock_client)

    res = service.health_check()
    assert res.reachable is False
    assert "unreachable" in res.message.lower() or "connection" in res.message.lower()

def test_model_available_found():
    """Verify model_available returns available=True when model is in list."""
    mock_model = MagicMock()
    mock_model.model = "qwen2.5:3b"
    mock_response = MagicMock()
    mock_response.models = [mock_model]

    mock_client = MagicMock()
    mock_client.list.return_value = mock_response

    service = OllamaService(model="qwen2.5:3b", client=mock_client)
    res = service.model_available()
    assert res.available is True
    assert res.model == "qwen2.5:3b"

def test_model_available_missing():
    """Verify model_available returns available=False when model is not found."""
    mock_model = MagicMock()
    mock_model.model = "llama3:8b"
    mock_response = MagicMock()
    mock_response.models = [mock_model]

    mock_client = MagicMock()
    mock_client.list.return_value = mock_response

    service = OllamaService(model="qwen2.5:3b", client=mock_client)
    res = service.model_available()
    assert res.available is False

def test_select_tool_normalization_with_tool_call():
    """Verify normalization of native tool call into ToolSelectionResult."""
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "calculator"
    mock_tool_call.function.arguments = {"expression": "25 * 16"}

    mock_msg = MagicMock()
    mock_msg.content = ""
    mock_msg.tool_calls = [mock_tool_call]

    mock_res = MagicMock()
    mock_res.message = mock_msg
    mock_res.total_duration = 150_000_000  # 150 ms in nanoseconds

    mock_client = MagicMock()
    mock_client.chat.return_value = mock_res

    service = OllamaService(model="qwen2.5:3b", client=mock_client)
    result = service.select_tool("What is 25 * 16?")
    assert result.tool_called is True
    assert result.tool_name == "calculator"
    assert result.arguments == {"expression": "25 * 16"}
    assert result.model == "qwen2.5:3b"
    assert result.duration_ms == 150.0

def test_select_tool_normalization_with_no_tool_call():
    """Verify normalization when model does not trigger any tool call."""
    mock_msg = MagicMock()
    mock_msg.content = "Just answering directly"
    mock_msg.tool_calls = None

    mock_res = MagicMock()
    mock_res.message = mock_msg
    mock_res.total_duration = 80_000_000

    mock_client = MagicMock()
    mock_client.chat.return_value = mock_res

    service = OllamaService(model="qwen2.5:3b", client=mock_client)
    result = service.select_tool("Tell me a joke")
    assert result.tool_called is False
    assert result.tool_name is None
    assert result.arguments is None
    assert result.model == "qwen2.5:3b"
    assert result.raw_response == "Just answering directly"
    assert result.duration_ms == 80.0

def test_select_tool_raises_connection_error_on_network_failure():
    """Verify custom OllamaConnectionError is raised on network failure."""
    mock_client = MagicMock()
    mock_client.chat.side_effect = ConnectionError("Failed to establish connection")

    service = OllamaService(client=mock_client)
    with pytest.raises(OllamaConnectionError):
        service.select_tool("test query")
