# Tool Description Optimization Specification

## 1. Purpose & Research Objective
The goal of the optimizer is to measure and improve AI agent tool-selection accuracy by refining **ONLY tool descriptions** while keeping the underlying model (`qwen2.5:3b`), tool names, and parameter schemas completely fixed.

The optimization process operates strictly on the **tuning split (35 queries)**. Held-out test queries (15 queries) are completely isolated and never accessed by the optimizer during generation, validation, or selection.

---

## 2. Optimization Loop

The core refinement process follows a strict iterative loop:

```
ROUND 0 (Baseline anchor loaded from results/evaluation_tuning_20261024_124416.json)
    ↓
Identify tuning mistakes (misclassified queries, expected tools, predicted tools)
    ↓
Send mistakes + current descriptions to local Ollama optimizer LLM (temperature=0.0)
    ↓
Generate candidate descriptions
    ↓
Validate candidate descriptions against strict guardrails (length, copying, immutability)
    ↓
If validation fails:
    REJECT candidate (record rejection reason, best state unchanged, increment non-improvements)
Else:
    Evaluate candidate descriptions on tuning set (split="tuning")
    Compare candidate tuning accuracy with current best accuracy:
    If candidate accuracy STRICTLY improves (candidate_acc > best_acc):
        ACCEPT candidate (candidate becomes current best, reset non-improvements)
    Else:
        REJECT candidate (best state unchanged, increment non-improvements)
    ↓
Check stopping conditions (100% accuracy, 2 consecutive non-improvements, or 8 rounds)
    ↓
Repeat until stopping condition met
```

---

## 3. What Can and Cannot Change

### Permitted Modifications
- **`tool.description` ONLY**: The semantic text guiding the model on tool capabilities, trigger conditions, and exclusion boundaries.

### Strictly Immutable Components
Tool Definition Immutability: Tool names, parameters, parameter types, required fields, schemas, and tool count are locked. Only tool descriptions may be modified.

Specifically immutable:
- Tool names (`FIXED_TOOL_NAMES`: 10 canonical tools)
- Tool count (must remain exactly 10)
- Tool order
- Parameter names, types, and descriptions
- Required parameter lists
- LLM model (`qwen2.5:3b`)
- Inference temperature (`0.0`)
- Dataset queries, labels, and partition splits
- Evaluator scoring logic and majority vote resolution

---

## 4. Optimizer Prompt Strategy

The optimizer LLM receives:
1. Current tool definitions and current descriptions.
2. Observed tuning mistakes from the current round (query ID, user query text, expected tool, and predicted tool).
3. Explicit behavioral guidelines:
   - State what the tool does.
   - Explain when it should be selected.
   - Explain when it should NOT be selected to prevent known confusions.
   - Distinguish the tool from neighboring confused tools.
   - Strictly keep all descriptions under 40 words.
   - Do NOT copy user query text.
   - Do NOT invent capabilities.
   - Return structured JSON only.

---

## 5. Validation Guardrails

Before any candidate can be evaluated by the benchmark engine, it must pass strict automated validation:

1. **JSON Schema Integrity**: Must parse as a valid JSON object containing all 10 canonical tool keys under `"descriptions"`.
2. **No Extra / Missing Tools**: Exactly 10 tools corresponding to `FIXED_TOOL_NAMES`.
3. **Non-Empty Text**: No description may be empty or whitespace-only.
4. **Length Budget**: Every description must be strictly fewer than 40 words (`< 40 words`). Any description with $\ge 40$ words is rejected.
5. **Query-Copying Guardrail & Known Limitations**:
   - **Exact 4-gram copying is strictly rejected**: Candidate descriptions are compared against all tuning query texts. Any continuous sequence of 4 or more words (4-grams) copied from tuning queries triggers immediate rejection.
   - **Semantic paraphrasing limitation**: Lexical n-gram matching deterministically detects verbatim phrase copying. However, semantic paraphrases that convey similar meaning using entirely different words are not guaranteed to be detected without introducing a secondary LLM judge, which would introduce nondeterminism and latency. This is an acknowledged and documented limitation of the deterministic guardrail. Prompt steering ("Do not copy or paraphrase the specific user queries") serves as the primary semantic constraint.
6. **Schema Immutability**: Candidate tools are compared against current tools to ensure tool names, parameter schemas, types, and required fields are byte-for-byte identical.
7. **No Silent Repairs**: If any validation rule fails, the candidate is rejected with an explicit rejection reason recorded in the round artifact.

---

## 6. Acceptance & Stopping Rules

### Acceptance Rule: Strict Improvement
$$\text{Candidate is accepted if and only if } \text{Accuracy}_{\text{candidate}} > \text{Accuracy}_{\text{current best}}$$
- A candidate with equal accuracy (e.g., $80.00\% \to 80.00\%$) is **REJECTED**.
- A candidate with lower accuracy is **REJECTED**.

### Stopping Conditions
The loop terminates as soon as any of the following triggers:
1. **100% Tuning Accuracy**: Accuracy reaches $35/35 = 100.0\%$.
2. **Two Consecutive Non-Improvements**: Two consecutive rounds fail to strictly improve accuracy (e.g., Round 1 accepted, Round 2 rejected, Round 3 rejected $\to$ STOP).
3. **Maximum Rounds Limit**: Reaching the maximum limit of 8 optimization rounds.

---

## 7. Cache Behavior & Identity Isolation

- Every set of candidate descriptions produces a distinct SHA-256 **Tool Definition Hash** via `compute_tools_hash()`.
- The evaluation cache key incorporates:
  $$\text{Cache Key} = \text{SHA-256}(\text{model} : \text{tool\_definition\_hash} : \text{query\_id} : \text{run\_index} : \text{query\_text\_hash})$$
- Because the tool definition hash changes whenever descriptions change, candidate evaluations never collide with or overwrite baseline cache entries.
- Original baseline cache entries remain intact on disk.

---

## 8. Round Artifacts & Persistence

All optimization records are saved sequentially under `results/optimization/`:
- `round_00.json`: Baseline anchor record (initialized from verified Phase 4 baseline).
- `round_01.json`, `round_02.json`, ...: Detailed per-round records containing:
  - `round_number`
  - `best_accuracy_before`
  - `candidate_accuracy`
  - `accuracy_delta`
  - `accepted` (boolean)
  - `rejection_reason` (if rejected)
  - `current_descriptions`
  - `candidate_descriptions`
  - `mistakes_input`
  - `candidate_tool_definition_hash`
  - `description_diffs`
- `summary.json`: Comprehensive run summary detailing initial accuracy, final best accuracy, rounds executed, accepted rounds, consecutive non-improvements, and termination reason.

---

## 9. Tuning vs. Held-Out Separation

- **Tuning Set (35 queries)**: Used exclusively for mistake analysis, prompt construction, candidate validation, and candidate evaluation.
- **Held-Out Set (15 queries)**: Strictly isolated. The optimizer contains explicit checks that reject any input containing non-tuning or held-out queries.
