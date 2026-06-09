"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/Cards";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";
import type { Run } from "@/lib/types";

export default function RunsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [rows, setRows] = useState<Run[]>();
  const [error, setError] = useState<unknown>();
  useEffect(() => { client.runs(projectId).then(setRows).catch(setError); }, [projectId]);
  if (error) return <ErrorState error={error} />;
  if (!rows) return <LoadingState />;
  return <div className="space-y-5"><h1 className="text-2xl font-semibold">Runs</h1><DataTable rows={rows} columns={[
    { header: "Run", cell: (r) => <Link className="text-accent" href={`/projects/${projectId}/runs/${r.run_id}`}>{r.run_id}</Link> },
    { header: "Provider", cell: (r) => r.provider },
    { header: "Model", cell: (r) => r.model },
    { header: "Pass rate", cell: (r) => `${Math.round(r.pass_rate * 100)}%` },
    { header: "Gate", cell: (r) => <StatusBadge value={r.quality_gate_status} /> }
  ]} /></div>;
}
