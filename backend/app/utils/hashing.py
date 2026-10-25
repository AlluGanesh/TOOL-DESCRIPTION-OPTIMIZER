"""Deterministic SHA-256 hashing utilities for tools, datasets, and cache keys."""

import hashlib
import json
from typing import Any, Dict, List, Union

from backend.app.models.query_models import EvaluationQuery
from backend.app.models.tool_models import ToolDefinition

def compute_content_hash(data: Any) -> str:
    """Computes a deterministic SHA-256 hex digest for serializable data."""
    if isinstance(data, str):
        serialized = data
    else:
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def compute_tools_hash(tools: List[Union[ToolDefinition, Dict[str, Any]]]) -> str:
    """Computes a deterministic SHA-256 hash of a list of tool definitions.
    
    Tools are sorted by name to guarantee identical digests regardless of list order.
    """
    normalized_list = []
    for tool in tools:
        if isinstance(tool, ToolDefinition):
            normalized_list.append(tool.model_dump())
        elif isinstance(tool, dict):
            normalized_list.append(tool)
        else:
            raise TypeError(f"Unsupported tool type: {type(tool)}")

    # Sort tools alphabetically by name for deterministic serialization
    sorted_tools = sorted(normalized_list, key=lambda t: t.get("name", ""))
    return compute_content_hash(sorted_tools)

def compute_dataset_hash(queries: List[Union[EvaluationQuery, Dict[str, Any]]]) -> str:
    """Computes a deterministic SHA-256 hash of a dataset partition.
    
    Queries are sorted by id to guarantee identical digests regardless of list order.
    """
    normalized_list = []
    for q in queries:
        if isinstance(q, EvaluationQuery):
            normalized_list.append(q.model_dump())
        elif isinstance(q, dict):
            normalized_list.append(q)
        else:
            raise TypeError(f"Unsupported query type: {type(q)}")

    sorted_queries = sorted(normalized_list, key=lambda q: q.get("id", ""))
    return compute_content_hash(sorted_queries)

def compute_evaluation_cache_key(
    model: str,
    tool_definition_hash: str,
    query_id: str,
    query_text: str,
    run_index: int = 0,
) -> str:
    """Generates a stable, reproducible SHA-256 cache key for an evaluation inference call."""
    query_text_hash = compute_content_hash(query_text.strip())
    composite = f"{model}:{tool_definition_hash}:{query_id}:{run_index}:{query_text_hash}"
    return hashlib.sha256(composite.encode("utf-8")).hexdigest()
