from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "local")
    data_dir: Path = Path(os.getenv("DATA_DIR", "../data")).resolve()
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_small_model: str = os.getenv("OPENAI_SMALL_MODEL", "gpt-4.1-nano")
    openai_judge_model: str = os.getenv("OPENAI_JUDGE_MODEL", "gpt-4.1-mini")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    openai_max_output_tokens: int = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "700"))
    mock_provider_latency_ms: int = int(os.getenv("MOCK_PROVIDER_LATENCY_MS", "35"))
    default_quality_gate_path: str = os.getenv("DEFAULT_QUALITY_GATE_PATH", "quality_gates.yaml")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


def get_settings() -> Settings:
    return Settings()
