import React from 'react';

export const ExperimentWorkflowDiagram: React.FC = () => {
  const steps = [
    {
      step: '01',
      title: 'Define 10 Tools',
      desc: 'Canonical tools with locked names, parameters, and baseline descriptions.',
      phase: 'Setup',
    },
    {
      step: '02',
      title: 'Create 50 Labeled Queries',
      desc: 'Curated operational requests across 11 classes, including 5 none queries.',
      phase: 'Dataset',
    },
    {
      step: '03',
      title: 'Split Dataset',
      desc: '35 queries for tuning optimization; 15 queries strictly isolated for held-out evaluation.',
      phase: 'Isolation',
    },
    {
      step: '04',
      title: 'Measure Baseline',
      desc: 'Anchor evaluation: Tuning = 80.00% (28/35), Held-out = 73.33% (11/15).',
      phase: 'Baseline',
    },
    {
      step: '05',
      title: 'Extract Tuning Mistakes',
      desc: 'Identify misclassified tuning queries, expected labels, and confusing neighbors.',
      phase: 'Analysis',
    },
    {
      step: '06',
      title: 'Generate Candidates',
      desc: 'Local model meta-prompter proposes clearer operational boundaries.',
      phase: 'Optimization',
    },
    {
      step: '07',
      title: 'Apply Guardrails',
      desc: 'Enforce schema immutability, <40 words length, and 4-gram copy prevention.',
      phase: 'Validation',
    },
    {
      step: '08',
      title: 'Evaluate on Tuning Set',
      desc: 'Deterministic scoring on the 35 tuning queries at temperature=0.0.',
      phase: 'Testing',
    },
    {
      step: '09',
      title: 'Accept / Reject Candidate',
      desc: 'Strict improvement rule: Round 1 accepted (85.71%); Rounds 2 & 3 rejected.',
      phase: 'Decision',
    },
    {
      step: '10',
      title: 'Evaluate on Held-Out Set',
      desc: 'Evaluate the accepted Round 1 descriptions on the 15 unseen test queries.',
      phase: 'Generalization',
    },
    {
      step: '11',
      title: 'Compare Generalization',
      desc: 'Measure out-of-sample impact: 73.33% → 80.00% (+6.67 pp, 0 regressions).',
      phase: 'Evidence',
    },
  ];

  return (
    <section className="card" id="workflow">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">How Does It Work?</h2>
          <p className="card-subtitle">
            The 11-step experimental methodology from tool definition to held-out generalization testing
          </p>
        </div>
        <span className="badge badge-blue">CONTROLLED PROTOCOL</span>
      </div>

      <div className="workflow-steps-grid">
        {steps.map((item) => (
          <div key={item.step} className="workflow-card">
            <div className="workflow-header">
              <span className="workflow-step-num font-mono">{item.step}</span>
              <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>
                {item.phase}
              </span>
            </div>
            <h3 className="workflow-title">{item.title}</h3>
            <p className="workflow-desc">{item.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
};
