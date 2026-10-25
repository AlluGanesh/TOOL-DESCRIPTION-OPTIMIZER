"""Optimizer service implementing iterative LLM-based tool description optimization."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from backend.app.core.config import DATA_QUERIES_FILE, OPTIMIZATION_DIR, RESULTS_DIR
from backend.app.core.constants import (
    FIXED_TOOL_NAMES,
    MAX_CONSECUTIVE_NON_IMPROVEMENTS,
    MAX_DESCRIPTION_WORD_COUNT,
    MAX_OPTIMIZATION_ROUNDS,
)
from backend.app.core.exceptions import AppBaseException, OptimizerError
from backend.app.core.logging import logger
from backend.app.models.evaluation_models import EvaluationMistake
from backend.app.models.optimization_models import (
    CandidateDescriptions,
    DescriptionDiff,
    OptimizationRoundRecord,
    OptimizationSummary,
    ValidationResult,
)
from backend.app.models.query_models import EvaluationQuery
from backend.app.models.tool_models import ToolDefinition
from backend.app.services.dataset_service import load_queries
from backend.app.services.evaluator_service import EvaluatorService, evaluator_service
from backend.app.services.ollama_service import OllamaService, ollama_service
from backend.app.services.tool_service import load_canonical_tools
from backend.app.utils.hashing import compute_dataset_hash, compute_tools_hash

OPTIMIZER_SYSTEM_PROMPT = """You are optimizing tool descriptions for an AI tool-selection benchmark.

You may change ONLY the descriptions.

Do not change tool names, parameters, schemas, or capabilities.

Use the observed tuning mistakes to make descriptions more discriminative.

For each description:
- state what the tool does
- state when it should be used
- state when it should not be used if this prevents a known confusion
- distinguish it from the specific neighboring tool involved in an observed mistake

Do not copy or paraphrase the specific user queries.
Do not invent capabilities.
Keep every description under 40 words.

