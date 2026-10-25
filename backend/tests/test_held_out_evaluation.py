"""Unit tests for Phase 7 controlled held-out evaluation and custom tool definitions.

Covers:
- Evaluating baseline tool definitions.
- Evaluating custom optimized tool definitions.
- Ensuring tool schemas, parameters, and properties remain unchanged while only descriptions differ.
- Cache key differentiation between baseline and candidate tool hashes.
- Isolation of the held-out split.
- Strict rejection of held-out queries by the optimizer.
- Loading tools from canonical JSON and optimization round artifacts.
- Evaluator CLI --tools-file and split normalization.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.app.core.config import RESULTS_DIR, TOOLS_FILE
from backend.app.core.constants import ALL_LABELS, FIXED_TOOL_NAMES, HELD_OUT_QUERY_COUNT
from backend.app.core.exceptions import EvaluatorError, OptimizerError, ToolDefinitionError
from backend.app.evaluate import parse_args
from backend.app.models.evaluation_models import EvaluationMistake
from backend.app.models.query_models import EvaluationQuery
from backend.app.models.tool_models import ToolDefinition, ToolSelectionResult
from backend.app.services.cache_service import CacheService
from backend.app.services.dataset_service import load_queries
from backend.app.services.evaluator_service import EvaluatorService
from backend.app.services.optimizer_service import OptimizerService
from backend.app.services.tool_service import load_canonical_tools, load_tools_from_file
from backend.app.utils.hashing import compute_evaluation_cache_key, compute_tools_hash

@pytest.fixture
def baseline_tools():
    return load_canonical_tools()

@pytest.fixture
def round_01_file():
    path = RESULTS_DIR / "optimization" / "round_01.json"
    assert path.exists(), f"Expected optimization artifact at {path}"
    return path

@pytest.fixture
def optimized_tools(round_01_file):
    return load_tools_from_file(round_01_file)

def test_load_tools_from_file_formats(round_01_file, tmp_path):
    """Verify load_tools_from_file handles canonical list, round artifact dict, and invalid paths."""
    # 1. Load from canonical list
    tools_from_canon = load_tools_from_file(TOOLS_FILE)
    assert len(tools_from_canon) == 10
    assert [t.name for t in tools_from_canon] == FIXED_TOOL_NAMES

    # 2. Load from round artifact dict
    tools_from_artifact = load_tools_from_file(round_01_file)
    assert len(tools_from_artifact) == 10
    assert tools_from_artifact[0].description == "Searches the web for information."

    # 3. Nonexistent file
    with pytest.raises(ToolDefinitionError, match="not found"):
        load_tools_from_file(tmp_path / "missing.json")

    # 4. Invalid structure
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text(json.dumps({"unexpected": "structure"}), encoding="utf-8")
    with pytest.raises(ToolDefinitionError, match="Unsupported tools file format"):
        load_tools_from_file(invalid_file)

def test_tool_schemas_remain_unchanged_only_descriptions_differ(baseline_tools, optimized_tools):
    """Verify schemas, parameters, types, and properties are identical; only descriptions differ."""
    assert len(baseline_tools) == len(optimized_tools) == 10

    base_map = {t.name: t for t in baseline_tools}
    opt_map = {t.name: t for t in optimized_tools}

    assert set(base_map.keys()) == set(opt_map.keys()) == set(FIXED_TOOL_NAMES)

    descriptions_differ_count = 0
    for name in FIXED_TOOL_NAMES:
        b_tool = base_map[name]
        o_tool = opt_map[name]

        # Parameters and schema must be byte-for-byte identical
        assert b_tool.parameters.model_dump() == o_tool.parameters.model_dump(), (
            f"Schema mismatch for tool '{name}'"
        )
        assert b_tool.name == o_tool.name

        if b_tool.description != o_tool.description:
            descriptions_differ_count += 1

    # In Round 1, exactly 7 descriptions changed (search_docs, read_file, write_file remained unchanged)
    assert descriptions_differ_count > 0, "Expected at least one description to differ"

def test_cache_keys_differ_for_different_tool_definition_hashes(baseline_tools, optimized_tools):
    """Verify that identical queries produce distinct cache keys when tool descriptions differ."""
    base_hash = compute_tools_hash(baseline_tools)
    opt_hash = compute_tools_hash(optimized_tools)

    assert base_hash != opt_hash, "Baseline and optimized tool hashes must be distinct"

    query_id = "Q004"
    query_text = "What is the current status of the Artemis space mission schedule?"
    model = "qwen2.5:3b"

    key_baseline = compute_evaluation_cache_key(
        model=model,
        tool_definition_hash=base_hash,
        query_id=query_id,
        query_text=query_text,
        run_index=0,
    )
    key_optimized = compute_evaluation_cache_key(
        model=model,
        tool_definition_hash=opt_hash,
        query_id=query_id,
        query_text=query_text,
        run_index=0,
    )

    assert key_baseline != key_optimized, "Cache keys must not collide across tool definition changes"

def test_baseline_and_custom_tool_evaluation(tmp_path, baseline_tools, optimized_tools):
    """Verify EvaluatorService runs both baseline and custom optimized tool definitions."""
    all_queries = load_queries()
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

    # 1. Baseline evaluation on held-out
    res_baseline = evaluator.evaluate(
        split="held-out",
        tools=baseline_tools,
        queries=all_queries,
    )
    assert res_baseline.total_queries == HELD_OUT_QUERY_COUNT
    assert res_baseline.metadata.tool_definition_hash == compute_tools_hash(baseline_tools)
    assert res_baseline.metadata.split == "held-out"

    # 2. Optimized evaluation on held_out (supporting underscore notation)
    res_optimized = evaluator.evaluate(
        split="held_out",
        tools=optimized_tools,
        queries=all_queries,
    )
    assert res_optimized.total_queries == HELD_OUT_QUERY_COUNT
    assert res_optimized.metadata.tool_definition_hash == compute_tools_hash(optimized_tools)
    assert res_optimized.metadata.split == "held-out"
    assert res_baseline.metadata.tool_definition_hash != res_optimized.metadata.tool_definition_hash

def test_held_out_split_remains_isolated(tmp_path):
    """Verify held-out queries are disjoint from tuning queries and only 15 queries are evaluated."""
    all_queries = load_queries()
    tuning_ids = {q.id for q in all_queries if q.split == "tuning"}
    held_out_ids = {q.id for q in all_queries if q.split == "held-out"}

    assert len(tuning_ids) == 35
    assert len(held_out_ids) == 15
    assert tuning_ids.isdisjoint(held_out_ids)

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

    res = evaluator.evaluate(split="held-out", queries=all_queries)
    evaluated_ids = {q.query_id for q in res.queries}

    assert evaluated_ids == held_out_ids
    assert evaluated_ids.isdisjoint(tuning_ids)

def test_optimizer_cannot_receive_held_out_queries():
    """Verify optimizer strictly rejects mistakes originating from the held-out partition."""
    optimizer = OptimizerService()

    held_out_mistake = EvaluationMistake(
        query_id="Q004",
        query="What is the current status of the Artemis space mission schedule?",
        expected_tool="search_web",
        predicted_tool="none",
        split="held-out",
        difficulty="hard",
        predictions_by_run=["none"],
    )

    with pytest.raises(OptimizerError, match="Research integrity violation"):
        optimizer.validate_mistakes_input([held_out_mistake])

def test_evaluate_cli_tools_file_argument(monkeypatch, round_01_file):
    """Verify CLI argument parsing accepts --tools-file and --split held_out."""
    test_args = [
        "evaluate.py",
        "--split",
        "held_out",
        "--tools-file",
        str(round_01_file),
        "--runs",
        "1",
    ]
    monkeypatch.setattr("sys.argv", test_args)
    parsed = parse_args()
    assert parsed.split == "held_out"
    assert parsed.tools_file == str(round_01_file)
    assert parsed.runs == 1
