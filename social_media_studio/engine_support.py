from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any


SCHEMA_VERSION = 1
TASK_STATES = {
    "PENDING", "READY", "RUNNING", "WAITING_INPUT", "BLOCKED",
    "FAILED", "COMPLETED", "STALE", "CANCELLED",
}
RIGHTS_ALLOWED = {"OWNED", "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN"}
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class StudioError(RuntimeError):
    """Base error for the standalone Social Media Studio runtime."""


class ProjectNotFound(StudioError):
    pass


class ContractError(StudioError):
    pass


class ClaimError(StudioError):
    pass


class GateError(StudioError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _now()).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, default: Any = None) -> Any:
    return json.loads(value) if value is not None else default


def _safe_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ContractError(f"{label} must match {_ID.pattern}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(root: Path, candidate: str | Path) -> Path:
    path = Path(candidate)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve(strict=True)
    base = root.resolve(strict=True)
    if resolved != base and base not in resolved.parents:
        raise ContractError(f"artifact path escapes project workspace: {candidate}")
    if not resolved.is_file():
        raise ContractError(f"artifact must be a regular file: {candidate}")
    return resolved


@dataclass(frozen=True)
class TaskClaim:
    project_id: str
    task_id: str
    worker_id: str
    claim_token: str
    lease_until: str
    attempt: int


