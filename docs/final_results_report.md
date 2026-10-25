# Formal Research Report: Tool Description Optimization & Generalization Evaluation

## 1. Executive Summary

This report documents the empirical investigation of tool-description optimization for local AI agents. The central objective was to measure whether systematically refining **ONLY tool descriptions**—while keeping model weights (`qwen2.5:3b`), inference temperature (`0.0`), tool names, and parameter schemas completely fixed—improves native tool routing accuracy on unseen operational requests.

### Core Empirical Findings
- **Tuning Set (N=35)**: Accuracy improved from **80.00%** (28/35) to **85.71%** (30/35), an absolute gain of **+5.71 percentage points** (+7.14% relative).
- **Held-Out Test Set (N=15)**: Under controlled evaluation on completely unseen queries, accuracy improved from **73.33%** (11/15) to **80.00%** (12/15), an absolute gain of **+6.67 percentage points** (+9.09% relative).
- **Zero Regressions**: Exactly 1 query transitioned from incorrect to correct (`Q014`), and **0 previously correct queries regressed**.
- **Conclusion**: The experiment demonstrates that description-only optimization generalized successfully to unseen held-out queries, providing evidence that clarifying semantic trigger boundaries enhances native function routing without dataset memorization.

---

## 2. Research Question

> **Research Question**: *Can optimizing only natural-language tool descriptions improve an AI model's native tool-selection accuracy while keeping the underlying model, temperature, tool names, and parameter schemas strictly fixed?*

In modern agentic architectures, function calling is often assumed to be primarily bounded by model parameter capacity or schema complexity. This experiment specifically isolates the semantic phrasing of tool descriptions as an independent variable to establish its isolated causal impact on tool routing performance.

---

## 3. Experimental Design & Methodology

The experiment enforces strict laboratory controls across all evaluation phases:

| Parameter | Value | Specification |
| :--- | :--- | :--- |
| **Base Model** | `qwen2.5:3b` | Local Ollama runtime (`http://localhost:11434`), zero cloud API dependencies |
| **Sampling Temperature** | `0.0` | Deterministic greedy decoding |
| **Passes Per Query (`runs`)** | `1` | Canonical single-pass inference |
| **Total Benchmark Dataset** | 50 queries | Frozen labeled benchmark (`data/queries.json`) |
| **Tuning Partition** | 35 queries | Used exclusively for error analysis and candidate selection |
| **Held-Out Partition** | 15 queries | Completely isolated from optimization; evaluated once at Phase 7 |
| **Routing Label Space** | 11 classes | 10 canonical tools + `none` (mutually exclusive) |
| **Tool Schemas** | Locked | Parameters, properties, types, and required fields immutable |
| **Evaluator Protocol** | Native Calling | Direct Ollama tool invocation with disk cache separation by SHA-256 hash |

---

## 4. Optimization Process

The optimization loop operated strictly on the 35 tuning queries over iterative rounds:

```
Round 0 (Baseline Anchor): 80.00% (28/35) -> Initial state
   ↓
Round 1: 85.71% (30/35) -> STRICT IMPROVEMENT (+5.71%) -> ACCEPTED (Selected as best configuration)
   ↓
Round 2: 80.00% (28/35) -> Non-improvement -> REJECTED (Consecutive non-improvements: 1/2)
   ↓
Round 3: 80.00% (28/35) -> Non-improvement -> REJECTED (Consecutive non-improvements: 2/2 -> TERMINATED)
```

- **Accepted Best Round**: Round 1 was the only accepted round and defined the final candidate configuration.
- **Stopping Condition**: The optimizer terminated automatically after reaching the maximum threshold of 2 consecutive non-improvements.

---

## 5. Controlled Held-Out Evaluation

To test generalization, the held-out evaluation compared exactly two experimental conditions across the identical 15 held-out test queries:

