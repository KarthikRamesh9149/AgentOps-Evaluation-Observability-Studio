"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { MetricCard, StatusBadge } from "@/components/Cards";
import { EmptyState, ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";
import type { Project, Run } from "@/lib/types";

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>();
  const [runs, setRuns] = useState<Run[]>([]);
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    client.projects().then(async (items) => {
      setProjects(items);
      if (items[0]) setRuns(await client.runs(items[0].project_id));
    }).catch(setError);
  }, []);
  if (error) return <ErrorState error={error} />;
  if (!projects) return <LoadingState />;
  const latest = runs[0];
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-normal">AgentOps Evaluation & Observability Studio</h1>
        <p className="mt-2 max-w-3xl text-slate-600">Local-first evaluation projects, prompt versions, datasets, mock/OpenAI providers, traces, quality gates, reviews, and exportable reports.</p>
      </header>
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Projects" value={projects.length} />
        <MetricCard label="Latest pass rate" value={latest ? `${Math.round(latest.pass_rate * 100)}%` : "No runs"} />
        <MetricCard label="p95 latency" value={latest ? `${Math.round(latest.p95_latency_ms)} ms` : "No runs"} />
        <MetricCard label="Estimated cost" value={latest ? `$${latest.estimated_cost.toFixed(6)}` : "$0.000000"} />
      </div>
      {projects[0] ? (
        <section className="rounded-md border border-line bg-white p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm uppercase text-slate-500">Demo project</div>
              <h2 className="mt-1 text-xl font-semibold">{projects[0].name}</h2>
              <p className="mt-1 text-sm text-slate-600">{projects[0].description}</p>
            </div>
            {latest ? <StatusBadge value={latest.quality_gate_status} /> : null}
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href={`/projects/${projects[0].project_id}`} className="rounded-md bg-ink px-3 py-2 text-sm font-medium text-white">Open dashboard</Link>
            <Link href="/observability" className="rounded-md border border-line px-3 py-2 text-sm font-medium">Observability</Link>
            <Link href="/reports" className="rounded-md border border-line px-3 py-2 text-sm font-medium">Reports</Link>
          </div>
        </section>
      ) : <EmptyState title="No local projects yet" detail="Run make seed-demo to create deterministic demo artifacts." />}
    </div>
  );
}
