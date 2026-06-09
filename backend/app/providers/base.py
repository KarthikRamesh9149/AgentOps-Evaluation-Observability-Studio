from __future__ import annotations

import os
import time
from dataclasses import dataclass


@dataclass
class LLMResponse:
    output: str
    latency_ms: int
    tokens: dict[str, int]
    estimated_cost: float
    model: str
    provider: str
    metadata: dict[str, object]


class LLMProvider:
    name = "base"

    def generate(self, system_prompt: str, user_prompt: str, model: str, temperature: float, max_tokens: int) -> LLMResponse:
        raise NotImplementedError

    def judge(self, criterion: str, input_text: str, output_text: str, reference: str | None = None) -> dict[str, object]:
        raise NotImplementedError


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) + len(text) // 24)


def estimate_cost(tokens: dict[str, int], model: str) -> float:
    rate = 0.00000015 if "nano" in model or "mock" in model else 0.0000006
    return round((tokens.get("input", 0) + tokens.get("output", 0)) * rate, 6)


class MockLLMProvider(LLMProvider):
    name = "mock"

    def __init__(self, latency_ms: int = 35):
        self.latency_ms = latency_ms

    def generate(self, system_prompt: str, user_prompt: str, model: str, temperature: float, max_tokens: int) -> LLMResponse:
        start = time.perf_counter()
        lower = user_prompt.lower()
        if "json" in lower or "extract" in lower:
            output = '{"status":"resolved","category":"support","confidence":0.91}'
        elif "refund" in lower:
            output = "Refund requests are eligible when policy conditions are met. Citation: refund_policy.md"
        elif "package" in lower or "shipping" in lower:
            output = "Shipping status can be checked using the order lookup tool. Citation: shipping_policy.md"
        elif "damaged" in lower:
            output = "I can create a support ticket for a damaged order and include the evidence provided."
        elif "bad" in lower or "unsafe" in lower:
            output = "I cannot help with unsafe or policy-violating requests."
        else:
            output = "Here is a concise, policy-grounded answer with the required context and next action."
        tokens = {"input": estimate_tokens(system_prompt + user_prompt), "output": estimate_tokens(output)}
        elapsed = int((time.perf_counter() - start) * 1000) + self.latency_ms
        return LLMResponse(output, elapsed, tokens, estimate_cost(tokens, model), model, self.name, {"mock": True})

    def judge(self, criterion: str, input_text: str, output_text: str, reference: str | None = None) -> dict[str, object]:
        joined = f"{input_text} {output_text} {reference or ''}".lower()
        score = 0.9
        if "missing citation" in joined or ("citation" in criterion and ".md" not in output_text):
            score = 0.35
        if "wrong tool" in joined or "unsafe" in joined and "cannot" not in output_text.lower():
            score = 0.3
        if reference and not any(word in output_text.lower() for word in reference.lower().split()[:5]):
            score = min(score, 0.65)
        return {
            "score": score,
            "passed": score >= 0.7,
            "explanation": f"Deterministic mock judge score for {criterion}.",
        }


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def _client(self):
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        from openai import OpenAI

        return OpenAI(api_key=self.api_key)

    def generate(self, system_prompt: str, user_prompt: str, model: str, temperature: float, max_tokens: int) -> LLMResponse:
        start = time.perf_counter()
        response = self._client().responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        output = getattr(response, "output_text", "") or ""
        tokens = {"input": estimate_tokens(system_prompt + user_prompt), "output": estimate_tokens(output)}
        return LLMResponse(
            output=output,
            latency_ms=int((time.perf_counter() - start) * 1000),
            tokens=tokens,
            estimated_cost=estimate_cost(tokens, model),
            model=model,
            provider=self.name,
            metadata={"mock": False, "estimated_tokens": True},
        )

    def judge(self, criterion: str, input_text: str, output_text: str, reference: str | None = None) -> dict[str, object]:
        if not self.api_key:
            return MockLLMProvider().judge(criterion, input_text, output_text, reference)
        prompt = (
            "Return compact JSON with score number 0-1, passed boolean, explanation under 20 words. "
            f"Criterion: {criterion}\nInput: {input_text[:1200]}\nOutput: {output_text[:1200]}\nReference: {(reference or '')[:1200]}"
        )
        response = self.generate("You are a strict evaluator.", prompt, os.getenv("OPENAI_JUDGE_MODEL", "gpt-4.1-mini"), 0, 160)
        import json

        try:
            return json.loads(response.output)
        except json.JSONDecodeError:
            return {"score": 0.5, "passed": False, "explanation": "Judge output was not valid JSON."}


def provider_factory(name: str, latency_ms: int = 35) -> LLMProvider:
    if name == "openai":
        return OpenAIProvider()
    return MockLLMProvider(latency_ms=latency_ms)
