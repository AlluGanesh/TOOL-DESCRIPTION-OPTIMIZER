import { BackendHealth, BackendToolDefinition, ToolSelectionResponse } from '../types/api';
import { FinalResultsData } from '../types/results';

export class DataService {
  /**
   * Fetches the verified experimental results from the static/persisted data endpoint.
   */
  static async getFinalResults(): Promise<FinalResultsData> {
    try {
      const response = await fetch('/data/final_results.json', {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
        },
      });

      if (!response.ok) {
        throw new Error(
          `Failed to load research results: HTTP ${response.status} ${response.statusText}`
        );
      }

      const data = (await response.json()) as FinalResultsData;
      
      // Basic schema assertion
      if (!data.metadata || !data.accuracy_summary || !data.held_out_query_details) {
        throw new Error('Malformed results dataset: missing core sections.');
      }

      return data;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      throw new Error(`Data loading error: ${message}`);
    }
  }

  /**
   * Checks live backend API health status.
   */
  static async checkBackendHealth(): Promise<BackendHealth | null> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);

      const response = await fetch('/health', {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        return null;
      }
      return (await response.json()) as BackendHealth;
    } catch {
      return null;
    }
  }

  /**
   * Fetches canonical tool definitions from live backend REST route if available.
   */
  static async getCanonicalTools(): Promise<BackendToolDefinition[] | null> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);

      const response = await fetch('/api/tools', {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        return null;
      }
      return (await response.json()) as BackendToolDefinition[];
    } catch {
      return null;
    }
  }

  /**
   * Executes live native tool selection via POST /api/tools/select
   */
  static async selectToolLive(query: string): Promise<ToolSelectionResponse> {
    const response = await fetch('/api/tools/select', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Live tool selection failed: HTTP ${response.status} ${response.statusText}`);
    }

    return (await response.json()) as ToolSelectionResponse;
  }
}
