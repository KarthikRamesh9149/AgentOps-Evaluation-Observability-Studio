"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";

export default function PromptsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [rows, setRows] = useState<Record<string, string | number>[]>();
  const [error, setError] = useState<unknown>();
  useEffect(() => { client.prompts(projectId).then((items) => setRows(items as Record<string, string | number>[])).catch(setError); }, [projectId]);
  if (error) return <ErrorState error={error} />;
  if (!rows) return <LoadingState />;
  return <div className="space-y-5"><h1 className="text-2xl font-semibold">Prompt Versions</h1><DataTable rows={rows} columns={[
    { header: "Prompt", cell: (r) => String(r.name) },
    { header: "ID", cell: (r) => String(r.prompt_id) },
    { header: "Version", cell: (r) => String(r.version) },
    { header: "Model", cell: (r) => String(r.model) }
  ]} /></div>;
}
