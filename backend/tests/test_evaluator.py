"""Comprehensive unit tests for the EvaluatorService, caching, metrics, and voting logic.

All tests utilize mocked Ollama interactions and run fully isolated from live servers.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.app.core.constants import ALL_LABELS, FIXED_TOOL_NAMES
from backend.app.core.exceptions import EvaluatorError, OllamaConnectionError
from backend.app.models.evaluation_models import EvaluationResult
from backend.app.models.query_models import EvaluationQuery
from backend.app.models.tool_models import ToolDefinition, ToolParameterSchema, ToolSelectionResult
from backend.app.services.cache_service import CacheService
from backend.app.services.evaluator_service import (
    EvaluatorService,
    execute_with_retry,
    resolve_majority_vote,
)
from backend.app.utils.hashing import (
    compute_dataset_hash,
    compute_evaluation_cache_key,
    compute_tools_hash,
)
from backend.app.utils.metrics import (
    build_confusion_matrix,
    calculate_accuracy,
    calculate_per_tool_metrics,
)

@pytest.fixture
def dummy_tools():
    """Generates standard 10 dummy tools matching fixed tool names."""
    return [
        ToolDefinition(
            name=name,
            description=f"Description for {name}",
            parameters=ToolParameterSchema(
                type="object",
                properties={"arg": {"type": "string"}},
                required=["arg"],
            ),
        )
        for name in FIXED_TOOL_NAMES
    ]

@pytest.fixture
def sample_tuning_queries():
    """Generates 35 dummy tuning queries to satisfy exact split count requirements."""
    queries = []
    for idx in range(1, 36):
        tool = FIXED_TOOL_NAMES[(idx - 1) % len(FIXED_TOOL_NAMES)] if idx <= 32 else "none"
        queries.append(
            EvaluationQuery(
                id=f"T{idx:03d}",
                query=f"Sample query text number {idx} for tuning",
                correct_tool=tool,
                split="tuning",
                difficulty="medium",
                notes="Test notes",
            )
        )
    return queries

@pytest.fixture
def sample_held_out_queries():
    """Generates 15 dummy held-out queries to satisfy exact split count requirements."""
    queries = []
    for idx in range(1, 16):
        tool = FIXED_TOOL_NAMES[(idx - 1) % len(FIXED_TOOL_NAMES)] if idx <= 13 else "none"
        queries.append(
            EvaluationQuery(
                id=f"H{idx:03d}",
                query=f"Sample query text number {idx} for held-out",
                correct_tool=tool,
                split="held-out",
                difficulty="hard",
                notes="Test notes",
            )
        )
    return queries

# 1. Split filtering
def test_split_filtering(tmp_path, dummy_tools, sample_tuning_queries, sample_held_out_queries):
    """Verify evaluator processes only queries matching the requested split."""
    combined = sample_tuning_queries + sample_held_out_queries
    mock_ollama = MagicMock()
    mock_ollama.model = "qwen2.5:3b"
    mock_ollama.select_tool.return_value = ToolSelectionResult(
        tool_called=True, tool_name="search_web", model="qwen2.5:3b"
    )

    evaluator = EvaluatorService(
        ollama_svc=mock_ollama,
        cache_svc=CacheService(cache_dir=tmp_path / "cache"),
        results_dir=tmp_path / "results",
    )

    res_tuning = evaluator.evaluate(split="tuning", tools=dummy_tools, queries=combined)
    assert res_tuning.total_queries == 35
    assert mock_ollama.select_tool.call_count == 35

    mock_ollama.select_tool.reset_mock()
    res_held_out = evaluator.evaluate(split="held-out", tools=dummy_tools, queries=combined)
    assert res_held_out.total_queries == 15
    assert mock_ollama.select_tool.call_count == 15

# 2. Invalid split rejection
def test_invalid_split_rejection(tmp_path, dummy_tools):
    """Verify evaluator rejects invalid split identifiers with an EvaluatorError."""
    evaluator = EvaluatorService(
        cache_svc=CacheService(cache_dir=tmp_path / "cache"),
        results_dir=tmp_path / "results",
    )
    with pytest.raises(EvaluatorError) as exc_info:
        evaluator.evaluate(split="training_set", tools=dummy_tools)
    assert "Invalid split" in str(exc_info.value)

# 3. Correct prediction
def test_correct_prediction(tmp_path, dummy_tools, sample_tuning_queries):
    """Verify correct predictions are counted and marked accurate."""
    mock_ollama = MagicMock()
    mock_ollama.model = "qwen2.5:3b"

    # Always predict matching tool
    def mock_select(query, tools):
        target = next(q.correct_tool for q in sample_tuning_queries if q.query == query)
        called = (target != "none")
        return ToolSelectionResult(
            tool_called=called,
            tool_name=target if called else None,
            model="qwen2.5:3b",
        )
    mock_ollama.select_tool.side_effect = mock_select

    evaluator = EvaluatorService(
        ollama_svc=mock_ollama,
        cache_svc=CacheService(cache_dir=tmp_path / "cache"),
        results_dir=tmp_path / "results",
    )

    result = evaluator.evaluate(split="tuning", tools=dummy_tools, queries=sample_tuning_queries)
    assert result.correct_count == 35
    assert result.accuracy == 1.0
    assert len(result.mistakes) == 0

# 4. Incorrect prediction
def test_incorrect_prediction(tmp_path, dummy_tools, sample_tuning_queries):
    """Verify misrouted predictions are identified, counted as mistakes, and recorded."""
    mock_ollama = MagicMock()
    mock_ollama.model = "qwen2.5:3b"
    # Always predict calculator regardless of actual label
    mock_ollama.select_tool.return_value = ToolSelectionResult(
        tool_called=True, tool_name="calculator", model="qwen2.5:3b"
    )

    evaluator = EvaluatorService(
        ollama_svc=mock_ollama,
        cache_svc=CacheService(cache_dir=tmp_path / "cache"),
        results_dir=tmp_path / "results",
    )

    result = evaluator.evaluate(split="tuning", tools=dummy_tools, queries=sample_tuning_queries)
    assert len(result.mistakes) > 0
    mistake = result.mistakes[0]
    assert mistake.predicted_tool == "calculator"
    assert mistake.expected_tool != "calculator"

# 5. 'none' prediction
def test_none_prediction(tmp_path, dummy_tools, sample_tuning_queries):
    """Verify that when no tool call occurs, it correctly resolves to 'none'."""
    mock_ollama = MagicMock()
    mock_ollama.model = "qwen2.5:3b"
    # Model returns no tool call
    mock_ollama.select_tool.return_value = ToolSelectionResult(
        tool_called=False, tool_name=None, model="qwen2.5:3b"
    )

    evaluator = EvaluatorService(
        ollama_svc=mock_ollama,
        cache_svc=CacheService(cache_dir=tmp_path / "cache"),
        results_dir=tmp_path / "results",
    )

    result = evaluator.evaluate(split="tuning", tools=dummy_tools, queries=sample_tuning_queries)
    # All predictions should be 'none'
    for q in result.queries:
        assert q.final_prediction == "none"

# 6. Confusion matrix generation
def test_confusion_matrix_generation():
    """Verify confusion matrix contains complete 11x11 classes with correct cell counts."""
    expected = ["calculator", "search_web", "search_web", "none"]
    predicted = ["calculator", "search_docs", "search_web", "none"]

    matrix = build_confusion_matrix(expected, predicted, ALL_LABELS)

    assert len(matrix) == len(ALL_LABELS)
    for row_label in ALL_LABELS:
        assert len(matrix[row_label]) == len(ALL_LABELS)

    # Check specific cell counts
    assert matrix["calculator"]["calculator"] == 1
    assert matrix["search_web"]["search_web"] == 1
    assert matrix["search_web"]["search_docs"] == 1
    assert matrix["none"]["none"] == 1
    assert matrix["search_web"]["calculator"] == 0

# 7. Precision calculation
def test_precision_calculation():
    """Verify precision formula (TP / (TP + FP))."""
    expected = ["calculator", "calculator", "search_web"]
    predicted = ["calculator", "search_web", "calculator"]

    metrics = calculate_per_tool_metrics(expected, predicted, ALL_LABELS)
    calc_m = metrics["calculator"]

    # Calculator: TP=1, FP=1 (predicted calculator for search_web) -> Precision = 1/2 = 0.5
    assert calc_m.true_positives == 1
    assert calc_m.false_positives == 1
    assert calc_m.precision == 0.5

# 8. Recall calculation
def test_recall_calculation():
    """Verify recall formula (TP / (TP + FN))."""
    expected = ["calculator", "calculator", "search_web"]
    predicted = ["calculator", "search_web", "search_web"]

    metrics = calculate_per_tool_metrics(expected, predicted, ALL_LABELS)
    calc_m = metrics["calculator"]

    # Calculator: TP=1, FN=1 (expected calculator, predicted search_web) -> Recall = 1/2 = 0.5
    assert calc_m.true_positives == 1
    assert calc_m.false_negatives == 1
    assert calc_m.recall == 0.5

# 9. Accuracy calculation
def test_accuracy_calculation():
    """Verify exact match accuracy ratio."""
    assert calculate_accuracy(10, 20) == 0.5
    assert calculate_accuracy(0, 50) == 0.0
    assert calculate_accuracy(50, 50) == 1.0
    assert calculate_accuracy(0, 0) == 0.0

# 10. Majority voting across multiple runs
def test_majority_voting():
    """Verify majority vote selects candidate with highest frequency."""
    runs = ["search_web", "search_docs", "search_web"]
    assert resolve_majority_vote(runs) == "search_web"

    runs2 = ["calculator", "calculator", "get_weather"]
    assert resolve_majority_vote(runs2) == "calculator"

# 11. Deterministic tie handling
def test_deterministic_tie_handling():
    """Verify ties deterministically pick the candidate with lower index in ALL_LABELS."""
    # search_web index is 0, search_docs index is 1
    assert resolve_majority_vote(["search_docs", "search_web"]) == "search_web"

    # read_file index is 2, write_file index is 3
    assert resolve_majority_vote(["write_file", "read_file"]) == "read_file"

# 12. Cache key generation
def test_cache_key_generation():
    """Verify cache keys are deterministic SHA-256 digests and sensitive to all parameters."""
    k1 = compute_evaluation_cache_key("qwen2.5:3b", "hash1", "Q001", "query text", 0)
    k2 = compute_evaluation_cache_key("qwen2.5:3b", "hash1", "Q001", "query text", 0)
    k3 = compute_evaluation_cache_key("qwen2.5:3b", "hash1", "Q001", "query text", 1)
    k4 = compute_evaluation_cache_key("qwen2.5:3b", "hash2", "Q001", "query text", 0)

    assert k1 == k2
    assert k1 != k3
    assert k1 != k4
    assert len(k1) == 64

# 13. Cache hit behavior
def test_cache_hit_behavior(tmp_path, dummy_tools, sample_tuning_queries):
    """Verify cached entries prevent duplicate Ollama model invocations."""
    mock_ollama = MagicMock()
    mock_ollama.model = "qwen2.5:3b"
    mock_ollama.select_tool.return_value = ToolSelectionResult(
        tool_called=True, tool_name="search_web", model="qwen2.5:3b"
    )

    cache = CacheService(cache_dir=tmp_path / "cache")
    evaluator = EvaluatorService(
        ollama_svc=mock_ollama,
        cache_svc=cache,
        results_dir=tmp_path / "results",
    )

    # First run: Cache misses
    res1 = evaluator.evaluate(split="tuning", tools=dummy_tools, queries=sample_tuning_queries)
    assert mock_ollama.select_tool.call_count == 35
    for q in res1.queries:
        assert q.run_details[0].cache_hit is False

    # Second run: All cache hits
    mock_ollama.select_tool.reset_mock()
    res2 = evaluator.evaluate(split="tuning", tools=dummy_tools, queries=sample_tuning_queries)
    assert mock_ollama.select_tool.call_count == 0  # Zero network calls
    for q in res2.queries:
        assert q.run_details[0].cache_hit is True

# 14. Retry behavior
def test_retry_behavior():
    """Verify transient failures trigger retries up to max_retries."""
    attempts = [0]

    def flaky_func():
        attempts[0] += 1
        if attempts[0] < 3:
            raise ConnectionError("Temporary network blip")
        return "success"

    res = execute_with_retry(flaky_func, max_retries=3, delay_seconds=0.01)
    assert res == "success"
    assert attempts[0] == 3

# 15. Ollama failure is NOT converted to 'none'
def test_ollama_failure_not_converted_to_none(tmp_path, dummy_tools, sample_tuning_queries):
    """Verify that an unrecoverable Ollama failure raises an exception and does NOT record 'none'."""
    mock_ollama = MagicMock()
    mock_ollama.model = "qwen2.5:3b"
    mock_ollama.select_tool.side_effect = OllamaConnectionError("Server unreachable")

    evaluator = EvaluatorService(
        ollama_svc=mock_ollama,
        cache_svc=CacheService(cache_dir=tmp_path / "cache"),
        results_dir=tmp_path / "results",
    )

    with pytest.raises(OllamaConnectionError):
        evaluator.evaluate(split="tuning", tools=dummy_tools, queries=sample_tuning_queries)

# 16. Tool hash stability
def test_tool_hash_stability(dummy_tools):
    """Verify tool definition hash is stable across reordered tool lists."""
    h1 = compute_tools_hash(dummy_tools)
    reordered = list(reversed(dummy_tools))
    h2 = compute_tools_hash(reordered)
    assert h1 == h2

    # Modified description changes the hash
    modified = [dummy_tools[0].model_copy(update={"description": "Changed"})] + dummy_tools[1:]
    h3 = compute_tools_hash(modified)
    assert h1 != h3

# 17. Dataset hash stability
def test_dataset_hash_stability(sample_tuning_queries):
    """Verify dataset hash is stable across reordered query lists."""
    h1 = compute_dataset_hash(sample_tuning_queries)
    reordered = list(reversed(sample_tuning_queries))
    h2 = compute_dataset_hash(reordered)
    assert h1 == h2

# 18. Deterministic label ordering
def test_deterministic_label_ordering():
    """Verify label sequence strictly matches canonical order."""
    assert ALL_LABELS[0] == "search_web"
    assert ALL_LABELS[-1] == "none"
    assert len(ALL_LABELS) == 11

# 19. Evaluator result schema
def test_evaluator_result_schema(tmp_path, dummy_tools, sample_tuning_queries):
    """Verify evaluation output strictly conforms to the EvaluationResult Pydantic schema."""
    mock_ollama = MagicMock()
    mock_ollama.model = "qwen2.5:3b"
    mock_ollama.select_tool.return_value = ToolSelectionResult(
        tool_called=True, tool_name="search_web", model="qwen2.5:3b"
    )

    evaluator = EvaluatorService(
        ollama_svc=mock_ollama,
        cache_svc=CacheService(cache_dir=tmp_path / "cache"),
        results_dir=tmp_path / "results",
    )

    res = evaluator.evaluate(split="tuning", tools=dummy_tools, queries=sample_tuning_queries)
    assert isinstance(res, EvaluationResult)
    data = res.model_dump()
    assert "metadata" in data
    assert "accuracy" in data
    assert "confusion_matrix" in data
    assert "per_tool_metrics" in data
    assert "mistakes" in data

# 20. No execution of selected tools
def test_no_execution_of_selected_tools(tmp_path, dummy_tools, sample_tuning_queries):
    """Verify the evaluator evaluates tool selection only and never executes tool actions."""
    mock_ollama = MagicMock()
    mock_ollama.model = "qwen2.5:3b"
    # Return a write_file selection
    mock_ollama.select_tool.return_value = ToolSelectionResult(
        tool_called=True,
        tool_name="write_file",
        arguments={"path": str(tmp_path / "should_not_exist.txt"), "content": "malicious"},
        model="qwen2.5:3b",
    )

    evaluator = EvaluatorService(
        ollama_svc=mock_ollama,
        cache_svc=CacheService(cache_dir=tmp_path / "cache"),
        results_dir=tmp_path / "results",
    )

    evaluator.evaluate(split="tuning", tools=dummy_tools, queries=sample_tuning_queries)
    # The file path in arguments must NOT exist
    assert not (tmp_path / "should_not_exist.txt").exists()
