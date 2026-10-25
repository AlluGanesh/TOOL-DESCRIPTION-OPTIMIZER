import React from 'react';

export const LimitationsCard: React.FC = () => {
  const limitations = [
    {
      title: 'Small Held-Out Sample Size',
      desc: 'The held-out test partition contains exactly 15 queries. While each of the 11 classes is represented and the gain is measurable (+6.67 pp), evaluating 15 queries demonstrates generalization within this benchmark but does not prove universal performance across unconstrained distributions.',
    },
    {
      title: 'Single Model Tested',
      desc: 'All experiments used qwen2.5:3b. Model-specific inductive biases, tokenization characteristics, and prompt sensitivities mean these specific descriptions may perform differently on larger or alternatively architected models (e.g., Llama-3, Mistral, Claude, GPT-4o).',
    },
    {
      title: 'Deterministic Single-Pass Inference',
      desc: 'Evaluation employed temperature 0.0 and runs=1. While deterministic greedy decoding guarantees exact run-to-run reproducibility, it does not characterize stochastic sampling variance across non-zero temperatures.',
    },
    {
      title: 'Deterministic Lexical Guardrail Limitation',
      desc: "The optimizer's query-copying guardrail detects exact 4-gram lexical overlaps. As documented in the optimizer design, lexical n-gram matching does not detect semantic paraphrasing where identical intent is expressed with completely disjoint vocabulary.",
    },
    {
      title: 'Description-Only Optimization Scope',
      desc: 'The experimental protocol intentionally held schemas, parameter names, parameter types, required lists, and model prompts constant. Conclusions apply exclusively to the isolated impact of natural-language tool descriptions under fixed schema conditions.',
    },
    {
      title: 'Synthetic Operational Domain',
      desc: 'The benchmark contains 50 synthetic operational queries. A larger, multi-turn, multi-domain benchmark with noisy or conversational inputs would provide a more rigorous test of agent robustness in production.',
    },
  ];

  return (
    <div className="card" id="limitations">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">Threats to Validity & Limitations</h2>
          <p className="card-subtitle">
            Methodological boundaries, sample constraints, and experimental controls
          </p>
        </div>
        <span className="badge badge-warning">SCIENTIFIC RIGOR</span>
      </div>

      <div className="limitations-grid">
        {limitations.map((lim, index) => (
          <div key={index} className="limitation-item">
            <div className="limitation-icon">⚠️</div>
            <div className="limitation-text">
              <div className="limitation-title">{lim.title}</div>
              <div>{lim.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
