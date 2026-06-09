from __future__ import annotations

from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.schemas.models import Span, Trace, now_iso


def run_rag(project_id: str, question: str, docs_dir: Path) -> tuple[dict[str, object], Trace, list[Span]]:
    docs = [(path.name, path.read_text(encoding="utf-8")) for path in sorted(docs_dir.glob("*.md"))]
    if not docs:
        docs = [("product_faq.md", "Refunds and shipping are handled by support policies.")]
    names, texts = zip(*docs, strict=False)
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([*texts, question])
    sims = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    best_index = int(sims.argmax())
    citation = names[best_index]
    context = texts[best_index]
    answer = f"{context.splitlines()[0]} Citation: {citation}"
    trace = Trace(project_id=project_id, name="local-rag-qa", app_type="rag", input=question, output=answer, end_time=now_iso(), latency_ms=42, scores={"retrieval_similarity": float(sims[best_index])})
    spans = [
        Span(trace_id=trace.trace_id, span_type="retriever", name="tfidf.retrieve", input_summary=question, output_summary=citation, end_time=now_iso(), latency_ms=12),
        Span(trace_id=trace.trace_id, span_type="llm", name="mock.answer", input_summary=context[:240], output_summary=answer[:240], end_time=now_iso(), latency_ms=30),
    ]
    return {"answer": answer, "citations": [citation], "context": context[:1000], "score": float(sims[best_index])}, trace, spans