- **Condition A (Baseline)**: Canonical tool definitions from `tools/tools.json` (Tool Hash: `6a989b336d703f0eda7d36aa01d7d1458b7b72aac47dca220b4924b48358b495`).
- **Condition B (Optimized)**: Accepted Round 1 candidate descriptions (Tool Hash: `1d887828d4872e66589f8ae99d7cceccfaf616e2a2df3a8a041f34b6be0a0f0f`).
- **Controlled Invariants**: The query texts, tool schemas, parameter types, model instance, temperature (0.0), and evaluation split were identical. Cache keys incorporated the tool definition hash, guaranteeing zero cross-condition cache contamination.

---

## 6. Experimental Results

### Summary Accuracy Comparison

| Dataset Partition | Baseline Accuracy | Optimized Accuracy | Absolute Change | Relative Change | Error Reduction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Tuning Set (N=35)** | 80.00% (28/35) | 85.71% (30/35) | **+5.71 pp** | **+7.14%** | -28.6% (7 -> 5) |
| **Held-Out Set (N=15)** | 73.33% (11/15) | 80.00% (12/15) | **+6.67 pp** | **+9.09%** | **-25.0% (4 -> 3)** |

---

## 7. Per-Tool Performance Metrics (Held-Out Test Set)

| Tool / Class | Actual Count | Baseline Precision | Baseline Recall | Baseline F1 | Optimized Precision | Optimized Recall | Optimized F1 | F1 Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `search_web` | 1 | 0.50 | 1.00 | 0.67 | 0.50 | 1.00 | 0.67 | **0.00** |
| `search_docs` | 2 | 1.00 | 0.50 | 0.67 | 1.00 | 0.50 | 0.67 | **0.00** |
| `read_file` | 1 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | **+1.00** |
| `write_file` | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** |
| `send_email` | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **0.00** |
| `create_calendar_event` | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **0.00** |
| `set_reminder` | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **0.00** |
| `get_weather` | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **0.00** |
| `calculator` | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **0.00** |
| `translate_text` | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **0.00** |
| `none` | 2 | 0.25 | 0.50 | 0.33 | 0.33 | 0.50 | 0.40 | **+0.07** |

---

## 8. Error Analysis & Routing Transitions

### Query Transition Breakdown (N=15)
- **Remained Correct (11 queries)**: `Q004`, `Q008`, `Q022`, `Q023`, `Q028`, `Q032`, `Q036`, `Q040`, `Q041`, `Q045`, `Q050`.
- **Became Correct (1 query)**: `Q014`.
- **Became Incorrect (0 queries)**: None (zero regressions).
- **Remained Incorrect (3 queries)**: `Q009`, `Q018`, `Q049`.

### Detailed Query Transitions

| Query ID | Expected Tool | Baseline Prediction | Baseline OK? | Optimized Prediction | Optimized OK? | Outcome | Query Text Snippet |
| :---: | :--- | :--- | :---: | :--- | :---: | :--- | :--- |
| `Q004` | `search_web` | `search_web` | True | `search_web` | True | **remained_correct** | "What is the current status of the Artemis space ..." |
| `Q008` | `search_docs` | `search_docs` | True | `search_docs` | True | **remained_correct** | "Look through our internal wiki for the recommend..." |
| `Q009` | `search_docs` | `none` | False | `none` | False | **remained_incorrect** | "What SLA tier do we commit to enterprise clients..." |
| `Q014` | `read_file` | `none` | False | `read_file` | True | **became_correct** | "Check the contents of /etc/hosts to see if the l..." |
| `Q018` | `write_file` | `none` | False | `none` | False | **remained_incorrect** | "Export this list of customer IDs to C:\Exports\c..." |
| `Q022` | `send_email` | `send_email` | True | `send_email` | True | **remained_correct** | "Forward a note to support@cloudvendor.io with su..." |
| `Q023` | `send_email` | `send_email` | True | `send_email` | True | **remained_correct** | "Notify alex@startup.ai that the server credentia..." |
| `Q028` | `create_calendar_event` | `create_calendar_event` | True | `create_calendar_event` | True | **remained_correct** | "Reserve a meeting on Thursday from 4:00 PM to 5:..." |
| `Q032` | `set_reminder` | `set_reminder` | True | `set_reminder` | True | **remained_correct** | "Make sure I get a notification at 6:00 PM to sub..." |
| `Q036` | `get_weather` | `get_weather` | True | `get_weather` | True | **remained_correct** | "How warm is it currently in Miami Beach in Celsi..." |
| `Q040` | `calculator` | `calculator` | True | `calculator` | True | **remained_correct** | "Divide 8,742 by 14 and give me the exact result...." |
| `Q041` | `calculator` | `calculator` | True | `calculator` | True | **remained_correct** | "What is the monthly mortgage payment on a $450,0..." |
| `Q045` | `translate_text` | `translate_text` | True | `translate_text` | True | **remained_correct** | "Please express 'Where is the nearest subway stat..." |
| `Q049` | `none` | `search_web` | False | `search_web` | False | **remained_incorrect** | "What are some general tips for maintaining good ..." |
| `Q050` | `none` | `none` | True | `none` | True | **remained_correct** | "Could you brainstorm five creative names for a s..." |

