export function LoadingState({ label = "Loading local artifacts" }: { label?: string }) {
  return <div className="rounded-md border border-line bg-white p-5 text-sm text-slate-600">{label}...</div>;
}

export function ErrorState({ error }: { error: unknown }) {
  return <div className="rounded-md border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error instanceof Error ? error.message : "Request failed"}</div>;
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-6">
      <div className="text-sm font-semibold">{title}</div>
      <div className="mt-1 text-sm text-slate-500">{detail}</div>
    </div>
  );
}
