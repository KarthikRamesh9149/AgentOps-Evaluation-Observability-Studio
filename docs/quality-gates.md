# Quality Gates

Quality gates live at `data/projects/{project_id}/quality_gates.yaml`.

## Thresholds

- Minimum pass rate
- Minimum average score
- Minimum faithfulness
- Minimum citation accuracy
- Maximum p95 latency
- Maximum average cost
- Maximum failure rate
- Blocked failure categories
- Required evaluators

## Behavior

The gate returns `pass`, `warn`, or `fail`. CLI eval commands exit `0` for pass or warn and `1` for fail.

## CI Usage

The workflow seeds demo data, runs mock evals, and applies the quality gate without secrets.
