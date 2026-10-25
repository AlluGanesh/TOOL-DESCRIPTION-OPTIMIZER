import React, { useEffect, useState } from 'react';
import { DataService } from './services/apiService';
import { FinalResultsData } from './types/results';

import { Header } from './components/layout/Header';
import { Navigation } from './components/layout/Navigation';
import { Footer } from './components/layout/Footer';

// Story Components (Phase 11)
import { ProjectProblemHero } from './components/story/ProjectProblemHero';
import { ExperimentWorkflowDiagram } from './components/story/ExperimentWorkflowDiagram';
import { LockedVsOptimizableCard } from './components/story/LockedVsOptimizableCard';
import { ToolCatalogGrid } from './components/story/ToolCatalogGrid';
import { BaselineExperimentCard } from './components/story/BaselineExperimentCard';
import { TechnicalDeepDive } from './components/story/TechnicalDeepDive';

// Interactive Live Demo (Phase 11)
import { LiveToolSelectionDemo } from './components/demo/LiveToolSelectionDemo';

// Presentation Stepper & Controls (Phase 11)
import { PresentationControls } from './components/presentation/PresentationControls';

// Verified Research Visualization Components (Phase 9/10)
import { AccuracyComparison } from './components/evaluation/AccuracyComparison';
import { HeldOutSummary } from './components/evaluation/HeldOutSummary';
import { QueryTransitions } from './components/evaluation/QueryTransitions';
import { ToolDescriptionDiffTable } from './components/tools/ToolDescriptionDiffTable';
import { OptimizationJourney } from './components/optimization/OptimizationJourney';
import { LimitationsCard } from './components/conclusion/LimitationsCard';
import { ScientificConclusionCard } from './components/conclusion/ScientificConclusionCard';

