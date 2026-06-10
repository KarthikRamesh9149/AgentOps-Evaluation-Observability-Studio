"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import { MetricCard } from "@/components/Cards";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";

export default function ObservabilityPage() {
  const [summary, setSummary] = useState<Record<string, unknown>>();
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    client.projects().then(async (projects) => {
      if (projects[0]) setSummary(await client.observability(projects[0].project_id));
      else setSummary({});
    }).catch(setError);
  }, []);
  if (error) return <ErrorState error={error} />;
  if (!summary) return <LoadingState />;
  const latency = Object.entries((summary.latency_by_span_type as Record<string, number> | undefined) ?? {}).map(([name, value]) => ({ name, value }));
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Observability</h1>
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Total traces" value={String(summary.total_traces ?? 0)} />
        <MetricCard label="Success rate" value={`${Math.round(Number(summary.success_rate ?? 0) * 100)}%`} />
        <MetricCard label="p95 latency" value={`${Math.round(Number(summary.p95_latency_ms ?? 0))} ms`} />
        <MetricCard label="Total estimated cost" value={`$${Number(summary.total_estimated_cost ?? 0).toFixed(6)}`} />
      </div>
      <div className="overflow-x-auto rounded-md border border-line bg-white p-4">
        <BarChart width={900} height={300} data={latency}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#2563eb" />
        </BarChart>
      </div>
    </div>
  );
}
