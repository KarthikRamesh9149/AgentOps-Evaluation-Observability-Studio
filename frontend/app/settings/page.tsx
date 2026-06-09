"use client";

import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";

export default function SettingsPage() {
  const [providers, setProviders] = useState<Record<string, unknown>>();
  const [evaluators, setEvaluators] = useState<unknown[]>([]);
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    Promise.all([client.settingsProviders(), client.settingsEvaluators()])
      .then(([p, e]) => { setProviders(p); setEvaluators(e); })
      .catch(setError);
  }, []);
  if (error) return <ErrorState error={error} />;
  if (!providers) return <LoadingState />;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <div className="rounded-md border border-line bg-white p-5 text-sm">
        <div>Default provider: <span className="font-medium">{String(providers.default)}</span></div>
        <div className="mt-1 text-slate-600">OpenAI mode is opt-in through environment variables. Mock mode is deterministic and used by tests and CI.</div>
      </div>
      <DataTable rows={evaluators as Record<string, string>[]} columns={[
        { header: "Evaluator", cell: (r) => r.name },
        { header: "Type", cell: (r) => r.type }
      ]} />
    </div>
  );
}