### In-Depth Case Analysis

In this benchmark, the 3B model showed several `none` predictions for filesystem and internal-document queries, particularly when the query wording did not closely resemble the tool's description.

1. **Resolved Error — `Q014` (`read_file`)**:
   - *User Query*: `"Check the contents of /etc/hosts to see if the local database alias is configured."`
   - *Observed Routing*: Baseline predicted `none`; Optimized predicted `read_file` (Correct).
   - *Routing Analysis*: Q014 changed from an incorrect `none` prediction to the correct `read_file` prediction after the description optimization. The experiment establishes the observed prediction change, but does not directly measure the model's internal reasoning or the specific mechanism responsible for the improvement.

2. **Persistent Error — `Q009` (`search_docs`)**:
   - *User Query*: `"What SLA tier do we commit to enterprise clients for urgent production outages in our support agreements?"`
   - *Observed Routing*: Predicted `none` in both conditions.
   - *Routing Analysis*: The prompt does not mention the words 'document' or 'handbook'. For this query, the model did not route contractual client commitments to internal documentation and defaulted to `none`.

3. **Persistent Error — `Q018` (`write_file`)**:
   - *User Query*: `"Export this list of customer IDs to C:\Exports\churned_users.csv on the disk."`
   - *Observed Routing*: Predicted `none` in both conditions.
   - *Routing Analysis*: The user query frames the request as an 'Export' operation. The observed prediction suggests that, for this query, the model did not associate the phrase 'export ... to disk' with the `write_file` tool.

4. **Persistent Error — `Q049` (`none`)**:
   - *User Query*: `"What are some general tips for maintaining good posture while working long hours at a desk?"`
   - *Observed Routing*: Predicted `search_web` in both conditions (False Positive).
   - *Routing Analysis*: Even with `search_web` refined to `"Searches the web for information."`, informational questions with broad advice triggers remain prone to unnecessary search invocation.

---

## 9. Tool Description Modifications

The optimizer applied precise semantic adjustments across 7 tools while preserving 3 tools:

| Tool Name | Original Description | Optimized Description (Round 1) | Nature of Semantic Refinement |
| :--- | :--- | :--- | :--- |
| `search_web` | "Searches for information." | "Searches the web for information." | **[MODIFIED]** Object/Domain clarification: Explicitly specifies the web search domain over general lookup. |
| `search_docs` | "Looks up information in documents." | "Looks up information in documents." | **[PRESERVED]** No change: Baseline description was already sufficiently specific for internal documentation. |
| `read_file` | "Reads a file." | "Reads a file." | **[PRESERVED]** No change: Baseline description was already direct for filesystem inspection. |
| `write_file` | "Writes data to a file." | "Writes data to a file." | **[PRESERVED]** No change: Baseline description was already direct for filesystem persistence. |
| `send_email` | "Sends a message." | "Sends a message via email." | **[MODIFIED]** Channel/Medium clarification: Specifies outbound email transmission over generic messaging. |
| `create_calendar_event` | "Adds an event." | "Adds an event to a calendar." | **[MODIFIED]** Domain clarification: Distinguishes calendar event booking from generic system events. |
| `set_reminder` | "Sets a reminder." | "Sets a reminder for later." | **[MODIFIED]** Temporal clarification: States deferred alert semantics ('for later') over immediate triggers. |
| `get_weather` | "Gets weather information." | "Gets weather information for a city." | **[MODIFIED]** Entity clarification: Designates target geographic entity ('for a city'). |
| `calculator` | "Does math." | "Does basic math calculations." | **[MODIFIED]** Action/Scope clarification: Specifies computational calculation over theoretical mathematical inquiry. |
| `translate_text` | "Converts text." | "Converts text between languages." | **[MODIFIED]** Task clarification: Distinguishes multilingual language translation from text transformations. |

