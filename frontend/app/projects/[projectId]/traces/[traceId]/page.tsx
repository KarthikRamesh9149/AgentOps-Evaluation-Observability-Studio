"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { MetricCard, StatusBadge } from "@/components/Cards";
import { TraceWaterfall } from "@/components/TraceWaterfall";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";
import type { Span, Trace } from "@/lib/types";

export default function TraceDetailPage() {
  const { projectId, traceId } = useParams<{ projectId: string; traceId: string }>();
  const [trace, setTrace] = useState<Trace>();
  const [spans, setSpans] = useState<Span[]>([]);
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    Promise.all([client.trace(projectId, traceId), client.spans(projectId, traceId)])
      .then(([t, s]) => { setTrace(t); setSpans(s); })
      .catch(setError);
  }, [projectId, traceId]);
  if (error) return <ErrorState error={error} />;
  if (!trace) return <LoadingState />;
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{trace.name}</h1>
        <StatusBadge value={trace.status} />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="App type" value={trace.app_type} />
        <MetricCard label="Latency" value={`${trace.latency_ms} ms`} />
        <MetricCard label="Estimated cost" value={`$${trace.estimated_cost.toFixed(6)}`} />
      </div>
      <TraceWaterfall spans={spans} />
    </div>
  );
}
