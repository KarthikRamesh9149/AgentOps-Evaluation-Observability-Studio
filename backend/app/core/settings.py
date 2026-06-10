from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_local_env() -> None:
    candidates = [Path.cwd() / ".env", *[parent / ".env" for parent in Path.cwd().parents]]
    for path in candidates:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        os.environ.setdefault("LOCAL_ENV_DIR", str(path.parent))
        return


_load_local_env()


def _data_dir() -> Path:
    raw = Path(os.getenv("DATA_DIR", "../data"))
    if raw.is_absolute():
        return raw.resolve()
    base = Path(os.getenv("LOCAL_ENV_DIR", Path.cwd()))
    return (base / raw).resolve()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "local")
    data_dir: Path = _data_dir()
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_small_model: str = os.getenv("OPENAI_SMALL_MODEL", "gpt-4.1-nano")
    openai_judge_model: str = os.getenv("OPENAI_JUDGE_MODEL", "gpt-4.1-mini")
    openai_enable_judge: bool = os.getenv("OPENAI_ENABLE_JUDGE", "false").lower() in {
        "1",
        "true",
        "yes",
    }
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
