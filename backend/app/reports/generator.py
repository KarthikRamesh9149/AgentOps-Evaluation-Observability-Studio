from __future__ import annotations

from html import escape

from app.schemas.models import EvalResult, EvalRun, ReportManifest, new_id


def build_report(project_name: str, run: EvalRun, results: list[EvalResult], metrics: dict[str, object]) -> tuple[ReportManifest, str, str, dict[str, object]]:
    worst = sorted(results, key=lambda item: (item.passed, item.scores.get("average", 0)))[:5]
    lines = [
        f"# {project_name} Evaluation Report",
        "",
        "## Executive Summary",
        f"- Run: `{run.run_id}`",
        f"- Provider/model: `{run.provider}` / `{run.model}`",
        f"- Pass rate: {run.pass_rate:.1%}",
        f"- Average score: {run.average_score:.2f}",
        f"- p95 latency: {run.p95_latency_ms:.0f} ms",
        f"- Estimated cost: ${run.estimated_cost:.6f}",
        f"- Quality gate: {run.quality_gate_status}",
        "",
        "## Failure Summary",
    ]
    failure_categories = metrics.get("failure_categories", {})
    if isinstance(failure_categories, dict) and failure_categories:
        lines += [f"- {category}: {count}" for category, count in failure_categories.items()]
    else:
        lines.append("- No failures recorded.")
    lines += ["", "## Worst Cases"]
    for result in worst:
        lines += [
            f"### Case `{result.case_id}`",
            f"- Passed: {result.passed}",
            f"- Failure category: {result.failure_category}",
            f"- Latency: {result.latency_ms} ms",
            f"- Trace: `{result.trace_id}`",
            f"- Output: {result.output[:400]}",
            "",
        ]
    lines += [
        "## Recommended Fixes",
        "- Tighten prompt instructions for recurring failed categories.",
        "- Add missing citations or retrieval context when citation accuracy drops.",
        "- Review wrong-tool failures against expected tool-call metadata.",
        "",
        "## Appendix",
        "Case-level evaluator results are stored in `results.jsonl` next to this report.",
    ]
    markdown = "\n".join(lines) + "\n"
    html = "<!doctype html><html><head><meta charset='utf-8'><title>Evaluation Report</title><style>body{font-family:Inter,Arial,sans-serif;margin:40px;line-height:1.5;color:#172026}code{background:#eef2f7;padding:2px 5px;border-radius:4px}pre{white-space:pre-wrap}</style></head><body><pre>" + escape(markdown) + "</pre></body></html>"
    report_id = new_id("report")
    manifest = ReportManifest(
        report_id=report_id,
        project_id=run.project_id,
        run_id=run.run_id,
        title=f"{project_name} report for {run.run_id}",
        markdown_path=f"data/projects/{run.project_id}/reports/{report_id}.md",
        html_path=f"data/projects/{run.project_id}/reports/{report_id}.html",
        json_path=f"data/projects/{run.project_id}/reports/{report_id}.json",
    )
    return manifest, markdown, html, {"run": run.model_dump(), "metrics": metrics, "worst_cases": [item.model_dump() for item in worst]}
