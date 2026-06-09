"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";
import type { Trace } from "@/lib/types";

export default function TracesPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [rows, setRows] = useState<Trace[]>();
  const [error, setError] = useState<unknown>();
  useEffect(() => { client.traces(projectId).then(setRows).catch(setError); }, [projectId]);
  if (error) return <ErrorState error={error} />;
  if (!rows) return <LoadingState />;
  return <div className="space-y-5"><h1 className="text-2xl font-semibold">Traces</h1><DataTable rows={rows} columns={[
    { header: "Trace", cell: (r) => <Link className="text-accent" href={`/projects/${projectId}/traces/${r.trace_id}`}>{r.trace_id}</Link> },
    { header: "Type", cell: (r) => r.app_type },
    { header: "Status", cell: (r) => r.status },
    { header: "Latency", cell: (r) => `${r.latency_ms} ms` },
    { header: "Cost", cell: (r) => `$${r.estimated_cost.toFixed(6)}` }
  ]} /></div>;
}
