export function MetricCard({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <div className="text-xs font-medium uppercase text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {detail ? <div className="mt-1 text-sm text-slate-500">{detail}</div> : null}
    </div>
  );
}

export function StatusBadge({ value }: { value: string }) {
  const color = value === "pass" || value === "completed" || value === "improved" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : value === "fail" || value === "regression" ? "bg-red-50 text-red-700 border-red-200" : "bg-amber-50 text-amber-700 border-amber-200";
  return <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-medium ${color}`}>{value}</span>;
}
