"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";

export default function DatasetsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [rows, setRows] = useState<Record<string, string | number>[]>();
  const [error, setError] = useState<unknown>();
  useEffect(() => { client.datasets(projectId).then((items) => setRows(items as Record<string, string | number>[])).catch(setError); }, [projectId]);
  if (error) return <ErrorState error={error} />;
  if (!rows) return <LoadingState />;
  return <div className="space-y-5"><h1 className="text-2xl font-semibold">Datasets</h1><DataTable rows={rows} columns={[
    { header: "Dataset", cell: (r) => String(r.name) },
    { header: "ID", cell: (r) => String(r.dataset_id) },
    { header: "Cases", cell: (r) => String(r.case_count) },
    { header: "Tags", cell: (r) => Array.isArray(r.tags) ? r.tags.join(", ") : "" }
  ]} /></div>;
}
