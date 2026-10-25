"""Pydantic schemas for evaluation runs, per-query metrics, confusion matrices, and mistakes."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class PerRunPrediction(BaseModel):
    """Result of an individual inference run for a query."""
    run_index: int
    predicted_tool: str
    tool_called: bool
    arguments: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    cache_hit: bool = False
    raw_response: Optional[str] = None

class EvaluationQueryResult(BaseModel):
    """Evaluation outcome for an individual benchmark query."""
    query_id: str
    query: str
    expected_tool: str
    split: str
    difficulty: str
    predictions_by_run: List[str]
    final_prediction: str
    correct: bool
    run_details: List[PerRunPrediction] = Field(default_factory=list)

class EvaluationMistake(BaseModel):
    """Details of an incorrect tool selection prediction."""
    query_id: str
    query: str
    expected_tool: str
    predicted_tool: str
    split: str
    difficulty: str
    predictions_by_run: List[str]
    notes: Optional[str] = None

class EvaluationMetadata(BaseModel):
    """Provenance and runtime configuration for an evaluation run."""
    run_id: str
    model: str
    split: str
    runs_per_query: int
    timestamp: str
    total_queries: int
    tool_definition_hash: str
    dataset_hash: str

class PerToolMetrics(BaseModel):
    """Per-category classification metrics."""
    tool: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    total_actual: int
    total_predicted: int

class EvaluationResult(BaseModel):
    """Complete serialized evaluation run record."""
    metadata: EvaluationMetadata
    total_queries: int
    correct_count: int
    accuracy: float
    per_tool_metrics: Dict[str, PerToolMetrics]
    confusion_matrix: Dict[str, Dict[str, int]]
    mistakes: List[EvaluationMistake]
    queries: List[EvaluationQueryResult]

class EvaluationRequest(BaseModel):
    """Payload to initiate an evaluation run."""
    split: Literal["tuning", "held-out", "held_out"] = "tuning"
    runs_per_query: int = Field(default=1, ge=1)
    force_refresh: bool = False
    tools_file: Optional[str] = None
