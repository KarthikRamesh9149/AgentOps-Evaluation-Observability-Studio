# Repository Threat Model

## Product Surface

AgentOps Evaluation & Observability Studio is a local-first FastAPI and Next.js application. It stores projects, prompts, datasets, runs, traces, reviews, quality gates, reports, and sample documents as local JSON, JSONL, YAML, Markdown, and HTML files under `data/`.

## Assets

- Optional `OPENAI_API_KEY` and model configuration from environment variables.
- Local prompt text, datasets, evaluation outputs, traces, reports, and review annotations.
- File-system integrity under the configured `DATA_DIR`.
- CI trust in mock-mode tests that must not call external APIs.

## Trust Boundaries

- HTTP clients can submit project IDs, prompt IDs, dataset IDs, run IDs, review IDs, JSONL content, prompt text, and report requests.
- The backend crosses from API input into local file paths and local artifact writes.
- Optional OpenAI calls cross from local execution to an external model provider only when explicitly configured.
- The frontend reads local API data and renders report/output content.

## Attacker-Controlled Inputs

- Path-like identifiers in routes and payloads.
- Dataset JSONL rows, prompt templates, metadata, expected citations, regexes, and review notes.
- Run and comparison selectors.
- Report export requests and HTML-rendered model outputs.

## Required Invariants

- Authenticate every route except the sanitized liveness probe.
- Store only token digests, enforce scoped roles, and support overlapping records for rotation.
- Keep backend bearer credentials in the Next.js server process, never browser storage or public build variables.
- Reject oversized requests and rate-limit identities before route execution.
- Reject path traversal and unsafe file names before any file read/write.
- Never expose environment secrets through API responses.
- Do not commit `.env` or real keys.
- Keep OpenAI mode opt-in and never required for tests or CI.
- Treat generated reports as local artifacts and escape rendered HTML content.
- Store concise evaluator explanations only; do not store hidden prompts or private reasoning.

## High-Impact Failure Modes

- Missing authentication or an authorization policy that lets read-only tokens mutate artifacts.
- Token disclosure through browser bundles, environment responses, traces, or logs.
- Resource exhaustion through unbounded bodies or request floods.
- Path traversal causing reads or writes outside `DATA_DIR`.
- Secret leakage through settings, traces, reports, logs, or frontend rendering.
- Unexpected external API calls in tests or default local workflows.
- Corrupted local artifacts breaking project load paths without useful errors.
- Stored HTML/script injection through report rendering or output display.
- Quality gate bypass due to incorrect metric aggregation or failed category handling.

## Operational Residual Risks

The token model represents service identities rather than individual humans and does not provide SSO, MFA, or lifecycle automation. The in-memory limiter is process-local. File storage assumes a trusted single-writer deployment. Any shared or internet-facing deployment should add TLS, an identity-aware proxy or IdP, a distributed limiter, centralized audit logs, and database/object-store controls.
