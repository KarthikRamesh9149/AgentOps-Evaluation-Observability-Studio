# Evaluation Design

Evaluators return structured objects with `evaluator`, `score`, `passed`, `explanation`, `severity`, and metadata.

## Rule Evaluators

- Exact match
- Keyword match
- JSON validity and JSON schema
- Regex match
- Length rules
- Refusal behavior
- Required sections
- Citation accuracy
- Tool selection and tool success

## Judge Evaluators

Mock judge evaluators are deterministic. OpenAI judge mode is optional and requests compact JSON with short explanations to limit token use.

## Scoring

Each case receives individual evaluator scores plus an average score. A case passes only when all configured evaluators pass.

## Failure Categories

The runner maps failed evaluator families to categories such as `json_invalid`, `missing_citation`, `wrong_tool`, `unsafe`, `faithfulness`, and `quality`.

## Regression Detection

Run comparison computes pass-rate, score, latency, and cost deltas plus improved and worsened case IDs.
