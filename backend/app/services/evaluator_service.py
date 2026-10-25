"""Evaluator service for deterministic, cached, and reliable tool-selection evaluation."""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Union

from backend.app.core.config import RESULTS_DIR
from backend.app.core.constants import (
    ALL_LABELS,
    HELD_OUT_QUERY_COUNT,
    TUNING_QUERY_COUNT,
)
from backend.app.core.exceptions import AppBaseException, EvaluatorError
from backend.app.core.logging import logger
from backend.app.models.evaluation_models import (
    EvaluationMetadata,
    EvaluationMistake,
    EvaluationQueryResult,
    EvaluationResult,
    PerRunPrediction,
)
from backend.app.models.query_models import EvaluationQuery
from backend.app.models.tool_models import ToolDefinition
from backend.app.services.cache_service import CacheService, cache_service
from backend.app.services.dataset_service import load_queries
from backend.app.services.ollama_service import OllamaService, ollama_service
from backend.app.services.tool_service import load_canonical_tools
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

def resolve_majority_vote(
    predictions: List[str],
    label_order: List[str] = ALL_LABELS,
) -> str:
    """Resolves multiple run predictions using majority vote with deterministic tie-breaking.
    
    Tie-Breaking Rule:
    If multiple tools tie with the highest frequency, the tool that appears earliest in
    label_order (the canonical fixed label sequence) is deterministically selected.
    """
    if not predictions:
        return "none"
    if len(predictions) == 1:
        return predictions[0]

    counts = Counter(predictions)
    max_count = max(counts.values())
    top_candidates = [item for item, cnt in counts.items() if cnt == max_count]

    if len(top_candidates) == 1:
        return top_candidates[0]

    # Deterministic tie-breaker: Lowest index in canonical label_order
    top_candidates.sort(
        key=lambda item: label_order.index(item) if item in label_order else 999
    )
    return top_candidates[0]

def execute_with_retry(
    fn: Callable[[], Any],
    max_retries: int = 3,
    delay_seconds: float = 0.5,
    backoff_factor: float = 1.5,
) -> Any:
    """Executes a callable with exponential backoff on transient errors.
    
    CRITICAL: Does NOT convert errors to 'none'. Raises the failure if all retries are exhausted.
    """
    current_delay = delay_seconds
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Inference attempt %d/%d failed: %s. Retrying in %.2fs...",
                attempt,
                max_retries,
                exc,
                current_delay,
            )
            if attempt < max_retries:
                time.sleep(current_delay)
                current_delay *= backoff_factor

    logger.error("All %d inference attempts failed.", max_retries)
    if isinstance(last_error, AppBaseException):
        raise last_error
    raise EvaluatorError(f"Inference execution failed after {max_retries} attempts: {last_error}")