export const App: React.FC = () => {
  const [data, setData] = useState<FinalResultsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

  // Presentation Mode State
  const [mode, setMode] = useState<'dashboard' | 'presentation'>('dashboard');
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [showSpeakerNotes, setShowSpeakerNotes] = useState<boolean>(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Load verified final experimental results from public/data/final_results.json
      const results = await DataService.getFinalResults();
      setData(results);

      // 2. Check live backend connectivity
      const health = await DataService.checkBackendHealth();
      setBackendConnected(health !== null && health.status === 'ok');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Global Keyboard Navigation (Guarded against active input/textarea typing)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable)
      ) {
        return;
      }

      if (e.key === 'Escape') {
        if (mode === 'presentation') {
          setMode('dashboard');
        }
      } else if (e.key === 'n' || e.key === 'N') {
        setShowSpeakerNotes((prev) => !prev);
      } else if (e.key === 'ArrowRight') {
        if (mode === 'presentation') {
          setCurrentStep((prev) => Math.min(prev + 1, 8));
        }
      } else if (e.key === 'ArrowLeft') {
        if (mode === 'presentation') {
          setCurrentStep((prev) => Math.max(prev - 1, 1));
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mode]);

  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner"></div>
        <h2 style={{ fontSize: '1.25rem', marginTop: '1rem' }}>
          Loading Research Artifacts...
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Reading verified experimental dataset from results/final_results.json
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="state-container">
        <div
          style={{
            maxWidth: '550px',
            background: 'var(--bg-card)',
            border: '1px solid var(--accent-red-border)',
            borderRadius: '12px',
            padding: '2rem',
            textAlign: 'left',
          }}
        >
          <span className="badge badge-error" style={{ marginBottom: '0.75rem' }}>
            FAILED TO LOAD EXPERIMENT RESULTS
          </span>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: '#f87171' }}>
            Research Dataset Unavailable
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
            {error || 'No research data was returned.'}
          </p>
          <button
            className="filter-btn active"
            onClick={loadData}
            style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', cursor: 'pointer' }}
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-app">
      <Header
        backendConnected={backendConnected}
        compiledAt={data.metadata.compiled_at}
        mode={mode}
        onToggleMode={() => {
          setMode(mode === 'dashboard' ? 'presentation' : 'dashboard');
        }}
        showSpeakerNotes={showSpeakerNotes}
        onToggleSpeakerNotes={() => setShowSpeakerNotes(!showSpeakerNotes)}
      />

      {/* Navigation Bar */}
      <Navigation
        mode={mode}
        currentStep={currentStep}
        totalSteps={8}
        onSelectStep={(step) => setCurrentStep(step)}
      />

      {/* Presentation Mode Stepper & Speaker Prompter */}
      {mode === 'presentation' && (
        <PresentationControls
          currentStep={currentStep}
          totalSteps={8}
          onPrev={() => setCurrentStep((prev) => Math.max(prev - 1, 1))}
          onNext={() => setCurrentStep((prev) => Math.min(prev + 1, 8))}
          onSelectStep={(s) => setCurrentStep(s)}
          onExit={() => setMode('dashboard')}
          showSpeakerNotes={showSpeakerNotes}
          onToggleSpeakerNotes={() => setShowSpeakerNotes(!showSpeakerNotes)}
        />
      )}

      <main className="dashboard-container dashboard-main">
        {mode === 'presentation' ? (
          /* ===============================================================
             PRESENTATION MODE (8 GUIDED STEPS FOR INTERVIEWERS)
             =============================================================== */
          <div className="presentation-step-view">
            {/* Step 1: Problem & Research Question */}
            {currentStep === 1 && (
              <div>
                <ProjectProblemHero />
              </div>
            )}

            {/* Step 2: Experimental Controls & Tools */}
            {currentStep === 2 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <LockedVsOptimizableCard />
                <ToolCatalogGrid />
              </div>
            )}

            {/* Step 3: Live Native Tool Selection */}
            {currentStep === 3 && (
              <div>
                <LiveToolSelectionDemo backendConnected={backendConnected} />
              </div>
            )}

            {/* Step 4: Baseline & Dataset Split */}
            {currentStep === 4 && (
              <div>
                <BaselineExperimentCard accuracy={data.accuracy_summary} />
              </div>
            )}

            {/* Step 5: Optimization & Description Changes */}
            {currentStep === 5 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <OptimizationJourney summary={data.optimization_rounds_summary} />
                <ToolDescriptionDiffTable diffs={data.tool_description_diffs} />
              </div>
            )}

            {/* Step 6: Held-Out Result Climax */}
            {currentStep === 6 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <HeldOutSummary summary={data.accuracy_summary.held_out} />
                <AccuracyComparison accuracy={data.accuracy_summary} />
              </div>
            )}

            {/* Step 7: Query Transitions */}
            {currentStep === 7 && (
              <div>
                <QueryTransitions
                  counts={data.query_transition_counts}
                  queries={data.held_out_query_details}
                />
              </div>
            )}

            {/* Step 8: Limitations & Conclusion */}
            {currentStep === 8 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <LimitationsCard />
                <ScientificConclusionCard />
              </div>
            )}
          </div>
        ) : (
          /* ===============================================================
             FULL DASHBOARD MODE (ALL 13 NARRATIVE SECTIONS)
             =============================================================== */
          <>
            {/* 01. What is this project? */}
            <ProjectProblemHero />

            {/* 02. How does it work? 11-step pipeline */}
            <ExperimentWorkflowDiagram />

            {/* 03. What is fixed vs. what changes? */}
            <LockedVsOptimizableCard />

            {/* 04. The 10 canonical tools & schemas */}
            <ToolCatalogGrid />

            {/* 05. Live Native Tool Selection Demo */}
            <LiveToolSelectionDemo backendConnected={backendConnected} />

            {/* 06. Baseline Experiment Anchor */}
            <BaselineExperimentCard accuracy={data.accuracy_summary} />

            {/* 07. Optimization Journey (Rounds 0-3) */}
            <OptimizationJourney summary={data.optimization_rounds_summary} />

            {/* 08. Before vs After Description Diffs */}
            <ToolDescriptionDiffTable diffs={data.tool_description_diffs} />

            {/* 09. Controlled Held-Out Evaluation (Visual Climax: 73.33% -> 80.00%) */}
            <HeldOutSummary summary={data.accuracy_summary.held_out} />
            <AccuracyComparison accuracy={data.accuracy_summary} />

            {/* 10. Query Transitions Breakdown (Q014 case study) */}
            <QueryTransitions
              counts={data.query_transition_counts}
              queries={data.held_out_query_details}
            />

            {/* 11. Technical Deep Dive (Confusion Matrices, Per-tool metrics, Provenance, Architecture) */}
            <TechnicalDeepDive
              confusionMatrices={data.confusion_matrices}
              perToolMetrics={data.per_tool_metrics}
              integrityHashes={data.integrity_hashes}
            />

            {/* 12. Limitations & Threats to Validity */}
            <LimitationsCard />

            {/* 13. Final Formal Scientific Conclusion */}
            <ScientificConclusionCard />
          </>
        )}
      </main>

      <Footer metadata={data.metadata} hashes={data.integrity_hashes} />
    </div>
  );
};

export default App;
