# System Architecture Specification

## 1. System Topology & Decoupling

`tool-description-optimizer` is architected as a modular, decoupled research platform comprising three distinct operational tiers:

```
┌────────────────────────────────────────────────────────┐
│             Frontend Visualization Layer               │
│          (React 18 + TypeScript + Vite 5.4)            │
│                 http://localhost:5173/                 │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP REST (Proxy)
                           ▼
┌────────────────────────────────────────────────────────┐
│             Backend Research Engine (API)              │
│               (FastAPI + Python 3.10+)                 │
│                 http://127.0.0.1:8000                  │
│                                                        │
│  ├── API Routers (/api/tools, /api/evaluation, etc.)   │
│  ├── EvaluatorService (Deterministic Native Scoring)   │
│  ├── OptimizerService (Meta-Prompt Refinement Engine)  │
│  ├── ReportService (Artifact & Visual Compilation)     │
│  ├── DatasetService (Validation & Split Isolation)     │
│  └── CacheService (SHA-256 Content-Addressed Storage)  │
└──────────────────────────┬─────────────────────────────┘
                           │ Local Socket / HTTP
                           ▼
┌────────────────────────────────────────────────────────┐
│              Local Inference Runtime                   │
│          (Ollama Daemon • http://localhost:11434)      │
│              Model: qwen2.5:3b • Temp: 0.0             │
└────────────────────────────────────────────────────────┘
```

### Architectural Boundaries
1. **Frontend-to-Backend Decoupling**: The frontend communicates strictly with the backend FastAPI REST API via `/api/*` and `/health`, or loads verified historical artifacts (`/data/final_results.json`). The frontend is strictly prohibited from communicating directly with the Ollama daemon.
2. **Deterministic Inference**: Inference is performed locally using Ollama (`qwen2.5:3b`) at greedy sampling temperature (`temperature = 0.0`), ensuring $0 cloud API costs, zero external data leakage, and exact run-to-run reproducibility.
3. **Headless Execution**: The backend research engine is fully executable from CLI commands (`evaluate.py`, `optimize.py`, `pytest`) without requiring the frontend server to be active.

---

## 2. Backend Service Decomposition

The core research engine in `backend/app/` is partitioned into decoupled service layers:

### A. `ollama_service.py` (`OllamaService`)
- Manages low-level socket communication with the local Ollama daemon (`http://localhost:11434`).
- Converts canonical tools into Ollama function-calling schemas via `tools_to_ollama_format()`.
- Executes native tool calling using `client.chat(model=..., messages=..., tools=..., options={"temperature": 0.0})`.
- Inspects response payloads for native `tool_calls`. If tool calls are present, extracts the function name; otherwise, deterministically assigns `"none"`. Does **not** perform text-scraping heuristics on unformatted natural language.

### B. `dataset_service.py` (`DatasetService`)
- Loads and strictly validates the labeled benchmark (`data/queries.json`, $N=50$).
- Enforces 15 structural and distribution invariants:
  - Total queries: exactly 50
  - Tuning partition: exactly 35 queries
  - Held-out partition: exactly 15 queries
  - Label space: strictly 11 categories (10 canonical tools + `"none"`)
  - Exactly 5 `"none"` ground-truth queries
  - Complete representation: all 11 classes present in both tuning and held-out partitions
  - Zero tool-name leakage into query text
  - Difficulty distribution balance (easy, medium, hard)
- **Held-Out Protection**: Rejects any optimization routine that attempts to access or load held-out queries.

### C. `evaluator_service.py` (`EvaluatorService`)
- Executes deterministic scoring of tool routing accuracy against benchmark queries.
- Manages multi-pass execution (`runs_per_query`) and resolves ties deterministically using the canonical sequence order in `ALL_LABELS`.
- Computes macro and per-class classification metrics: Precision, Recall, and F1 scores.
- Generates exhaustive $11 \times 11$ confusion matrices including the `"none"` category.
- Logs structured `EvaluationMistake` objects capturing query ID, input text, expected tool, and predicted tool.

### D. `optimizer_service.py` (`OptimizerService`)
- Orchestrates iterative description optimization over the tuning dataset ($N=35$).
- Operates strictly on observed tuning mistakes from the current best round.
- Formulates structured meta-prompts instructing the local LLM to refine descriptions by clarifying capability scope, operational triggers, and negative boundaries against confused neighbors.
- Enforces strict validation guardrails:
  - Schema immutability: parameter names, types, required fields, and tool counts are locked.
  - Length budget: strictly $< 40$ words per description.
  - Query-copying guardrail: detects and rejects continuous 4-word lexical sequences copied from tuning queries.
- Applies strict improvement acceptance: candidates are accepted if and only if tuning accuracy strictly exceeds the current anchor ($\text{Acc}_{\text{cand}} > \text{Acc}_{\text{best}}$).
- Stops automatically on 2 consecutive non-improvements or reaching maximum round budget (3 rounds).

### E. `cache_service.py` (`CacheService`)
- Content-addressed disk cache under `cache/{cache_key}.json`.
- Cache key format:
  $$\text{Cache Key} = \text{SHA-256}(\text{model} : \text{tool\_definition\_hash} : \text{query\_id} : \text{run\_index} : \text{query\_text\_hash})$$
