from __future__ import annotations

from app.schemas.models import Span, Trace, now_iso


TOOLS = {
    "Where is my package?": "lookup_order",
    "Can I get a refund?": "refund_policy_lookup",
    "My order arrived damaged.": "create_support_ticket",
    "Cancel my order.": "cancel_order",
    "Create a support ticket.": "create_support_ticket",
}


def run_support_agent(project_id: str, user_input: str) -> tuple[dict[str, object], Trace, list[Span]]:
    selected = next((tool for phrase, tool in TOOLS.items() if phrase.lower().rstrip(".?") in user_input.lower()), "knowledge_search")
    result = f"Selected `{selected}` and returned a concise support next step."
    trace = Trace(project_id=project_id, name="local-support-tool-agent", app_type="agent", input=user_input, output=result, end_time=now_iso(), latency_ms=55, scores={"tool_success": 1.0})
    spans = [
        Span(trace_id=trace.trace_id, span_type="agent_step", name="agent.plan", input_summary=user_input, output_summary=selected, end_time=now_iso(), latency_ms=15),
        Span(trace_id=trace.trace_id, span_type="tool", name=selected, input_summary=user_input, output_summary="ok", end_time=now_iso(), latency_ms=25, metadata={"tool": selected}),
        Span(trace_id=trace.trace_id, span_type="llm", name="agent.finalize", input_summary=selected, output_summary=result, end_time=now_iso(), latency_ms=15),
    ]
    return {"answer": result, "tool_calls": [selected], "status": "ok"}, trace, spans
