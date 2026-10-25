import React from 'react';

interface NavigationProps {
  mode: 'dashboard' | 'presentation';
  currentStep?: number;
  totalSteps?: number;
  onSelectStep?: (step: number) => void;
}

export const Navigation: React.FC<NavigationProps> = ({
  mode,
  currentStep = 1,
  onSelectStep,
}) => {
  if (mode === 'presentation') {
    const stepNames = [
      'Problem & Question',
      'Controls & Tools',
      'Live Tool Selection',
      'Baseline & Split',
      'Optimization & Diffs',
      'Held-Out Result',
      'Query Transitions',
      'Limitations & Conclusion',
    ];

    return (
      <nav className="dashboard-nav" aria-label="Presentation Stepper Navigation">
        <div className="dashboard-container">
          <div className="nav-links presentation-nav-links">
            {stepNames.map((name, idx) => {
              const stepNum = idx + 1;
              const isActive = stepNum === currentStep;
              return (
                <button
                  key={stepNum}
                  onClick={() => onSelectStep && onSelectStep(stepNum)}
                  className={`nav-link-btn ${isActive ? 'active' : ''}`}
                  type="button"
                >
                  <span className="font-mono">{stepNum}.</span> {name}
                </button>
              );
            })}
          </div>
        </div>
      </nav>
    );
  }

  const navItems = [
    { label: '01. Overview', href: '#project-overview' },
    { label: '02. Workflow', href: '#workflow' },
    { label: '03. Controls', href: '#experimental-controls' },
    { label: '04. Canonical Tools', href: '#tool-catalog' },
    { label: '05. Live Demo', href: '#live-demo' },
    { label: '06. Baseline', href: '#baseline-anchor' },
    { label: '07. Optimization', href: '#optimization' },
    { label: '08. Description Diffs', href: '#descriptions' },
    { label: '09. Held-Out Climax', href: '#held-out-result' },
    { label: '10. Query Transitions', href: '#transitions' },
    { label: '11. Technical Deep Dive', href: '#technical-deep-dive' },
    { label: '12. Limitations', href: '#limitations' },
    { label: '13. Conclusion', href: '#conclusion' },
  ];

  return (
    <nav className="dashboard-nav" aria-label="Dashboard Sections">
      <div className="dashboard-container">
        <div className="nav-links">
          {navItems.map((item) => (
            <a key={item.href} href={item.href} className="nav-link">
              {item.label}
            </a>
          ))}
        </div>
      </div>
    </nav>
  );
};
