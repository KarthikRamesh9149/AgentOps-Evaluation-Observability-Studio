"use client";

import { useEffect, useState } from "react";
import { MetricCard } from "@/components/Cards";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";
import type { Project, Run } from "@/lib/types";

export default function ComparePage() {
  const [projects, setProjects] = useState<Project[]>();
  const [runs, setRuns] = useState<Run[]>([]);
  const [comparison, setComparison] = useState<Record<string, unknown>>();
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    client.projects().then(async (p) => {
      setProjects(p);
      if (p[0]) {
        const r = await client.runs(p[0].project_id);
        setRuns(r);
        if (r.length > 1) setComparison(await client.compareRuns(p[0].project_id, r[1].run_id, r[0].run_id));
      }
    }).catch(setError);
  }, []);
  if (error) return <ErrorState error={error} />;
  if (!projects) return <LoadingState />;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Run Comparison</h1>
      {comparison ? (
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard label="Pass rate delta" value={Number(comparison.pass_rate_delta ?? 0).toFixed(2)} />
          <MetricCard label="Score delta" value={Number(comparison.score_delta ?? 0).toFixed(2)} />
          <MetricCard label="Latency delta" value={`${Math.round(Number(comparison.latency_delta_ms ?? 0))} ms`} />
          <MetricCard label="Regression" value={String(comparison.regression_status)} />
        </div>
      ) : <div className="rounded-md border border-line bg-white p-5 text-sm text-slate-600">Run at least two evaluations to compare prompt, model, and run performance.</div>}
      <div className="rounded-md border border-line bg-white p-5 text-sm">Available runs: {runs.length}</div>
    </div>
  );
}
