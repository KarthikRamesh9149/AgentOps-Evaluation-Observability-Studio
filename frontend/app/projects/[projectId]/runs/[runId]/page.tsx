"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { MetricCard, StatusBadge } from "@/components/Cards";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";
import type { EvalResult, Run } from "@/lib/types";

export default function RunDetailPage() {
  const { projectId, runId } = useParams<{ projectId: string; runId: string }>();
  const [run, setRun] = useState<Run>();
  const [results, setResults] = useState<EvalResult[]>([]);
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    Promise.all([client.run(projectId, runId), client.results(projectId, runId)])
      .then(([r, res]) => { setRun(r); setResults(res); })
      .catch(setError);
  }, [projectId, runId]);
  if (error) return <ErrorState error={error} />;
  if (!run) return <LoadingState />;
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Run {run.run_id}</h1>
        <StatusBadge value={run.quality_gate_status} />
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Pass rate" value={`${Math.round(run.pass_rate * 100)}%`} />
        <MetricCard label="Average score" value={run.average_score.toFixed(2)} />
        <MetricCard label="p95 latency" value={`${Math.round(run.p95_latency_ms)} ms`} />
        <MetricCard label="Estimated cost" value={`$${run.estimated_cost.toFixed(6)}`} />
      </div>
      <DataTable rows={results} columns={[
        { header: "Case", cell: (r) => r.case_id },
        { header: "Passed", cell: (r) => <StatusBadge value={r.passed ? "pass" : "fail"} /> },
        { header: "Failure", cell: (r) => r.failure_category },
        { header: "Latency", cell: (r) => `${r.latency_ms} ms` },
        { header: "Trace", cell: (r) => r.trace_id ? <Link className="text-accent" href={`/projects/${projectId}/traces/${r.trace_id}`}>Open trace</Link> : "None" },
        { header: "Output", cell: (r) => <span className="line-clamp-3 text-slate-600">{r.output}</span> }
      ]} />
    </div>
  );
}