class EvaluatorService:
    """Core evaluation engine measuring native tool-selection behavior."""

    def __init__(
        self,
        ollama_svc: Optional[OllamaService] = None,
        cache_svc: Optional[CacheService] = None,
        results_dir: Optional[Union[str, Path]] = None,
    ):
        self.ollama_svc = ollama_svc or ollama_service
        self.cache_svc = cache_svc or cache_service
        self.results_dir = Path(results_dir) if results_dir else RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def evaluate(
        self,
        split: str = "tuning",
        runs_per_query: int = 1,
        force_refresh: bool = False,
        tools: Optional[List[ToolDefinition]] = None,
        queries: Optional[List[EvaluationQuery]] = None,
    ) -> EvaluationResult:
        """Executes tool-selection evaluation on the requested partition.
        
        Args:
            split: 'tuning' (35 queries) or 'held-out' (15 queries).
            runs_per_query: Number of passes per query for majority voting.
            force_refresh: If True, bypasses disk cache and calls model directly.
            tools: Optional custom tools. If None, loads canonical tools/tools.json.
            queries: Optional queries. If None, loads data/queries.json.
            
        Returns:
            EvaluationResult containing metadata, accuracy, per-tool metrics,
            confusion matrix, mistakes, and per-query predictions.
        """
        # 1. Validate split
        norm_split = split.replace("_", "-")
        if norm_split not in ("tuning", "held-out"):
            raise EvaluatorError(
                f"Invalid split '{split}'. Evaluator strictly supports 'tuning' or 'held-out'."
            )
        if runs_per_query < 1:
            raise EvaluatorError(
                f"runs_per_query must be at least 1, received: {runs_per_query}"
            )

        # 2. Load and hash canonical tools
        tools_list = tools if tools is not None else load_canonical_tools()
        tools_hash = compute_tools_hash(tools_list)

        # 3. Load and filter dataset
        all_queries = queries if queries is not None else load_queries()
        split_queries = [q for q in all_queries if q.split == norm_split]

        # 4. Strict split count assertions
        expected_count = TUNING_QUERY_COUNT if norm_split == "tuning" else HELD_OUT_QUERY_COUNT
        if len(split_queries) != expected_count:
            raise EvaluatorError(
                f"Split '{split}' expected {expected_count} queries, found {len(split_queries)}"
            )

        dataset_hash = compute_dataset_hash(split_queries)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_id = f"eval_{norm_split}_{timestamp_str}"

        query_results: List[EvaluationQueryResult] = []
        mistakes: List[EvaluationMistake] = []
        expected_labels: List[str] = []
        final_predictions: List[str] = []
        total_queries = len(split_queries)

        print(f"\nEvaluating {total_queries} queries in split '{split}' (runs_per_query={runs_per_query})...", flush=True)

        # 5. Evaluate each query
        for idx, q in enumerate(split_queries, start=1):
            query_start = time.perf_counter()
            predictions_by_run: List[str] = []
            run_details: List[PerRunPrediction] = []

            for run_idx in range(runs_per_query):
                cache_key = compute_evaluation_cache_key(
                    model=self.ollama_svc.model,
                    tool_definition_hash=tools_hash,
                    query_id=q.id,
                    query_text=q.query,
                    run_index=run_idx,
                )

                if not force_refresh and self.cache_svc.has(cache_key):
                    cached_data = self.cache_svc.get(cache_key)
                    if cached_data is not None:
                        tool_called = cached_data.get("tool_called", False)
                        pred_tool = cached_data.get("tool_name") if tool_called else "none"
                        if not pred_tool:
                            pred_tool = "none"

                        prediction_record = PerRunPrediction(
                            run_index=run_idx,
                            predicted_tool=pred_tool,
                            tool_called=tool_called,
                            arguments=cached_data.get("arguments"),
                            duration_ms=cached_data.get("duration_ms"),
                            cache_hit=True,
                            raw_response=cached_data.get("raw_response"),
                        )
                        run_details.append(prediction_record)
                        predictions_by_run.append(pred_tool)
                        continue

                # Cache miss or force_refresh: Invoke Ollama with retries
                def _do_inference():
                    return self.ollama_svc.select_tool(q.query, tools=tools_list)

                inference_result = execute_with_retry(_do_inference)

                tool_called = inference_result.tool_called
                pred_tool = inference_result.tool_name if tool_called else "none"
                if not pred_tool:
                    pred_tool = "none"

                # Persist to disk cache
                cache_payload = {
                    "tool_called": tool_called,
                    "tool_name": inference_result.tool_name,
                    "arguments": inference_result.arguments,
                    "raw_response": inference_result.raw_response,
                    "duration_ms": inference_result.duration_ms,
                    "model": inference_result.model,
                }
                self.cache_svc.set(cache_key, cache_payload)

                prediction_record = PerRunPrediction(
                    run_index=run_idx,
                    predicted_tool=pred_tool,
                    tool_called=tool_called,
                    arguments=inference_result.arguments,
                    duration_ms=inference_result.duration_ms,
                    cache_hit=False,
                    raw_response=inference_result.raw_response,
                )
                run_details.append(prediction_record)
                predictions_by_run.append(pred_tool)

            # Resolve final prediction across runs
            final_pred = resolve_majority_vote(predictions_by_run, ALL_LABELS)
            is_correct = (final_pred == q.correct_tool)
            query_elapsed = time.perf_counter() - query_start

            print(
                f"[{idx}/{total_queries}] {q.id} completed in {query_elapsed:.1f}s | "
                f"predicted={final_pred} | correct={str(is_correct).lower()}",
                flush=True,
            )

            query_result = EvaluationQueryResult(
                query_id=q.id,
                query=q.query,
                expected_tool=q.correct_tool,
                split=q.split,
                difficulty=q.difficulty,
                predictions_by_run=predictions_by_run,
                final_prediction=final_pred,
                correct=is_correct,
                run_details=run_details,
            )
            query_results.append(query_result)
            expected_labels.append(q.correct_tool)
            final_predictions.append(final_pred)

            if not is_correct:
                mistakes.append(
                    EvaluationMistake(
                        query_id=q.id,
                        query=q.query,
                        expected_tool=q.correct_tool,
                        predicted_tool=final_pred,
                        split=q.split,
                        difficulty=q.difficulty,
                        predictions_by_run=predictions_by_run,
                        notes=q.notes,
                    )
                )

        # 6. Compute metrics
        total_queries = len(split_queries)
        correct_count = sum(1 for r in query_results if r.correct)
        accuracy = calculate_accuracy(correct_count, total_queries)
        per_tool = calculate_per_tool_metrics(expected_labels, final_predictions, ALL_LABELS)
        confusion_mat = build_confusion_matrix(expected_labels, final_predictions, ALL_LABELS)

        metadata = EvaluationMetadata(
            run_id=run_id,
            model=self.ollama_svc.model,
            split=norm_split,
            runs_per_query=runs_per_query,
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_queries=total_queries,
            tool_definition_hash=tools_hash,
            dataset_hash=dataset_hash,
        )

        result = EvaluationResult(
            metadata=metadata,
            total_queries=total_queries,
            correct_count=correct_count,
            accuracy=accuracy,
            per_tool_metrics=per_tool,
            confusion_matrix=confusion_mat,
            mistakes=mistakes,
            queries=query_results,
        )

        # 7. Persist evaluation output JSON
        self._save_results(result, norm_split, timestamp_str)
        return result

    def _save_results(
        self,
        result: EvaluationResult,
        split: str,
        timestamp: str,
    ) -> Path:
        """Persists evaluation results to results/ directory."""
        output_file = self.results_dir / f"evaluation_{split}_{timestamp}.json"
        latest_file = self.results_dir / f"evaluation_{split}_latest.json"

        data = result.model_dump()
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            with open(latest_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Evaluation results written to %s", output_file)
        except Exception as exc:
            logger.error("Failed to save evaluation results: %s", exc)

        return output_file

    @staticmethod
    def format_terminal_summary(result: EvaluationResult) -> str:
        """Generates a structured human-readable terminal report."""
        meta = result.metadata
        lines = [
            "=" * 70,
            f"EVALUATION REPORT: {meta.run_id}",
            "=" * 70,
            f"Model:                {meta.model}",
            f"Split:                {meta.split} ({result.total_queries} queries)",
            f"Runs Per Query:       {meta.runs_per_query}",
            f"Tool Definition Hash: {meta.tool_definition_hash[:16]}...",
            f"Dataset Hash:         {meta.dataset_hash[:16]}...",
            "-" * 70,
            f"ACCURACY:             {result.correct_count} / {result.total_queries} "
            f"({result.accuracy * 100:.2f}%)",
            "-" * 70,
            f"{'Tool':<24} {'TP':<4} {'FP':<4} {'FN':<4} {'Precision':<10} {'Recall':<10} {'F1':<10}",
            "-" * 70,
        ]

        for tool_name, metrics in result.per_tool_metrics.items():
            lines.append(
                f"{tool_name:<24} {metrics.true_positives:<4} {metrics.false_positives:<4} "
                f"{metrics.false_negatives:<4} {metrics.precision:<10.2f} "
                f"{metrics.recall:<10.2f} {metrics.f1_score:<10.2f}"
            )

        lines.extend([
            "-" * 70,
            f"MISTAKES RECORDED: {len(result.mistakes)}",
        ])

        if result.mistakes:
            lines.append("-" * 70)
            for m in result.mistakes:
                lines.append(
                    f"[{m.query_id}] Expected: {m.expected_tool:<15} Predicted: {m.predicted_tool:<15}"
                )
                lines.append(f"  Query: \"{m.query}\"")
                if m.notes:
                    lines.append(f"  Notes: {m.notes}")

        lines.append("=" * 70)
        return "\n".join(lines)

# Default global evaluator service instance
evaluator_service = EvaluatorService()
