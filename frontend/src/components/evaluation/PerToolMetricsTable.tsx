import React from 'react';
import { ToolClassMetric } from '../../types/results';
import { Badge } from '../common/Badge';

interface PerToolMetricsTableProps {
  metrics: Record<string, ToolClassMetric>;
}

export const PerToolMetricsTable: React.FC<PerToolMetricsTableProps> = ({ metrics }) => {
  const orderedTools = [
    'search_web',
    'search_docs',
    'read_file',
    'write_file',
    'send_email',
    'create_calendar_event',
    'set_reminder',
    'get_weather',
    'calculator',
    'translate_text',
    'none',
  ];

  return (
    <div className="card" id="per-tool">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">Per-Tool Classification Performance</h2>
          <p className="card-subtitle">
            Class-level precision, recall, and F1 scores on the 15 held-out test queries
          </p>
        </div>
        <span className="badge badge-success">read_file F1: 0.00 → 1.00</span>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Tool / Routing Class</th>
              <th style={{ textAlign: 'center' }}>Test Count</th>
              <th style={{ textAlign: 'center' }}>Baseline Prec</th>
              <th style={{ textAlign: 'center' }}>Baseline Rec</th>
              <th style={{ textAlign: 'center' }}>Baseline F1</th>
              <th style={{ textAlign: 'center' }}>Optimized Prec</th>
              <th style={{ textAlign: 'center' }}>Optimized Rec</th>
              <th style={{ textAlign: 'center' }}>Optimized F1</th>
              <th style={{ textAlign: 'center' }}>F1 Delta</th>
            </tr>
          </thead>
          <tbody>
            {orderedTools.map((toolName) => {
              const m = metrics[toolName];
              if (!m) return null;

              const isReadFile = toolName === 'read_file';
              const isNone = toolName === 'none';
              const isGain = m.f1_delta > 0;

              return (
                <tr
                  key={toolName}
                  className={isReadFile ? 'highlight-success' : isNone ? 'highlight-success' : ''}
                >
                  <td>
                    <span
                      className="tool-tag font-mono"
                      style={{
                        fontWeight: isReadFile || isNone ? 700 : 500,
                        color: isReadFile ? 'var(--accent-green)' : 'inherit',
                      }}
                    >
                      {toolName}
                    </span>
                    {isReadFile && (
                      <span
                        style={{
                          marginLeft: '0.5rem',
                          fontSize: '0.7rem',
                          color: 'var(--accent-green)',
                          fontWeight: 600,
                        }}
                      >
                        ★ MAJOR GAIN
                      </span>
                    )}
                    {isNone && (
                      <span
                        style={{
                          marginLeft: '0.5rem',
                          fontSize: '0.7rem',
                          color: '#67e8f9',
                          fontWeight: 600,
                        }}
                      >
                        IMPROVED
                      </span>
                    )}
                  </td>
                  <td className="font-mono" style={{ textAlign: 'center' }}>
                    {m.actual_count}
                  </td>
                  <td className="font-mono" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    {m.baseline.precision.toFixed(2)}
                  </td>
                  <td className="font-mono" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    {m.baseline.recall.toFixed(2)}
                  </td>
                  <td
                    className="font-mono"
                    style={{
                      textAlign: 'center',
                      fontWeight: 600,
                      color: m.baseline.f1_score === 0 ? '#f87171' : 'var(--text-primary)',
                    }}
                  >
                    {m.baseline.f1_score.toFixed(2)}
                  </td>
                  <td className="font-mono" style={{ textAlign: 'center' }}>
                    {m.optimized.precision.toFixed(2)}
                  </td>
                  <td className="font-mono" style={{ textAlign: 'center' }}>
                    {m.optimized.recall.toFixed(2)}
                  </td>
                  <td
                    className="font-mono"
                    style={{
                      textAlign: 'center',
                      fontWeight: 700,
                      color: isGain ? 'var(--accent-green)' : 'var(--text-primary)',
                    }}
                  >
                    {m.optimized.f1_score.toFixed(2)}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {m.f1_delta > 0 ? (
                      <Badge variant="success">
                        +{m.f1_delta.toFixed(2)}
                      </Badge>
                    ) : m.f1_delta < 0 ? (
                      <Badge variant="error">
                        {m.f1_delta.toFixed(2)}
                      </Badge>
                    ) : (
                      <span className="font-mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        0.00
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '1rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        <div>
          <strong style={{ color: 'var(--accent-green)' }}>read_file:</strong> Precision jumped from 0.00 to 1.00; Recall jumped from 0.00 to 1.00 (F1: 0.00 → 1.00).
        </div>
        <div>
          <strong style={{ color: 'var(--accent-cyan)' }}>none:</strong> Precision improved from 0.25 to 0.33; Recall preserved at 0.50 (F1: 0.33 → 0.40).
        </div>
      </div>
    </div>
  );
};
