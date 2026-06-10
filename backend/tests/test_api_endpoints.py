from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.core.settings import Settings
from app.main import app
from app.storage.repositories import RepositoryHub


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    settings = Settings(data_dir=tmp_path)

    def override_settings() -> Settings:
        return settings

    def override_repo() -> RepositoryHub:
        return RepositoryHub(settings.data_dir)

    app.dependency_overrides[routes.get_settings] = override_settings
    app.dependency_overrides[routes.repo] = override_repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_project(client: TestClient) -> None:
    response = client.post(
        "/projects",
        json={
            "project_id": "api-demo",
            "name": "API Demo",
            "description": "Endpoint coverage workspace",
            "project_type": "mixed",
        },
    )
    assert response.status_code == 200, response.text
    prompt = client.post(
        "/projects/api-demo/prompts",
        json={
            "prompt_id": "support",
            "name": "Support",
            "system_prompt": "Answer concisely. Citation: refund_policy.md",
            "user_template": "{input}",
        },
    )
    assert prompt.status_code == 200, prompt.text
    dataset = client.post(
        "/projects/api-demo/datasets",
        json={
            "meta": {"dataset_id": "cases", "name": "Cases"},
            "cases": [
                {
                    "case_id": "case-refund",
                    "input": "Can I get a refund?",
                    "expected_keywords": ["Refund"],
                    "expected_citations": ["refund_policy.md"],
                    "reference_answer": "Refund policy applies.",
                    "category": "rag",
                }
            ],
        },
    )
    assert dataset.status_code == 200, dataset.text


def test_project_prompt_dataset_endpoints(client: TestClient) -> None:
    seed_project(client)
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/projects").json()[0]["project_id"] == "api-demo"
    patched = client.patch("/projects/api-demo", json={"tags": ["api", "tested"]})
    assert patched.status_code == 200
    assert "tested" in patched.json()["tags"]
    assert client.get("/projects/api-demo/prompts").json()[0]["prompt_id"] == "support"
    version = client.post(
        "/projects/api-demo/prompts/support/versions",
        json={"name": "Support v2", "system_prompt": "v2", "user_template": "{input}"},
    )
    assert version.json()["version"] == 2
    assert len(client.get("/projects/api-demo/prompts/support/versions").json()) == 2
    assert client.get("/projects/api-demo/datasets/cases").json()["case_count"] == 1
    added = client.post(
        "/projects/api-demo/datasets/cases/cases",
        json={"case_id": "case-2", "input": "Where is my package?"},
    )
    assert added.status_code == 200
    assert len(client.get("/projects/api-demo/datasets/cases/cases").json()) == 2


def test_run_report_trace_observability_quality_and_review_endpoints(client: TestClient) -> None:
    seed_project(client)
    run_response = client.post(
        "/projects/api-demo/runs",
        json={
            "prompt_id": "support",
            "prompt_version": 1,
            "dataset_id": "cases",
            "provider": "mock",
            "model": "mock-enterprise-eval",
            "evaluators": ["length"],
        },
    )
    assert run_response.status_code == 200, run_response.text
    run = run_response.json()
    run_id = run["run_id"]
    assert run["quality_gate_status"] == "pass"
    assert client.get(f"/projects/api-demo/runs/{run_id}/metrics").json()["total_cases"] == 1
    results = client.get(f"/projects/api-demo/runs/{run_id}/results").json()
    assert results[0]["trace_id"]
    assert client.get(f"/projects/api-demo/runs/{run_id}/report").json()["markdown"].startswith("#")
    gate = client.post(f"/projects/api-demo/runs/{run_id}/apply-quality-gate")
    assert gate.json()["status"] == "pass"
    exported = client.post("/projects/api-demo/export-report", json={"run_id": run_id})
    assert exported.status_code == 200
    assert client.get("/projects/api-demo/reports").json()
    trace_id = results[0]["trace_id"]
    assert client.get(f"/projects/api-demo/traces/{trace_id}").json()["trace_id"] == trace_id
    assert client.get(f"/projects/api-demo/traces/{trace_id}/spans").json()
    assert client.get("/projects/api-demo/observability/summary").json()["total_traces"] >= 1
    assert isinstance(client.get("/projects/api-demo/observability/failures").json(), dict)
    review = client.post(
        "/projects/api-demo/reviews",
        json={
            "project_id": "api-demo",
            "run_id": run_id,
            "case_id": "case-refund",
            "trace_id": trace_id,
            "reviewer_label": "accepted",
        },
    )
    assert review.status_code == 200
    review_id = review.json()["review_id"]
    updated = client.patch(
        f"/projects/api-demo/reviews/{review_id}",
        json={"reviewer_note": "Looks correct."},
    )
    assert updated.json()["reviewer_note"] == "Looks correct."
    gate_config = client.get("/projects/api-demo/quality-gates")
    assert gate_config.status_code == 200
    assert client.post("/projects/api-demo/quality-gates/evaluate-run", json={"run_id": run_id}).json()[
        "status"
    ] == "pass"


def test_sample_app_settings_and_error_endpoints(client: TestClient) -> None:
    seed_project(client)
    rag = client.post("/projects/api-demo/sample-apps/rag/run", json={"question": "Can I get a refund?"})
    assert rag.status_code == 200
    assert rag.json()["trace_id"]
    agent = client.post("/projects/api-demo/sample-apps/agent/run", json={"input": "Create a support ticket."})
    assert agent.status_code == 200
    assert agent.json()["tool_calls"] == ["create_support_ticket"]
    providers = client.get("/settings/providers").json()
    assert providers["providers"][0]["name"] == "mock"
    assert client.get("/settings/evaluators").json()
    missing = client.get("/projects/api-demo/runs/not-real")
    assert missing.status_code == 404
    blocked = client.get("/projects/..%2Fsecret")
    assert blocked.status_code in {400, 404}
