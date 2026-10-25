import React, { useState } from 'react';

export interface CanonicalToolInfo {
  name: string;
  description: string;
  parameters: {
    properties: Record<string, { type: string; description: string }>;
    required: string[];
  };
}

export const CANONICAL_TOOLS_DATA: CanonicalToolInfo[] = [
  {
    name: 'search_web',
    description: 'Searches for information.',
    parameters: {
      properties: { query: { type: 'string', description: 'The search query string.' } },
      required: ['query'],
    },
  },
  {
    name: 'search_docs',
    description: 'Looks up information in documents.',
    parameters: {
      properties: { query: { type: 'string', description: 'The query to search internal documentation.' } },
      required: ['query'],
    },
  },
  {
    name: 'read_file',
    description: 'Reads a file.',
    parameters: {
      properties: { path: { type: 'string', description: 'The path of the file to read.' } },
      required: ['path'],
    },
  },
  {
    name: 'write_file',
    description: 'Writes data to a file.',
    parameters: {
      properties: {
        path: { type: 'string', description: 'The path of the file to write.' },
        content: { type: 'string', description: 'The content to write to the file.' },
      },
      required: ['path', 'content'],
    },
  },
  {
    name: 'send_email',
    description: 'Sends a message.',
    parameters: {
      properties: {
        recipient: { type: 'string', description: 'Email address of the recipient.' },
        subject: { type: 'string', description: 'Subject line of the email.' },
        body: { type: 'string', description: 'Body text of the email message.' },
      },
      required: ['recipient', 'subject', 'body'],
    },
  },
  {
    name: 'create_calendar_event',
    description: 'Adds an event.',
    parameters: {
      properties: {
        title: { type: 'string', description: 'Title of the event.' },
        start_time: { type: 'string', description: 'ISO 8601 start time.' },
        duration_minutes: { type: 'integer', description: 'Duration in minutes.' },
      },
      required: ['title', 'start_time'],
    },
  },
  {
    name: 'set_reminder',
    description: 'Sets a reminder.',
    parameters: {
      properties: {
        reminder_text: { type: 'string', description: 'The reminder content.' },
        remind_at: { type: 'string', description: 'ISO 8601 reminder trigger timestamp.' },
      },
      required: ['reminder_text', 'remind_at'],
    },
  },
  {
    name: 'get_weather',
    description: 'Gets weather information.',
    parameters: {
      properties: { location: { type: 'string', description: 'City name or geographical location.' } },
      required: ['location'],
    },
  },
  {
    name: 'calculator',
    description: 'Does math.',
    parameters: {
      properties: { expression: { type: 'string', description: 'Mathematical expression to evaluate.' } },
      required: ['expression'],
    },
  },
  {
    name: 'translate_text',
    description: 'Converts text.',
    parameters: {
      properties: {
        text: { type: 'string', description: 'Text to translate.' },
        target_language: { type: 'string', description: 'Target natural language name.' },
      },
      required: ['text', 'target_language'],
    },
  },
];

export const ToolCatalogGrid: React.FC = () => {
  const [selectedTool, setSelectedTool] = useState<string | null>(null);

  return (
    <section className="card" id="tool-catalog">
      <div className="card-header">
        <div className="card-title-group">
          <h2 className="card-title">The 10 Canonical Tools & Schemas</h2>
          <p className="card-subtitle">
            The fixed catalog of tools that the model must choose between for every user query
          </p>
        </div>
        <span className="badge badge-neutral">10 TOOLS + NONE (11 CLASSES)</span>
      </div>

      <div className="tool-catalog-grid">
        {CANONICAL_TOOLS_DATA.map((tool) => {
          const isSelected = selectedTool === tool.name;
          const paramKeys = Object.keys(tool.parameters.properties);

          return (
            <div
              key={tool.name}
              className={`tool-catalog-card ${isSelected ? 'active-card' : ''}`}
              onClick={() => setSelectedTool(isSelected ? null : tool.name)}
              tabIndex={0}
              role="button"
              aria-label={`Tool ${tool.name}`}
            >
              <div className="tool-card-top">
                <span className="tool-card-name font-mono">{tool.name}</span>
                <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>
                  {paramKeys.length} param{paramKeys.length > 1 ? 's' : ''}
                </span>
              </div>

              <div className="tool-card-desc">"{tool.description}"</div>

              <div className="tool-card-params">
                {paramKeys.map((k) => (
                  <span key={k} className="param-pill font-mono">
                    {k}: {tool.parameters.properties[k].type}
                    {tool.parameters.required.includes(k) && <strong style={{ color: 'var(--accent-amber)' }}>*</strong>}
                  </span>
                ))}
              </div>
            </div>
          );
        })}

        {/* None Card */}
        <div className="tool-catalog-card none-special-card">
          <div className="tool-card-top">
            <span className="tool-card-name font-mono" style={{ color: 'var(--accent-amber)' }}>
              none (11th Class)
            </span>
            <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>
              No Tool
            </span>
          </div>
          <div className="tool-card-desc">
            "No tool required. Assigned to conversational, creative, or theoretical queries."
          </div>
          <div className="tool-card-params">
            <span className="param-pill font-mono" style={{ color: 'var(--text-muted)' }}>
              tool_called: false
            </span>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        * Asterisk indicates required parameter in the locked JSON Schema. Click any card to inspect parameter types.
      </div>
    </section>
  );
};
