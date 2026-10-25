"""Unit tests for tool description optimizer, validation guardrails, and optimization loop."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.app.core.constants import FIXED_TOOL_NAMES, MAX_OPTIMIZATION_ROUNDS
from backend.app.core.exceptions import OptimizerError
from backend.app.models.evaluation_models import (
    EvaluationMetadata,
    EvaluationMistake,
    EvaluationQueryResult,
    EvaluationResult,
    PerToolMetrics,
)
from backend.app.models.optimization_models import CandidateDescriptions, OptimizationRoundRecord
from backend.app.models.tool_models import ToolDefinition, ToolParameterSchema
from backend.app.services.evaluator_service import EvaluatorService
from backend.app.services.ollama_service import OllamaService
from backend.app.services.optimizer_service import (
    OptimizerService,
    detect_query_copying,
    validate_tool_immutability,
)
from backend.app.services.tool_service import load_canonical_tools
from backend.app.utils.hashing import compute_evaluation_cache_key, compute_tools_hash

@pytest.fixture
def canonical_tools():
    return load_canonical_tools()

@pytest.fixture
def valid_candidate_descriptions():
    return {
        "search_web": "Searches the live public internet for current facts and news.",
        "search_docs": "Searches internal company documentation, procedural guides, and manuals.",
        "read_file": "Reads file contents from a specific file path provided by the user.",
        "write_file": "Writes or overwrites text data to a specific file path.",
        "send_email": "Dispatches an email message to a specified recipient with subject and body.",
        "create_calendar_event": "Schedules a calendar event with a concrete start and end time.",
        "set_reminder": "Sets a notification reminder for a task or future moment in time.",
        "get_weather": "Fetches meteorological weather forecasts for a specific city name.",
        "calculator": "Evaluates numerical mathematical expressions and calculations.",
        "translate_text": "Translates written text from one natural language into another language.",
    }

@pytest.fixture
def optimizer(tmp_path):
    mock_ollama = MagicMock(spec=OllamaService)
    mock_ollama.model = "qwen2.5:3b"
    mock_evaluator = MagicMock(spec=EvaluatorService)
    opt_dir = tmp_path / "results" / "optimization"
    return OptimizerService(
        ollama_svc=mock_ollama,
        evaluator_svc=mock_evaluator,
        optimization_dir=opt_dir,
    )

# 1. Valid optimizer JSON parses
def test_valid_optimizer_json_parses(optimizer, canonical_tools, valid_candidate_descriptions):
    candidate_dict = {"descriptions": valid_candidate_descriptions}
    res = optimizer.validate_candidate_descriptions(candidate_dict, canonical_tools, tuning_queries=[])
    assert res.is_valid is True
    assert res.rejection_reason is None

# 2. Missing tool rejected
def test_missing_tool_rejected(optimizer, canonical_tools, valid_candidate_descriptions):
    bad_descriptions = dict(valid_candidate_descriptions)
    del bad_descriptions["calculator"]
    res = optimizer.validate_candidate_descriptions({"descriptions": bad_descriptions}, canonical_tools, tuning_queries=[])
    assert res.is_valid is False
    assert "missing" in res.rejection_reason.lower()
    assert "calculator" in res.rejection_reason

# 3. Unknown tool rejected
def test_unknown_tool_rejected(optimizer, canonical_tools, valid_candidate_descriptions):
    bad_descriptions = dict(valid_candidate_descriptions)
    bad_descriptions["execute_bash"] = "Runs bash command."
    res = optimizer.validate_candidate_descriptions({"descriptions": bad_descriptions}, canonical_tools, tuning_queries=[])
    assert res.is_valid is False
    assert "unknown" in res.rejection_reason.lower()
    assert "execute_bash" in res.rejection_reason

# 4. Changed tool name rejected
def test_changed_tool_name_rejected(canonical_tools):
    cand_tools = [t.model_copy(deep=True) for t in canonical_tools]
    cand_tools[0].name = "renamed_tool"
    res = validate_tool_immutability(canonical_tools, cand_tools)
    assert res.is_valid is False
    assert "name changed" in res.rejection_reason.lower()

# 5. Changed parameter schema rejected
def test_changed_parameter_schema_rejected(canonical_tools):
    cand_tools = [t.model_copy(deep=True) for t in canonical_tools]
    cand_tools[0].parameters.type = "array"
    res = validate_tool_immutability(canonical_tools, cand_tools)
    assert res.is_valid is False
    assert "parameter schema" in res.rejection_reason.lower()

# 6. Changed required parameter rejected
def test_changed_required_parameter_rejected(canonical_tools):
    cand_tools = [t.model_copy(deep=True) for t in canonical_tools]
    cand_tools[0].parameters.required = ["extra_param"]
    res = validate_tool_immutability(canonical_tools, cand_tools)
    assert res.is_valid is False
    assert "required parameters changed" in res.rejection_reason.lower()

# 7. Changed tool count rejected
def test_changed_tool_count_rejected(canonical_tools):
    cand_tools = canonical_tools[:9]
    res = validate_tool_immutability(canonical_tools, cand_tools)
    assert res.is_valid is False
    assert "count changed" in res.rejection_reason.lower()

# 8. Empty description rejected
def test_empty_description_rejected(optimizer, canonical_tools, valid_candidate_descriptions):
    bad_descriptions = dict(valid_candidate_descriptions)
    bad_descriptions["calculator"] = "   "
    res = optimizer.validate_candidate_descriptions({"descriptions": bad_descriptions}, canonical_tools, tuning_queries=[])
    assert res.is_valid is False
    assert "empty" in res.rejection_reason.lower()

# 9. Description >=40 words rejected
def test_description_ge_40_words_rejected(optimizer, canonical_tools, valid_candidate_descriptions):
    bad_descriptions = dict(valid_candidate_descriptions)
    bad_descriptions["calculator"] = " ".join(["word"] * 40)
    res = optimizer.validate_candidate_descriptions({"descriptions": bad_descriptions}, canonical_tools, tuning_queries=[])
    assert res.is_valid is False
    assert "fewer than 40 words" in res.rejection_reason.lower()

# 10. Query-copying guardrail rejects obvious copied text
def test_query_copying_guardrail_rejects_copied_text(optimizer, canonical_tools, valid_candidate_descriptions):
    bad_descriptions = dict(valid_candidate_descriptions)
    # Copied 4-gram from Q006: "internal architecture documentation referencing"
    bad_descriptions["search_docs"] = "Searches internal architecture documentation referencing vector systems."
    sample_tuning_queries = [
        "Find all internal architecture documentation referencing vector search.",
        "Lookup the employee handbook section covering parental leave.",
    ]
    res = optimizer.validate_candidate_descriptions({"descriptions": bad_descriptions}, canonical_tools, tuning_queries=sample_tuning_queries)
    assert res.is_valid is False
    assert "query-copying guardrail" in res.rejection_reason.lower()

def test_query_copying_guardrail_paraphrase_limitation_documented(optimizer, canonical_tools, valid_candidate_descriptions):
    """Verifies documented limitation: semantic paraphrase without 4-gram overlap passes lexical filter."""
    paraphrase_descriptions = dict(valid_candidate_descriptions)
    # Reworded concept without sharing any 4-gram with the tuning query
    paraphrase_descriptions["search_docs"] = "Locates procedural manuals and engineering guidelines inside local repositories."
    sample_tuning_queries = [
        "Find all internal architecture documentation referencing vector search.",
        "Lookup the employee handbook section covering parental leave.",
    ]
    res = optimizer.validate_candidate_descriptions({"descriptions": paraphrase_descriptions}, canonical_tools, tuning_queries=sample_tuning_queries)
    assert res.is_valid is True

# 11. Valid description-only changes accepted
def test_valid_description_only_changes_accepted(optimizer, canonical_tools, valid_candidate_descriptions):
    candidate_tools = optimizer.build_candidate_tools(canonical_tools, valid_candidate_descriptions)
    immutability_res = validate_tool_immutability(canonical_tools, candidate_tools)
    assert immutability_res.is_valid is True
    # Verify description actually changed
    assert candidate_tools[0].description == valid_candidate_descriptions[candidate_tools[0].name]
    # Verify parameters remained unchanged
    assert candidate_tools[0].parameters == canonical_tools[0].parameters

# 12. Candidate tool hash changes when descriptions change
def test_candidate_tool_hash_changes_when_descriptions_change(optimizer, canonical_tools, valid_candidate_descriptions):
    cand_tools = optimizer.build_candidate_tools(canonical_tools, valid_candidate_descriptions)
    orig_hash = compute_tools_hash(canonical_tools)
    cand_hash = compute_tools_hash(cand_tools)
    assert orig_hash != cand_hash
    assert len(cand_hash) == 64

# 13. Cache identity changes when tool descriptions change
def test_cache_identity_changes_when_tool_descriptions_change(optimizer, canonical_tools, valid_candidate_descriptions):
    cand_tools = optimizer.build_candidate_tools(canonical_tools, valid_candidate_descriptions)
    orig_tool_hash = compute_tools_hash(canonical_tools)
    cand_tool_hash = compute_tools_hash(cand_tools)

    key_orig = compute_evaluation_cache_key("qwen2.5:3b", orig_tool_hash, "Q001", "some query", 0)
    key_cand = compute_evaluation_cache_key("qwen2.5:3b", cand_tool_hash, "Q001", "some query", 0)
    assert key_orig != key_cand

# 14. Candidate evaluation uses tuning split
def test_candidate_evaluation_uses_tuning_split(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}

    mock_eval_res = MagicMock(spec=EvaluationResult)
    mock_eval_res.accuracy = 0.8571
    mock_eval_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_eval_res

    mistakes = [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}]
    optimizer.run_optimization_round(1, 0.80, canonical_tools, mistakes)

    optimizer.evaluator_svc.evaluate.assert_called_once()
    kwargs = optimizer.evaluator_svc.evaluate.call_args.kwargs
    assert kwargs["split"] == "tuning"

# 15. Held-out split is rejected/not accessible to optimizer
def test_held_out_split_rejected_by_optimizer(optimizer):
    held_out_mistakes = [
        {"query_id": "Q004", "split": "held-out", "expected_tool": "search_web", "predicted_tool": "none", "query": "Test"}
    ]
    with pytest.raises(OptimizerError) as exc_info:
        optimizer.validate_mistakes_input(held_out_mistakes)
    assert "research integrity violation" in str(exc_info.value).lower()
    assert "held-out" in str(exc_info.value).lower()

def test_held_out_query_id_rejected_even_without_split_attribute(optimizer):
    """Verifies research integrity: held-out query ID is rejected even if split key is omitted."""
    # Q004 is a held-out query in data/queries.json
    mistakes_no_split = [
        {"query_id": "Q004", "expected_tool": "search_web", "predicted_tool": "none", "query": "Test"}
    ]
    with pytest.raises(OptimizerError) as exc_info:
        optimizer.validate_mistakes_input(mistakes_no_split)
    assert "research integrity violation" in str(exc_info.value).lower()
    assert "not in the tuning dataset" in str(exc_info.value).lower()

def test_optimizer_candidate_generation_uses_configured_ollama_model(optimizer, canonical_tools):
    """Verifies that candidate generation calls OllamaService with temperature 0.0."""
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": {}}
    messages = [{"role": "user", "content": "test"}]
    optimizer.call_optimizer_llm(messages)
    optimizer.ollama_svc.generate_json.assert_called_once_with(messages=messages, temperature=0.0)


# 16. Strict improvement accepts
def test_strict_improvement_accepts(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}
    mock_res = MagicMock(spec=EvaluationResult)
    mock_res.accuracy = 0.8571
    mock_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_res

    mistakes = [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}]
    accepted, next_acc, _, _, rec = optimizer.run_optimization_round(1, 0.80, canonical_tools, mistakes)
    assert accepted is True
    assert next_acc == 0.8571
    assert rec.accepted is True

# 17. Equal accuracy rejects
def test_equal_accuracy_rejects(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}
    mock_res = MagicMock(spec=EvaluationResult)
    mock_res.accuracy = 0.8000
    mock_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_res

    mistakes = [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}]
    accepted, next_acc, _, _, rec = optimizer.run_optimization_round(1, 0.80, canonical_tools, mistakes)
    assert accepted is False
    assert next_acc == 0.8000
    assert rec.accepted is False
    assert "did not strictly improve" in rec.rejection_reason

# 18. Lower accuracy rejects
def test_lower_accuracy_rejects(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}
    mock_res = MagicMock(spec=EvaluationResult)
    mock_res.accuracy = 0.7714
    mock_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_res

    mistakes = [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}]
    accepted, next_acc, _, _, rec = optimizer.run_optimization_round(1, 0.80, canonical_tools, mistakes)
    assert accepted is False
    assert next_acc == 0.8000
    assert rec.accepted is False

# 19. Accepted candidate becomes next round's current descriptions
def test_accepted_candidate_becomes_next_round_descriptions(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}
    mock_res = MagicMock(spec=EvaluationResult)
    mock_res.accuracy = 0.8571
    mock_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_res

    mistakes = [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}]
    accepted, next_acc, next_tools, _, _ = optimizer.run_optimization_round(1, 0.80, canonical_tools, mistakes)
    assert accepted is True
    assert next_tools[0].description == valid_candidate_descriptions[next_tools[0].name]

# 20. Rejected candidate does not replace current descriptions
def test_rejected_candidate_does_not_replace_current_descriptions(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}
    mock_res = MagicMock(spec=EvaluationResult)
    mock_res.accuracy = 0.7500
    mock_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_res

    mistakes = [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}]
    accepted, next_acc, next_tools, _, _ = optimizer.run_optimization_round(1, 0.80, canonical_tools, mistakes)
    assert accepted is False
    assert next_tools[0].description == canonical_tools[0].description

# 21. Two consecutive non-improvements stop optimization
def test_two_consecutive_non_improvements_stop_optimization(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}
    # Round 1 reject, Round 2 reject -> stop
    mock_res = MagicMock(spec=EvaluationResult)
    mock_res.accuracy = 0.8000
    mock_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_res

    with patch.object(optimizer, "initialize_round_zero") as mock_init:
        mock_init.return_value = (
            0.80,
            [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}],
            canonical_tools,
            MagicMock(spec=OptimizationRoundRecord, dataset_hash="mock_data_hash"),
        )
        summary = optimizer.run_optimization_loop(max_rounds=8)
        assert summary.stop_reason == "consecutive_non_improvements"
        assert summary.total_rounds == 2
        assert summary.accepted_rounds == 0

# 22. 100% accuracy stops optimization
def test_100_percent_accuracy_stops_optimization(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}
    mock_res = MagicMock(spec=EvaluationResult)
    mock_res.accuracy = 1.0000
    mock_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_res

    with patch.object(optimizer, "initialize_round_zero") as mock_init:
        mock_init.return_value = (
            0.80,
            [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}],
            canonical_tools,
            MagicMock(spec=OptimizationRoundRecord, dataset_hash="mock_data_hash"),
        )
        summary = optimizer.run_optimization_loop(max_rounds=8)
        assert summary.stop_reason == "reached_100_percent"
        assert summary.final_accuracy == 1.0000
        assert summary.total_rounds == 1

# 23. Maximum 8 rounds enforced
def test_maximum_8_rounds_enforced(optimizer, canonical_tools, valid_candidate_descriptions):
    # Alternating accept and reject so consecutive non-improvements stays < 2
    accuracies = [0.82, 0.82, 0.84, 0.84, 0.86, 0.86, 0.88, 0.88]
    call_idx = [0]

    def mock_evaluate(*args, **kwargs):
        acc = accuracies[call_idx[0]]
        call_idx[0] += 1
        res = MagicMock(spec=EvaluationResult)
        res.accuracy = acc
        res.mistakes = [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}]
        return res

    optimizer.evaluator_svc.evaluate.side_effect = mock_evaluate
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}

    with patch.object(optimizer, "initialize_round_zero") as mock_init:
        mock_init.return_value = (
            0.80,
            [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}],
            canonical_tools,
            MagicMock(spec=OptimizationRoundRecord, dataset_hash="mock_data_hash"),
        )
        summary = optimizer.run_optimization_loop(max_rounds=8)
        assert summary.total_rounds == 8
        assert summary.stop_reason == "max_rounds_reached"

# 24. Previous round results are preserved
def test_previous_round_results_preserved(optimizer, canonical_tools, valid_candidate_descriptions):
    optimizer.ollama_svc.generate_json.return_value = {"descriptions": valid_candidate_descriptions}
    mock_res = MagicMock(spec=EvaluationResult)
    mock_res.accuracy = 0.8571
    mock_res.mistakes = []
    optimizer.evaluator_svc.evaluate.return_value = mock_res

    with patch.object(optimizer, "initialize_round_zero") as mock_init:
        mock_init.return_value = (
            0.80,
            [{"query_id": "Q006", "split": "tuning", "expected_tool": "search_docs", "predicted_tool": "none", "query": "Find docs"}],
            canonical_tools,
            MagicMock(spec=OptimizationRoundRecord, dataset_hash="mock_data_hash"),
        )
        summary = optimizer.run_optimization_loop(max_rounds=1)

    assert (optimizer.optimization_dir / "round_01.json").exists()
    assert (optimizer.optimization_dir / "summary.json").exists()

# 25. Round 0 correctly initializes from the existing verified baseline
def test_round_zero_initializes_from_verified_baseline(optimizer):
    baseline_path = Path("results/evaluation_tuning_20261024_124416.json")
    assert baseline_path.exists()

    init_acc, mistakes, tools, rec = optimizer.initialize_round_zero(baseline_path)
    assert init_acc == 0.80
    assert len(mistakes) == 7
    assert len(tools) == 10
    assert rec.round_number == 0
    assert rec.best_accuracy_before == 0.80
    assert (optimizer.optimization_dir / "round_00.json").exists()
