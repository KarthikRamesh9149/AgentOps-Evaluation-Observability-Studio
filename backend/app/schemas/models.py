from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


ProjectType = Literal["prompt_eval", "rag_eval", "agent_eval", "json_output_eval", "mixed"]
RunStatus = Literal["queued", "running", "completed", "failed"]
GateStatus = Literal["pass", "warn", "fail", "not_run"]


class Project(BaseModel):
    project_id: str = Field(default_factory=lambda: new_id("project"))
    name: str
    description: str = ""
    project_type: ProjectType = "mixed"
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    tags: list[str] = []
    default_provider: str = "mock"
    default_model: str = "mock-enterprise-eval"
    quality_gate_config_path: str = "quality_gates.yaml"
    metadata: dict[str, Any] = {}


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    project_type: ProjectType | None = None
    tags: list[str] | None = None
    default_provider: str | None = None
    default_model: str | None = None
    metadata: dict[str, Any] | None = None


class PromptVersion(BaseModel):
    prompt_id: str = Field(default_factory=lambda: new_id("prompt"))
    version: int = 1
    name: str
    system_prompt: str = "You are a precise enterprise support assistant."
    user_template: str = "{input}"
    model: str = "mock-enterprise-eval"
    temperature: float = 0.2
    max_output_tokens: int = 700
    created_at: str = Field(default_factory=now_iso)
    tags: list[str] = []
    notes: str = ""
    metadata: dict[str, Any] = {}


class DatasetCase(BaseModel):
    case_id: str = Field(default_factory=lambda: new_id("case"))
    input: str
    expected_output: str | None = None
    expected_keywords: list[str] = []
    reference_answer: str | None = None
    expected_json_schema: dict[str, Any] | None = None
    expected_tool_calls: list[str] = []
    expected_citations: list[str] = []
    metadata: dict[str, Any] = {}
    tags: list[str] = []
    category: str = "general"


class DatasetMeta(BaseModel):
    dataset_id: str = Field(default_factory=lambda: new_id("dataset"))
    name: str
    description: str = ""
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    case_count: int = 0
    tags: list[str] = []
    metadata: dict[str, Any] = {}


class EvaluatorResult(BaseModel):
    evaluator: str
    score: float
    passed: bool
    explanation: str
    severity: str = "info"
    metadata: dict[str, Any] = {}


class EvalResult(BaseModel):
    case_id: str
    input: str
    output: str
    expected_output: str | None = None
    reference_answer: str | None = None
    evaluator_results: list[EvaluatorResult] = []
    scores: dict[str, float] = {}
    passed: bool
    failure_category: str = "none"
    severity: str = "info"
    latency_ms: int
    tokens: dict[str, int] = {}
    estimated_cost: float = 0.0
    trace_id: str | None = None
    created_at: str = Field(default_factory=now_iso)


class RunRequest(BaseModel):
    prompt_id: str
    prompt_version: int = 1
    dataset_id: str
    provider: str = "mock"
    model: str = "mock-enterprise-eval"
    evaluators: list[str] = [
        "keyword",
        "json_validity",
        "citation_accuracy",
        "faithfulness",
        "tool_selection",
        "helpfulness_judge",
    ]
    baseline_run_id: str | None = None
    max_cases: int | None = None


class EvalRun(BaseModel):
    run_id: str = Field(default_factory=lambda: new_id("run"))
    project_id: str
    prompt_id: str
    prompt_version: int
    dataset_id: str
    provider: str
    model: str
    status: RunStatus = "queued"
    started_at: str = Field(default_factory=now_iso)
    completed_at: str | None = None
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    average_score: float = 0.0
    pass_rate: float = 0.0
    average_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    estimated_cost: float = 0.0
    regression_status: str = "not_compared"
    quality_gate_status: GateStatus = "not_run"
    metadata: dict[str, Any] = {}


class Trace(BaseModel):
    trace_id: str = Field(default_factory=lambda: new_id("trace"))
    project_id: str
    run_id: str | None = None
    name: str
    app_type: str = "eval"
    input: str = ""
    output: str = ""
    status: str = "ok"
    start_time: str = Field(default_factory=now_iso)
    end_time: str | None = None
    latency_ms: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    scores: dict[str, float] = {}
    metadata: dict[str, Any] = {}


class Span(BaseModel):
    span_id: str = Field(default_factory=lambda: new_id("span"))
    trace_id: str
    parent_span_id: str | None = None
    span_type: str
    name: str
    input_summary: str = ""
    output_summary: str = ""
    status: str = "ok"
    start_time: str = Field(default_factory=now_iso)
    end_time: str | None = None
    latency_ms: int = 0
    tokens: dict[str, int] = {}
    estimated_cost: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = {}


class ReviewAnnotation(BaseModel):
    review_id: str = Field(default_factory=lambda: new_id("review"))
    project_id: str
    run_id: str
    case_id: str
    trace_id: str | None = None
    reviewer_label: str = "needs_human_review"
    reviewer_note: str = ""
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class QualityGate(BaseModel):
    minimum_pass_rate: float = 0.75
    minimum_average_score: float = 0.70
    minimum_faithfulness: float = 0.70
    minimum_citation_accuracy: float = 0.70
    maximum_p95_latency_ms: int = 15000
    maximum_average_cost: float = 0.05
    maximum_failure_rate: float = 0.25
    blocked_failure_categories: list[str] = ["unsafe", "wrong_tool", "json_invalid"]
    warning_thresholds: dict[str, float] = {"minimum_pass_rate": 0.85}
    required_evaluators: list[str] = ["keyword", "helpfulness_judge"]


class ReportManifest(BaseModel):
    report_id: str = Field(default_factory=lambda: new_id("report"))
    project_id: str
    run_id: str | None = None
    title: str
    markdown_path: str
    html_path: str
    json_path: str
    created_at: str = Field(default_factory=now_iso)
    metadata: dict[str, Any] = {}
