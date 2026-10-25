import React, { useState } from 'react';
import { ConfusionMatrixBundle } from '../../types/results';

interface ConfusionMatrixHeatmapProps {
  bundle: ConfusionMatrixBundle;
}

export const ConfusionMatrixHeatmap: React.FC<ConfusionMatrixHeatmapProps> = ({ bundle }) => {
  const [activeTab, setActiveTab] = useState<'optimized' | 'baseline' | 'both'>('both');
  const [hoveredCell, setHoveredCell] = useState<{
    matrix: 'baseline' | 'optimized';
    actual: string;
    predicted: string;
    count: number;
  } | null>(null);

  const labels = bundle.label_order;

  const renderMatrixGrid = (
    matrix: Record<string, Record<string, number>>,
    matrixType: 'baseline' | 'optimized',
    title: string,
    subtitle: string
  ) => {
    return (
      <div style={{ flex: 1, minWidth: '320px' }}>
        <div style={{ marginBottom: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: matrixType === 'optimized' ? 'var(--accent-green)' : '#93c5fd' }}>
              {title}
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{subtitle}</span>
          </div>
          <span className={`badge ${matrixType === 'optimized' ? 'badge-success' : 'badge-blue'}`}>
            {matrixType === 'optimized' ? '12/15 Correct' : '11/15 Correct'}
          </span>
        </div>

        <div className="matrix-wrapper">
          <table className="matrix-table">
            <thead>
              <tr>
                <th style={{ textAlign: 'right', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Actual ↓ / Pred →
                </th>
                {labels.map((lbl) => (
                  <th key={lbl} className="vertical-header" title={`Predicted: ${lbl}`}>
                    {lbl}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {labels.map((actual) => (
                <tr key={actual}>
                  <th style={{ textAlign: 'right', paddingRight: '0.6rem', fontSize: '0.7rem' }}>
                    {actual}
                  </th>
                  {labels.map((pred) => {
                    const count = matrix[actual]?.[pred] || 0;
                    const isDiagonal = actual === pred;
                    const isHit = isDiagonal && count > 0;
                    const isError = !isDiagonal && count > 0;

                    let cellClass = 'matrix-cell zero';
                    if (isHit) {
                      cellClass = count > 1 ? 'matrix-cell diagonal-hit high' : 'matrix-cell diagonal-hit';
                    } else if (isError) {
                      cellClass = 'matrix-cell off-diagonal-error';
                    }

                    return (
                      <td key={pred}>
                        <div
                          className={cellClass}
                          onMouseEnter={() =>
                            setHoveredCell({
                              matrix: matrixType,
                              actual,
                              predicted: pred,
                              count,
                            })
                          }
                          onMouseLeave={() => setHoveredCell(null)}
                          title={`Actual: ${actual}\nPredicted: ${pred}\nCount: ${count}`}
                        >
                          {count > 0 ? count : '·'}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="card" id="confusion-matrix">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">Held-Out Confusion Matrices</h2>
          <p className="card-subtitle">
            11×11 class-level routing contingency matrices across all canonical tools and none
          </p>
        </div>

        <div className="filter-buttons">
          <button
            className={`filter-btn ${activeTab === 'both' ? 'active' : ''}`}
            onClick={() => setActiveTab('both')}
          >
            Side-by-Side
          </button>
          <button
            className={`filter-btn ${activeTab === 'baseline' ? 'active' : ''}`}
            onClick={() => setActiveTab('baseline')}
          >
            Baseline Only
          </button>
          <button
            className={`filter-btn ${activeTab === 'optimized' ? 'active' : ''}`}
            onClick={() => setActiveTab('optimized')}
          >
            Optimized Only
          </button>
        </div>
      </div>

      {/* Hover Inspection Inspector */}
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.35)',
          padding: '0.6rem 1rem',
          borderRadius: '6px',
          border: '1px solid var(--border-color)',
          fontSize: '0.8rem',
          marginBottom: '1rem',
          minHeight: '40px',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
        }}
      >
        {hoveredCell ? (
          <>
            <span style={{ color: 'var(--text-muted)' }}>Cell Inspector:</span>
            <span>
              Condition:{' '}
              <strong style={{ color: hoveredCell.matrix === 'optimized' ? 'var(--accent-green)' : '#93c5fd' }}>
                {hoveredCell.matrix.toUpperCase()}
              </strong>
            </span>
            <span>
              Actual: <code className="font-mono">{hoveredCell.actual}</code>
            </span>
            <span>→</span>
            <span>
              Predicted: <code className="font-mono">{hoveredCell.predicted}</code>
            </span>
            <span>
              Count: <strong className="font-mono">{hoveredCell.count}</strong>
            </span>
            <span>
              {hoveredCell.actual === hoveredCell.predicted ? (
                hoveredCell.count > 0 ? (
                  <span className="badge badge-success">True Positive</span>
                ) : (
                  <span className="badge badge-neutral">No occurrences</span>
                )
              ) : hoveredCell.count > 0 ? (
                <span className="badge badge-error">Routing Error</span>
              ) : (
                <span className="badge badge-neutral">0 errors</span>
              )}
            </span>
          </>
        ) : (
          <span style={{ color: 'var(--text-muted)' }}>
            Hover over any matrix cell to inspect actual class, predicted class, and transition outcome.
          </span>
        )}
      </div>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '2rem',
        }}
      >
        {(activeTab === 'both' || activeTab === 'baseline') &&
          renderMatrixGrid(
            bundle.baseline,
            'baseline',
            'Baseline Held-Out Matrix',
            'Canonical Tool Descriptions (Condition A)'
          )}

        {(activeTab === 'both' || activeTab === 'optimized') &&
          renderMatrixGrid(
            bundle.optimized,
            'optimized',
            'Optimized Held-Out Matrix',
            'Round 1 Candidate Descriptions (Condition B)'
          )}
      </div>

      <div style={{ marginTop: '1.25rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
        <strong>Key Contrast:</strong> In the baseline matrix, <code className="font-mono">read_file</code> was misclassified as <code className="font-mono">none</code>. In the optimized matrix, <code className="font-mono">read_file</code> shifted onto the diagonal (1 true positive, 0 misclassifications).
      </div>
    </div>
  );
};
