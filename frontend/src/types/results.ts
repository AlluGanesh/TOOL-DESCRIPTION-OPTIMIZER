/**
 * TypeScript definitions for Phase 8/9 verified research results.
 * Matches exact structure in results/final_results.json.
 */

export interface ExperimentMetadata {
  experiment_name: string;
  compiled_at: string;
  model: string;
  temperature: number;
  runs_per_query: number;
  total_tools: number;
  total_classes: number;
  total_queries: number;
  tuning_queries: number;
  held_out_queries: number;
}

export interface ExperimentalControls {
  model_fixed: boolean;
  temperature_fixed: boolean;
  tool_schemas_fixed: boolean;
  parameter_names_fixed: boolean;
  parameter_types_fixed: boolean;
  required_fields_fixed: boolean;
  tool_names_fixed: boolean;
  number_of_tools_fixed: boolean;
  queries_dataset_fixed: boolean;
  only_descriptions_modified: boolean;
}

export interface IntegrityHashes {
  canonical_tools_hash: string;
  optimized_tools_hash: string;
  tuning_dataset_hash: string;
  held_out_dataset_hash: string;
}

export interface SplitAccuracyDetail {
  correct: number;
  total: number;
  accuracy: number;
  accuracy_pct: number;
  errors: number;
}

export interface TuningAccuracySummary {
  baseline: SplitAccuracyDetail;
  optimized: SplitAccuracyDetail;
  absolute_improvement_pp: number;
  relative_improvement_pct: number;
}

export interface HeldOutAccuracySummary {
  baseline: SplitAccuracyDetail;
  optimized: SplitAccuracyDetail;
  absolute_improvement_pp: number;
  relative_improvement_pct: number;
  error_reduction_pct: number;
}

export interface AccuracySummary {
  tuning: TuningAccuracySummary;
  held_out: HeldOutAccuracySummary;
}

export interface QueryTransitionCounts {
  remained_correct: number;
  became_correct: number;
  became_incorrect: number;
  remained_incorrect: number;
  remained_correct_ids: string[];
  became_correct_ids: string[];
  became_incorrect_ids: string[];
  remained_incorrect_ids: string[];
}

export interface RoundAccuracyItem {
  round: number;
  accuracy: number;
  status: string;
}

export interface OptimizationRoundsSummary {
  total_rounds: number;
  accepted_rounds: number;
  best_round: number;
  stop_reason: string;
  round_accuracies: RoundAccuracyItem[];
}

export interface ToolMetricScores {
  precision: number;
  recall: number;
  f1_score: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
}

export interface ToolClassMetric {
  tool: string;
  actual_count: number;
  baseline: ToolMetricScores;
  optimized: ToolMetricScores;
  f1_delta: number;
}

export interface ConfusionMatrixBundle {
  baseline: Record<string, Record<string, number>>;
  optimized: Record<string, Record<string, number>>;
  label_order: string[];
}

export interface ToolDescriptionDiff {
  tool_name: string;
  original_description: string;
  optimized_description: string;
  changed: boolean;
  nature_of_change: string;
}

export type QueryTransitionType =
  | 'remained_correct'
  | 'became_correct'
  | 'became_incorrect'
  | 'remained_incorrect';

export interface HeldOutQueryDetail {
  query_id: string;
  query: string;
  expected_tool: string;
  difficulty: string;
  notes: string;
  baseline_prediction: string;
  baseline_correct: boolean;
  optimized_prediction: string;
  optimized_correct: boolean;
  transition: QueryTransitionType;
}

export interface FinalResultsData {
  metadata: ExperimentMetadata;
  experimental_controls: ExperimentalControls;
  integrity_hashes: IntegrityHashes;
  accuracy_summary: AccuracySummary;
  query_transition_counts: QueryTransitionCounts;
  optimization_rounds_summary: OptimizationRoundsSummary;
  per_tool_metrics: Record<string, ToolClassMetric>;
  confusion_matrices: ConfusionMatrixBundle;
  tool_description_diffs: ToolDescriptionDiff[];
  held_out_query_details: HeldOutQueryDetail[];
}
