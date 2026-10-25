export interface BackendHealth {
  status: string;
}

export interface ToolProperty {
  type: string;
  description: string;
}

export interface ToolParameters {
  type: string;
  properties: Record<string, ToolProperty>;
  required: string[];
}

export interface BackendToolDefinition {
  name: string;
  description: string;
  parameters: ToolParameters;
}

export interface BackendConnectionState {
  isChecking: boolean;
  isConnected: boolean;
  version?: string;
  endpoint: string;
  errorMessage?: string;
}

export interface ToolSelectionResponse {
  tool_called: boolean;
  tool_name: string | null;
  arguments: Record<string, unknown> | null;
  model: string;
  raw_response?: string | null;
  duration_ms?: number | null;
}