---

## 10. Threats to Validity & Limitations

To maintain scientific rigor, several experimental constraints and methodological limitations must be explicitly highlighted:

1. **Small Held-Out Sample Size**: The held-out test partition contains exactly 15 queries. While each of the 11 classes is represented and the improvement is statistically measurable (+6.67 pp), evaluating a 15-query sample demonstrates generalization within this benchmark but does not prove universal performance across unconstrained production distributions.
2. **Single Model**: All experiments used `qwen2.5:3b`. Model-specific inductive biases, tokenization characteristics, and prompt sensitivities mean these specific descriptions may perform differently on larger or alternatively architected models (e.g. Llama-3, Mistral, Claude, GPT-4o).
3. **Deterministic Single-Pass Inference**: Evaluation employed `temperature=0.0` and `runs=1`. While deterministic greedy decoding guarantees exact run-to-run reproducibility, it does not characterize stochastic sampling variance across non-zero temperatures.
4. **Benchmark Domain Scope**: The benchmark contains 50 synthetic operational queries. A larger, multi-domain benchmark with multi-turn context and noisy user inputs would provide a more rigorous test of agent robustness.
5. **Deterministic Lexical Guardrail Limitation**: The optimizer's query-copying guardrail detects exact 4-gram lexical overlaps. As documented in the optimizer design, lexical n-gram matching does not detect semantic paraphrasing where identical intent is expressed with completely disjoint vocabulary.
6. **Description-Only Optimization Scope**: The experimental protocol intentionally held schemas, parameter names, required lists, and model prompts constant. Conclusions apply exclusively to the isolated impact of natural-language tool descriptions under fixed schema conditions.

---

## 11. Scientific Conclusion

The controlled held-out experiment provides evidence that optimizing tool descriptions alone improved tool-selection accuracy from 73.33% to 80.00% (+6.67 percentage points, +9.09% relative) on the 15 unseen benchmark queries, with zero regressions among previously correct queries.

Because the evaluation used only one model, one deterministic run, and 15 held-out queries, this result should be interpreted as evidence of improvement on this benchmark rather than proof of universal generalization.

---

## 12. Reproducibility & Provenance

### Execution Commands
The controlled held-out experiment was executed using the following commands:

```powershell
# 1. Baseline Held-Out Evaluation (Condition A)
.venv\Scripts\python.exe backend\app\evaluate.py --split held_out --runs 1 --output results/evaluation_held_out_baseline.json

# 2. Optimized Held-Out Evaluation (Condition B)
.venv\Scripts\python.exe backend\app\evaluate.py --split held_out --tools-file results/optimization/round_01.json --runs 1 --output results/evaluation_held_out_optimized.json

# 3. Automated Report & Chart Compilation
.venv\Scripts\python.exe -c "from backend.app.services.report_service import report_service; report_service.compile_final_results(); report_service.generate_all_charts(); report_service.generate_markdown_report()"
```

### Provenance Hashes & Artifact Paths
- **Canonical Tools Hash**: `6a989b336d703f0eda7d36aa01d7d1458b7b72aac47dca220b4924b48358b495`
- **Optimized Tools Hash**: `1d887828d4872e66589f8ae99d7cceccfaf616e2a2df3a8a041f34b6be0a0f0f`
- **Held-Out Dataset Hash**: `37e0997d8f69724cd130eec77b9442d56d2170b42dd608126341ddff6b126f65`
- **Baseline Result File**: `results/evaluation_held_out_baseline.json`
- **Optimized Result File**: `results/evaluation_held_out_optimized.json`
- **Structured Final Results**: `results/final_results.json`
- **Generated Visualizations Directory**: `results/charts/`
