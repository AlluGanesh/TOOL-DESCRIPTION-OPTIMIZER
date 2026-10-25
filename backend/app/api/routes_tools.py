"""API routes for tools inspection and native tool selection."""

from typing import List
from fastapi import APIRouter

from backend.app.models.tool_models import (
    ToolDefinition,
    ToolSelectionRequest,
    ToolSelectionResult,
)
from backend.app.services.ollama_service import ollama_service
from backend.app.services.tool_service import load_canonical_tools

router = APIRouter(prefix="/tools", tags=["tools"])

@router.get("", response_model=List[ToolDefinition])
@router.get("/", response_model=List[ToolDefinition], include_in_schema=False)
def get_canonical_tools():
    """Returns the canonical 10 fixed tool definitions from tools/tools.json."""
    return load_canonical_tools()

@router.post("/select", response_model=ToolSelectionResult)
def select_tool(payload: ToolSelectionRequest):
    """Executes native tool calling via Ollama for a user query against the 10 fixed tools."""
    return ollama_service.select_tool(query=payload.query)
