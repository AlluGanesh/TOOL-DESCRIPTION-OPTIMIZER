import React from 'react';
import { AccuracySummary } from '../../types/results';

interface HeroMetricCardProps {
  accuracy: AccuracySummary;
}

export const HeroMetricCard: React.FC<HeroMetricCardProps> = ({ accuracy }) => {
  const heldOut = accuracy.held_out;

  return (
    <div className="card hero-card" id="overview">
      <div className="hero-badge-row">
        <span className="badge badge-success">CONTROLLED EVALUATION</span>
        <span className="badge badge-blue">PHASE 8 & 9 VERIFIED</span>
      </div>

      <h1 className="hero-title">Tool Description Optimizer</h1>
      <p className="hero-subtitle">
        Evaluating whether LLM-generated tool descriptions improve AI agent tool selection.
      </p>

      {/* Hero Research Result — Most Prominent Metric */}
      <div className="hero-metric-display">
        <div className="hero-metric-core">
          <span className="hero-metric-label">Held-Out Tool-Selection Accuracy</span>
          <div className="hero-metric-values">
            <span className="hero-val-baseline">
              {heldOut.baseline.accuracy_pct.toFixed(2)}%
            </span>
            <span className="hero-val-arrow">→</span>
            <span className="hero-val-optimized">
              {heldOut.optimized.accuracy_pct.toFixed(2)}%
            </span>
          </div>
        </div>

        <div className="hero-gains-badge-group">
          <div className="gain-badge positive">
            ▲ +{heldOut.absolute_improvement_pp.toFixed(2)} percentage points
          </div>
          <div className="gain-badge positive">
            ▲ +{heldOut.relative_improvement_pct.toFixed(2)}% relative improvement
          </div>
          <div className="gain-badge neutral">
            🎯 15 unseen benchmark queries
          </div>
          <div className="gain-badge positive">
            🛡️ 0 regressions
          </div>
        </div>
      </div>

      <div className="hero-footer-notes">
        <div className="hero-note-item">
          <strong style={{ color: 'var(--text-primary)' }}>Baseline:</strong> 11 / 15 correct ({heldOut.baseline.accuracy_pct.toFixed(2)}%)
        </div>
        <div className="hero-note-item">
          <strong style={{ color: 'var(--accent-green)' }}>Optimized:</strong> 12 / 15 correct ({heldOut.optimized.accuracy_pct.toFixed(2)}%)
        </div>
        <div className="hero-note-item">
          <strong style={{ color: 'var(--text-secondary)' }}>Error Reduction:</strong> -{heldOut.error_reduction_pct.toFixed(1)}% (4 → 3 errors)
        </div>
      </div>
    </div>
  );
};
