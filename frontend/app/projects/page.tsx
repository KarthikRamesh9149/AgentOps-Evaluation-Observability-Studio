"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>();
  const [error, setError] = useState<unknown>();
  useEffect(() => { client.projects().then(setProjects).catch(setError); }, []);
  if (error) return <ErrorState error={error} />;
  if (!projects) return <LoadingState />;
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Projects</h1>
      <DataTable rows={projects} columns={[
        { header: "Project", cell: (p) => <Link className="font-medium text-accent" href={`/projects/${p.project_id}`}>{p.name}</Link> },
        { header: "Type", cell: (p) => p.project_type },
        { header: "Provider", cell: (p) => p.default_provider },
        { header: "Tags", cell: (p) => p.tags.join(", ") }
      ]} />
    </div>
  );
}
