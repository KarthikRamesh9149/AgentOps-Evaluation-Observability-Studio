import type { EvalResult, Project, Run, Span, Trace } from "./types";

const API_BASE = "/api/backend";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const client = {
  health: () => api<{ status: string; provider: string }>("/health"),
  projects: () => api<Project[]>("/projects"),
  createProject: (payload: Partial<Project>) => api<Project>("/projects", { method: "POST", body: JSON.stringify(payload) }),
  project: (id: string) => api<Project>(`/projects/${id}`),
  prompts: (projectId: string) => api<unknown[]>(`/projects/${projectId}/prompts`),
  datasets: (projectId: string) => api<unknown[]>(`/projects/${projectId}/datasets`),
  runs: (projectId: string) => api<Run[]>(`/projects/${projectId}/runs`),
  run: (projectId: string, runId: string) => api<Run>(`/projects/${projectId}/runs/${runId}`),
  results: (projectId: string, runId: string) => api<EvalResult[]>(`/projects/${projectId}/runs/${runId}/results`),
  metrics: (projectId: string, runId: string) => api<Record<string, unknown>>(`/projects/${projectId}/runs/${runId}/metrics`),
  startRun: (projectId: string) =>
    api<Run>(`/projects/${projectId}/runs`, {
      method: "POST",
      body: JSON.stringify({ prompt_id: "support-agent", prompt_version: 1, dataset_id: "prompt-regression-eval", provider: "mock", model: "mock-enterprise-eval" })
    }),
  compareRuns: (projectId: string, runA: string, runB: string) =>
    api<Record<string, unknown>>(`/projects/${projectId}/compare-runs`, { method: "POST", body: JSON.stringify({ run_a: runA, run_b: runB }) }),
  traces: (projectId: string) => api<Trace[]>(`/projects/${projectId}/traces`),
  trace: (projectId: string, traceId: string) => api<Trace>(`/projects/${projectId}/traces/${traceId}`),
  spans: (projectId: string, traceId: string) => api<Span[]>(`/projects/${projectId}/traces/${traceId}/spans`),
  observability: (projectId: string) => api<Record<string, unknown>>(`/projects/${projectId}/observability/summary`),
  failures: (projectId: string) => api<Record<string, number>>(`/projects/${projectId}/observability/failures`),
  reviews: (projectId: string) => api<unknown[]>(`/projects/${projectId}/reviews`),
  reports: (projectId: string) => api<unknown[]>(`/projects/${projectId}/reports`),
  settingsProviders: () => api<Record<string, unknown>>("/settings/providers"),
  settingsEvaluators: () => api<unknown[]>("/settings/evaluators")
};
