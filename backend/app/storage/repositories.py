from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.errors import NotFoundError, ValidationFailure
from app.schemas.models import (
    DatasetCase,
    DatasetMeta,
    EvalResult,
    EvalRun,
    Project,
    ProjectUpdate,
    PromptVersion,
    QualityGate,
    ReportManifest,
    ReviewAnnotation,
    Span,
    Trace,
    now_iso,
)
from app.storage.file_store import FileStore, validate_id


class RepositoryHub:
    def __init__(self, data_dir: Path):
        self.store = FileStore(data_dir)
        for folder in [
            "projects",
            "datasets",
            "prompts",
            "runs",
            "traces",
            "reports",
            "artifacts",
            "reviews",
            "sample_docs",
        ]:
            self.store.ensure_dir(folder)

    def project_dir(self, project_id: str) -> Path:
        return self.store.ensure_dir("projects", validate_id(project_id, "project_id"))

    def create_project(self, project: Project) -> Project:
        project.project_id = validate_id(project.project_id, "project_id")
        base = self.project_dir(project.project_id)
        for folder in ["prompts", "datasets", "runs", "traces", "reports", "reviews"]:
            (base / folder).mkdir(parents=True, exist_ok=True)
        self.store.write_json(base / "project.json", project)
        self.write_quality_gate(project.project_id, QualityGate())
        return project

    def list_projects(self) -> list[Project]:
        projects: list[Project] = []
        for file in sorted((self.store.root / "projects").glob("*/project.json")):
            try:
                projects.append(Project.model_validate(self.store.read_json(file)))
            except ValidationFailure:
                continue
        return projects

    def get_project(self, project_id: str) -> Project:
        return Project.model_validate(self.store.read_json(self.project_dir(project_id) / "project.json"))

    def update_project(self, project_id: str, update: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        updates = update.model_dump(exclude_none=True)
        for key, value in updates.items():
            setattr(project, key, value)
        project.updated_at = now_iso()
        self.store.write_json(self.project_dir(project_id) / "project.json", project)
        return project

    def delete_project(self, project_id: str) -> dict[str, str]:
        base = self.project_dir(project_id)
        if not (base / "project.json").exists():
            raise NotFoundError(f"Project not found: {project_id}")
        marker = base / ".deleted"
        marker.write_text(now_iso(), encoding="utf-8")
        return {"status": "deleted", "project_id": project_id}

    def prompt_root(self, project_id: str, prompt_id: str) -> Path:
        return self.project_dir(project_id) / "prompts" / validate_id(prompt_id, "prompt_id")

    def create_prompt(self, project_id: str, prompt: PromptVersion) -> PromptVersion:
        root = self.prompt_root(project_id, prompt.prompt_id)
        root.mkdir(parents=True, exist_ok=True)
        prompt.version = 1
        self.store.write_yaml(root / "v1.yaml", prompt)
        return prompt

    def list_prompts(self, project_id: str) -> list[PromptVersion]:
        prompts: list[PromptVersion] = []
        for folder in sorted((self.project_dir(project_id) / "prompts").glob("*")):
            versions = sorted(folder.glob("v*.yaml"))
            if versions:
                prompts.append(PromptVersion.model_validate(self.store.read_yaml(versions[-1])))
        return prompts

    def list_prompt_versions(self, project_id: str, prompt_id: str) -> list[PromptVersion]:
        root = self.prompt_root(project_id, prompt_id)
        versions = [PromptVersion.model_validate(self.store.read_yaml(path)) for path in sorted(root.glob("v*.yaml"))]
        if not versions:
            raise NotFoundError(f"Prompt not found: {prompt_id}")
        return versions

    def get_prompt_version(self, project_id: str, prompt_id: str, version: int) -> PromptVersion:
        return PromptVersion.model_validate(self.store.read_yaml(self.prompt_root(project_id, prompt_id) / f"v{version}.yaml"))

    def create_prompt_version(self, project_id: str, prompt_id: str, prompt: PromptVersion) -> PromptVersion:
        versions = self.list_prompt_versions(project_id, prompt_id)
        prompt.prompt_id = prompt_id
        prompt.version = max(item.version for item in versions) + 1
        prompt.created_at = now_iso()
        self.store.write_yaml(self.prompt_root(project_id, prompt_id) / f"v{prompt.version}.yaml", prompt)
        return prompt

    def dataset_paths(self, project_id: str, dataset_id: str) -> tuple[Path, Path]:
        dataset_id = validate_id(dataset_id, "dataset_id")
        root = self.project_dir(project_id) / "datasets"
        root.mkdir(parents=True, exist_ok=True)
        return root / f"{dataset_id}.jsonl", root / f"{dataset_id}.meta.json"

    def create_dataset(self, project_id: str, meta: DatasetMeta, cases: list[DatasetCase] | None = None) -> DatasetMeta:
        meta.dataset_id = validate_id(meta.dataset_id, "dataset_id")
        cases = cases or []
        meta.case_count = len(cases)
        data_path, meta_path = self.dataset_paths(project_id, meta.dataset_id)
        self.store.write_jsonl(data_path, cases)
        self.store.write_json(meta_path, meta)
        return meta

    def list_datasets(self, project_id: str) -> list[DatasetMeta]:
        metas: list[DatasetMeta] = []
        for path in sorted((self.project_dir(project_id) / "datasets").glob("*.meta.json")):
            metas.append(DatasetMeta.model_validate(self.store.read_json(path)))
        return metas

    def get_dataset(self, project_id: str, dataset_id: str) -> DatasetMeta:
        _, meta_path = self.dataset_paths(project_id, dataset_id)
        return DatasetMeta.model_validate(self.store.read_json(meta_path))

    def list_cases(self, project_id: str, dataset_id: str) -> list[DatasetCase]:
        data_path, _ = self.dataset_paths(project_id, dataset_id)
        return [DatasetCase.model_validate(row) for row in self.store.read_jsonl(data_path)]

    def add_case(self, project_id: str, dataset_id: str, case: DatasetCase) -> DatasetCase:
        cases = self.list_cases(project_id, dataset_id)
        cases.append(case)
        data_path, meta_path = self.dataset_paths(project_id, dataset_id)
        meta = DatasetMeta.model_validate(self.store.read_json(meta_path))
        meta.case_count = len(cases)
        meta.updated_at = now_iso()
        self.store.write_jsonl(data_path, cases)
        self.store.write_json(meta_path, meta)
        return case

    def delete_dataset(self, project_id: str, dataset_id: str) -> dict[str, str]:
        data_path, meta_path = self.dataset_paths(project_id, dataset_id)
        for path in [data_path, meta_path]:
            if path.exists():
                path.unlink()
        return {"status": "deleted", "dataset_id": dataset_id}

    def run_dir(self, project_id: str, run_id: str) -> Path:
        path = self.project_dir(project_id) / "runs" / validate_id(run_id, "run_id")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_run(self, run: EvalRun, results: list[EvalResult], metrics: dict[str, Any]) -> None:
        root = self.run_dir(run.project_id, run.run_id)
        self.store.write_json(root / "run.json", run)
        self.store.write_jsonl(root / "results.jsonl", results)
        self.store.write_json(root / "metrics.json", metrics)

    def update_run(self, run: EvalRun) -> None:
        self.store.write_json(self.run_dir(run.project_id, run.run_id) / "run.json", run)

    def get_run(self, project_id: str, run_id: str) -> EvalRun:
        return EvalRun.model_validate(self.store.read_json(self.run_dir(project_id, run_id) / "run.json"))

    def list_runs(self, project_id: str) -> list[EvalRun]:
        runs: list[EvalRun] = []
        for file in sorted((self.project_dir(project_id) / "runs").glob("*/run.json"), reverse=True):
            runs.append(EvalRun.model_validate(self.store.read_json(file)))
        return runs

    def get_results(self, project_id: str, run_id: str) -> list[EvalResult]:
        return [EvalResult.model_validate(row) for row in self.store.read_jsonl(self.run_dir(project_id, run_id) / "results.jsonl")]

    def get_metrics(self, project_id: str, run_id: str) -> dict[str, Any]:
        return self.store.read_json(self.run_dir(project_id, run_id) / "metrics.json")

    def write_trace(self, trace: Trace, spans: list[Span]) -> None:
        root = self.project_dir(trace.project_id) / "traces" / validate_id(trace.trace_id, "trace_id")
        root.mkdir(parents=True, exist_ok=True)
        self.store.write_json(root / "trace.json", trace)
        self.store.write_jsonl(root / "spans.jsonl", spans)

    def list_traces(self, project_id: str) -> list[Trace]:
        traces: list[Trace] = []
        for file in sorted((self.project_dir(project_id) / "traces").glob("*/trace.json"), reverse=True):
            traces.append(Trace.model_validate(self.store.read_json(file)))
        return traces

    def get_trace(self, project_id: str, trace_id: str) -> Trace:
        root = self.project_dir(project_id) / "traces" / validate_id(trace_id, "trace_id")
        return Trace.model_validate(self.store.read_json(root / "trace.json"))

    def get_spans(self, project_id: str, trace_id: str) -> list[Span]:
        root = self.project_dir(project_id) / "traces" / validate_id(trace_id, "trace_id")
        return [Span.model_validate(row) for row in self.store.read_jsonl(root / "spans.jsonl")]

    def write_report(self, project_id: str, manifest: ReportManifest, markdown: str, html: str, payload: dict[str, Any]) -> ReportManifest:
        root = self.project_dir(project_id) / "reports"
        root.mkdir(parents=True, exist_ok=True)
        self.store._atomic_write(root / f"{manifest.report_id}.md", markdown)
        self.store._atomic_write(root / f"{manifest.report_id}.html", html)
        self.store.write_json(root / f"{manifest.report_id}.json", payload | {"manifest": manifest.model_dump()})
        self.store.write_json(root / f"{manifest.report_id}.manifest.json", manifest)
        return manifest

    def list_reports(self, project_id: str) -> list[ReportManifest]:
        reports: list[ReportManifest] = []
        for path in sorted((self.project_dir(project_id) / "reports").glob("*.manifest.json"), reverse=True):
            reports.append(ReportManifest.model_validate(self.store.read_json(path)))
        return reports

    def get_report(self, project_id: str, report_id: str) -> dict[str, Any]:
        root = self.project_dir(project_id) / "reports"
        report_id = validate_id(report_id, "report_id")
        return {
            "manifest": self.store.read_json(root / f"{report_id}.manifest.json"),
            "markdown": (root / f"{report_id}.md").read_text(encoding="utf-8"),
            "html": (root / f"{report_id}.html").read_text(encoding="utf-8"),
            "json": self.store.read_json(root / f"{report_id}.json"),
        }

    def write_review(self, review: ReviewAnnotation) -> ReviewAnnotation:
        root = self.project_dir(review.project_id) / "reviews"
        root.mkdir(parents=True, exist_ok=True)
        self.store.write_json(root / f"{validate_id(review.review_id, 'review_id')}.json", review)
        return review

    def list_reviews(self, project_id: str) -> list[ReviewAnnotation]:
        return [
            ReviewAnnotation.model_validate(self.store.read_json(path))
            for path in sorted((self.project_dir(project_id) / "reviews").glob("*.json"), reverse=True)
        ]

    def get_review(self, project_id: str, review_id: str) -> ReviewAnnotation:
        return ReviewAnnotation.model_validate(self.store.read_json(self.project_dir(project_id) / "reviews" / f"{validate_id(review_id, 'review_id')}.json"))

    def write_quality_gate(self, project_id: str, gate: QualityGate) -> QualityGate:
        self.store.write_yaml(self.project_dir(project_id) / "quality_gates.yaml", gate)
        return gate

    def get_quality_gate(self, project_id: str) -> QualityGate:
        path = self.project_dir(project_id) / "quality_gates.yaml"
        if not path.exists():
            return self.write_quality_gate(project_id, QualityGate())
        return QualityGate.model_validate(self.store.read_yaml(path))