Return JSON only."""

def detect_query_copying(
    descriptions: Dict[str, str],
    queries: List[str],
    min_ngram_size: int = 4,
) -> Optional[str]:
    """Detects verbatim query copying by searching for continuous sequences of words
    from tuning queries appearing in any candidate description.
    """
    for q in queries:
        q_words = re.findall(r"\b\w+\b", q.lower())
        if len(q_words) < min_ngram_size:
            continue
        for i in range(len(q_words) - min_ngram_size + 1):
            ngram_words = q_words[i : i + min_ngram_size]
            ngram_str = " ".join(ngram_words)

            for tool_name, desc in descriptions.items():
                desc_words = re.findall(r"\b\w+\b", desc.lower())
                for j in range(len(desc_words) - min_ngram_size + 1):
                    desc_ngram = " ".join(desc_words[j : j + min_ngram_size])
                    if ngram_str == desc_ngram:
                        return (
                            f"Tool '{tool_name}' description contains copied text from "
                            f"tuning query: '{ngram_str}'"
                        )
    return None

def validate_tool_immutability(
    current_tools: List[ToolDefinition],
    candidate_tools: List[ToolDefinition],
) -> ValidationResult:
    """Verifies that candidate tools differ ONLY in descriptions compared to current tools.
    
    Ensures identical tool names, counts, parameter schemas, and property types.
    """
    if len(current_tools) != len(candidate_tools):
        return ValidationResult(
            is_valid=False,
            rejection_reason=(
                f"Tool count changed: expected {len(current_tools)}, found {len(candidate_tools)}"
            ),
        )

    for curr, cand in zip(current_tools, candidate_tools):
        if curr.name != cand.name:
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Tool name changed or reordered: expected '{curr.name}', found '{cand.name}'",
            )
        if curr.parameters.type != cand.parameters.type:
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Tool '{curr.name}' parameter schema type changed: '{curr.parameters.type}' -> '{cand.parameters.type}'",
            )
        if curr.parameters.required != cand.parameters.required:
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Tool '{curr.name}' required parameters changed: {curr.parameters.required} -> {cand.parameters.required}",
            )
        if curr.parameters.properties != cand.parameters.properties:
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Tool '{curr.name}' parameter properties changed.",
            )

    return ValidationResult(is_valid=True)

class OptimizerService:
    """Coordinates iterative description optimization with strict guardrails."""

    def __init__(
        self,
        ollama_svc: Optional[OllamaService] = None,
        evaluator_svc: Optional[EvaluatorService] = None,
        optimization_dir: Optional[Union[str, Path]] = None,
        queries_file: Optional[Union[str, Path]] = None,
    ):
        self.ollama_svc = ollama_svc or ollama_service
        self.evaluator_svc = evaluator_svc or evaluator_service
        self.optimization_dir = Path(optimization_dir) if optimization_dir else OPTIMIZATION_DIR
        self.optimization_dir.mkdir(parents=True, exist_ok=True)
        self.queries_file = Path(queries_file) if queries_file else DATA_QUERIES_FILE

    def validate_mistakes_input(
        self,
        mistakes: List[Any],
        tuning_queries: Optional[List[EvaluationQuery]] = None,
    ) -> None:
        """Enforces research integrity: confirms all mistakes originate from tuning partition."""
        if tuning_queries is None:
            all_queries = load_queries(self.queries_file)
            tuning_queries = [q for q in all_queries if q.split == "tuning"]

        tuning_ids = {q.id for q in tuning_queries}

        for m in mistakes:
            qid = getattr(m, "query_id", None) or (m.get("query_id") if isinstance(m, dict) else None)
            split = getattr(m, "split", None) or (m.get("split") if isinstance(m, dict) else None)

            if split and split != "tuning":
                raise OptimizerError(
                    f"Research integrity violation: Mistake {qid} belongs to split '{split}'. "
                    f"Optimizer strictly accepts ONLY 'tuning' mistakes."
                )
            if qid and qid not in tuning_ids:
                raise OptimizerError(
                    f"Research integrity violation: Mistake query ID '{qid}' is not in the tuning dataset."
                )

    def construct_prompt(
        self,
        current_tools: List[ToolDefinition],
        mistakes: List[Any],
    ) -> List[Dict[str, str]]:
        """Constructs the prompt containing current tools and observed tuning mistakes."""
        # 1. Format current tools
        tools_text_parts = []
        for t in current_tools:
            params = list(t.parameters.properties.keys())
            tools_text_parts.append(
                f"- Tool: {t.name}\n"
                f"  Parameters: {', '.join(params)}\n"
                f"  Current Description: \"{t.description}\""
            )
        tools_section = "\n\n".join(tools_text_parts)

        # 2. Format tuning mistakes
        mistakes_parts = []
        for idx, m in enumerate(mistakes, start=1):
            qid = getattr(m, "query_id", None) or m.get("query_id", f"M{idx}")
            expected = getattr(m, "expected_tool", None) or m.get("expected_tool", "")
            predicted = getattr(m, "predicted_tool", None) or m.get("predicted_tool", "")
            query_text = getattr(m, "query", None) or m.get("query", "")

            mistakes_parts.append(
                f"[{idx}] Query ID: {qid}\n"
                f"    User Query: \"{query_text}\"\n"
                f"    Expected Tool: {expected}\n"
                f"    Model Predicted: {predicted}"
            )
        mistakes_section = "\n\n".join(mistakes_parts) if mistakes_parts else "No mistakes observed."

        # 3. Format expected output schema template
        example_schema = {
            "descriptions": {name: f"Refined description for {name}." for name in FIXED_TOOL_NAMES}
        }
        schema_str = json.dumps(example_schema, indent=2)

        user_content = (
            f"Here are the 10 fixed tools and their current descriptions:\n\n"
            f"{tools_section}\n\n"
            f"Here are the {len(mistakes)} observed mistakes on the tuning set:\n\n"
            f"{mistakes_section}\n\n"
            f"Generate refined descriptions for ALL 10 tools to resolve these routing confusions.\n"
            f"Requirements:\n"
            f"1. Every description must be under {MAX_DESCRIPTION_WORD_COUNT} words.\n"
            f"2. Clearly state what the tool does, when to use it, and when NOT to use it.\n"
            f"3. Do not copy or quote the user query text directly.\n"
            f"4. Do not invent capabilities.\n"
            f"5. Provide descriptions for all 10 tools in this exact JSON structure:\n\n"
            f"{schema_str}"
        )

        return [
            {"role": "system", "content": OPTIMIZER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def call_optimizer_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Invokes local Ollama with temperature=0.0 and parses JSON output."""
        return self.ollama_svc.generate_json(messages=messages, temperature=0.0)

    def validate_candidate_descriptions(
        self,
        candidate_dict: Any,
        current_tools: List[ToolDefinition],
        tuning_queries: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Strict validation / guardrails check for candidate descriptions."""
        # 1. Output type check
        if not isinstance(candidate_dict, dict):
            return ValidationResult(
                is_valid=False,
                rejection_reason="Optimizer output is not a JSON object.",
            )

        if "descriptions" not in candidate_dict:
            return ValidationResult(
                is_valid=False,
                rejection_reason="Optimizer output missing top-level 'descriptions' key.",
            )

        descriptions = candidate_dict["descriptions"]
        if not isinstance(descriptions, dict):
            return ValidationResult(
                is_valid=False,
                rejection_reason="'descriptions' field is not a key-value dictionary.",
            )

        # 2. Tool name coverage check
        expected_names = set(FIXED_TOOL_NAMES)
        actual_names = set(descriptions.keys())

        missing = expected_names - actual_names
        if missing:
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Candidate descriptions missing required tools: {sorted(missing)}",
            )

        extra = actual_names - expected_names
        if extra:
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Candidate descriptions contain unknown tools: {sorted(extra)}",
            )

        if len(descriptions) != len(FIXED_TOOL_NAMES):
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Expected {len(FIXED_TOOL_NAMES)} tool descriptions, found {len(descriptions)}",
            )

        # 3. Content length & emptiness checks
        for name in FIXED_TOOL_NAMES:
            desc = descriptions[name]
            if not isinstance(desc, str):
                return ValidationResult(
                    is_valid=False,
                    rejection_reason=f"Description for tool '{name}' is not a string.",
                )

            stripped = desc.strip()
            if not stripped:
                return ValidationResult(
                    is_valid=False,
                    rejection_reason=f"Description for tool '{name}' is empty.",
                )

            words = stripped.split()
            if len(words) >= MAX_DESCRIPTION_WORD_COUNT:
                return ValidationResult(
                    is_valid=False,
                    rejection_reason=(
                        f"Description for tool '{name}' is {len(words)} words; "
                        f"must be strictly fewer than {MAX_DESCRIPTION_WORD_COUNT} words."
                    ),
                )

        # 4. Query-copying guardrail
        if tuning_queries is None:
            all_queries = load_queries(self.queries_file)
            tuning_queries = [q.query for q in all_queries if q.split == "tuning"]

        copy_violation = detect_query_copying(descriptions, tuning_queries, min_ngram_size=4)
        if copy_violation:
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Query-copying guardrail violation: {copy_violation}",
            )

        # 5. Immutability validation against current tools
        candidate_tools = self.build_candidate_tools(current_tools, descriptions)
        immutability_res = validate_tool_immutability(current_tools, candidate_tools)
        if not immutability_res.is_valid:
            return immutability_res

        return ValidationResult(is_valid=True)

    def build_candidate_tools(
        self,
        current_tools: List[ToolDefinition],
        candidate_descriptions: Dict[str, str],
    ) -> List[ToolDefinition]:
        """Constructs a cloned list of ToolDefinition objects with updated descriptions only."""
        updated: List[ToolDefinition] = []
        for tool in current_tools:
            new_desc = candidate_descriptions.get(tool.name, tool.description)
            cloned = tool.model_copy(update={"description": new_desc}, deep=True)
            updated.append(cloned)
        return updated

    def compute_description_diffs(
        self,
        current_tools: List[ToolDefinition],
        candidate_descriptions: Dict[str, str],
    ) -> List[DescriptionDiff]:
        """Computes before-and-after description comparisons for all tools."""
        diffs: List[DescriptionDiff] = []
        for tool in current_tools:
            after_desc = candidate_descriptions.get(tool.name, tool.description)
            diffs.append(
                DescriptionDiff(
                    tool_name=tool.name,
                    before_description=tool.description,
                    after_description=after_desc,
                    changed=(tool.description != after_desc),
                )
            )
        return diffs

    def initialize_round_zero(
        self,
        baseline_path: Optional[Union[str, Path]] = None,
    ) -> Tuple[float, List[Any], List[ToolDefinition], OptimizationRoundRecord]:
        """Loads and verifies Round 0 baseline from existing verified evaluation artifact."""
        target_path: Path
        if baseline_path:
            target_path = Path(baseline_path)
        else:
            latest = RESULTS_DIR / "evaluation_tuning_latest.json"
            if latest.exists():
                target_path = latest
            else:
                target_path = Path("results/evaluation_tuning_20261024_124416.json")

        if not target_path.exists():
            raise OptimizerError(
                f"Baseline evaluation artifact not found at {target_path}. "
                f"Run baseline evaluation before starting optimization."
            )

        with open(target_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)

        baseline_acc = float(baseline_data["accuracy"])
        baseline_mistakes = baseline_data.get("mistakes", [])
        canonical_tools = load_canonical_tools()

        current_desc_map = {t.name: t.description for t in canonical_tools}
        dataset_hash = baseline_data["metadata"]["dataset_hash"]
        tool_hash = baseline_data["metadata"]["tool_definition_hash"]
        model_name = baseline_data["metadata"]["model"]

        # Ensure mistakes originate strictly from tuning
        self.validate_mistakes_input(baseline_mistakes)

        # Build Round 0 baseline anchor record
        round_0_record = OptimizationRoundRecord(
            round_number=0,
            best_accuracy_before=baseline_acc,
            candidate_accuracy=baseline_acc,
            accuracy_delta=0.0,
            accepted=True,
            rejection_reason=None,
            current_descriptions=current_desc_map,
            candidate_descriptions=current_desc_map,
            mistakes_input=[
                m if isinstance(m, dict) else m.model_dump() for m in baseline_mistakes
            ],
            model=model_name,
            candidate_tool_definition_hash=tool_hash,
            dataset_hash=dataset_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
            description_diffs=[],
        )

        round_0_file = self.optimization_dir / "round_00.json"
        if not round_0_file.exists():
            with open(round_0_file, "w", encoding="utf-8") as f:
                json.dump(round_0_record.model_dump(), f, indent=2, ensure_ascii=False)

        return baseline_acc, baseline_mistakes, canonical_tools, round_0_record

    def run_optimization_round(
        self,
        round_num: int,
        best_accuracy_before: float,
        current_tools: List[ToolDefinition],
        current_mistakes: List[Any],
        runs_per_query: int = 1,
        force_refresh: bool = False,
    ) -> Tuple[bool, float, List[ToolDefinition], List[Any], OptimizationRoundRecord]:
        """Executes one optimization cycle: prompt -> LLM -> validate -> evaluate -> accept/reject."""
        current_desc_map = {t.name: t.description for t in current_tools}
        all_queries = load_queries(self.queries_file)
        tuning_queries = [q for q in all_queries if q.split == "tuning"]
        dataset_hash = compute_dataset_hash(tuning_queries)
        tuning_query_texts = [q.query for q in tuning_queries]

        # 1. Enforce research integrity on mistakes input
        self.validate_mistakes_input(current_mistakes, tuning_queries)

        mistakes_payload = [
            m if isinstance(m, dict) else m.model_dump() for m in current_mistakes
        ]

        logger.info(
            "Starting Optimization Round %d with %d tuning mistakes",
            round_num,
            len(current_mistakes),
        )

        # 2. Build prompt and invoke optimizer LLM
        messages = self.construct_prompt(current_tools, current_mistakes)
        try:
            candidate_dict = self.call_optimizer_llm(messages)
        except Exception as exc:
            rejection_reason = f"Optimizer LLM call failed or produced invalid JSON: {exc}"
            logger.warning("Round %d rejected at generation: %s", round_num, rejection_reason)
            record = OptimizationRoundRecord(
                round_number=round_num,
                best_accuracy_before=best_accuracy_before,
                candidate_accuracy=None,
                accuracy_delta=None,
                accepted=False,
                rejection_reason=rejection_reason,
                current_descriptions=current_desc_map,
                candidate_descriptions=None,
                mistakes_input=mistakes_payload,
                model=self.ollama_svc.model,
                candidate_tool_definition_hash=None,
                dataset_hash=dataset_hash,
                timestamp=datetime.now(timezone.utc).isoformat(),
                description_diffs=[],
            )
            self._save_round_record(record, round_num)
            return False, best_accuracy_before, current_tools, current_mistakes, record

        # 3. Guardrail validation
        validation_res = self.validate_candidate_descriptions(
            candidate_dict=candidate_dict,
            current_tools=current_tools,
            tuning_queries=tuning_query_texts,
        )

        candidate_descriptions = candidate_dict.get("descriptions", {})
        diffs = self.compute_description_diffs(current_tools, candidate_descriptions)

        if not validation_res.is_valid:
            logger.warning(
                "Round %d candidate rejected at validation: %s",
                round_num,
                validation_res.rejection_reason,
            )
            record = OptimizationRoundRecord(
                round_number=round_num,
                best_accuracy_before=best_accuracy_before,
                candidate_accuracy=None,
                accuracy_delta=None,
                accepted=False,
                rejection_reason=validation_res.rejection_reason,
                current_descriptions=current_desc_map,
                candidate_descriptions=candidate_descriptions,
                mistakes_input=mistakes_payload,
                model=self.ollama_svc.model,
                candidate_tool_definition_hash=None,
                dataset_hash=dataset_hash,
                timestamp=datetime.now(timezone.utc).isoformat(),
                description_diffs=diffs,
            )
            self._save_round_record(record, round_num)
            return False, best_accuracy_before, current_tools, current_mistakes, record

        # 4. Candidate tools construction & evaluation on tuning split ONLY
        candidate_tools = self.build_candidate_tools(current_tools, candidate_descriptions)
        cand_tool_hash = compute_tools_hash(candidate_tools)

        eval_result = self.evaluator_svc.evaluate(
            split="tuning",
            tools=candidate_tools,
            runs_per_query=runs_per_query,
            force_refresh=force_refresh,
        )

        candidate_acc = eval_result.accuracy
        acc_delta = round(candidate_acc - best_accuracy_before, 4)

        # 5. Strict improvement acceptance criterion
        if candidate_acc > best_accuracy_before:
            accepted = True
            rejection_reason = None
            next_best_acc = candidate_acc
            next_best_tools = candidate_tools
            next_best_mistakes = eval_result.mistakes
            logger.info(
                "Round %d ACCEPTED: accuracy improved from %.2f%% to %.2f%% (+%.2f%%)",
                round_num,
                best_accuracy_before * 100,
                candidate_acc * 100,
                acc_delta * 100,
            )
        else:
            accepted = False
            rejection_reason = (
                f"Accuracy did not strictly improve: candidate={candidate_acc * 100:.2f}% "
                f"<= best={best_accuracy_before * 100:.2f}%"
            )
            next_best_acc = best_accuracy_before
            next_best_tools = current_tools
            next_best_mistakes = current_mistakes
            logger.info(
                "Round %d REJECTED: candidate accuracy %.2f%% did not strictly improve over %.2f%%",
                round_num,
                candidate_acc * 100,
                best_accuracy_before * 100,
            )

        record = OptimizationRoundRecord(
            round_number=round_num,
            best_accuracy_before=best_accuracy_before,
            candidate_accuracy=candidate_acc,
            accuracy_delta=acc_delta,
            accepted=accepted,
            rejection_reason=rejection_reason,
            current_descriptions=current_desc_map,
            candidate_descriptions=candidate_descriptions,
            mistakes_input=mistakes_payload,
            model=self.ollama_svc.model,
            candidate_tool_definition_hash=cand_tool_hash,
            dataset_hash=dataset_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
            description_diffs=diffs,
        )
        self._save_round_record(record, round_num)
        return accepted, next_best_acc, next_best_tools, next_best_mistakes, record

    def run_optimization_loop(
        self,
        max_rounds: int = MAX_OPTIMIZATION_ROUNDS,
        runs_per_query: int = 1,
        force_refresh: bool = False,
        baseline_file: Optional[Union[str, Path]] = None,
    ) -> OptimizationSummary:
        """Executes the full multi-round optimization loop with stopping conditions."""
        run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_id = f"opt_{run_timestamp}"

        # Initialize Round 0 baseline
        initial_acc, best_mistakes, best_tools, round_0_rec = self.initialize_round_zero(
            baseline_path=baseline_file
        )
        best_acc = initial_acc
        best_round = 0
        consecutive_non_improvements = 0
        rounds_history: List[OptimizationRoundRecord] = [round_0_rec]
        stop_reason = "max_rounds_reached"

        print("=" * 60)
        print("TOOL DESCRIPTION OPTIMIZATION")
        print("=" * 60)
        print(f"Round 0 (Baseline)")
        print(f"Tuning accuracy: {best_acc * 100:.2f}% (Mistakes: {len(best_mistakes)})")
        print(f"Tool Definition Hash: {compute_tools_hash(best_tools)[:16]}...")
        print("-" * 60)

        for round_idx in range(1, max_rounds + 1):
            if best_acc >= 1.0:
                stop_reason = "reached_100_percent"
                print("\n100% tuning accuracy achieved. Stopping optimization.")
                break

            if consecutive_non_improvements >= MAX_CONSECUTIVE_NON_IMPROVEMENTS:
                stop_reason = "consecutive_non_improvements"
                print(
                    f"\n{MAX_CONSECUTIVE_NON_IMPROVEMENTS} consecutive non-improving rounds reached. Stopping."
                )
                break

            print(f"\nRound {round_idx}")
            print(f"Mistakes supplied to optimizer: {len(best_mistakes)}")
            print("Generating candidate descriptions...")

            accepted, next_best_acc, next_best_tools, next_best_mistakes, record = (
                self.run_optimization_round(
                    round_num=round_idx,
                    best_accuracy_before=best_acc,
                    current_tools=best_tools,
                    current_mistakes=best_mistakes,
                    runs_per_query=runs_per_query,
                    force_refresh=force_refresh,
                )
            )

            rounds_history.append(record)

            if accepted:
                print(
                    f"Candidate evaluated: {record.candidate_accuracy * 100:.2f}% | "
                    f"Result: ACCEPTED (+{record.accuracy_delta * 100:.2f}%)"
                )
                best_acc = next_best_acc
                best_tools = next_best_tools
                best_mistakes = next_best_mistakes
                best_round = round_idx
                consecutive_non_improvements = 0
            else:
                cand_acc_str = (
                    f"{record.candidate_accuracy * 100:.2f}%"
                    if record.candidate_accuracy is not None
                    else "N/A"
                )
                print(
                    f"Candidate evaluated: {cand_acc_str} | Result: REJECTED "
                    f"({record.rejection_reason})"
                )
                consecutive_non_improvements += 1

        # Compile final summary
        summary = OptimizationSummary(
            run_id=run_id,
            model=self.ollama_svc.model,
            initial_accuracy=initial_acc,
            final_accuracy=best_acc,
            accuracy_improvement=round(best_acc - initial_acc, 4),
            total_rounds=len(rounds_history) - 1,
            accepted_rounds=sum(1 for r in rounds_history[1:] if r.accepted),
            best_round=best_round,
            consecutive_non_improvements=consecutive_non_improvements,
            stop_reason=stop_reason,
            best_tool_definition_hash=compute_tools_hash(best_tools),
            dataset_hash=round_0_rec.dataset_hash,
            best_descriptions={t.name: t.description for t in best_tools},
            rounds=rounds_history,
        )

        self._save_summary(summary)

        print("\n" + "=" * 60)
        print("OPTIMIZATION SUMMARY")
        print("=" * 60)
        print(f"Run ID:                       {summary.run_id}")
        print(f"Initial Accuracy:             {summary.initial_accuracy * 100:.2f}%")
        print(f"Final Best Accuracy:          {summary.final_accuracy * 100:.2f}%")
        print(f"Accuracy Delta:               +{summary.accuracy_improvement * 100:.2f}%")
        print(f"Best Round:                   Round {summary.best_round}")
        print(f"Total Rounds Executed:        {summary.total_rounds}")
        print(f"Accepted Rounds:              {summary.accepted_rounds}")
        print(f"Consecutive Non-Improvements: {summary.consecutive_non_improvements}")
        print(f"Stop Reason:                  {summary.stop_reason}")
        print("=" * 60)

        return summary

    def _save_round_record(self, record: OptimizationRoundRecord, round_num: int) -> Path:
        """Persists individual round record under results/optimization/round_{round_num:02d}.json."""
        output_file = self.optimization_dir / f"round_{round_num:02d}.json"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(record.model_dump(), f, indent=2, ensure_ascii=False)
            logger.info("Saved optimization round %d to %s", round_num, output_file)
        except Exception as exc:
            logger.error("Failed to save round %d: %s", round_num, exc)
        return output_file

    def _save_summary(self, summary: OptimizationSummary) -> Path:
        """Persists summary JSON to results/optimization/summary.json."""
        summary_file = self.optimization_dir / "summary.json"
        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary.model_dump(), f, indent=2, ensure_ascii=False)
            logger.info("Saved optimization summary to %s", summary_file)
        except Exception as exc:
            logger.error("Failed to save optimization summary: %s", exc)
        return summary_file

# Default global optimizer service instance
optimizer_service = OptimizerService()
