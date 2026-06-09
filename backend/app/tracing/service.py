from __future__ import annotations

from app.schemas.models import Span, Trace, now_iso


def trace_for_eval(project_id: str, run_id: str, case_id: str, input_text: str, output: str, latency_ms: int, tokens: dict[str, int], cost: float, scores: dict[str, float]) -> tuple[Trace, list[Span]]:
    trace = Trace(
        project_id=project_id,
        run_id=run_id,
        name=f"eval-case-{case_id}",
        app_type="eval",
        input=input_text[:2000],
        output=output[:2000],
        end_time=now_iso(),
        latency_ms=latency_ms,
        total_tokens=sum(tokens.values()),
        estimated_cost=cost,
        scores=scores,
    )
    spans = [
        Span(
            trace_id=trace.trace_id,
            span_type="llm",
            name="provider.generate",
            input_summary=input_text[:300],
            output_summary=output[:300],
            end_time=now_iso(),
            latency_ms=latency_ms,
            tokens=tokens,
            estimated_cost=cost,
        ),
        Span(
            trace_id=trace.trace_id,
            span_type="evaluator",
            name="case.evaluators",
            input_summary="Structured evaluator suite",
            output_summary=str(scores)[:300],
            end_time=now_iso(),
            latency_ms=max(1, latency_ms // 10),
            metadata={"scores": scores},
        ),
    ]
    return trace, spans


def summarize_traces(traces: list[Trace], spans_by_trace: dict[str, list[Span]]) -> dict[str, object]:
    latencies = [trace.latency_ms for trace in traces]
    costs = [trace.estimated_cost for trace in traces]
    failures = [trace for trace in traces if trace.status != "ok"]
    span_type_latency: dict[str, int] = {}
    for spans in spans_by_trace.values():
        for span in spans:
            span_type_latency[span.span_type] = span_type_latency.get(span.span_type, 0) + span.latency_ms
    return {
        "total_traces": len(traces),
        "success_rate": (len(traces) - len(failures)) / len(traces) if traces else 0,
        "failure_rate": len(failures) / len(traces) if traces else 0,
        "average_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
        "p95_latency_ms": percentile(latencies, 95),
        "total_estimated_cost": round(sum(costs), 6),
        "average_cost": round(sum(costs) / len(costs), 6) if costs else 0,
        "latency_by_span_type": span_type_latency,
    }


def percentile(values: list[int | float], p: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((p / 100) * (len(ordered) - 1)))
    return float(ordered[index])
