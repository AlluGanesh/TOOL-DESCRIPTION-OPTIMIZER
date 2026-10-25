"""Unit tests for configuration loading, tool validation, and schema conversion."""

import pytest
from backend.app.core.config import OLLAMA_HOST, OLLAMA_MODEL, TOOLS_FILE
from backend.app.core.constants import FIXED_TOOL_NAMES
from backend.app.services.tool_service import (
    load_canonical_tools,
    tool_to_ollama_format,
    tools_to_ollama_format,
)

def test_ollama_configuration():
    """Verify Ollama host and model configuration load expected defaults."""
    assert OLLAMA_HOST is not None
    assert "11434" in OLLAMA_HOST
    assert OLLAMA_MODEL == "qwen2.5:3b"

def test_canonical_tools_loading():
    """Verify loading from tools/tools.json."""
    assert TOOLS_FILE.exists(), f"Tools file missing at {TOOLS_FILE}"
    tools = load_canonical_tools()

    # Exactly 10 tools
    assert len(tools) == 10
    assert len(tools) == len(FIXED_TOOL_NAMES)

def test_canonical_tool_names_match_fixed():
    """Verify all 10 fixed tool names are present without alteration."""
    tools = load_canonical_tools()
    tool_names = [t.name for t in tools]
    assert sorted(tool_names) == sorted(FIXED_TOOL_NAMES)

def test_canonical_tool_schemas_preserved():
    """Verify parameters, types, and required fields are defined for all tools."""
    tools = load_canonical_tools()
    for tool in tools:
        assert tool.name in FIXED_TOOL_NAMES
        assert isinstance(tool.description, str) and len(tool.description) > 0
        assert tool.parameters.type == "object"
        assert isinstance(tool.parameters.properties, dict)
        assert isinstance(tool.parameters.required, list)
        assert len(tool.parameters.properties) > 0

def test_tool_to_ollama_format_conversion():
    """Verify translation of canonical tools into native Ollama function schema."""
    tools = load_canonical_tools()
    calculator_tool = next(t for t in tools if t.name == "calculator")

    ollama_tool = tool_to_ollama_format(calculator_tool)
    assert ollama_tool["type"] == "function"
    assert "function" in ollama_tool
    func = ollama_tool["function"]
    assert func["name"] == "calculator"
    assert func["description"] == calculator_tool.description
    assert "expression" in func["parameters"]["properties"]
    assert "expression" in func["parameters"]["required"]

    all_ollama_tools = tools_to_ollama_format(tools)
    assert len(all_ollama_tools) == 10
    for ot in all_ollama_tools:
        assert ot["type"] == "function"
        assert ot["function"]["name"] in FIXED_TOOL_NAMES
