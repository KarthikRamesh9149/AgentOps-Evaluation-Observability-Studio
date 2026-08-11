# API

Base URL: `http://127.0.0.1:8000`

## Authentication

Every endpoint except `GET /health` requires `Authorization: Bearer <API_AUTH_TOKEN>`.
Set a unique high-entropy `API_AUTH_TOKEN` of at least 32 characters outside source control before binding the backend to any network interface. Startup rejects a missing token in non-local environments, short configured tokens, and `ALLOW_INSECURE_LOCAL_DEMO=true` outside `APP_ENV=local`. For the offline localhost demo only, `APP_ENV=local` together with `ALLOW_INSECURE_LOCAL_DEMO=true` explicitly disables request authentication; it is disabled by default.

Authentication failures intentionally return only `401 Unauthorized` and do not reveal whether a token is configured or valid.

## Health

- `GET /health`

## Projects

- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `DELETE /projects/{project_id}`

## Prompts

- `GET /projects/{project_id}/prompts`
- `POST /projects/{project_id}/prompts`
- `GET /projects/{project_id}/prompts/{prompt_id}`
- `POST /projects/{project_id}/prompts/{prompt_id}/versions`
- `GET /projects/{project_id}/prompts/{prompt_id}/versions`
- `GET /projects/{project_id}/prompts/{prompt_id}/versions/{version}`

## Datasets

- `GET /projects/{project_id}/datasets`
- `POST /projects/{project_id}/datasets`
- `POST /projects/{project_id}/datasets/import-jsonl`
- `GET /projects/{project_id}/datasets/{dataset_id}`
- `GET /projects/{project_id}/datasets/{dataset_id}/cases`
- `POST /projects/{project_id}/datasets/{dataset_id}/cases`
- `DELETE /projects/{project_id}/datasets/{dataset_id}`

## Eval Runs

- `POST /projects/{project_id}/runs`
- `GET /projects/{project_id}/runs`
- `GET /projects/{project_id}/runs/{run_id}`
- `GET /projects/{project_id}/runs/{run_id}/results`
- `GET /projects/{project_id}/runs/{run_id}/metrics`
- `GET /projects/{project_id}/runs/{run_id}/report`
- `POST /projects/{project_id}/runs/{run_id}/apply-quality-gate`

## Comparisons

- `POST /projects/{project_id}/compare-runs`
- `POST /projects/{project_id}/compare-prompts`
- `POST /projects/{project_id}/compare-models`

## Reports, Samples, Traces, Observability, Review, Gates, Settings

The backend implements report export/list/detail, local RAG and agent sample runs, trace list/detail/spans, observability summary/latency/cost/failure/evaluator endpoints, review CRUD, quality gate read/write/evaluate, and provider/evaluator settings endpoints.
