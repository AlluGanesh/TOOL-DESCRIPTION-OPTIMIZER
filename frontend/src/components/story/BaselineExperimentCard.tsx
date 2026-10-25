import React from 'react';
import { AccuracySummary } from '../../types/results';

interface BaselineExperimentCardProps {
  accuracy: AccuracySummary;
}

export const BaselineExperimentCard: React.FC<BaselineExperimentCardProps> = ({ accuracy }) => {
  const { tuning, held_out } = accuracy;

  return (
    <section className="card" id="baseline-anchor">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">Baseline Benchmark & Dataset Partitioning</h2>
          <p className="card-subtitle">
            Evaluating canonical tool descriptions on the 50-query benchmark before description optimization
          </p>
        </div>
        <span className="badge badge-neutral">INITIAL ANCHOR STATE</span>
      </div>

      <div className="baseline-split-grid">
        {/* Tuning Partition */}
        <div className="baseline-partition-box">
          <div className="baseline-partition-badge">
            <span className="badge badge-blue">TUNING SPLIT (N=35)</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Visible to Optimizer</span>
          </div>

          <div className="baseline-score-row">
            <div className="baseline-big-score font-mono">
              {tuning.baseline.accuracy_pct.toFixed(2)}%
            </div>
            <div className="baseline-count-sub font-mono">
              {tuning.baseline.correct} / {tuning.baseline.total} correct
            </div>
          </div>

          <p className="baseline-desc">
            The 35 tuning queries were used during optimization rounds to identify routing mistakes, formulate meta-prompts, and validate candidate descriptions.
          </p>

          <div className="baseline-mistakes-note">
            ⚠️ <strong>Baseline Mistakes:</strong> 7 queries misclassified. These 7 mistakes served as input to the optimization loop.
          </div>
        </div>

        {/* Held-Out Partition */}
        <div className="baseline-partition-box held-out-highlight">
          <div className="baseline-partition-badge">
            <span className="badge badge-success">HELD-OUT TEST SPLIT (N=15)</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--accent-green)' }}>Strictly Isolated</span>
          </div>

          <div className="baseline-score-row">
            <div className="baseline-big-score font-mono" style={{ color: 'var(--text-primary)' }}>
              {held_out.baseline.accuracy_pct.toFixed(2)}%
            </div>
            <div className="baseline-count-sub font-mono">
              {held_out.baseline.correct} / {held_out.baseline.total} correct
            </div>
          </div>

          <p className="baseline-desc">
            The 15 held-out benchmark queries were completely isolated from optimization. They were not seen, evaluated, or accessed by the optimizer during description refinement.
          </p>

          <div className="baseline-mistakes-note" style={{ borderColor: 'rgba(16, 185, 129, 0.25)', background: 'rgba(16, 185, 129, 0.05)' }}>
            🎯 <strong>Why Held-Out Matters:</strong> Generalization cannot be established on tuning data alone. The held-out benchmark queries measure out-of-sample routing accuracy.
          </div>
        </div>
      </div>
    </section>
  );
};
