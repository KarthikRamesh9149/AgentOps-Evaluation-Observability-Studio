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
    # Comma-separated token_id:role:sha256 records. Only hashes are configured.
    api_tokens: str = os.getenv("API_TOKENS", "")
    # This is deliberately opt-in and only honored for a local demo process.
    allow_insecure_local_demo: bool = os.getenv("ALLOW_INSECURE_LOCAL_DEMO", "false").lower() in {
        "1",
        "true",
        "yes",
    }
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
    max_request_bytes: int = int(os.getenv("MAX_REQUEST_BYTES", "1048576"))
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    def __post_init__(self) -> None:
        app_env = self.app_env.lower()
        from app.core.auth import parse_token_registry

        parse_token_registry(self.api_tokens)
        if self.allow_insecure_local_demo and app_env != "local":
            raise ValueError("ALLOW_INSECURE_LOCAL_DEMO is only permitted when APP_ENV=local")
        if app_env != "local" and not self.api_tokens:
            raise ValueError("API_TOKENS is required when APP_ENV is not local")
        if not 1024 <= self.max_request_bytes <= 10 * 1024 * 1024:
            raise ValueError("MAX_REQUEST_BYTES must be between 1024 and 10485760")
        if self.rate_limit_requests < 1 or self.rate_limit_window_seconds < 1:
            raise ValueError("Rate-limit values must be positive")

    @property
    def insecure_local_demo_enabled(self) -> bool:
        return self.app_env.lower() == "local" and self.allow_insecure_local_demo

    @property
    def token_registry(self) -> dict[str, tuple[str, str]]:
        from app.core.auth import parse_token_registry

        return parse_token_registry(self.api_tokens)


def get_settings() -> Settings:
    return Settings()
