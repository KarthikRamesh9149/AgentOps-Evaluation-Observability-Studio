# Local Development

## Install

```bash
make backend-install
make frontend-install
```

## Environment

Copy `.env.example` if you want to customize local settings. Mock mode is default. Set `OPENAI_API_KEY` only for explicit OpenAI runs.

## Seed Demo Data

```bash
make seed-demo
```

## Run

```bash
make backend-dev
make frontend-dev
```

## Test

```bash
make backend-test
make frontend-typecheck
make frontend-build
```

## Troubleshooting

- If the frontend shows a request error, confirm the backend is on `127.0.0.1:8000`.
- If OpenAI mode fails, confirm `OPENAI_API_KEY` is set in your shell.
- If artifacts look stale, remove the specific local project folder under `data/projects`.
