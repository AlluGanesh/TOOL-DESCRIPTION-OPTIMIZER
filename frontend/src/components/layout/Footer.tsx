import React from 'react';
import { IntegrityHashes, ExperimentMetadata } from '../../types/results';

interface FooterProps {
  metadata: ExperimentMetadata;
  hashes: IntegrityHashes;
}

export const Footer: React.FC<FooterProps> = ({ metadata, hashes }) => {
  return (
    <footer className="dashboard-footer">
      <div className="dashboard-container footer-content">
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            {metadata.experiment_name}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Evaluating whether LLM-generated tool descriptions improve AI agent tool selection.
          </div>
        </div>

        <div className="footer-hashes">
          <div>
            Canonical Tools SHA: <span style={{ color: 'var(--text-secondary)' }}>{hashes.canonical_tools_hash.slice(0, 10)}...</span>
          </div>
          <div>
            Optimized Tools SHA: <span style={{ color: 'var(--accent-green)' }}>{hashes.optimized_tools_hash.slice(0, 10)}...</span>
          </div>
          <div>
            Held-Out SHA: <span style={{ color: 'var(--text-secondary)' }}>{hashes.held_out_dataset_hash.slice(0, 10)}...</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
