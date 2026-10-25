"""API routes for triggering evaluations and inspecting evaluation results."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from backend.app.core.config import RESULTS_DIR
from backend.app.models.evaluation_models import EvaluationRequest, EvaluationResult
from backend.app.services.evaluator_service import evaluator_service

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.post("/run", response_model=EvaluationResult)
@router.post("", response_model=EvaluationResult, include_in_schema=False)
def run_evaluation(payload: EvaluationRequest):
    """Thin API route to trigger evaluation via the EvaluatorService."""
    tools = None
    if payload.tools_file:
        from backend.app.services.tool_service import load_tools_from_file
        tools = load_tools_from_file(payload.tools_file)

    split = payload.split.replace("_", "-")
    return evaluator_service.evaluate(
        split=split,
        runs_per_query=payload.runs_per_query,
        force_refresh=payload.force_refresh,
        tools=tools,
    )

@router.get("/latest", response_model=EvaluationResult)
def get_latest_evaluation(split: str = "tuning"):
    """Retrieves the most recent evaluation output record for a split if one exists."""
    latest_file = RESULTS_DIR / f"evaluation_{split}_latest.json"
    if not latest_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No previous evaluation run found for split '{split}'."
        )
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return EvaluationResult.model_validate(data)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read evaluation record: {exc}"
        ) from exc