- Ensures that changing a tool description changes the cache key, guaranteeing zero cross-condition cache contamination between baseline and candidate rounds.

### F. `report_service.py` (`ReportService`)
- Aggregates output logs from tuning optimization and controlled held-out evaluations.
- Computes transition metrics (remained correct, became correct, regressed, remained incorrect).
- Emits structured [final_results.json](file:///c:/Users/allug/OneDrive/Desktop/TOOL-DESCRIPTION-OPTIMIZER/results/final_results.json) and compiles 16 high-resolution visualization charts (8 PNG, 8 SVG) in [results/charts/](file:///c:/Users/allug/OneDrive/Desktop/TOOL-DESCRIPTION-OPTIMIZER/results/charts).
- Generates the formal research report [final_results_report.md](file:///c:/Users/allug/OneDrive/Desktop/TOOL-DESCRIPTION-OPTIMIZER/docs/final_results_report.md).

---

## 3. Data Flow & Provenance Architecture

```
                    ┌────────────────────────┐
                    │    tools/tools.json    │
                    │   (Canonical Tools)    │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │    data/queries.json   │
                    │   (50 Labeled Queries) │
                    └─────┬────────────┬─────┘
                          │            │
            Tuning (N=35) │            │ Held-Out (N=15)
                          ▼            │
         ┌──────────────────────────┐  │ (Locked until Phase 7)
         │   Optimization Loop      │  │
         │   (Round 0 → Round 3)    │  │
         │   Accepted: Round 1      │  │
         └────────────┬─────────────┘  │
                      │                │
                      │ Best Candidate │
                      ▼                ▼
         ┌────────────────────────────────────────────────┐
         │     Controlled Held-Out Generalization Test     │
         │   Condition A (Baseline) vs Condition B (Opt)   │
         └────────────────────┬───────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────────────┐
         │       results/final_results.json (Verified)     │
         │       results/charts/*.svg & *.png             │
         └────────────────────┬───────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────────────┐
         │        Frontend Research Dashboard (UI)        │
         └────────────────────────────────────────────────┘
```

### Deterministic Integrity Hashes
Provenance is verified cryptographically via SHA-256 hashes:
- **Canonical Tools Hash**: `6a989b336d703f0eda7d36aa01d7d1458b7b72aac47dca220b4924b48358b495`
- **Candidate Round 1 Tools Hash**: `1d887828d4872e66589f8ae99d7cceccfaf616e2a2df3a8a041f34b6be0a0f0f`
- **Tuning Dataset Hash**: `10328b74aba349b092ae97bf0896b1d12fffa135a45bfd211f82f1a5e30ca13c`
- **Held-Out Dataset Hash**: `37e0997d8f69724cd130eec77b9442d56d2170b42dd608126341ddff6b126f65`

---

## 4. Frontend Component Hierarchy

The frontend dashboard located in `frontend/src/` is structured as a typed research presentation layer:

```
App.tsx
├── Header.tsx (Branding, compile timestamp, live backend heartbeat pulse)
├── Navigation.tsx (Sticky section quick-jump links)
└── Main Content Container
    ├── HeroMetricCard.tsx (Held-Out Tool-Selection Accuracy: 73.33% → 80.00%, +6.67 pp, 0 regressions)
    ├── ExperimentConfigCard.tsx (Model: qwen2.5:3b, Temp: 0.0, 50 queries, 11 classes, frozen schemas)
    ├── AccuracyComparison.tsx (Tuning: 80.00% → 85.71% vs Held-Out: 73.33% → 80.00% comparative progress bars)
    ├── HeldOutSummary.tsx (Dedicated Held-Out before/after breakdown: 11/15 → 12/15, -25.0% errors)
    ├── QueryTransitions.tsx (11 remained correct, 1 became correct [Q014], 3 remained incorrect [Q009, Q018, Q049])
    ├── PerToolMetricsTable.tsx (Class-level precision, recall, and F1 deltas highlighting read_file and none)
    ├── ConfusionMatrixHeatmap.tsx (Interactive 11×11 baseline and optimized heatmaps with hover inspection)
    ├── ToolDescriptionDiffTable.tsx (Before & after diffs: 7 modified, 3 preserved)
    ├── OptimizationJourney.tsx (Round 0 to Round 3 progression timeline with stopping condition trigger)
    ├── LimitationsCard.tsx (Small sample N=15, single model, greedy decoding, 4-gram guardrail, description scope)
    └── ScientificConclusionCard.tsx (Peer-audited, scientifically conservative conclusion)
Footer.tsx (Provenance hashes, experiment metadata, and documentation links)
```

---

## 5. Security & Operational Boundary Summary

1. **Zero External Secrets**: No cloud API keys, access tokens, passwords, or cloud credentials exist or are required.
2. **Localhost Network Isolation**: All REST and LLM endpoints operate strictly over `127.0.0.1` and `localhost`.
3. **Immutability Protection**: Experimental JSON artifacts in `results/`, benchmark data in `data/queries.json`, and canonical tools in `tools/tools.json` are frozen and protected against inadvertent runtime modification.
