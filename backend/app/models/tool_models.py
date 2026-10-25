"""Pydantic schemas for tool definitions, requests, and tool selection results."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ToolParameterSchema(BaseModel):
    """Schema defining parameters for a tool."""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)

class ToolDefinition(BaseModel):
    """Tool schema containing fixed name, parameters, and optimizable description."""
    name: str
    description: str
    parameters: ToolParameterSchema

class ToolSelectionRequest(BaseModel):
    """Request payload for tool selection."""
    query: str

class ToolSelectionResult(BaseModel):
    """Normalized response representation of a tool selection outcome."""
    tool_called: bool
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    model: str
    raw_response: Optional[str] = None
    duration_ms: Optional[float] = None

class OllamaHealthResponse(BaseModel):
    """Response payload indicating Ollama server reachability."""
    reachable: bool
    host: str
    message: Optional[str] = None

class OllamaModelResponse(BaseModel):
    """Response payload indicating configured model availability."""
    available: bool
    model: str
    host: str
    available_models: List[str] = Field(default_factory=list)
    message: Optional[str] = None
