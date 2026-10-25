import React from 'react';

export interface PresentationStepInfo {
  number: number;
  title: string;
  category: string;
  whatToSay: string;
  whyItMatters: string;
  avoid: string;
}

export const PRESENTATION_STEPS: PresentationStepInfo[] = [
  {
    number: 1,
    title: 'Problem & Research Question',
    category: 'Foundation',
    whatToSay:
      'This project studies whether improving only the natural-language descriptions of tools can make an LLM better at choosing the correct tool.',
    whyItMatters:
      'The goal is to isolate the effect of tool descriptions rather than changing the model itself.',
    avoid:
      'Do not describe this as an autonomous agent that executes arbitrary actions.',
  },
  {
    number: 2,
    title: 'Experimental Controls & Tools',
    category: 'Setup',
    whatToSay:
      'To ensure a controlled experiment, model weights, tool names, schemas, and parameter types were locked byte-for-byte. Only the description text was allowed to change.',
    whyItMatters:
      'In production, parameter schemas represent established API contracts that cannot easily be rewritten.',
    avoid:
      'Do not say the tool schemas were optimized.',
  },
  {
    number: 3,
    title: 'Live Native Tool Selection',
    category: 'Mechanism',
    whatToSay:
      'Here we demonstrate native tool calling via local Ollama. The model receives the 10 tool schemas and emits structured tool calls directly from token probabilities.',
    whyItMatters:
      'Demonstrating live function calling proves that tool selection occurs natively rather than via text scraping.',
    avoid:
      'Do not present live demo runs as benchmark accuracy measurements.',
  },
  {
    number: 4,
    title: 'Baseline & Dataset Split',
    category: 'Baseline',
    whatToSay:
      'The benchmark uses 50 queries: 35 for tuning and 15 strictly held out. Baseline accuracy was 80.00% on tuning and 73.33% on held-out.',
    whyItMatters:
      'Separating tuning from held-out prevents claiming training adaptation as true generalization.',
    avoid:
      'Do not refer to the 15 held-out queries as production or real-world data.',
  },
  {
    number: 5,
    title: 'Optimization & Description Changes',
    category: 'Optimization',
    whatToSay:
      'The optimizer analyzed tuning mistakes and generated refined descriptions that passed strict guardrails: under 40 words and 4-gram copy prevention. Round 1 improved tuning accuracy to 85.71% and was accepted.',
    whyItMatters:
      'Strict guardrails ensure the model does not memorize benchmark query text.',
    avoid:
      'Do not claim that we know the internal cognitive mechanism of the optimizer.',
  },
  {
    number: 6,
    title: 'Held-Out Generalization Result',
    category: 'Primary Evidence',
    whatToSay:
      'The optimization reached 85.71% on the tuning set, but the important result is the held-out evaluation. On 15 benchmark queries that were not used during optimization, accuracy improved from 73.33% to 80.00%.',
    whyItMatters:
      'The held-out set provides the evidence for whether the improvement extends beyond the queries used for optimization.',
    avoid:
      'Do not present 85.71% as the final generalization result.',
  },
  {
    number: 7,
    title: 'Query Transitions & Case Studies',
    category: 'Analysis',
    whatToSay:
      'On the held-out set, Q014 transitioned from an incorrect none prediction to the correct read_file prediction. Crucially, zero previously correct queries regressed.',
    whyItMatters:
      'Measuring regressions is essential in ML systems to ensure gains do not introduce catastrophic forgetting.',
    avoid:
      'Do not claim that we know why the model internally changed its token activations for Q014.',
  },
  {
    number: 8,
    title: 'Limitations & Scientific Conclusion',
    category: 'Conclusion',
    whatToSay:
      'The experiment provides evidence of improvement on this benchmark with one model and 15 held-out queries. We do not claim universal generalization across all LLMs.',
    whyItMatters:
      'Scientific honesty and recognizing methodological limitations strengthens technical credibility.',
    avoid:
      'Do not use words like "proved", "guaranteed", or "universal".',
  },
];

interface PresentationControlsProps {
  currentStep: number;
  totalSteps: number;
  onPrev: () => void;
  onNext: () => void;
  onSelectStep: (step: number) => void;
  onExit: () => void;
  showSpeakerNotes: boolean;
  onToggleSpeakerNotes: () => void;
}

export const PresentationControls: React.FC<PresentationControlsProps> = ({
  currentStep,
  totalSteps,
  onPrev,
  onNext,
  onSelectStep,
  onExit,
  showSpeakerNotes,
  onToggleSpeakerNotes,
}) => {
  const currentStepData = PRESENTATION_STEPS[currentStep - 1];

  return (
    <div className="presentation-controls-wrapper">
      {/* Top Stepper Bar */}
      <div className="presentation-stepper-bar">
        <div className="stepper-meta-group">
          <span className="badge badge-success" style={{ fontSize: '0.72rem' }}>
            PRESENTATION MODE
          </span>
          <span className="stepper-step-indicator font-mono">
            Step {currentStep} of {totalSteps}: <strong>{currentStepData.title}</strong>
          </span>
        </div>

        {/* Step Dots */}
        <div className="stepper-dots-row">
          {PRESENTATION_STEPS.map((s) => (
            <button
              key={s.number}
              className={`stepper-dot ${s.number === currentStep ? 'active' : s.number < currentStep ? 'completed' : ''}`}
              onClick={() => onSelectStep(s.number)}
              title={`Step ${s.number}: ${s.title}`}
              type="button"
            >
              {s.number}
            </button>
          ))}
        </div>

        {/* Navigation Actions */}
        <div className="stepper-actions-group">
          <button
            className={`notes-toggle-btn ${showSpeakerNotes ? 'active' : ''}`}
            onClick={onToggleSpeakerNotes}
            title="Toggle Speaker Notes (Press 'N')"
            type="button"
          >
            📝 Notes {showSpeakerNotes ? 'ON' : 'OFF'}
          </button>

          <button
            className="stepper-nav-btn font-mono"
            onClick={onPrev}
            disabled={currentStep === 1}
            title="Previous Step (Left Arrow)"
            type="button"
          >
            ← Prev
          </button>

          <button
            className="stepper-nav-btn font-mono next-btn"
            onClick={onNext}
            disabled={currentStep === totalSteps}
            title="Next Step (Right Arrow)"
            type="button"
          >
            Next →
          </button>

          <button
            className="exit-presentation-btn"
            onClick={onExit}
            title="Exit Presentation Mode (Press Escape)"
            type="button"
          >
            ✕ Exit
          </button>
        </div>
      </div>

      {/* Speaker Notes Drawer */}
      {showSpeakerNotes && currentStepData && (
        <aside className="speaker-notes-drawer" aria-label="Speaker Prompter Notes">
          <div className="notes-header">
            <span className="notes-badge">🎙️ SPEAKER PROMPTER — STEP {currentStep}: {currentStepData.title}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Press 'N' to hide</span>
          </div>

          <div className="notes-body-grid">
            <div className="notes-section">
              <span className="notes-section-label">🗣️ What to Say:</span>
              <p className="notes-text say-text">"{currentStepData.whatToSay}"</p>
            </div>

            <div className="notes-section">
              <span className="notes-section-label">💡 Why It Matters:</span>
              <p className="notes-text why-text">{currentStepData.whyItMatters}</p>
            </div>

            <div className="notes-section">
              <span className="notes-section-label">⚠️ Trap to Avoid:</span>
              <p className="notes-text avoid-text">{currentStepData.avoid}</p>
            </div>
          </div>
        </aside>
      )}
    </div>
  );
};
