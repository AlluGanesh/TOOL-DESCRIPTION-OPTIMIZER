"""Basic sanity test to verify imports and health check structure."""

def test_imports():
    """Verify core imports load without circular dependency errors."""
    from backend.app.main import app
    from backend.app.core.config import OLLAMA_HOST, OLLAMA_MODEL
    from backend.app.core.constants import FIXED_TOOL_NAMES, BASELINE_TOOL_DESCRIPTIONS
    from backend.app.utils.validation import validate_tool_names
    from backend.app.utils.metrics import calculate_accuracy

    assert app is not None
    assert OLLAMA_HOST is not None
    assert OLLAMA_MODEL == "qwen2.5:3b"
    assert len(FIXED_TOOL_NAMES) == 10
    assert len(BASELINE_TOOL_DESCRIPTIONS) == 10
    assert validate_tool_names(FIXED_TOOL_NAMES) is True
    assert calculate_accuracy(10, 20) == 0.5
