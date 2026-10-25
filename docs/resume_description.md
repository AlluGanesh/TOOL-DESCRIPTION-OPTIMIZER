# Resume & Portfolio Project Descriptions: Tool Description Optimizer

This document provides concise, technically accurate bullet points and narrative summaries suitable for resumes, portfolios, LinkedIn project entries, and cover letters. All descriptions reflect the verified, peer-audited held-out experimental outcomes.

---

## Version 1: Standard Software / AI Engineer Resume (Concise Bullets)

**Tool Description Optimizer | Python, FastAPI, React, TypeScript, Ollama, Pytest**
- Built an LLM tool-selection evaluation and optimization framework that automatically refines natural-language tool descriptions while keeping model weights, tool schemas, and parameters strictly fixed.
- Engineered a deterministic evaluation pipeline for local models (`qwen2.5:3b`, `temp=0.0`) with content-addressed SHA-256 caching, automated retries, and macro/per-class F1 metric tracking across 11 routing classes.
- Implemented an iterative meta-prompting optimizer with strict guardrails (schema immutability, length budget, and 4-gram lexical copy prevention) that improved tuning accuracy from 80.00% to 85.71%.
- Validated generalization on an isolated 15-query held-out benchmark, improving accuracy from 73.33% to 80.00% (+6.67 pp, +9.09% relative) with zero regressions among previously correct queries.
- Developed a full-stack research dashboard (FastAPI + React 18 / TypeScript / Vite) featuring interactive 11×11 confusion matrix heatmaps, class F1 deltas, query transition inspectors, and before/after diff tables.

---

## Version 2: Machine Learning Systems / Agentic AI Focus (Detailed Technical Bullets)

**Tool Description Optimization & Generalization Benchmark | Python, FastAPI, React, Ollama**
- **Research Problem**: Addressed routing misclassifications in local agentic function calling by isolating tool description semantics as an independent variable while locking schemas, tool names, and inference parameters.
- **Controlled Benchmarking**: Designed a frozen 50-query benchmark across 10 canonical tools plus a null class (`none`), enforcing strict 35-tuning / 15-held-out stratification and cryptographic SHA-256 dataset provenance.
- **Optimization Engine**: Formulated an iterative prompt-optimization loop analyzing observed routing mistakes; enforced 4-gram lexical copy detection and byte-level schema immutability to prevent dataset memorization.
- **Empirical Generalization**: Achieved +6.67 percentage points (+9.09% relative) gain on unseen held-out queries (73.33% → 80.00%), reducing routing error rate by 25.0% and increasing `read_file` F1 from 0.00 to 1.00 with 0 regressions.
- **Architecture & Reliability**: Built a decoupled FastAPI backend with 94 automated unit/integration tests and an interactive React/TypeScript visualization dashboard displaying real-time health, contingency matrices, and optimization trajectories.

---

## Version 3: Short Project Narrative (Portfolio / Cover Letter / LinkedIn)

> **Tool Description Optimizer: Empirical Generalization in Agentic Function Calling**
>
> In agentic AI systems, function calling failures are frequently blamed on model capacity or schema complexity, but the natural-language phrasing of tool descriptions is often an overlooked bottleneck. I developed an empirical research platform to test whether optimizing only tool descriptions improves native tool routing without altering model weights, function names, or parameter schemas.
>
> Using a local 3B model (`qwen2.5:3b`, `temp=0.0`) and a frozen 50-query benchmark, the system executed iterative refinement on a 35-query tuning set, increasing accuracy from 80.00% to 85.71%. To verify out-of-sample generalization, the candidate was evaluated against an isolated 15-query held-out test set, where accuracy improved from 73.33% (11/15) to 80.00% (12/15) with zero regressions among previously correct queries. The project includes a decoupled FastAPI engine, 94 automated tests, and a modern React/TypeScript research dashboard.

---

## Documented Future Work (Non-Claimed Extensions)

The following areas represent planned technical investigations and are explicitly documented as future research:
1. **Benchmark Scale**: Expanding dataset from 50 queries to 500+ diverse, multi-turn, and noisy conversational prompts.
2. **Cross-Model Evaluation**: Testing whether descriptions optimized on a 3B model transfer effectively to alternative architectures (e.g., Llama-3, Mistral-7B, Claude-3.5-Sonnet, GPT-4o).
3. **Stochastic Temperature Analysis**: Running multi-pass bootstrap sampling across non-zero temperatures ($T \in [0.2, 0.7]$) to quantify variance confidence intervals.
4. **Semantic Paraphrase Detection**: Upgrading the 4-gram lexical guardrail with embedding cosine similarity checks to detect semantic query copying with disjoint vocabulary.
5. **Human vs. LLM Comparison**: Conducting side-by-side benchmarking comparing human-engineered descriptions against LLM-optimized candidates.
6. **Cost & Latency Trade-Off Analysis**: Measuring prompt token expansion overhead versus downstream tool-calling retry reduction.
