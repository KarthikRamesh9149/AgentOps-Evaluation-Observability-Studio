# Tracing Design

Traces follow OpenTelemetry-style concepts while staying local.

## Trace Model

A trace captures project, run, app type, input, output, status, latency, token estimate, estimated cost, and scores.

## Span Model

Spans capture parent-child linkage, span type, name, summaries, status, latency, tokens, estimated cost, errors, and metadata.

## Span Types

Supported span types include `llm`, `retriever`, `reranker`, `tool`, `evaluator`, `guardrail`, `parser`, `agent_step`, `report`, and `quality_gate`.

## Waterfall

The frontend trace detail page renders spans as a simple latency waterfall.

## Storage

Traces are stored as `trace.json`; spans are stored as `spans.jsonl`.
