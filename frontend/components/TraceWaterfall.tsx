import type { Span } from "@/lib/types";

export function TraceWaterfall({ spans }: { spans: Span[] }) {
  const max = Math.max(...spans.map((span) => span.latency_ms), 1);
  return (
    <div className="space-y-3">
      {spans.map((span) => (
        <div key={span.span_id} className="rounded-md border border-line bg-white p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="text-sm font-semibold">{span.name}</div>
              <div className="text-xs text-slate-500">{span.span_type} / {span.status}</div>
            </div>
            <div className="text-sm font-medium">{span.latency_ms} ms</div>
          </div>
          <div className="mt-3 h-2 rounded bg-slate-100">
            <div className="h-2 rounded bg-accent" style={{ width: `${Math.max(4, (span.latency_ms / max) * 100)}%` }} />
          </div>
          <div className="mt-3 grid gap-3 text-xs text-slate-600 md:grid-cols-2">
            <div>{span.input_summary}</div>
            <div>{span.output_summary}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
