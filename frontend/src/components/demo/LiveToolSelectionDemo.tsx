import React, { useState } from 'react';
import { DataService } from '../../services/apiService';
import { ToolSelectionResponse } from '../../types/api';
import { Badge } from '../common/Badge';

interface LiveToolSelectionDemoProps {
  backendConnected: boolean | null;
}

const DEMO_EXAMPLES = [
  'What is 25 multiplied by 16?',
  'Check the contents of /etc/hosts to see if database alias is configured',
  'Look through our internal wiki for the employee data deletion procedure',
  'What is the current status of the Artemis space mission schedule?',
  'Send an email to support@vendor.com about duplicate invoice items',
  'Brainstorm five creative names for a sustainable bamboo home brand',
];

export const LiveToolSelectionDemo: React.FC<LiveToolSelectionDemoProps> = ({
  backendConnected,
}) => {
  const [query, setQuery] = useState<string>(DEMO_EXAMPLES[0]);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ToolSelectionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunSelection = async () => {
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await DataService.selectToolLive(query.trim());
      setResult(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card demo-card" id="live-demo">
      <div className="card-header">
        <div className="card-title-group">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <h2 className="card-title">Live Native Tool Selection Demo</h2>
            <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
              LIVE LOCAL INFERENCE
            </span>
          </div>
          <p className="card-subtitle">
            Enter an operational request to observe how the local <code className="font-mono">qwen2.5:3b</code> model selects a tool using native function calling at <code className="font-mono">temperature=0.0</code>.
          </p>
        </div>

        <div className="demo-status-pill">
          <span className={`pulse-dot ${backendConnected ? '' : 'offline'}`}></span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            {backendConnected ? 'Backend Connected' : 'Backend Offline'}
          </span>
        </div>
      </div>

      {/* Distinction Banner */}
      <div className="demo-distinction-banner">
        <strong>Live Demo Notice:</strong> This interactive console demonstrates live native tool calling via the local Ollama daemon. It is an interactive system demonstration, not an experimental benchmark measurement.
      </div>

      {/* Preset Demo Buttons */}
      <div className="demo-preset-section">
        <span className="demo-preset-label">Demo Examples (Click to load):</span>
        <div className="demo-preset-buttons">
          {DEMO_EXAMPLES.map((ex, idx) => (
            <button
              key={idx}
              className={`preset-query-btn ${query === ex ? 'active-preset' : ''}`}
              onClick={() => {
                setQuery(ex);
                setError(null);
              }}
              type="button"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Query Input Box */}
      <div className="demo-input-row">
        <input
          type="text"
          className="demo-text-input font-sans"
          placeholder="Type any operational query..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleRunSelection();
            }
          }}
          disabled={loading}
          aria-label="User operational query"
        />
        <button
          className="demo-run-btn font-mono"
          onClick={handleRunSelection}
          disabled={loading || !query.trim()}
          type="button"
        >
          {loading ? 'Evaluating...' : 'Select Tool Live ➔'}
        </button>
      </div>

      {/* Offline Notice if backend not reachable */}
      {backendConnected === false && (
        <div className="demo-offline-warning">
          ⚠️ Local inference is unavailable. Start the FastAPI backend (<code className="font-mono">.venv\Scripts\python.exe -m uvicorn backend.app.main:app</code>) and Ollama daemon to enable the live demo.
        </div>
      )}

      {/* Error Output */}
      {error && (
        <div className="demo-error-box" role="alert">
          <strong>Inference Error:</strong> {error}
        </div>
      )}

      {/* Live Result Display */}
      {result && (
        <div className="demo-result-container" aria-live="polite">
          <div className="demo-result-header">
            <div>
              <span className="demo-result-label">Observed Tool Selection</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginTop: '0.2rem' }}>
                <span
                  className="tool-tag font-mono"
                  style={{
                    fontSize: '1.05rem',
                    fontWeight: 700,
                    color: result.tool_called ? 'var(--accent-green)' : 'var(--accent-amber)',
                    border: result.tool_called ? '1px solid var(--accent-green-border)' : '1px solid var(--accent-amber-border)',
                    padding: '0.25rem 0.65rem',
                  }}
                >
                  {result.tool_called ? result.tool_name : 'none (No Tool)'}
                </span>
                {result.tool_called ? (
                  <Badge variant="success">Native Tool Call</Badge>
                ) : (
                  <Badge variant="warning">Direct Natural Language</Badge>
                )}
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span className="demo-result-label">Model & Latency</span>
              <div className="font-mono" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                {result.model} • {result.duration_ms !== null ? `${result.duration_ms} ms` : 'N/A'}
              </div>
            </div>
          </div>

          {/* Extracted JSON Arguments */}
          <div className="demo-args-section">
            <span className="demo-result-label">Extracted Function Arguments:</span>
            <pre className="demo-args-code font-mono">
              {result.arguments && Object.keys(result.arguments).length > 0
                ? JSON.stringify(result.arguments, null, 2)
                : result.tool_called
                ? '{} (No arguments emitted)'
                : 'null (Model did not invoke a tool)'}
            </pre>
          </div>

          <div className="demo-mechanism-note">
            ⚡ <strong>Mechanism:</strong> This response was generated via local greedy token decoding (<code className="font-mono">temp=0.0</code>) through Ollama's native tool-calling protocol.
          </div>
        </div>
      )}
    </section>
  );
};
