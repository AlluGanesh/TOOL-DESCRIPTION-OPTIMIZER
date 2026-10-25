"""Service for loading and validating the labeled 50-query benchmark dataset."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from backend.app.core.config import DATA_QUERIES_FILE
from backend.app.core.constants import FIXED_TOOL_NAMES
from backend.app.core.exceptions import AppBaseException
from backend.app.models.query_models import EvaluationQuery

ALLOWED_TOOL_LABELS: Set[str] = set(FIXED_TOOL_NAMES) | {"none"}
ALLOWED_SPLITS: Set[str] = {"tuning", "held-out"}
ALLOWED_DIFFICULTIES: Set[str] = {"easy", "medium", "hard"}

EXPECTED_TOTAL_COUNT = 50
EXPECTED_TUNING_COUNT = 35
EXPECTED_HELD_OUT_COUNT = 15
EXPECTED_NONE_COUNT = 5

class DatasetValidationError(AppBaseException):
    """Raised when the benchmark dataset violates integrity or structure constraints."""
    def __init__(self, message: str):
        super().__init__(f"Dataset validation failed: {message}", status_code=500)

def load_queries(file_path: Optional[Union[str, Path]] = None) -> List[EvaluationQuery]:
    """Loads and validates the 50 queries dataset from data/queries.json."""
    path = Path(file_path) if file_path else DATA_QUERIES_FILE
    if not path.exists():
        raise DatasetValidationError(f"Queries file not found at: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as exc:
        raise DatasetValidationError(f"Failed to parse JSON from {path}: {exc}") from exc

    if not isinstance(raw_data, list):
        raise DatasetValidationError(f"Expected JSON array of queries, got {type(raw_data).__name__}")

    queries = [EvaluationQuery.model_validate(item) for item in raw_data]
    validate_dataset(queries)
    return queries

def validate_dataset(queries: List[EvaluationQuery]) -> Dict[str, Any]:
    """Strictly validates all 15 integrity and distribution constraints for the dataset."""
    # 1. Total record count
    if len(queries) != EXPECTED_TOTAL_COUNT:
        raise DatasetValidationError(
            f"Expected exactly {EXPECTED_TOTAL_COUNT} queries, found {len(queries)}"
        )

    ids = [q.id for q in queries]
    query_texts = [q.query.strip().lower() for q in queries]

    # 3. Unique IDs
    if len(ids) != len(set(ids)):
        duplicates = [x for x in ids if ids.count(x) > 1]
        raise DatasetValidationError(f"Duplicate query IDs found: {set(duplicates)}")

    # 4 & 13. Unique & Non-empty queries
    for q in queries:
        if not q.query.strip():
            raise DatasetValidationError(f"Query {q.id} has empty query text")

    if len(query_texts) != len(set(query_texts)):
        duplicate_queries = [x for x in query_texts if query_texts.count(x) > 1]
        raise DatasetValidationError(f"Duplicate query texts found: {set(duplicate_queries)}")

    # 5. Fixed label space
    for q in queries:
        if q.correct_tool not in ALLOWED_TOOL_LABELS:
            raise DatasetValidationError(
                f"Query {q.id} has invalid tool label '{q.correct_tool}'. Allowed: {ALLOWED_TOOL_LABELS}"
            )

    # 6. Valid splits
    for q in queries:
        if q.split not in ALLOWED_SPLITS:
            raise DatasetValidationError(
                f"Query {q.id} has invalid split '{q.split}'. Allowed: {ALLOWED_SPLITS}"
            )

    # 7 & 8. Split distribution counts
    tuning_queries = [q for q in queries if q.split == "tuning"]
    held_out_queries = [q for q in queries if q.split == "held-out"]

    if len(tuning_queries) != EXPECTED_TUNING_COUNT:
        raise DatasetValidationError(
            f"Expected exactly {EXPECTED_TUNING_COUNT} tuning queries, found {len(tuning_queries)}"
        )
    if len(held_out_queries) != EXPECTED_HELD_OUT_COUNT:
        raise DatasetValidationError(
            f"Expected exactly {EXPECTED_HELD_OUT_COUNT} held-out queries, found {len(held_out_queries)}"
        )

    # 9. All 11 classes present in dataset
    all_classes_in_data = {q.correct_tool for q in queries}
    missing_classes = ALLOWED_TOOL_LABELS - all_classes_in_data
    if missing_classes:
        raise DatasetValidationError(f"Missing tool classes in dataset: {missing_classes}")

    # 10. Held-out coverage across all classes
    held_out_classes = {q.correct_tool for q in held_out_queries}
    missing_held_out = ALLOWED_TOOL_LABELS - held_out_classes
    if missing_held_out:
        raise DatasetValidationError(f"Held-out set missing tool classes: {missing_held_out}")

    # 11. Exactly 5 'none' queries
    none_queries = [q for q in queries if q.correct_tool == "none"]
    if len(none_queries) != EXPECTED_NONE_COUNT:
        raise DatasetValidationError(
            f"Expected exactly {EXPECTED_NONE_COUNT} 'none' queries, found {len(none_queries)}"
        )

    # 12. No tool-name leakage into query text
    for q in queries:
        lower_query = q.query.lower()
        for tool_name in FIXED_TOOL_NAMES:
            # Check for exact tool name identifier in query (e.g. search_web, read_file)
            if tool_name in lower_query:
                raise DatasetValidationError(
                    f"Label leakage detected in query {q.id}: mentions tool identifier '{tool_name}'"
                )

    # 14. Difficulty validation
    for q in queries:
        if q.difficulty not in ALLOWED_DIFFICULTIES:
            raise DatasetValidationError(
                f"Query {q.id} has invalid difficulty '{q.difficulty}'. Allowed: {ALLOWED_DIFFICULTIES}"
            )

    return {
        "total_count": len(queries),
        "tuning_count": len(tuning_queries),
        "held_out_count": len(held_out_queries),
        "none_count": len(none_queries),
        "valid": True,
    }
