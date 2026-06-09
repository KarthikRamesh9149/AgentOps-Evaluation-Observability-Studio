from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.errors import http_error
from app.core.settings import Settings, get_settings
from app.quality_gates.service import evaluate_quality_gate
from app.reports.generator import build_report
from app.runners.engine import compare_runs, evaluator_settings, run_prompt_eval
from app.sample_apps.agent import run_support_agent
from app.sample_apps.rag import run_rag
from app.schemas.models import (
    DatasetCase,
    DatasetMeta,
    Project,
    ProjectUpdate,
    PromptVersion,
    QualityGate,
    ReviewAnnotation,
    RunRequest,
    now_iso,
)
from app.storage.repositories import RepositoryHub
from app.tracing.service import summarize_traces

router = APIRouter()


def repo(settings: Settings = Depends(get_settings)) -> RepositoryHub:
    return RepositoryHub(settings.data_dir)


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    return {"status": "ok", "app_env": settings.app_env, "data_dir": str(settings.data_dir), "provider": settings.llm_provider}


@router.get("/projects")
def list_projects(repository: RepositoryHub = Depends(repo)) -> list[Project]:
    return repository.list_projects()


@router.post("/projects")
def create_project(project: Project, repository: RepositoryHub = Depends(repo)) -> Project:
    try:
        return repository.create_project(project)
    except Exception as exc:
        raise http_error(exc) from exc


@router.get("/projects/{project_id}")
def get_project(project_id: str, repository: RepositoryHub = Depends(repo)) -> Project:
    try:
        return repository.get_project(project_id)
    except Exception as exc:
        raise http_error(exc) from exc


@router.patch("/projects/{project_id}")
def update_project(project_id: str, update: ProjectUpdate, repository: RepositoryHub = Depends(repo)) -> Project:
    try:
        return repository.update_project(project_id, update)
    except Exception as exc:
        raise http_error(exc) from exc


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, repository: RepositoryHub = Depends(repo)) -> dict[str, str]:
    try:
        return repository.delete_project(project_id)
    except Exception as exc:
        raise http_error(exc) from exc


@router.get("/projects/{project_id}/prompts")
def list_prompts(project_id: str, repository: RepositoryHub = Depends(repo)) -> list[PromptVersion]:
    return repository.list_prompts(project_id)


@router.post("/projects/{project_id}/prompts")
def create_prompt(project_id: str, prompt: PromptVersion, repository: RepositoryHub = Depends(repo)) -> PromptVersion:
    return repository.create_prompt(project_id, prompt)


@router.get("/projects/{project_id}/prompts/{prompt_id}")
def get_prompt(project_id: str, prompt_id: str, repository: RepositoryHub = Depends(repo)) -> list[PromptVersion]:
    return repository.list_prompt_versions(project_id, prompt_id)


@router.post("/projects/{project_id}/prompts/{prompt_id}/versions")
def create_prompt_version(project_id: str, prompt_id: str, prompt: PromptVersion, repository: RepositoryHub = Depends(repo)) -> PromptVersion:
    return repository.create_prompt_version(project_id, prompt_id, prompt)


@router.get("/projects/{project_id}/prompts/{prompt_id}/versions")
def list_prompt_versions(project_id: str, prompt_id: str, repository: RepositoryHub = Depends(repo)) -> list[PromptVersion]:
    return repository.list_prompt_versions(project_id, prompt_id)


@router.get("/projects/{project_id}/prompts/{prompt_id}/versions/{version}")
def get_prompt_version(project_id: str, prompt_id: str, version: int, repository: RepositoryHub = Depends(repo)) -> PromptVersion:
    return repository.get_prompt_version(project_id, prompt_id, version)


@router.get("/projects/{project_id}/datasets")
def list_datasets(project_id: str, repository: RepositoryHub = Depends(repo)) -> list[DatasetMeta]:
    return repository.list_datasets(project_id)


@router.post("/projects/{project_id}/datasets")
def create_dataset(project_id: str, payload: dict[str, Any], repository: RepositoryHub = Depends(repo)) -> DatasetMeta:
    meta = DatasetMeta.model_validate(payload.get("meta", payload))
    cases = [DatasetCase.model_validate(row) for row in payload.get("cases", [])]
    return repository.create_dataset(project_id, meta, cases)


@router.post("/projects/{project_id}/datasets/import-jsonl")
def import_jsonl(project_id: str, payload: dict[str, Any], repository: RepositoryHub = Depends(repo)) -> DatasetMeta:
    meta = DatasetMeta.model_validate(payload.get("meta", {"name": payload.get("dataset_id", "Imported dataset"), "dataset_id": payload.get("dataset_id")}))
    cases = [DatasetCase.model_validate(row) for row in payload.get("cases", [])]
    return repository.create_dataset(project_id, meta, cases)


@router.get("/projects/{project_id}/datasets/{dataset_id}")
def get_dataset(project_id: str, dataset_id: str, repository: RepositoryHub = Depends(repo)) -> DatasetMeta:
    return repository.get_dataset(project_id, dataset_id)


