# Architecture

The system is a local web app with a FastAPI backend and Next.js frontend. The backend owns all artifact reads and writes. The frontend is a dashboard and workflow surface that calls the local API.

## Backend

- `app/api`: route handlers.
- `app/storage`: safe file store and repositories.
- `app/providers`: mock and OpenAI model abstractions.
- `app/evaluators`: rule and judge evaluator registry.
- `app/runners`: batch runner, metrics, comparison, and regression logic.
- `app/tracing`: trace and span helpers.
- `app/reports`: Markdown and HTML report generation.
- `app/sample_apps`: local RAG and support-agent examples.
- `app/cli`: local CI-style commands.

## Frontend

The frontend uses the Next.js App Router, TypeScript, Tailwind CSS, and Recharts. Pages fetch from `NEXT_PUBLIC_API_BASE`, defaulting to `http://127.0.0.1:8000`.

## Local File Storage

The repository layer maps project IDs to folders under `DATA_DIR/projects`. Identifiers are validated with a conservative allowlist. JSON, JSONL, YAML, Markdown, and HTML are written atomically where practical.

## Evaluation Runner

The runner loads a prompt version and dataset, renders each case, calls the provider, applies evaluators, writes results, writes traces, aggregates metrics, applies a quality gate, and creates reports.

## Provider Architecture

`MockLLMProvider` is deterministic and network-free. `OpenAIProvider` is optional and reads only from environment variables.

## Trace Architecture

Each eval case can create a trace with `llm` and `evaluator` spans. Sample apps add `retriever`, `tool`, and `agent_step` spans.
