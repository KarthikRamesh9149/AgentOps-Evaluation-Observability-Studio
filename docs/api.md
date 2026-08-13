# API and authentication

`GET /health` is the only unauthenticated endpoint. Application routes and generated API documentation fail closed behind bearer authentication.

Configure comma-separated `API_TOKENS` records in the form `token_id:role:sha256_digest`; never configure plaintext secrets. A client sends `Authorization: Bearer token_id.secret`. Roles are `viewer`, `reviewer`, `operator`, and `admin`: reads are available to every role, review writes to reviewer/operator/admin, general writes to operator/admin, and deletes to admin only.

The Next.js UI uses its same-origin `/api/backend/*` proxy. Set `AGENTOPS_API_BASE_INTERNAL` and `AGENTOPS_API_TOKEN` only in the frontend server environment. Never expose a token through a `NEXT_PUBLIC_*` variable.

Every request is subject to `MAX_REQUEST_BYTES`, `RATE_LIMIT_REQUESTS`, and `RATE_LIMIT_WINDOW_SECONDS`. Authentication errors are intentionally generic. `ALLOW_INSECURE_LOCAL_DEMO=true` bypasses authentication only with `APP_ENV=local`; it is an explicit localhost demo mode, not a deployment setting.

Interactive OpenAPI documentation is available at `/docs` after authentication. Route groups cover projects, prompts, datasets, runs/results/metrics, reports, sample apps, traces/spans, observability, reviews, quality gates, and provider/evaluator settings.