@router.get("/projects/{project_id}/datasets/{dataset_id}/cases")
def get_cases(project_id: str, dataset_id: str, repository: RepositoryHub = Depends(repo)) -> list[DatasetCase]:
    return repository.list_cases(project_id, dataset_id)


@router.post("/projects/{project_id}/datasets/{dataset_id}/cases")
def add_case(project_id: str, dataset_id: str, case: DatasetCase, repository: RepositoryHub = Depends(repo)) -> DatasetCase:
    return repository.add_case(project_id, dataset_id, case)


@router.delete("/projects/{project_id}/datasets/{dataset_id}")
def delete_dataset(project_id: str, dataset_id: str, repository: RepositoryHub = Depends(repo)) -> dict[str, str]:
    return repository.delete_dataset(project_id, dataset_id)


@router.post("/projects/{project_id}/runs")
def create_run(project_id: str, request: RunRequest, repository: RepositoryHub = Depends(repo), settings: Settings = Depends(get_settings)):
    try:
        if request.provider == "openai" and not settings.openai_api_key:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY is required for OpenAI mode")
        return run_prompt_eval(repository, project_id, request, settings.mock_provider_latency_ms)
    except HTTPException:
        raise
    except Exception as exc:
        raise http_error(exc) from exc


@router.get("/projects/{project_id}/runs")
def list_runs(project_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.list_runs(project_id)


@router.get("/projects/{project_id}/runs/{run_id}")
def get_run(project_id: str, run_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.get_run(project_id, run_id)


@router.get("/projects/{project_id}/runs/{run_id}/results")
def get_results(project_id: str, run_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.get_results(project_id, run_id)


@router.get("/projects/{project_id}/runs/{run_id}/metrics")
def get_metrics(project_id: str, run_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.get_metrics(project_id, run_id)


@router.get("/projects/{project_id}/runs/{run_id}/report")
def get_run_report(project_id: str, run_id: str, repository: RepositoryHub = Depends(repo)):
    root = repository.run_dir(project_id, run_id)
    return {"markdown": (root / "report.md").read_text(encoding="utf-8"), "html": (root / "report.html").read_text(encoding="utf-8")}


@router.post("/projects/{project_id}/runs/{run_id}/apply-quality-gate")
def apply_gate_to_run(project_id: str, run_id: str, repository: RepositoryHub = Depends(repo)):
    run = repository.get_run(project_id, run_id)
    result = evaluate_quality_gate(run, repository.get_metrics(project_id, run_id), repository.get_quality_gate(project_id))
    run.quality_gate_status = result["status"]  # type: ignore[assignment]
    repository.update_run(run)
    return result


@router.post("/projects/{project_id}/compare-runs")
def compare(project_id: str, payload: dict[str, str], repository: RepositoryHub = Depends(repo)):
    return compare_runs(repository, project_id, payload["run_a"], payload["run_b"])


@router.post("/projects/{project_id}/compare-prompts")
def compare_prompts(project_id: str, payload: dict[str, str]):
    return {"project_id": project_id, "comparison": "prompt", "prompt_a": payload.get("prompt_a"), "prompt_b": payload.get("prompt_b")}


@router.post("/projects/{project_id}/compare-models")
def compare_models(project_id: str, payload: dict[str, str]):
    return {"project_id": project_id, "comparison": "model", "model_a": payload.get("model_a"), "model_b": payload.get("model_b")}


@router.post("/projects/{project_id}/export-report")
def export_report(project_id: str, payload: dict[str, str], repository: RepositoryHub = Depends(repo)):
    run_id = payload["run_id"]
    project = repository.get_project(project_id)
    run = repository.get_run(project_id, run_id)
    results = repository.get_results(project_id, run_id)
    metrics = repository.get_metrics(project_id, run_id)
    manifest, markdown, html, report_payload = build_report(project.name, run, results, metrics)
    return repository.write_report(project_id, manifest, markdown, html, report_payload)


@router.get("/projects/{project_id}/reports")
def list_reports(project_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.list_reports(project_id)


@router.get("/projects/{project_id}/reports/{report_id}")
def get_report(project_id: str, report_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.get_report(project_id, report_id)


@router.post("/projects/{project_id}/sample-apps/rag/run")
def rag_run(project_id: str, payload: dict[str, str], repository: RepositoryHub = Depends(repo), settings: Settings = Depends(get_settings)):
    result, trace, spans = run_rag(project_id, payload.get("question", ""), settings.data_dir / "sample_docs")
    repository.write_trace(trace, spans)
    return result | {"trace_id": trace.trace_id}


@router.post("/projects/{project_id}/sample-apps/agent/run")
def agent_run(project_id: str, payload: dict[str, str], repository: RepositoryHub = Depends(repo)):
    result, trace, spans = run_support_agent(project_id, payload.get("input", ""))
    repository.write_trace(trace, spans)
    return result | {"trace_id": trace.trace_id}


@router.post("/projects/{project_id}/evals/rag")
def rag_eval(project_id: str, payload: dict[str, str], repository: RepositoryHub = Depends(repo), settings: Settings = Depends(get_settings)):
    return rag_run(project_id, payload, repository, settings)


@router.post("/projects/{project_id}/evals/agent")
def agent_eval(project_id: str, payload: dict[str, str], repository: RepositoryHub = Depends(repo)):
    return agent_run(project_id, payload, repository)


@router.get("/projects/{project_id}/traces")
def list_traces(project_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.list_traces(project_id)


@router.get("/projects/{project_id}/traces/{trace_id}")
def get_trace(project_id: str, trace_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.get_trace(project_id, trace_id)


@router.get("/projects/{project_id}/traces/{trace_id}/spans")
def get_spans(project_id: str, trace_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.get_spans(project_id, trace_id)


@router.get("/projects/{project_id}/observability/summary")
def observability_summary(project_id: str, repository: RepositoryHub = Depends(repo)):
    traces = repository.list_traces(project_id)
    spans = {trace.trace_id: repository.get_spans(project_id, trace.trace_id) for trace in traces}
    summary = summarize_traces(traces, spans)
    runs = repository.list_runs(project_id)
    summary["latest_runs"] = runs[:5]
    return summary


@router.get("/projects/{project_id}/observability/latency")
def observability_latency(project_id: str, repository: RepositoryHub = Depends(repo)):
    return [{"trace_id": trace.trace_id, "latency_ms": trace.latency_ms, "app_type": trace.app_type} for trace in repository.list_traces(project_id)]


@router.get("/projects/{project_id}/observability/costs")
def observability_costs(project_id: str, repository: RepositoryHub = Depends(repo)):
    return [{"trace_id": trace.trace_id, "estimated_cost": trace.estimated_cost, "app_type": trace.app_type} for trace in repository.list_traces(project_id)]


@router.get("/projects/{project_id}/observability/failures")
def observability_failures(project_id: str, repository: RepositoryHub = Depends(repo)):
    categories: dict[str, int] = {}
    for run in repository.list_runs(project_id):
        for category, count in repository.get_metrics(project_id, run.run_id).get("failure_categories", {}).items():
            categories[category] = categories.get(category, 0) + count
    return categories


@router.get("/projects/{project_id}/observability/evaluators")
def observability_evaluators(project_id: str, repository: RepositoryHub = Depends(repo)):
    scores: dict[str, list[float]] = {}
    for run in repository.list_runs(project_id):
        for name, value in repository.get_metrics(project_id, run.run_id).get("evaluator_scores", {}).items():
            scores.setdefault(name, []).append(float(value))
    return {name: sum(values) / len(values) for name, values in scores.items()}


@router.get("/projects/{project_id}/reviews")
def list_reviews(project_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.list_reviews(project_id)


@router.post("/projects/{project_id}/reviews")
def create_review(project_id: str, review: ReviewAnnotation, repository: RepositoryHub = Depends(repo)):
    review.project_id = project_id
    return repository.write_review(review)


@router.get("/projects/{project_id}/reviews/{review_id}")
def get_review(project_id: str, review_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.get_review(project_id, review_id)


@router.patch("/projects/{project_id}/reviews/{review_id}")
def update_review(project_id: str, review_id: str, payload: dict[str, str], repository: RepositoryHub = Depends(repo)):
    review = repository.get_review(project_id, review_id)
    review.reviewer_label = payload.get("reviewer_label", review.reviewer_label)
    review.reviewer_note = payload.get("reviewer_note", review.reviewer_note)
    review.updated_at = now_iso()
    return repository.write_review(review)


@router.get("/projects/{project_id}/quality-gates")
def get_gate(project_id: str, repository: RepositoryHub = Depends(repo)):
    return repository.get_quality_gate(project_id)


@router.put("/projects/{project_id}/quality-gates")
def put_gate(project_id: str, gate: QualityGate, repository: RepositoryHub = Depends(repo)):
    return repository.write_quality_gate(project_id, gate)


@router.post("/projects/{project_id}/quality-gates/evaluate-run")
def evaluate_gate(project_id: str, payload: dict[str, str], repository: RepositoryHub = Depends(repo)):
    run_id = payload["run_id"]
    return evaluate_quality_gate(repository.get_run(project_id, run_id), repository.get_metrics(project_id, run_id), repository.get_quality_gate(project_id))


@router.get("/settings/providers")
def providers(settings: Settings = Depends(get_settings)):
    return {
        "default": settings.llm_provider,
        "providers": [
            {"name": "mock", "requires_key": False, "token_saver": True},
            {"name": "openai", "requires_key": True, "configured": bool(settings.openai_api_key), "default_model": settings.openai_small_model},
        ],
    }


@router.get("/settings/evaluators")
def evaluators():
    return evaluator_settings()
