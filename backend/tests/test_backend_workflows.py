from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.settings import Settings
from app.evaluators.registry import evaluate_case
from app.providers.base import MockLLMProvider, OpenAIProvider
from app.quality_gates.service import evaluate_quality_gate
from app.runners.engine import compare_runs, run_prompt_eval
from app.schemas.models import DatasetCase, DatasetMeta, Project, PromptVersion, QualityGate, ReviewAnnotation, RunRequest
from app.storage.file_store import ValidationFailure, validate_id
from app.storage.repositories import RepositoryHub


@pytest.fixture()
def repo(tmp_path: Path) -> RepositoryHub:
    return RepositoryHub(tmp_path)


def seed_minimal(repo: RepositoryHub) -> None:
    repo.create_project(Project(project_id="demo", name="Demo"))
    repo.create_prompt("demo", PromptVersion(prompt_id="support", name="Support", user_template="{input}"))
    repo.create_dataset(
        "demo",
        DatasetMeta(dataset_id="cases", name="Cases"),
        [
            DatasetCase(case_id="case-refund", input="Can I get a refund?", expected_keywords=["Refund"], expected_citations=["refund_policy.md"], reference_answer="Refund policy applies.", category="rag"),
            DatasetCase(case_id="case-json", input="Extract json", expected_json_schema={"type": "object", "required": ["status"]}, category="json"),
        ],
    )


def test_storage_prompt_dataset_run_trace_review(repo: RepositoryHub) -> None:
    seed_minimal(repo)
    assert repo.get_project("demo").name == "Demo"
    assert repo.get_prompt_version("demo", "support", 1).prompt_id == "support"
    assert len(repo.list_cases("demo", "cases")) == 2
    run = run_prompt_eval(repo, "demo", RunRequest(prompt_id="support", dataset_id="cases"))
    assert run.status == "completed"
    assert repo.get_metrics("demo", run.run_id)["total_cases"] == 2
    assert repo.list_traces("demo")
    review = repo.write_review(ReviewAnnotation(project_id="demo", run_id=run.run_id, case_id="case-refund"))
    assert repo.get_review("demo", review.review_id).case_id == "case-refund"


def test_path_traversal_prevention() -> None:
    with pytest.raises(ValidationFailure):
        validate_id("../secret", "project_id")


def test_mock_provider_and_openai_missing_key() -> None:
    provider = MockLLMProvider()
    first = provider.generate("", "Can I get a refund?", "mock", 0.0, 100)
    second = provider.generate("", "Can I get a refund?", "mock", 0.0, 100)
    assert first.output == second.output
    assert first.tokens["output"] > 0
    os.environ.pop("OPENAI_API_KEY", None)
    judge = OpenAIProvider(api_key=None).judge("helpfulness", "input", "output", "reference")
    assert "score" in judge


def test_evaluators_cover_rules_and_judges() -> None:
    case = DatasetCase(input="Can I get a refund?", expected_keywords=["refund"], expected_citations=["refund_policy.md"], reference_answer="Refund policy applies.", category="rag")
    results = evaluate_case(["keyword", "citation_accuracy", "helpfulness_judge", "faithfulness"], case, "Refund allowed. Citation: refund_policy.md", MockLLMProvider())
    assert all(result.passed for result in results)
    json_case = DatasetCase(input="Extract json", expected_json_schema={"type": "object", "required": ["status"]}, category="json")
    failed = evaluate_case(["json_validity"], json_case, "not json", MockLLMProvider())[0]
    assert not failed.passed


def test_runner_comparison_and_quality_gate(repo: RepositoryHub) -> None:
    seed_minimal(repo)
    first = run_prompt_eval(repo, "demo", RunRequest(prompt_id="support", dataset_id="cases"))
    second = run_prompt_eval(repo, "demo", RunRequest(prompt_id="support", dataset_id="cases"))
    comparison = compare_runs(repo, "demo", first.run_id, second.run_id)
    assert comparison["regression_status"] in {"stable", "improved", "regression"}
    gate = evaluate_quality_gate(second, repo.get_metrics("demo", second.run_id), QualityGate(minimum_pass_rate=0.0))
    assert gate["status"] in {"pass", "warn"}


def test_cli_seed_and_run(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["DATA_DIR"] = str(tmp_path)
    seed = subprocess.run([sys.executable, "-m", "app.cli.main", "seed-demo"], cwd=Path(__file__).parents[1], env=env, text=True, capture_output=True, check=False)
    assert seed.returncode == 0, seed.stderr
    run = subprocess.run([sys.executable, "-m", "app.cli.main", "run-evals"], cwd=Path(__file__).parents[1], env=env, text=True, capture_output=True, check=False)
    assert "pass_rate" in run.stdout
