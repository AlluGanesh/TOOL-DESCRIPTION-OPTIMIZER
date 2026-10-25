import React from 'react';

export const ScientificConclusionCard: React.FC = () => {
  return (
    <div className="conclusion-card" id="conclusion">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
        <span className="badge badge-success" style={{ fontSize: '0.85rem' }}>
          FORMAL SCIENTIFIC CONCLUSION
        </span>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Phase 8 & 9 Peer Audit
        </span>
      </div>

      <div className="conclusion-quote">
        "The controlled held-out experiment provides evidence that optimizing tool descriptions alone improved tool-selection accuracy from 73.33% to 80.00% (+6.67 percentage points, +9.09% relative) on the 15 unseen benchmark queries, with zero regressions among previously correct queries."
      </div>

      <div className="conclusion-caveat">
        "Because the evaluation used only one model, one deterministic run, and 15 held-out queries, this result should be interpreted as evidence of improvement on this benchmark rather than proof of universal generalization."
      </div>
    </div>
  );
};
