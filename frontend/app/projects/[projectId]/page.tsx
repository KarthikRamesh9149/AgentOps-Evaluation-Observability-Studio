"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { MetricCard, StatusBadge } from "@/components/Cards";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";
import type { Project, Run } from "@/lib/types";

export default function ProjectDashboard() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project>();
  const [runs, setRuns] = useState<Run[]>([]);
  const [prompts, setPrompts] = useState<unknown[]>([]);
  const [datasets, setDatasets] = useState<unknown[]>([]);
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    Promise.all([client.project(projectId), client.runs(projectId), client.prompts(projectId), client.datasets(projectId)])
      .then(([p, r, pr, d]) => { setProject(p); setRuns(r); setPrompts(pr); setDatasets(d); })
      .catch(setError);
  }, [projectId]);
  async function startRun() {
    const run = await client.startRun(projectId);
    setRuns([run, ...runs]);
  }
  if (error) return <ErrorState error={error} />;
  if (!project) return <LoadingState />;
  const latest = runs[0];
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{project.name}</h1>
          <p className="mt-1 text-sm text-slate-600">{project.description}</p>
        </div>
        <button onClick={startRun} className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white">Run mock eval</button>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Datasets" value={datasets.length} />
        <MetricCard label="Prompt versions" value={prompts.length} />
        <MetricCard label="Runs" value={runs.length} />
        <MetricCard label="Latest pass rate" value={latest ? `${Math.round(latest.pass_rate * 100)}%` : "No runs"} />
      </div>
      <DataTable rows={runs.slice(0, 8)} columns={[
        { header: "Run", cell: (r) => <Link className="font-medium text-accent" href={`/projects/${projectId}/runs/${r.run_id}`}>{r.run_id}</Link> },
        { header: "Status", cell: (r) => <StatusBadge value={r.status} /> },
        { header: "Pass rate", cell: (r) => `${Math.round(r.pass_rate * 100)}%` },
        { header: "Score", cell: (r) => r.average_score.toFixed(2) },
        { header: "p95", cell: (r) => `${Math.round(r.p95_latency_ms)} ms` },
        { header: "Gate", cell: (r) => <StatusBadge value={r.quality_gate_status} /> }
      ]} />
    </div>
  );
}
