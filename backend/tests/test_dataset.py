"""Tests for verifying the integrity, distribution, and lack of leakage in data/queries.json."""

from collections import Counter
import pytest

from backend.app.core.constants import FIXED_TOOL_NAMES
from backend.app.services.dataset_service import (
    ALLOWED_DIFFICULTIES,
    ALLOWED_SPLITS,
    ALLOWED_TOOL_LABELS,
    EXPECTED_HELD_OUT_COUNT,
    EXPECTED_NONE_COUNT,
    EXPECTED_TOTAL_COUNT,
    EXPECTED_TUNING_COUNT,
    load_queries,
)

@pytest.fixture(scope="module")
def dataset():
    """Loads and parses the 50 queries dataset."""
    return load_queries()

def test_dataset_total_count(dataset):
    """Verify dataset contains exactly 50 labeled queries."""
    assert len(dataset) == EXPECTED_TOTAL_COUNT

def test_dataset_split_counts(dataset):
    """Verify split contains exactly 35 tuning and 15 held-out queries."""
    tuning = [q for q in dataset if q.split == "tuning"]
    held_out = [q for q in dataset if q.split == "held-out"]

    assert len(tuning) == EXPECTED_TUNING_COUNT
    assert len(held_out) == EXPECTED_HELD_OUT_COUNT
    assert len(tuning) + len(held_out) == EXPECTED_TOTAL_COUNT

def test_unique_ids(dataset):
    """Verify all query IDs are unique and properly formatted."""
    ids = [q.id for q in dataset]
    assert len(ids) == len(set(ids))
    for qid in ids:
        assert qid.startswith("Q")

def test_unique_non_empty_queries(dataset):
    """Verify all query texts are non-empty and unique."""
    queries = [q.query.strip() for q in dataset]
    assert len(queries) == len(set(queries))
    for q in queries:
        assert len(q) > 5

def test_fixed_label_space(dataset):
    """Verify all correct_tool labels belong strictly to the 10 fixed tools or 'none'."""
    labels = {q.correct_tool for q in dataset}
    assert labels.issubset(ALLOWED_TOOL_LABELS)
    assert labels == ALLOWED_TOOL_LABELS

def test_none_class_count(dataset):
    """Verify exactly 5 queries are labeled 'none'."""
    none_queries = [q for q in dataset if q.correct_tool == "none"]
    assert len(none_queries) == EXPECTED_NONE_COUNT

def test_held_out_class_coverage(dataset):
    """Verify every tool class and 'none' is represented in the held-out split."""
    held_out_classes = {q.correct_tool for q in dataset if q.split == "held-out"}
    assert held_out_classes == ALLOWED_TOOL_LABELS

def test_tuning_class_coverage(dataset):
    """Verify every tool class and 'none' is represented in the tuning split."""
    tuning_classes = {q.correct_tool for q in dataset if q.split == "tuning"}
    assert tuning_classes == ALLOWED_TOOL_LABELS

def test_no_tool_identifier_leakage(dataset):
    """Verify queries do not explicitly leak tool identifier names as prompt instructions."""
    for q in dataset:
        lower_text = q.query.lower()
        for tool_name in FIXED_TOOL_NAMES:
            assert tool_name not in lower_text, (
                f"Query {q.id} leaks tool identifier '{tool_name}': {q.query}"
            )

def test_difficulty_values_and_distribution(dataset):
    """Verify valid difficulty levels and a balanced difficulty distribution."""
    difficulties = [q.difficulty for q in dataset]
    for d in difficulties:
        assert d in ALLOWED_DIFFICULTIES

    counts = Counter(difficulties)
    # Ensure all difficulty levels are represented in both splits
    assert counts["easy"] >= 10
    assert counts["medium"] >= 10
    assert counts["hard"] >= 10

    tuning_diffs = Counter(q.difficulty for q in dataset if q.split == "tuning")
    held_out_diffs = Counter(q.difficulty for q in dataset if q.split == "held-out")

    assert all(tuning_diffs[d] > 0 for d in ALLOWED_DIFFICULTIES)
    assert all(held_out_diffs[d] > 0 for d in ALLOWED_DIFFICULTIES)

def test_all_required_fields_populated(dataset):
    """Verify every record has id, query, correct_tool, split, difficulty, and notes."""
    for q in dataset:
        assert q.id
        assert q.query
        assert q.correct_tool
        assert q.split in ALLOWED_SPLITS
        assert q.difficulty in ALLOWED_DIFFICULTIES
        assert q.notes and len(q.notes) > 5
