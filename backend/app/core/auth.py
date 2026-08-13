from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

ROLES = {"viewer", "reviewer", "operator", "admin"}


@dataclass(frozen=True)
class TokenPrincipal:
    token_id: str
    role: str


def token_digest(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def parse_token_registry(raw: str) -> dict[str, tuple[str, str]]:
    """Parse `token_id:role:sha256` records; plaintext secrets are never configured."""
    registry: dict[str, tuple[str, str]] = {}
    for record in filter(None, (item.strip() for item in raw.split(","))):
        parts = record.split(":")
        if len(parts) != 3:
            raise ValueError("API_TOKENS entries must be token_id:role:sha256")
        token_id, role, digest = parts
        if not token_id or not token_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError("API token IDs must be URL-safe identifiers")
        if role not in ROLES:
            raise ValueError(f"Unsupported API token role: {role}")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("API token digests must be lowercase SHA-256 hex")
        if token_id in registry:
            raise ValueError(f"Duplicate API token ID: {token_id}")
        registry[token_id] = (role, digest)
    return registry


def authenticate_bearer(authorization: str, registry: dict[str, tuple[str, str]]) -> TokenPrincipal | None:
    scheme, separator, credential = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer":
        return None
    token_id, dot, secret = credential.partition(".")
    record = registry.get(token_id)
    if not dot or not secret or record is None:
        # Keep comparable work on unknown IDs to reduce timing distinction.
        hmac.compare_digest(token_digest(secret), "0" * 64)
        return None
    role, expected_digest = record
    if not hmac.compare_digest(token_digest(secret), expected_digest):
        return None
    return TokenPrincipal(token_id=token_id, role=role)


def required_role(method: str, path: str) -> set[str]:
    if method == "GET":
        return ROLES
    if "/reviews" in path and method in {"POST", "PATCH"}:
        return {"reviewer", "operator", "admin"}
    if method == "DELETE":
        return {"admin"}
    return {"operator", "admin"}
