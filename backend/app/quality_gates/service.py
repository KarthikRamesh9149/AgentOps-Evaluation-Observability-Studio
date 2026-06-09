from __future__ import annotations

from app.schemas.models import EvalRun, QualityGate


def evaluate_quality_gate(run: EvalRun, metrics: dict[str, object], gate: QualityGate) -> dict[str, object]:
    failures: list[str] = []
    warnings: list[str] = []
    failure_rate = run.failed_cases / run.total_cases if run.total_cases else 0
    evaluator_scores = metrics.get("evaluator_scores", {}) if isinstance(metrics.get("evaluator_scores"), dict) else {}
    failure_categories = metrics.get("failure_categories", {}) if isinstance(metrics.get("failure_categories"), dict) else {}
    checks = {
        "minimum_pass_rate": run.pass_rate >= gate.minimum_pass_rate,
        "minimum_average_score": run.average_score >= gate.minimum_average_score,
        "maximum_p95_latency_ms": run.p95_latency_ms <= gate.maximum_p95_latency_ms,
        "maximum_average_cost": (run.estimated_cost / max(run.total_cases, 1)) <= gate.maximum_average_cost,
        "maximum_failure_rate": failure_rate <= gate.maximum_failure_rate,
    }
    if evaluator_scores.get("faithfulness", 1.0) < gate.minimum_faithfulness:
        checks["minimum_faithfulness"] = False
    if evaluator_scores.get("citation_accuracy", 1.0) < gate.minimum_citation_accuracy:
        checks["minimum_citation_accuracy"] = False
    for category in gate.blocked_failure_categories:
        if failure_categories.get(category, 0):
            checks[f"blocked_failure_category:{category}"] = False
    for name, passed in checks.items():
        if not passed:
            failures.append(name)
    for name, threshold in gate.warning_thresholds.items():
        if name == "minimum_pass_rate" and run.pass_rate < threshold and name not in failures:
            warnings.append(name)
    status = "fail" if failures else "warn" if warnings else "pass"
    return {"status": status, "checks": checks, "failures": failures, "warnings": warnings}
