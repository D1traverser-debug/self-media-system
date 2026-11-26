from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Mapping

from ..engine import ContractError, StudioError


class DomainAdapterError(StudioError):
    """A scoped domain adapter rejected its declared input or operation."""


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_jsonable(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    return value

def _mapping(payload: Any, label: str) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise DomainAdapterError(f"{label} must be a JSON object")
    return dict(payload)

def _string_tuple(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) and item.strip() for item in value):
        raise DomainAdapterError(f"{label} must be an array of non-empty strings")
    return tuple(value)

def _input_json(packet: Mapping[str, Any], name: str) -> dict[str, Any]:
    artifact = packet["input_artifacts"].get(name)
    if artifact is None:
        raise DomainAdapterError(f"required declared JSON input is unavailable: {name}")
    path = Path(artifact["path"])
    try:
        return _mapping(json.loads(path.read_text(encoding="utf-8")), f"input {name}")
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainAdapterError(f"cannot read JSON input {name}: {exc}") from exc

def _input_path(packet: Mapping[str, Any], name: str) -> Path:
    artifact = packet["input_artifacts"].get(name)
    if artifact is None:
        raise DomainAdapterError(f"required declared input is unavailable: {name}")
    path = Path(artifact["path"])
    if not path.is_file():
        raise DomainAdapterError(f"declared input file is missing: {name}")
    return path

def _safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    if not safe:
        raise DomainAdapterError("output name cannot be converted to a safe filename")
    return safe[:100]

def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise DomainAdapterError(f"adapter output already exists; refusing overwrite: {path.name}")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2) + "\n")

__all__ = [
    "asdict", "is_dataclass", "datetime", "json", "Path", "re", "Any", "Mapping",
    "ContractError", "StudioError", "DomainAdapterError",
    "_jsonable", "_mapping", "_string_tuple", "_input_json", "_input_path",
    "_safe_filename", "_write_json",
]
