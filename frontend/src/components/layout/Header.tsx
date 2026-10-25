import React from 'react';

interface HeaderProps {
  backendConnected: boolean | null;
  compiledAt: string;
  mode: 'dashboard' | 'presentation';
  onToggleMode: () => void;
  showSpeakerNotes?: boolean;
  onToggleSpeakerNotes?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  backendConnected,
  compiledAt,
  mode,
  onToggleMode,
  showSpeakerNotes,
  onToggleSpeakerNotes,
}) => {
  return (
    <header className="dashboard-header">
      <div className="dashboard-container header-content">
        <div className="brand-section">
          <div className="brand-logo-icon">TDO</div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="brand-title">Tool Description Optimizer</span>
              <span className="brand-badge">RESEARCH v1.0</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Controlled Generalization Evaluation • Compiled {new Date(compiledAt).toLocaleDateString()}
            </div>
          </div>
        </div>

        <div className="header-meta">
          {/* Mode Switcher Button */}
          <div className="mode-switcher-group">
            <button
              className={`mode-btn ${mode === 'dashboard' ? 'active' : ''}`}
              onClick={mode === 'presentation' ? onToggleMode : undefined}
              type="button"
              title="Full Dashboard (Exploration & Deep Dive)"
            >
              📊 Full Dashboard
            </button>
            <button
              className={`mode-btn ${mode === 'presentation' ? 'active' : ''}`}
              onClick={mode === 'dashboard' ? onToggleMode : undefined}
              type="button"
              title="Presentation Mode (8-Step Interview Stepper)"
            >
              🎙️ Presentation Mode
            </button>
          </div>

          {mode === 'presentation' && onToggleSpeakerNotes && (
            <button
              className={`mode-btn notes-header-btn ${showSpeakerNotes ? 'active-notes' : ''}`}
              onClick={onToggleSpeakerNotes}
              type="button"
              title="Toggle Speaker Prompter Notes (Press 'N')"
            >
              📝 Notes {showSpeakerNotes ? 'ON' : 'OFF'}
            </button>
          )}

          <div
            className="backend-indicator"
            title={
              backendConnected
                ? 'Connected to local FastAPI backend (http://localhost:8000)'
                : 'Using verified standalone research artifact (results/final_results.json)'
            }
          >
            <span
              className={`pulse-dot ${backendConnected ? '' : 'offline'}`}
            ></span>
            <span>
              {backendConnected === null
                ? 'Checking API...'
                : backendConnected
                ? 'FastAPI v1.0 Connected'
                : 'Artifact Mode (Verified)'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
