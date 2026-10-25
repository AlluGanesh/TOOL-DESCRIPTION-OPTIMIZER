import React, { useState } from 'react';
import { ConfusionMatrixBundle, IntegrityHashes, ToolClassMetric } from '../../types/results';
import { ConfusionMatrixHeatmap } from '../evaluation/ConfusionMatrixHeatmap';
import { PerToolMetricsTable } from '../evaluation/PerToolMetricsTable';

interface TechnicalDeepDiveProps {
  confusionMatrices: ConfusionMatrixBundle;
  perToolMetrics: Record<string, ToolClassMetric>;
  integrityHashes: IntegrityHashes;
}

export const TechnicalDeepDive: React.FC<TechnicalDeepDiveProps> = ({
  confusionMatrices,
  perToolMetrics,
  integrityHashes,
}) => {
  const [activeTab, setActiveTab] = useState<'matrices' | 'metrics' | 'provenance' | 'architecture'>('matrices');
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  return (
    <section className="card technical-deep-dive-card" id="technical-deep-dive">
      <div className="card-header" style={{ cursor: 'pointer' }} onClick={() => setIsExpanded(!isExpanded)}>
        <div className="card-title-group">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <h2 className="card-title">Technical Deep Dive & Laboratory Metrics</h2>
            <span className="badge badge-neutral">COLLAPSIBLE LAB REPORT</span>
          </div>
          <p className="card-subtitle">
            Fine-grained 11×11 confusion matrices, per-tool precision/recall/F1, SHA-256 provenance, and end-to-end architecture
          </p>
        </div>
        <button
          className="filter-btn font-mono"
          style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
          type="button"
          aria-expanded={isExpanded}
        >
          {isExpanded ? '▲ Collapse Section' : '▼ Expand Section'}
        </button>
      </div>

      {isExpanded && (
        <div className="technical-content-body">
          {/* Tabs Navigation */}
          <div className="technical-tabs-bar" role="tablist" aria-label="Technical Deep Dive Tabs">
            <button
              role="tab"
              aria-selected={activeTab === 'matrices'}
              className={`tech-tab-btn ${activeTab === 'matrices' ? 'active' : ''}`}
              onClick={() => setActiveTab('matrices')}
              type="button"
            >
              📊 1. Confusion Matrices (11×11)
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'metrics'}
              className={`tech-tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
              onClick={() => setActiveTab('metrics')}
              type="button"
            >
              📈 2. Per-Tool Metrics (P / R / F1)
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'provenance'}
              className={`tech-tab-btn ${activeTab === 'provenance' ? 'active' : ''}`}
              onClick={() => setActiveTab('provenance')}
              type="button"
            >
              🔒 3. Provenance & SHA-256 Hashes
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'architecture'}
              className={`tech-tab-btn ${activeTab === 'architecture' ? 'active' : ''}`}
              onClick={() => setActiveTab('architecture')}
              type="button"
            >
              🏗️ 4. System Architecture
            </button>
          </div>

          {/* Tab 1: Confusion Matrices */}
          {activeTab === 'matrices' && (
            <div className="tab-pane-content" role="tabpanel">
              <ConfusionMatrixHeatmap bundle={confusionMatrices} />
            </div>
          )}

          {/* Tab 2: Per-Tool Metrics */}
          {activeTab === 'metrics' && (
            <div className="tab-pane-content" role="tabpanel">
              <PerToolMetricsTable metrics={perToolMetrics} />
            </div>
          )}

          {/* Tab 3: Provenance Hashes */}
          {activeTab === 'provenance' && (
            <div className="tab-pane-content" role="tabpanel">
              <div className="card" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
                <div className="card-header">
                  <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Cryptographic Artifact Provenance</h3>
                  <span className="badge badge-success">IMMUTABLE EXPERIMENTAL HASHES</span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
                  To guarantee auditability and prevent data tampering, all benchmark queries, canonical schemas, and optimization artifacts are cryptographically verified using SHA-256 digests.
                </p>

                <div className="provenance-grid">
                  <div className="provenance-hash-row">
                    <span className="hash-label">Canonical Tools (<code className="font-mono">tools/tools.json</code>):</span>
                    <span className="hash-value font-mono">{integrityHashes.canonical_tools_hash}</span>
                  </div>
                  <div className="provenance-hash-row">
                    <span className="hash-label">Optimized Tools (<code className="font-mono">round_01.json</code>):</span>
                    <span className="hash-value font-mono">{integrityHashes.optimized_tools_hash}</span>
                  </div>
                  <div className="provenance-hash-row">
                    <span className="hash-label">Tuning Dataset (35 queries):</span>
                    <span className="hash-value font-mono">{integrityHashes.tuning_dataset_hash}</span>
                  </div>
                  <div className="provenance-hash-row">
                    <span className="hash-label">Held-Out Dataset (15 queries):</span>
                    <span className="hash-value font-mono">{integrityHashes.held_out_dataset_hash}</span>
                  </div>
                </div>

                <div style={{ marginTop: '1rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  All hashes are verified in automated CI tests (<code className="font-mono">backend/tests/test_provenance.py</code>) to enforce that zero modifications occur between experiment runs.
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: System Architecture */}
          {activeTab === 'architecture' && (
            <div className="tab-pane-content" role="tabpanel">
              <div className="card" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
                <div className="card-header">
                  <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>System Architecture & Pipeline Flow</h3>
                  <span className="badge badge-blue">LOCAL HARDWARE EXECUTION</span>
                </div>

                {/* Architecture Pipeline Diagram */}
                <div className="arch-flow-diagram">
                  <div className="arch-box react-box">
                    <span className="arch-icon">⚛️</span>
                    <span className="arch-title">React UI</span>
                    <span className="arch-sub">TypeScript / Vite</span>
                  </div>
                  <span className="arch-arrow">➔</span>
                  <div className="arch-box fast-box">
                    <span className="arch-icon">🚀</span>
                    <span className="arch-title">FastAPI Backend</span>
                    <span className="arch-sub">Python 3.12 / Pydantic</span>
                  </div>
                  <span className="arch-arrow">➔</span>
                  <div className="arch-box ollama-box">
                    <span className="arch-icon">🦙</span>
                    <span className="arch-title">Ollama Daemon</span>
                    <span className="arch-sub">Local REST API (:11434)</span>
                  </div>
                  <span className="arch-arrow">➔</span>
                  <div className="arch-box model-box">
                    <span className="arch-icon">🧠</span>
                    <span className="arch-title">qwen2.5:3b</span>
                    <span className="arch-sub">Native Function Calling</span>
                  </div>
                </div>

                <div className="arch-details-grid">
                  <div className="arch-detail-item">
                    <strong>1. Deterministic Caching:</strong>
                    <p>
                      All model inference requests during evaluation are hashed by prompt and tools schema and cached in <code className="font-mono">cache/</code> to eliminate redundant GPU invocations and ensure exact test reproducibility.
                    </p>
                  </div>
                  <div className="arch-detail-item">
                    <strong>2. Evaluator Service:</strong>
                    <p>
                      Executes batch tool selection over dataset queries, computes micro/macro accuracy, compiles 11×11 confusion matrices, and determines per-query transitions.
                    </p>
                  </div>
                  <div className="arch-detail-item">
                    <strong>3. Optimizer Service & Guardrails:</strong>
                    <p>
                      Inspects false predictions on tuning data, generates candidate descriptions, and strictly enforces guardrails (lexical copy prevention, max word limit, schema preservation).
                    </p>
                  </div>
                  <div className="arch-detail-item">
                    <strong>4. Held-Out Isolation:</strong>
                    <p>
                      The 15 held-out queries are never passed to the optimizer service or prompt synthesizer. They remain isolated until the final generalization checkpoint.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
