"""Service for loading, validating, and converting canonical tool definitions."""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from backend.app.core.config import TOOLS_FILE
from backend.app.core.constants import FIXED_TOOL_NAMES
from backend.app.core.exceptions import ToolDefinitionError
from backend.app.core.logging import logger
from backend.app.models.tool_models import ToolDefinition

def load_canonical_tools(file_path: Union[str, Path] = TOOLS_FILE) -> List[ToolDefinition]:
    """Loads and validates the fixed 10 tool definitions from tools/tools.json.
    
    Guarantees:
    - File exists and is valid JSON.
    - Exactly 10 tools are present.
    - Tool names match FIXED_TOOL_NAMES.
    - Parameter schemas are preserved.
    """
    path = Path(file_path)
    if not path.exists():
        raise ToolDefinitionError(f"Canonical tools file not found at: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_tools = json.load(f)
    except Exception as exc:
        raise ToolDefinitionError(f"Failed to read tools JSON: {exc}") from exc

    if not isinstance(raw_tools, list):
        raise ToolDefinitionError(f"Tools file must contain a JSON list, found: {type(raw_tools).__name__}")

    if len(raw_tools) != len(FIXED_TOOL_NAMES):
        raise ToolDefinitionError(
            f"Expected exactly {len(FIXED_TOOL_NAMES)} tools, found {len(raw_tools)}"
        )

    tools: List[ToolDefinition] = []
    loaded_names: List[str] = []

    for item in raw_tools:
        try:
            tool = ToolDefinition.model_validate(item)
            tools.append(tool)
            loaded_names.append(tool.name)
        except Exception as exc:
            raise ToolDefinitionError(f"Invalid tool definition structure: {exc}") from exc

    missing = set(FIXED_TOOL_NAMES) - set(loaded_names)
    extra = set(loaded_names) - set(FIXED_TOOL_NAMES)
    if missing or extra:
        raise ToolDefinitionError(
            f"Tool names mismatch. Missing: {missing}, Extra: {extra}"
        )

    return tools

def tool_to_ollama_format(tool: Union[ToolDefinition, Dict[str, Any]]) -> Dict[str, Any]:
    """Converts a single project tool definition into Ollama's native tool format."""
    if isinstance(tool, ToolDefinition):
        name = tool.name
        description = tool.description
        parameters = tool.parameters.model_dump()
    elif isinstance(tool, dict):
        name = tool["name"]
        description = tool["description"]
        params = tool.get("parameters", {})
        parameters = params.model_dump() if hasattr(params, "model_dump") else params
    else:
        raise ToolDefinitionError(f"Unsupported tool type: {type(tool)}")

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }

def tools_to_ollama_format(
    tools: List[Union[ToolDefinition, Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Converts a list of project tool definitions into Ollama's native tools payload format."""
    return [tool_to_ollama_format(t) for t in tools]

def load_tools_from_file(file_path: Union[str, Path]) -> List[ToolDefinition]:
    """Loads and validates tool definitions from a tools list JSON or optimization record JSON.
    
    Supports:
    - Canonical or custom tools JSON files containing a list of 10 tool definitions.
    - Optimization round artifacts (e.g. round_01.json, summary.json) containing candidate_descriptions
      or best_descriptions.
    """
    path = Path(file_path)
    if not path.exists():
        raise ToolDefinitionError(f"Tools file not found at: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise ToolDefinitionError(f"Failed to read tools JSON from {path}: {exc}") from exc

    if isinstance(data, list):
        return load_canonical_tools(path)

    if isinstance(data, dict):
        desc_map = (
            data.get("candidate_descriptions")
            or data.get("best_descriptions")
            or data.get("descriptions")
        )
        if isinstance(desc_map, dict):
            canonical_tools = load_canonical_tools()
            updated_tools: List[ToolDefinition] = []
            for tool in canonical_tools:
                new_desc = desc_map.get(tool.name, tool.description)
                cloned = tool.model_copy(update={"description": new_desc}, deep=True)
                updated_tools.append(cloned)
            return updated_tools

    raise ToolDefinitionError(
        f"Unsupported tools file format at {path}. Expected JSON list of tools or optimization record."
    )

