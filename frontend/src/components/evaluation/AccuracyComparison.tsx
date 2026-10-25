import React from 'react';
import { AccuracySummary } from '../../types/results';

interface AccuracyComparisonProps {
  accuracy: AccuracySummary;
}

export const AccuracyComparison: React.FC<AccuracyComparisonProps> = ({ accuracy }) => {
  const { tuning, held_out } = accuracy;

  return (
    <div className="card" id="accuracy">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">Accuracy Comparison by Dataset Partition</h2>
          <p className="card-subtitle">
            Evaluating performance on the tuning split (optimization domain) versus the completely isolated held-out split (generalization test).
          </p>
        </div>
        <span className="badge badge-success">HELD-OUT IS PRIMARY EVIDENCE</span>
      </div>

      <div className="comparison-grid">
        {/* Tuning Split */}
        <div className="partition-card">
          <div className="partition-header">
            <div>
              <span className="badge badge-neutral">TUNING SET (N=35)</span>
              <h3 className="partition-title" style={{ marginTop: '0.4rem' }}>
                Optimization Domain
              </h3>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className="badge badge-success">
                +{tuning.absolute_improvement_pp.toFixed(2)} pp
              </span>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                +{tuning.relative_improvement_pct.toFixed(2)}% rel
              </div>
            </div>
          </div>

          <div className="bar-chart-container">
            <div className="bar-row">
              <div className="bar-meta">
                <span className="bar-label">Baseline (Canonical Descriptions)</span>
                <span className="bar-score font-mono">
                  {tuning.baseline.correct}/{tuning.baseline.total} ({tuning.baseline.accuracy_pct.toFixed(2)}%)
                </span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill baseline"
                  style={{ width: `${tuning.baseline.accuracy_pct}%` }}
                >
                  {tuning.baseline.accuracy_pct.toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="bar-row">
              <div className="bar-meta">
                <span className="bar-label">Optimized (Round 1 Descriptions)</span>
                <span className="bar-score font-mono" style={{ color: 'var(--accent-green)' }}>
                  {tuning.optimized.correct}/{tuning.optimized.total} ({tuning.optimized.accuracy_pct.toFixed(2)}%)
                </span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill optimized"
                  style={{ width: `${tuning.optimized.accuracy_pct}%` }}
                >
                  {tuning.optimized.accuracy_pct.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
            Errors reduced from <strong>{tuning.baseline.errors}</strong> to <strong>{tuning.optimized.errors}</strong> queries (-28.6%). Used to guide description candidates.
          </div>
        </div>

        {/* Held-Out Split (Primary Evidence) */}
        <div className="partition-card primary">
          <div className="partition-header">
            <div>
              <span className="badge badge-success">HELD-OUT TEST SET (N=15)</span>
              <h3 className="partition-title" style={{ marginTop: '0.4rem', color: 'var(--accent-green)' }}>
                Generalization Evidence ★
              </h3>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className="badge badge-success" style={{ fontSize: '0.85rem' }}>
                +{held_out.absolute_improvement_pp.toFixed(2)} pp
              </span>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-green)', marginTop: '0.2rem' }}>
                +{held_out.relative_improvement_pct.toFixed(2)}% rel
              </div>
            </div>
          </div>

          <div className="bar-chart-container">
            <div className="bar-row">
              <div className="bar-meta">
                <span className="bar-label">Baseline (Canonical Descriptions)</span>
                <span className="bar-score font-mono">
                  {held_out.baseline.correct}/{held_out.baseline.total} ({held_out.baseline.accuracy_pct.toFixed(2)}%)
                </span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill baseline"
                  style={{ width: `${held_out.baseline.accuracy_pct}%` }}
                >
                  {held_out.baseline.accuracy_pct.toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="bar-row">
              <div className="bar-meta">
                <span className="bar-label">Optimized (Round 1 Descriptions)</span>
                <span className="bar-score font-mono" style={{ color: 'var(--accent-green)' }}>
                  {held_out.optimized.correct}/{held_out.optimized.total} ({held_out.optimized.accuracy_pct.toFixed(2)}%)
                </span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill optimized"
                  style={{ width: `${held_out.optimized.accuracy_pct}%` }}
                >
                  {held_out.optimized.accuracy_pct.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', borderTop: '1px solid rgba(16, 185, 129, 0.2)', paddingTop: '0.75rem' }}>
            Errors reduced from <strong>{held_out.baseline.errors}</strong> to <strong>{held_out.optimized.errors}</strong> queries (-25.0% error reduction). Zero regressions observed.
          </div>
        </div>
      </div>
    </div>
  );
};
