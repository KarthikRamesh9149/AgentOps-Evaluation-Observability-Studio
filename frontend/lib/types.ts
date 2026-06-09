export type Project = {
  project_id: string;
  name: string;
  description: string;
  project_type: string;
  tags: string[];
  default_provider: string;
  default_model: string;
};

export type Run = {
  run_id: string;
  project_id: string;
  prompt_id: string;
  prompt_version: number;
  dataset_id: string;
  provider: string;
  model: string;
  status: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  average_score: number;
  pass_rate: number;
  average_latency_ms: number;
  p95_latency_ms: number;
  estimated_cost: number;
  regression_status: string;
  quality_gate_status: string;
};

export type EvalResult = {
  case_id: string;
  input: string;
  output: string;
  passed: boolean;
  failure_category: string;
  severity: string;
  latency_ms: number;
  estimated_cost: number;
  trace_id?: string;
  scores: Record<string, number>;
};

export type Trace = {
  trace_id: string;
  project_id: string;
  run_id?: string;
  name: string;
  app_type: string;
  status: string;
  latency_ms: number;
  estimated_cost: number;
  scores: Record<string, number>;
};

export type Span = {
  span_id: string;
  trace_id: string;
  parent_span_id?: string;
  span_type: string;
  name: string;
  input_summary: string;
  output_summary: string;
  status: string;
  latency_ms: number;
  estimated_cost: number;
};
