import React from 'react';
import { OptimizationRoundsSummary } from '../../types/results';
import { Badge } from '../common/Badge';

interface OptimizationJourneyProps {
  summary: OptimizationRoundsSummary;
}

export const OptimizationJourney: React.FC<OptimizationJourneyProps> = ({ summary }) => {
  return (
    <div className="card" id="optimization">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">Optimization Journey & Progression</h2>
          <p className="card-subtitle">
            Iterative refinement rounds executed by the description optimizer on the tuning dataset (N=35)
          </p>
        </div>
        <span className="badge badge-success">BEST: ROUND 1 (85.71%)</span>
      </div>

      {/* Summary KPI Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          marginBottom: '1.75rem',
        }}
      >
        <div className="config-item">
          <span className="config-label">Total Rounds Executed</span>
          <span className="config-value">{summary.total_rounds}</span>
        </div>
        <div className="config-item">
          <span className="config-label">Accepted Rounds</span>
          <span className="config-value" style={{ color: 'var(--accent-green)' }}>
            {summary.accepted_rounds} (Round {summary.best_round})
          </span>
        </div>
        <div className="config-item">
          <span className="config-label">Best Tuning Accuracy</span>
          <span className="config-value" style={{ color: 'var(--accent-green)' }}>
            85.71% (+5.71 pp)
          </span>
        </div>
        <div className="config-item">
          <span className="config-label">Termination Trigger</span>
          <span className="config-value" style={{ fontSize: '0.85rem', color: 'var(--accent-amber)' }}>
            2 consecutive non-improvements
          </span>
        </div>
      </div>

      {/* Timeline Representation */}
      <div className="timeline-list">
        {summary.round_accuracies.map((round) => {
          const isRound0 = round.round === 0;
          const isAccepted = round.round === summary.best_round;
          const accuracyPct = (round.accuracy * 100).toFixed(2);

          let roundDescription = 'Initial canonical tool definitions from tools/tools.json';
          if (round.round === 1) {
            roundDescription = 'Strict tuning accuracy improvement (+5.71%) -> ACCEPTED';
          } else if (round.round === 2) {
            roundDescription = 'Non-improvement (80.00%) -> REJECTED (Consecutive: 1/2)';
          } else if (round.round === 3) {
            roundDescription = 'Non-improvement (80.00%) -> REJECTED (Consecutive: 2/2 -> TERMINATED)';
          }

          return (
            <div
              key={round.round}
              className={`timeline-item ${isAccepted ? 'accepted' : ''}`}
            >
              <div className="timeline-marker">
                {round.round}
              </div>

              <div className="timeline-item-header">
                <div>
                  <span className="timeline-round-title">
                    {isRound0
                      ? 'Round 0 — Baseline Anchor'
                      : `Round ${round.round} Iteration`}
                  </span>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {roundDescription}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div
                    className="timeline-score font-mono"
                    style={{ color: isAccepted ? 'var(--accent-green)' : 'inherit' }}
                  >
                    {accuracyPct}%
                  </div>
                  <div>
                    {isRound0 ? (
                      <Badge variant="blue">BASELINE</Badge>
                    ) : isAccepted ? (
                      <Badge variant="success">ACCEPTED (BEST)</Badge>
                    ) : (
                      <Badge variant="warning">REJECTED</Badge>
                    )}
                  </div>
                </div>
              </div>

              {/* Progress bar per round */}
              <div className="bar-track" style={{ height: '8px', marginTop: '0.5rem' }}>
                <div
                  className={`bar-fill ${isAccepted ? 'optimized' : 'baseline'}`}
                  style={{ width: `${accuracyPct}%` }}
                ></div>
              </div>

              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                Status: <code className="font-mono">{round.status}</code>
              </div>
            </div>
          );
        })}
      </div>

      <div className="config-highlight-box" style={{ marginTop: '1.5rem' }}>
        <strong>Experimental Integrity:</strong> Round 1 was selected exclusively via tuning set performance. No held-out queries or held-out labels were ever evaluated or seen during the optimization loop.
      </div>
    </div>
  );
};
