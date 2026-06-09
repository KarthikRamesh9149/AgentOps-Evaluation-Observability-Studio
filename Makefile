.PHONY: backend-install frontend-install backend-dev frontend-dev dev seed-demo backend-test backend-lint backend-typecheck frontend-typecheck frontend-build evals quality-gate report verify

backend-install:
	cd backend && python -m pip install -e ".[dev]"

frontend-install:
	cd frontend && npm install

backend-dev:
	cd backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend-dev:
	cd frontend && npm run dev

dev:
	$(MAKE) backend-dev

seed-demo:
	cd backend && python -m app.cli.main seed-demo

backend-test:
	cd backend && python -m pytest

backend-lint:
	cd backend && python -m ruff check app tests

backend-typecheck:
	cd backend && python -m mypy app

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-build:
	cd frontend && npm run build

evals:
	cd backend && python -m app.cli.main run-evals --project-id demo-agentops-quality-studio --prompt-id support-agent --dataset-id prompt-regression-eval

quality-gate:
	cd backend && python -m app.cli.main apply-quality-gate --project-id demo-agentops-quality-studio

report:
	cd backend && python -m app.cli.main generate-report --project-id demo-agentops-quality-studio

verify:
	$(MAKE) backend-lint
	$(MAKE) backend-typecheck
	$(MAKE) backend-test
	$(MAKE) frontend-typecheck
	$(MAKE) frontend-build
	$(MAKE) seed-demo
	$(MAKE) evals
	$(MAKE) quality-gate
