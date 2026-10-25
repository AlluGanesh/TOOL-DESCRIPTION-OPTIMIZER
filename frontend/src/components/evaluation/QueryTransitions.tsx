import React, { useState } from 'react';
import {
  HeldOutQueryDetail,
  QueryTransitionCounts,
  QueryTransitionType,
} from '../../types/results';
import { Badge } from '../common/Badge';

interface QueryTransitionsProps {
  counts: QueryTransitionCounts;
  queries: HeldOutQueryDetail[];
}

export const QueryTransitions: React.FC<QueryTransitionsProps> = ({
  counts,
  queries,
}) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filterTransitions = (query: HeldOutQueryDetail) => {
    if (selectedFilter !== 'all' && query.transition !== selectedFilter) {
      return false;
    }
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      const matchId = query.query_id.toLowerCase().includes(term);
      const matchText = query.query.toLowerCase().includes(term);
      const matchTool = query.expected_tool.toLowerCase().includes(term);
      return matchId || matchText || matchTool;
    }
    return true;
  };

  const filteredQueries = queries.filter(filterTransitions);

  const getTransitionBadge = (type: QueryTransitionType) => {
    switch (type) {
      case 'became_correct':
        return <Badge variant="success">★ Became Correct</Badge>;
      case 'remained_correct':
        return <Badge variant="blue">Remained Correct</Badge>;
      case 'remained_incorrect':
        return <Badge variant="warning">Remained Incorrect</Badge>;
      case 'became_incorrect':
        return <Badge variant="error">Regressed (None)</Badge>;
    }
  };

  return (
    <div className="card" id="transitions">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">Query Transition Breakdown</h2>
          <p className="card-subtitle">
            Query-by-query analysis of routing transitions between Baseline and Optimized conditions (N=15)
          </p>
        </div>
        <span className="badge badge-success">ZERO REGRESSIONS</span>
      </div>

      {/* 4 Summary Stat Cards */}
      <div className="transition-stats-row">
        <div className="transition-stat-card">
          <span className="transition-stat-count font-mono" style={{ color: '#93c5fd' }}>
            {counts.remained_correct}
          </span>
          <span className="transition-stat-label">Remained Correct</span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Persistent positive routing
          </span>
        </div>

        <div className="transition-stat-card became-correct">
          <span className="transition-stat-count font-mono" style={{ color: 'var(--accent-green)' }}>
            +{counts.became_correct}
          </span>
          <span className="transition-stat-label" style={{ color: 'var(--accent-green)' }}>
            Became Correct (Q014)
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--accent-green)', marginTop: '0.2rem' }}>
            Net accuracy driver
          </span>
        </div>

        <div className="transition-stat-card">
          <span className="transition-stat-count font-mono" style={{ color: 'var(--text-muted)' }}>
            {counts.became_incorrect}
          </span>
          <span className="transition-stat-label">Became Incorrect</span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Zero regressions
          </span>
        </div>

        <div className="transition-stat-card remained-incorrect">
          <span className="transition-stat-count font-mono" style={{ color: 'var(--accent-amber)' }}>
            {counts.remained_incorrect}
          </span>
          <span className="transition-stat-label" style={{ color: 'var(--accent-amber)' }}>
            Remained Incorrect
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Q009, Q018, Q049
          </span>
        </div>
      </div>

      {/* Key Case Highlights Grid: Q014 prominent + Q009, Q018, Q049 */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
          Key Case Studies (Observed Routing Transitions)
        </h3>

        <div className="case-cards-grid">
          {/* Q014 Card - Prominent */}
          <div className="case-card resolved">
            <div className="case-card-header">
              <span className="case-query-id" style={{ color: 'var(--accent-green)' }}>
                Q014 • Resolved Error
              </span>
              <Badge variant="success">Became Correct</Badge>
            </div>
            <p className="case-query-text">
              "Check the contents of /etc/hosts to see if the local database alias is configured."
            </p>
            <div className="case-routing-row">
              <span>Expected: <span className="tool-tag expected">read_file</span></span>
              <span>•</span>
              <span style={{ color: '#f87171' }}>Baseline: none</span>
              <span>→</span>
              <span style={{ color: '#34d399', fontWeight: 700 }}>Optimized: read_file</span>
            </div>
            <p className="case-analysis">
              Q014 changed from an incorrect <code className="font-mono">none</code> prediction to the correct <code className="font-mono">read_file</code> prediction after the description optimization. The experiment establishes the observed prediction change, but does not directly measure the model's internal reasoning or the specific mechanism responsible for the improvement.
            </p>
          </div>

          {/* Q009 Card */}
          <div className="case-card persistent">
            <div className="case-card-header">
              <span className="case-query-id" style={{ color: 'var(--accent-amber)' }}>
                Q009 • Persistent Error
              </span>
              <Badge variant="warning">Remained Incorrect</Badge>
            </div>
            <p className="case-query-text">
              "What SLA tier do we commit to enterprise clients for urgent production outages in our support agreements?"
            </p>
            <div className="case-routing-row">
              <span>Expected: <span className="tool-tag expected">search_docs</span></span>
              <span>•</span>
              <span style={{ color: '#f87171' }}>Baseline: none</span>
              <span>→</span>
              <span style={{ color: '#f87171' }}>Optimized: none</span>
            </div>
            <p className="case-analysis">
              The prompt does not mention the words 'document' or 'handbook'. For this query, the model did not route contractual client commitments to internal documentation and defaulted to <code className="font-mono">none</code>.
            </p>
          </div>

          {/* Q018 Card */}
          <div className="case-card persistent">
            <div className="case-card-header">
              <span className="case-query-id" style={{ color: 'var(--accent-amber)' }}>
                Q018 • Persistent Error
              </span>
              <Badge variant="warning">Remained Incorrect</Badge>
            </div>
            <p className="case-query-text">
              "Export this list of customer IDs to C:\Exports\churned_users.csv on the disk."
            </p>
            <div className="case-routing-row">
              <span>Expected: <span className="tool-tag expected">write_file</span></span>
              <span>•</span>
              <span style={{ color: '#f87171' }}>Baseline: none</span>
              <span>→</span>
              <span style={{ color: '#f87171' }}>Optimized: none</span>
            </div>
            <p className="case-analysis">
              The user query frames the request as an 'Export' operation. The observed prediction suggests that, for this query, the model did not associate the phrase 'export ... to disk' with the <code className="font-mono">write_file</code> tool.
            </p>
          </div>

          {/* Q049 Card */}
          <div className="case-card persistent">
            <div className="case-card-header">
              <span className="case-query-id" style={{ color: 'var(--accent-amber)' }}>
                Q049 • Persistent False Positive
              </span>
              <Badge variant="warning">Remained Incorrect</Badge>
            </div>
            <p className="case-query-text">
              "What are some general tips for maintaining good posture while working long hours at a desk?"
            </p>
            <div className="case-routing-row">
              <span>Expected: <span className="tool-tag expected">none</span></span>
              <span>•</span>
              <span style={{ color: '#f87171' }}>Baseline: search_web</span>
              <span>→</span>
              <span style={{ color: '#f87171' }}>Optimized: search_web</span>
            </div>
            <p className="case-analysis">
              Even with <code className="font-mono">search_web</code> refined to "Searches the web for information.", informational advice triggers remain prone to unnecessary search invocation.
            </p>
          </div>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="filter-bar">
        <div className="filter-buttons">
          <button
            className={`filter-btn ${selectedFilter === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedFilter('all')}
          >
            All Queries ({queries.length})
          </button>
          <button
            className={`filter-btn ${selectedFilter === 'became_correct' ? 'active' : ''}`}
            onClick={() => setSelectedFilter('became_correct')}
          >
            Became Correct ({counts.became_correct})
          </button>
          <button
            className={`filter-btn ${selectedFilter === 'remained_correct' ? 'active' : ''}`}
            onClick={() => setSelectedFilter('remained_correct')}
          >
            Remained Correct ({counts.remained_correct})
          </button>
          <button
            className={`filter-btn ${selectedFilter === 'remained_incorrect' ? 'active' : ''}`}
            onClick={() => setSelectedFilter('remained_incorrect')}
          >
            Remained Incorrect ({counts.remained_incorrect})
          </button>
        </div>

        <input
          type="text"
          className="search-input"
          placeholder="Filter by ID, tool, or query text..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Query Detail Table */}
      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Query ID</th>
              <th>Expected Tool</th>
              <th>Baseline Prediction</th>
              <th>Optimized Prediction</th>
              <th>Outcome</th>
              <th>User Query Snippet</th>
            </tr>
          </thead>
          <tbody>
            {filteredQueries.map((q) => (
              <tr
                key={q.query_id}
                className={
                  q.transition === 'became_correct'
                    ? 'highlight-success'
                    : q.transition === 'remained_incorrect'
                    ? 'highlight-error'
                    : ''
                }
              >
                <td className="font-mono" style={{ fontWeight: 700 }}>
                  {q.query_id}
                </td>
                <td>
                  <span className="tool-tag expected">{q.expected_tool}</span>
                </td>
                <td>
                  <span
                    className={`tool-tag ${
                      q.baseline_correct ? 'font-mono' : 'font-mono'
                    }`}
                    style={{
                      color: q.baseline_correct ? '#34d399' : '#f87171',
                    }}
                  >
                    {q.baseline_prediction}
                  </span>
                </td>
                <td>
                  <span
                    className="tool-tag font-mono"
                    style={{
                      color: q.optimized_correct ? '#34d399' : '#f87171',
                      fontWeight: q.transition === 'became_correct' ? 700 : 500,
                    }}
                  >
                    {q.optimized_prediction}
                  </span>
                </td>
                <td>{getTransitionBadge(q.transition)}</td>
                <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '420px' }}>
                  "{q.query}"
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
