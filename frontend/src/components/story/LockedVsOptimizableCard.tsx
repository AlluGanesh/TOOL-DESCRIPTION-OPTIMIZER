import React from 'react';

export const LockedVsOptimizableCard: React.FC = () => {
  return (
    <section className="card" id="experimental-controls">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">What is Fixed vs. What Changes?</h2>
          <p className="card-subtitle">
            Controlled laboratory invariants versus the single isolated independent variable
          </p>
        </div>
        <span className="badge badge-success">STRICT LABORATORY CONTROLS</span>
      </div>

      <div className="controls-split-container">
        {/* Left: LOCKED Panel */}
        <div className="control-panel locked-panel">
          <div className="control-panel-header">
            <span className="control-status-badge locked-badge">🔒 LOCKED INVARIANTS</span>
            <span className="control-panel-sub">Completely fixed across all rounds</span>
          </div>

          <div className="control-items-list">
            <div className="control-item-row">
              <span className="control-item-icon">🤖</span>
              <div>
                <strong>Base Model:</strong> <span className="font-mono">qwen2.5:3b</span> (zero weights modification)
              </div>
            </div>
            <div className="control-item-row">
              <span className="control-item-icon">🌡️</span>
              <div>
                <strong>Sampling Temperature:</strong> <span className="font-mono">0.0</span> (deterministic greedy decoding)
              </div>
            </div>
            <div className="control-item-row">
              <span className="control-item-icon">🔢</span>
              <div>
                <strong>Tool Count:</strong> Exactly 10 canonical tools + none
              </div>
            </div>
            <div className="control-item-row">
              <span className="control-item-icon">🏷️</span>
              <div>
                <strong>Tool Names:</strong> Locked (<code className="font-mono">search_web</code>, <code className="font-mono">read_file</code>, etc.)
              </div>
            </div>
            <div className="control-item-row">
              <span className="control-item-icon">⚙️</span>
              <div>
                <strong>Parameter Names & Types:</strong> String, integer, and object types locked
              </div>
            </div>
            <div className="control-item-row">
              <span className="control-item-icon">📋</span>
              <div>
                <strong>Required Fields & Schemas:</strong> JSON Schema structure immutable
              </div>
            </div>
            <div className="control-item-row">
              <span className="control-item-icon">📂</span>
              <div>
                <strong>Benchmark Dataset:</strong> 50 frozen labeled queries (35 tuning, 15 held-out)
              </div>
            </div>
          </div>
        </div>

        {/* Right: MUTABLE Panel */}
        <div className="control-panel mutable-panel">
          <div className="control-panel-header">
            <span className="control-status-badge mutable-badge">✏️ MUTABLE VARIABLE</span>
            <span className="control-panel-sub">The single independent variable</span>
          </div>

          <div className="mutable-highlight-content">
            <div className="mutable-big-title">Natural-Language Tool Descriptions</div>
            <p className="mutable-desc-text">
              The experiment changes the <strong>description text only</strong>. We do NOT optimize function schemas, parameters, code implementation, or model weights.
            </p>

            <div className="mutable-callout-box">
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                Example Semantic Refinement:
              </div>
              <div className="diff-preview-box">
                <span className="diff-del">"Searches for information."</span>
                <span className="diff-arrow">➔</span>
                <span className="diff-add">"Searches the web for information."</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                Clarifying the target search domain (web lookup vs. generic search) without touching parameters.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
