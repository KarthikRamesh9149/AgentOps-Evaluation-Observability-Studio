from __future__ import annotations

from statistics import mean, median

from app.evaluators.registry import REGISTRY, evaluate_case
from app.providers.base import provider_factory
from app.quality_gates.service import evaluate_quality_gate
from app.reports.generator import build_report
from app.schemas.models import EvalResult, EvalRun, RunRequest, now_iso
from app.storage.repositories import RepositoryHub
from app.tracing.service import percentile, trace_for_eval


def run_prompt_eval(repo: RepositoryHub, project_id: str, request: RunRequest, mock_latency_ms: int = 35) -> EvalRun:
    project = repo.get_project(project_id)
    prompt = repo.get_prompt_version(project_id, request.prompt_id, request.prompt_version)
    cases = repo.list_cases(project_id, request.dataset_id)
    provider = provider_factory(request.provider, latency_ms=mock_latency_ms)
    run = EvalRun(
        project_id=project_id,
        prompt_id=request.prompt_id,
        prompt_version=request.prompt_version,
        dataset_id=request.dataset_id,
        provider=request.provider,
        model=request.model or prompt.model,
        status="running",
        total_cases=len(cases),
    )
    results: list[EvalResult] = []
    for case in cases:
        rendered = prompt.user_template.replace("{input}", case.input)
        response = provider.generate(prompt.system_prompt, rendered, run.model, prompt.temperature, prompt.max_output_tokens)
        evals = evaluate_case(request.evaluators, case, response.output, provider)
        scores = {item.evaluator: item.score for item in evals}
        scores["average"] = mean(scores.values()) if scores else 1.0
        passed = all(item.passed for item in evals)
        failure_category = classify_failure(evals, case.category)
        trace, spans = trace_for_eval(project_id, run.run_id, case.case_id, case.input, response.output, response.latency_ms, response.tokens, response.estimated_cost, scores)
        repo.write_trace(trace, spans)
        results.append(
            EvalResult(
                case_id=case.case_id,
                input=case.input,
                output=response.output,
                expected_output=case.expected_output,
                reference_answer=case.reference_answer,
                evaluator_results=evals,
                scores=scores,
                passed=passed,
                failure_category=failure_category,
                severity=max((item.severity for item in evals if not item.passed), default="info"),
                latency_ms=response.latency_ms,
                tokens=response.tokens,
                estimated_cost=response.estimated_cost,
                trace_id=trace.trace_id,
            )
        )
    metrics = aggregate_metrics(results)
    run.status = "completed"
    run.completed_at = now_iso()
    run.passed_cases = sum(1 for item in results if item.passed)
    run.failed_cases = len(results) - run.passed_cases
    run.pass_rate = run.passed_cases / len(results) if results else 0
    run.average_score = float(metrics["average_score"])
    run.average_latency_ms = float(metrics["average_latency_ms"])
    run.p50_latency_ms = float(metrics["p50_latency_ms"])
    run.p95_latency_ms = float(metrics["p95_latency_ms"])
    run.estimated_cost = float(metrics["estimated_cost"])
    if request.baseline_run_id:
        run.regression_status = compare_runs(repo, project_id, request.baseline_run_id, run.run_id).get("regression_status", "not_compared")
    gate_result = evaluate_quality_gate(run, metrics, repo.get_quality_gate(project_id))
    run.quality_gate_status = gate_result["status"]  # type: ignore[assignment]
    metrics["quality_gate"] = gate_result
    repo.write_run(run, results, metrics)
    manifest, markdown, html, payload = build_report(project.name, run, results, metrics)
    repo.write_report(project_id, manifest, markdown, html, payload)
    root = repo.run_dir(project_id, run.run_id)
    repo.store._atomic_write(root / "report.md", markdown)
    repo.store._atomic_write(root / "report.html", html)
    return run


def aggregate_metrics(results: list[EvalResult]) -> dict[str, object]:
    latencies = [item.latency_ms for item in results]
    scores = [item.scores.get("average", 0.0) for item in results]
    evaluator_scores: dict[str, list[float]] = {}
    failure_categories: dict[str, int] = {}
    for item in results:
        if not item.passed:
            failure_categories[item.failure_category] = failure_categories.get(item.failure_category, 0) + 1
        for name, score in item.scores.items():
            if name != "average":
                evaluator_scores.setdefault(name, []).append(score)
    return {
        "total_cases": len(results),
        "passed_cases": sum(1 for item in results if item.passed),
        "failed_cases": sum(1 for item in results if not item.passed),
        "average_score": mean(scores) if scores else 0.0,
        "pass_rate": sum(1 for item in results if item.passed) / len(results) if results else 0.0,
        "average_latency_ms": mean(latencies) if latencies else 0.0,
        "p50_latency_ms": median(latencies) if latencies else 0.0,
        "p95_latency_ms": percentile(latencies, 95),
        "estimated_cost": round(sum(item.estimated_cost for item in results), 6),
        "failure_categories": failure_categories,
        "evaluator_scores": {name: mean(values) for name, values in evaluator_scores.items()},
    }


def classify_failure(evals: list[object], category: str) -> str:
    failed = [item for item in evals if not getattr(item, "passed", True)]
    if not failed:
        return "none"
    names = {getattr(item, "evaluator", "") for item in failed}
    if "json_validity" in names or "json_schema" in names:
        return "json_invalid"
    if "citation_accuracy" in names:
        return "missing_citation"
    if "tool_selection" in names or "tool_success" in names:
        return "wrong_tool"
    if "refusal" in names or category == "safety":
        return "unsafe"
    if "faithfulness" in names or "unsupported_claim" in names:
        return "faithfulness"
    return "quality"


def compare_runs(repo: RepositoryHub, project_id: str, run_a: str, run_b: str) -> dict[str, object]:
    a = repo.get_run(project_id, run_a)
    b = repo.get_run(project_id, run_b)
    results_a = {item.case_id: item for item in repo.get_results(project_id, run_a)}
    results_b = {item.case_id: item for item in repo.get_results(project_id, run_b)}
    improved = [case_id for case_id, result in results_b.items() if result.passed and case_id in results_a and not results_a[case_id].passed]
    worsened = [case_id for case_id, result in results_b.items() if not result.passed and case_id in results_a and results_a[case_id].passed]
    status = "regression" if b.pass_rate < a.pass_rate or worsened else "improved" if improved else "stable"
    return {
        "run_a": run_a,
        "run_b": run_b,
        "pass_rate_delta": b.pass_rate - a.pass_rate,
        "score_delta": b.average_score - a.average_score,
        "latency_delta_ms": b.average_latency_ms - a.average_latency_ms,
        "cost_delta": b.estimated_cost - a.estimated_cost,
        "improved_cases": improved,
        "worsened_cases": worsened,
        "new_failures": worsened,
        "fixed_failures": improved,
        "regression_status": status,
    }


def evaluator_settings() -> list[dict[str, object]]:
    return [{"name": name, "type": "judge" if "judge" in name or name in {"faithfulness", "unsupported_claim"} else "rule"} for name in sorted(REGISTRY)]
