"""Pydantic schemas for evaluation test queries."""

from typing import Literal
from pydantic import BaseModel, Field

QuerySplit = Literal["tuning", "held-out"]
QueryDifficulty = Literal["easy", "medium", "hard"]

class EvaluationQuery(BaseModel):
    """Schema representing an individual labeled evaluation benchmark query."""
    id: str = Field(..., description="Unique query identifier, e.g. Q001")
    query: str = Field(..., min_length=1, description="Realistic natural language user query")
    correct_tool: str = Field(..., description="Expected tool identifier from fixed label space or 'none'")
    split: QuerySplit = Field(..., description="Dataset split: 'tuning' or 'held-out'")
    difficulty: QueryDifficulty = Field(..., description="Difficulty level: 'easy', 'medium', or 'hard'")
    notes: str = Field(..., description="Rationale for ground truth and near-miss confusion risks")
