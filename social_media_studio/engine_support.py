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




def validate_brief(brief: dict[str, Any]) -> None:
    """Pure validation of the project outcome and release-policy envelope."""
    if not isinstance(brief, dict):
        raise ContractError("brief must be a JSON object")
    required = ["goal", "audience", "deliverables"]
    missing = [key for key in required if not brief.get(key)]
    if missing:
        raise ContractError(f"brief is missing required outcome fields: {missing}")
    if not isinstance(brief["goal"], str) or not isinstance(brief["audience"], str):
        raise ContractError("brief.goal and brief.audience must be strings")
    if not isinstance(brief["deliverables"], list) or not all(isinstance(item, str) and item.strip() for item in brief["deliverables"]):
        raise ContractError("brief.deliverables must be a non-empty array of strings")
    policy = brief.get("release_policy", {})
    if not isinstance(policy, dict):
        raise ContractError("brief.release_policy must be an object")
    for field in (
        "required_evidence_refs", "required_evidence_artifact_names",
        "required_review_rubrics", "required_artifact_names",
        "required_asset_names", "required_rights_statuses",
        "technical_qa_required_check_ids",
    ):
        value = policy.get(field, [])
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            raise ContractError(f"release_policy.{field} must be an array of non-empty strings")
    allowed_rights = set(policy.get("required_rights_statuses", sorted(RIGHTS_ALLOWED)))
    if not allowed_rights.issubset(RIGHTS_ALLOWED):
        raise ContractError("release_policy.required_rights_statuses contains a non-cleared rights status")
    contracts = policy.get("review_contracts", {})
    if not isinstance(contracts, dict) or not all(isinstance(value, dict) for value in contracts.values()):
        raise ContractError("release_policy.review_contracts must map rubric IDs to objects")
    for rubric, contract in contracts.items():
        _safe_id(rubric, "review rubric")
        for count_field in ("min_reviewers", "min_findings"):
            if count_field in contract and int(contract[count_field]) < 0:
                raise ContractError(f"review_contracts.{rubric}.{count_field} cannot be negative")
        if "dimension_floors" in contract and not isinstance(contract["dimension_floors"], dict):
            raise ContractError(f"review_contracts.{rubric}.dimension_floors must be an object")
        for boolean_field in (
            "reviewer_kind", "execution_mode", "blind_review", "require_digest_attestation",
            "require_context_id", "require_evidence_per_finding", "require_disposition_per_finding",
            "require_resolvable_evidence_refs", "distinct_contexts",
        ):
            if boolean_field in contract and boolean_field not in {"reviewer_kind", "execution_mode"} and not isinstance(contract[boolean_field], bool):
                raise ContractError(f"review_contracts.{rubric}.{boolean_field} must be boolean")
        if "score_dimensions" in contract and not isinstance(contract["score_dimensions"], list):
            raise ContractError(f"review_contracts.{rubric}.score_dimensions must be an array")
    if policy.get("require_technical_qa") and not isinstance(
        policy.get("technical_qa_artifact_name", "technical-qa-receipt"), str
    ):
        raise ContractError("release_policy.technical_qa_artifact_name must be a string")
