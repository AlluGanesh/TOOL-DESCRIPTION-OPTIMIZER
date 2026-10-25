import React from 'react';
import { ExperimentMetadata } from '../../types/results';

interface ExperimentConfigCardProps {
  metadata: ExperimentMetadata;
}

export const ExperimentConfigCard: React.FC<ExperimentConfigCardProps> = ({ metadata }) => {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">Experimental Configuration</h2>
          <p className="card-subtitle">Controlled laboratory benchmark settings</p>
        </div>
        <span className="badge badge-neutral">FROZEN CONTROLS</span>
      </div>

      <div className="config-grid">
        <div className="config-item">
          <span className="config-label">Base Model</span>
          <span className="config-value">{metadata.model}</span>
        </div>
        <div className="config-item">
          <span className="config-label">Sampling Temperature</span>
          <span className="config-value">{metadata.temperature.toFixed(1)}</span>
        </div>
        <div className="config-item">
          <span className="config-label">Runs Per Query</span>
          <span className="config-value">{metadata.runs_per_query}</span>
        </div>
        <div className="config-item">
          <span className="config-label">Total Queries</span>
          <span className="config-value">{metadata.total_queries}</span>
        </div>
        <div className="config-item">
          <span className="config-label">Tuning Queries</span>
          <span className="config-value">{metadata.tuning_queries}</span>
        </div>
        <div className="config-item">
          <span className="config-label">Held-Out Queries</span>
          <span className="config-value">{metadata.held_out_queries}</span>
        </div>
        <div className="config-item">
          <span className="config-label">Routing Classes</span>
          <span className="config-value">{metadata.total_classes}</span>
        </div>
        <div className="config-item">
          <span className="config-label">Fixed Tools</span>
          <span className="config-value">{metadata.total_tools} + none</span>
        </div>
      </div>

      <div className="config-highlight-box">
        <strong>Strict Control:</strong> The model and tool schemas were held constant. Only tool descriptions were optimized.
      </div>
    </div>
  );
};
