"""Validation utilities for tools and dataset schemas."""

from typing import List
from backend.app.core.constants import FIXED_TOOL_NAMES

def validate_tool_names(tool_names: List[str]) -> bool:
    """Verifies that all required 10 fixed tools are present and strictly match expected names."""
    return set(tool_names) == set(FIXED_TOOL_NAMES)
