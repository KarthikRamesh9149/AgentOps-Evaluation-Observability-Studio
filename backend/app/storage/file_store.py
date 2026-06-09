from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from app.core.errors import NotFoundError, ValidationFailure

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,96}$")
T = TypeVar("T", bound=BaseModel)


def validate_id(value: str, label: str = "id") -> str:
    if not ID_RE.match(value) or ".." in value or "/" in value or "\\" in value:
        raise ValidationFailure(f"Invalid {label}: {value!r}")
    return value


class FileStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, *parts: str) -> Path:
        clean = [validate_id(part, "path segment") for part in parts if part]
        target = self.root.joinpath(*clean).resolve()
        if self.root not in target.parents and target != self.root:
            raise ValidationFailure("Path traversal blocked")
        return target

    def ensure_dir(self, *parts: str) -> Path:
        target = self.path(*parts)
        target.mkdir(parents=True, exist_ok=True)
        return target

    def read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise NotFoundError(f"Missing file: {path.name}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationFailure(f"Corrupted JSON file: {path.name}") from exc

    def write_json(self, path: Path, payload: BaseModel | dict[str, Any] | list[Any]) -> None:
        self._atomic_write(path, json.dumps(_dump(payload), indent=2, sort_keys=True) + "\n")

    def read_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise NotFoundError(f"Missing file: {path.name}")
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ValidationFailure(f"Corrupted YAML file: {path.name}") from exc

    def write_yaml(self, path: Path, payload: BaseModel | dict[str, Any]) -> None:
        self._atomic_write(path, yaml.safe_dump(_dump(payload), sort_keys=False))

    def read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            raise NotFoundError(f"Missing file: {path.name}")
        rows: list[dict[str, Any]] = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationFailure(f"Invalid JSONL at {path.name}:{line_no}") from exc
            if not isinstance(row, dict):
                raise ValidationFailure(f"JSONL row must be an object at {path.name}:{line_no}")
            rows.append(row)
        return rows

    def write_jsonl(self, path: Path, rows: Iterable[BaseModel | dict[str, Any]]) -> None:
        text = "".join(json.dumps(_dump(row), sort_keys=True) + "\n" for row in rows)
        self._atomic_write(path, text)

    def _atomic_write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=path.parent) as tmp:
            tmp.write(text)
            tmp_name = tmp.name
        os.replace(tmp_name, path)


def _dump(payload: BaseModel | dict[str, Any] | list[Any]) -> Any:
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json")
    if isinstance(payload, list):
        return [_dump(item) if isinstance(item, BaseModel | dict) else item for item in payload]
    if isinstance(payload, dict):
        return {key: _dump(value) if isinstance(value, BaseModel | dict | list) else value for key, value in payload.items()}
    return payload
