"use client";

import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";

export default function FailuresPage() {
  const [rows, setRows] = useState<{ category: string; count: number }[]>();
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    client.projects().then(async (projects) => {
      if (!projects[0]) return setRows([]);
      const failures = await client.failures(projects[0].project_id);
      setRows(Object.entries(failures).map(([category, count]) => ({ category, count })));
    }).catch(setError);
  }, []);
  if (error) return <ErrorState error={error} />;
  if (!rows) return <LoadingState />;
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Failures</h1>
      <DataTable rows={rows} columns={[
        { header: "Category", cell: (r) => r.category },
        { header: "Count", cell: (r) => r.count },
        { header: "Recommended fix", cell: (r) => r.category === "missing_citation" ? "Add retrieval context and citation requirements." : r.category === "wrong_tool" ? "Tighten tool selection rules." : "Review prompt and dataset expectations." }
      ]} />
    </div>
  );
}
