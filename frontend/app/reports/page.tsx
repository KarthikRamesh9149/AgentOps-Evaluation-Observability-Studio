"use client";

import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";

export default function ReportsPage() {
  const [reports, setReports] = useState<Record<string, string>[]>();
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    client.projects().then(async (projects) => setReports(projects[0] ? (await client.reports(projects[0].project_id) as Record<string, string>[]) : [])).catch(setError);
  }, []);
  if (error) return <ErrorState error={error} />;
  if (!reports) return <LoadingState />;
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Reports</h1>
      <DataTable rows={reports} columns={[
        { header: "Report", cell: (r) => r.title },
        { header: "Run", cell: (r) => r.run_id },
        { header: "Markdown", cell: (r) => r.markdown_path },
        { header: "HTML", cell: (r) => r.html_path }
      ]} />
    </div>
  );
}
