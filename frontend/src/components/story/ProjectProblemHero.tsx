import React from 'react';

export const ProjectProblemHero: React.FC = () => {
  return (
    <section className="card story-hero-card" id="project-overview">
      <div className="hero-badge-row">
        <span className="badge badge-success">RESEARCH BENCHMARK</span>
        <span className="badge badge-blue">AGENT TOOL ROUTING</span>
      </div>

      <h1 className="story-hero-title">
        Can better tool descriptions make an LLM choose the right tool?
      </h1>
      <p className="story-hero-subtitle">
        Evaluating whether natural-language tool description optimization alone improves native tool selection while keeping the model, tool names, parameters, and schemas fixed.
      </p>

      {/* Conceptual Flow Diagram */}
      <div className="routing-flow-diagram" aria-label="Conceptual Tool Routing Flow">
        <div className="flow-step">
          <div className="flow-step-number">STEP 1</div>
          <div className="flow-step-box user-query-box">
            <span className="flow-icon">💬</span>
            <span className="flow-box-title">User Query</span>
            <span className="flow-box-sub">"Check /etc/hosts for db alias"</span>
          </div>
        </div>

        <div className="flow-arrow">➔</div>

        <div className="flow-step">
          <div className="flow-step-number">STEP 2</div>
          <div className="flow-step-box model-box">
            <span className="flow-icon">🧠</span>
            <span className="flow-box-title">Local LLM</span>
            <span className="flow-box-sub font-mono">qwen2.5:3b (temp=0.0)</span>
          </div>
        </div>

        <div className="flow-arrow">➔</div>

        <div className="flow-step">
          <div className="flow-step-number">STEP 3</div>
          <div className="flow-step-box native-call-box">
            <span className="flow-icon">⚡</span>
            <span className="flow-box-title">Native Tool Calling</span>
            <span className="flow-box-sub">Ollama Function Binding</span>
          </div>
        </div>

        <div className="flow-arrow">➔</div>

        <div className="flow-step">
          <div className="flow-step-number">OUTCOME</div>
          <div className="flow-step-box decision-box">
            <span className="flow-icon">🎯</span>
            <span className="flow-box-title">Tool Selection</span>
            <span className="flow-box-sub font-mono">1 of 10 Tools / none</span>
          </div>
        </div>
      </div>

      {/* Core Principle Cards */}
      <div className="core-principles-grid">
        <div className="principle-card">
          <div className="principle-number">01</div>
          <div className="principle-title">Receives the Query</div>
          <p className="principle-desc">
            The model receives an unstructured operational request from a user or upstream workflow.
          </p>
        </div>
        <div className="principle-card">
          <div className="principle-number">02</div>
          <div className="principle-title">Inspects Available Tools</div>
          <p className="principle-desc">
            The model is provided with 10 canonical tool definitions and their natural-language descriptions.
          </p>
        </div>
        <div className="principle-card">
          <div className="principle-number">03</div>
          <div className="principle-title">Selects Appropriate Tool</div>
          <p className="principle-desc">
            The model emits a native tool call (or decides no tool is required, predicting <code className="font-mono">none</code>).
          </p>
        </div>
        <div className="principle-card">
          <div className="principle-number">04</div>
          <div className="principle-title">Evaluates Accuracy</div>
          <p className="principle-desc">
            The experiment objectively scores whether that selection matches the ground-truth benchmark label.
          </p>
        </div>
      </div>

      <div className="agentic-boundary-notice">
        <strong>Research Scope Notice:</strong> This project investigates <em>tool selection and routing</em> in agent workflows. It is NOT a chatbot, autonomous coding agent, or general-purpose execution system. It isolates and measures the decision-making step of native tool selection.
      </div>
    </section>
  );
};
