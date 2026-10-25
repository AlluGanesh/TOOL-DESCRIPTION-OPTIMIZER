import React, { useState } from 'react';
import { ToolDescriptionDiff } from '../../types/results';
import { Badge } from '../common/Badge';

interface ToolDescriptionDiffTableProps {
  diffs: ToolDescriptionDiff[];
}

export const ToolDescriptionDiffTable: React.FC<ToolDescriptionDiffTableProps> = ({ diffs }) => {
  const [filter, setFilter] = useState<'all' | 'changed' | 'unchanged'>('all');

  const filteredDiffs = diffs.filter((d) => {
    if (filter === 'changed') return d.changed;
    if (filter === 'unchanged') return !d.changed;
    return true;
  });

  const changedCount = diffs.filter((d) => d.changed).length;
  const unchangedCount = diffs.filter((d) => !d.changed).length;

  return (
    <div className="card" id="descriptions">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">How the Tool Descriptions Changed</h2>
          <p className="card-subtitle">
            Side-by-side linguistic comparison of canonical baseline descriptions against Round 1 optimized descriptions
          </p>
        </div>

        <div className="filter-buttons">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All Tools ({diffs.length})
          </button>
          <button
            className={`filter-btn ${filter === 'changed' ? 'active' : ''}`}
            onClick={() => setFilter('changed')}
          >
            Modified ({changedCount})
          </button>
          <button
            className={`filter-btn ${filter === 'unchanged' ? 'active' : ''}`}
            onClick={() => setFilter('unchanged')}
          >
            Preserved ({unchangedCount})
          </button>
        </div>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '180px' }}>Tool Name</th>
              <th>Original Description (Condition A)</th>
              <th>Optimized Description (Round 1 / Condition B)</th>
              <th style={{ width: '110px', textAlign: 'center' }}>Status</th>
              <th>Nature of Semantic Refinement</th>
            </tr>
          </thead>
          <tbody>
            {filteredDiffs.map((d) => (
              <tr
                key={d.tool_name}
                className={d.changed ? 'highlight-success' : ''}
              >
                <td className="font-mono" style={{ fontWeight: 700 }}>
                  {d.tool_name}
                </td>
                <td style={{ color: d.changed ? '#f87171' : 'var(--text-secondary)' }}>
                  "{d.original_description}"
                </td>
                <td style={{ color: d.changed ? '#34d399' : 'var(--text-secondary)', fontWeight: d.changed ? 600 : 400 }}>
                  "{d.optimized_description}"
                </td>
                <td style={{ textAlign: 'center' }}>
                  {d.changed ? (
                    <Badge variant="success">MODIFIED</Badge>
                  ) : (
                    <Badge variant="neutral">PRESERVED</Badge>
                  )}
                </td>
                <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '300px' }}>
                  {d.nature_of_change}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '1rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        <div>
          <strong style={{ color: 'var(--accent-green)' }}>7 Modified:</strong> Clarified target domain (web, email, calendar), entity scope (city), and operational specificity.
        </div>
        <div>
          <strong style={{ color: 'var(--text-secondary)' }}>3 Preserved:</strong> <code className="font-mono">read_file</code>, <code className="font-mono">write_file</code>, and <code className="font-mono">search_docs</code> already possessed direct semantic triggers.
        </div>
      </div>
    </div>
  );
};
