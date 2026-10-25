# Evaluation Methodology & Benchmark Specification

## Overview
This document specifies the experimental benchmark dataset, evaluation engine architecture, and metrics protocol for measuring tool-selection accuracy of local AI agents using `qwen2.5:3b`.

> **Status**: The evaluation engine (`EvaluatorService`), CLI, controlled tuning optimization, and held-out evaluation have been fully executed and verified across Phases 3 through 9. Baseline tuning accuracy was measured at 80.00% (28/35), optimized tuning at 85.71% (30/35), baseline held-out at 73.33% (11/15), and optimized held-out at 80.00% (12/15). All 94 automated backend tests are passing.

---

## 1. Benchmark Dataset Structure (`data/queries.json`)

The benchmark dataset consists of exactly **50 labeled queries** formatted with the following schema:
- `id` (string): Unique identifier (`Q001` to `Q050`).
- `query` (string): Natural user prompt representing a realistic operational request.
- `correct_tool` (string): The single ground-truth tool identifier from the fixed label space.
- `split` (string): Partition flag, strictly `"tuning"` (35 queries) or `"held-out"` (15 queries).
- `difficulty` (string): Routing challenge classification (`"easy"`, `"medium"`, or `"hard"`).
- `notes` (string): Rationale for ground-truth assignment and identification of near-miss confusion risks.

---

## 2. Fixed Label Space

The routing space is strictly constrained to 11 mutually exclusive categories in canonical order:
1. `search_web`: Live internet queries and public information lookup.
2. `search_docs`: Internal knowledge base, employee policies, and company documentation.
3. `read_file`: Local filesystem inspection using explicit paths or filenames.
4. `write_file`: File creation or content persistence to disk at specified locations.
5. `send_email`: Outbound communication to email addresses or recipient names.
6. `create_calendar_event`: Scheduling meetings or reserving calendar slots with specific durations.
7. `set_reminder`: Personal alerts, time-based reminders, or operational nudges.
8. `get_weather`: Meteorological conditions and forecasts for cities or locations.
9. `calculator`: Deterministic arithmetic, financial calculations, or formulas.
10. `translate_text`: Cross-language text conversion and multilingual translation.
11. `none`: Requests where no available tool is appropriate (conversational, theoretical, or creative).

---

## 3. Dataset Splits & Isolation Protocol

| Split | Count | Purpose | Optimization Visibility |
| :--- | :---: | :--- | :---: |
| **`tuning`** | **35** | Training and validation set used during description refinement iterations. | Visible to optimizer |
| **`held-out`** | **15** | Generalization test set used solely for final post-optimization assessment. | **Strictly Isolated** |
| **Total** | **50** | Complete frozen benchmark. | — |

### Stratification & Class Balance
- **Tuning Set (35 queries)**: Contains 3 to 4 examples of each of the 10 tools, plus 3 `"none"` queries.
- **Held-Out Set (15 queries)**: Stratified so that **every single class** (all 10 tools + `"none"`) is represented with 1 to 2 queries.
- **Difficulty Balance**: Both splits contain a balanced mixture of easy, medium, and hard queries to avoid difficulty skew.

### Held-Out Isolation Guardrail
The optimizer is programmatically restricted to the `tuning` split. The `held-out` partition must never be exposed to the meta-prompting optimizer or used in iterative candidate selection loops.

---

## 4. Evaluator Engine Architecture (`EvaluatorService`)

The evaluator measures **tool routing decisions** directly from Ollama using native function calling:
1. **Tool Definitions**: Loads canonical tools from `tools/tools.json` and converts them through `tool_to_ollama_format()`.
2. **Deterministic Invocation**: Sends the user query together with the native tool schemas to Ollama at `temperature = 0.0`.
3. **Response Inspection**:
   - If the model generates a tool call, the tool name is captured as the prediction.
   - If the model does not generate a tool call, the prediction is recorded as `"none"`.
4. **No Tool Execution**: The evaluator **never** executes the predicted tool; it strictly evaluates tool routing decisions.
5. **Comparison & Mistake Recording**: Compares the predicted tool against `correct_tool`. If incorrect, logs an `EvaluationMistake` with query context and rationale.

---

## 5. Multiple Runs & Majority Voting

The evaluator supports multi-pass evaluation via `runs_per_query` (default = 1):
- For each query, `runs_per_query` independent inference calls are executed.
- Predictions across runs are aggregated into a frequency map.
- The final prediction is resolved via **majority vote**.
- **Deterministic Tie-Breaking Rule**:
  If multiple tools tie with the highest frequency, the candidate that appears earliest in the canonical `ALL_LABELS` sequence (`search_web`, `search_docs`, ..., `none`) is chosen. Randomness is never used.

---

## 6. Persistent Disk Caching (`cache/`)

To ensure experiment reproducibility and avoid redundant inference latency:
- Every inference response is cached to disk under `cache/{cache_key}.json`.
- The cache key is a deterministic SHA-256 digest computed from:
  `compute_evaluation_cache_key(model, tool_definition_hash, query_id, query_text, run_index)`
- If a query is re-evaluated with identical tools, model, query ID, and run index, the evaluator serves the result from the local cache (`cache_hit: true`).
- Supports an explicit `--no-cache` / `force_refresh` flag to bypass the cache when needed.

---

## 7. Transient Failure Retries

- Ollama calls are wrapped with `execute_with_retry(max_retries=3, delay_seconds=0.5, backoff_factor=1.5)`.
- If an operational or network failure persists after 3 retries, an exception (`OllamaConnectionError` / `EvaluatorError`) is raised.
- **Failure Isolation Guardrail**: A model or connection failure is **never** converted into a `"none"` prediction. A service failure is treated strictly as an evaluation error.

---

## 8. Metrics & Confusion Matrix

### Aggregate Accuracy
$$\text{Accuracy} = \frac{\text{Correct Predictions}}{\text{Total Evaluated Queries}}$$

### Per-Tool Metrics
For each label $L \in \text{ALL\_LABELS}$:
- **Precision**: $\frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$
- **Recall**: $\frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$
- **F1 Score**: $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$

### Confusion Matrix
- Format: Deterministic $11 \times 11$ matrix (Rows = Expected Tool, Columns = Predicted Tool).
- Complete label coverage: `none` is fully included as the 11th category.
- Zero-count cells are explicitly preserved.

---

## 9. Provenance & Hashes

Each evaluation output contains deterministic SHA-256 provenance hashes:
- `tool_definition_hash`: SHA-256 digest of canonically serialized and sorted tool definitions.
- `dataset_hash`: SHA-256 digest of the evaluated query partition sorted by query ID.

---

## 10. CLI Usage

The evaluator is independently runnable from the command line without requiring the frontend:

```bash
# Evaluate the tuning split (35 queries, 1 run per query)
py -m backend.app.evaluate --split tuning --runs 1

# Evaluate with 3 runs per query using majority voting
py -m backend.app.evaluate --split tuning --runs 3

# Force fresh inference calls (bypass cache)
py -m backend.app.evaluate --split tuning --runs 1 --no-cache

# Save results to a custom file path
py -m backend.app.evaluate --split tuning --output results/my_evaluation.json
```

Output records are automatically persisted in `results/`:
- `results/evaluation_{split}_{timestamp}.json` (timestamped archive)
- `results/evaluation_{split}_latest.json` (latest run pointer)

---

## 11. Review & Limitations
- **Current Review Status**: The 50 benchmark queries and entire backend test suite have been verified through 94 passing automated tests.
- **Human Review Limitation**: In the current single-developer environment, an independent second-person blind review of queries has not yet occurred. This is documented to maintain full research integrity.
