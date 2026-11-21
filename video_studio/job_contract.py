from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Any, Mapping


class MediaJobContractError(ValueError):
    """Raised when an owner media brief cannot be normalized safely."""


PRODUCTION_FAMILIES = {
    "engineering_proof",
    "cinematic_explainer",
    "news_fiction_meme",
    "social_image_set",
    "animation",
    "documentary",
    "tutorial",
    "product_film",
    "entertainment",
    "custom",
}
DELIVERABLE_KINDS = {
    "video",
    "image",
    "image_set",
    "audio",
    "subtitle",
    "cover",
    "social_copy",
    "editable_project_bundle",
    "evidence",
    "document",
    "archive",
    "file",
}
RIGHTS_STATUSES = {"OWNED", "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN", "UNKNOWN", "NOT_APPLICABLE"}
_RESOLUTION = re.compile(r"^([1-9][0-9]{1,4})x([1-9][0-9]{1,4})$")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MediaJobContractError(f"{label} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, label: str, *, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if value is None:
        return default
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise MediaJobContractError(f"{label} must be an array of non-empty strings")
    return tuple(item.strip() for item in value)


def _relative_name(value: Any) -> str:
    name = _text(value, "deliverable.name")
    if "\x00" in name or "\\" in name:
        raise MediaJobContractError(f"deliverable name must use a safe relative POSIX path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise MediaJobContractError(f"deliverable name must not be absolute or traverse directories: {name!r}")
    return name.rstrip("/") if name.endswith("/") else name


def _infer_kind(name: str) -> str:
    lowered = name.casefold()
    if lowered.endswith("/"):
        return "archive"
    suffix = PurePosixPath(name).suffix.casefold()
    if suffix in {".mp4", ".mov", ".mkv", ".webm", ".m4v"}:
        return "video"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        return "image"
    if suffix in {".wav", ".mp3", ".aac", ".flac", ".m4a", ".ogg"}:
        return "audio"
    if suffix in {".srt", ".vtt", ".ass"}:
        return "subtitle"
    if suffix in {".zip", ".tar", ".gz", ".7z"}:
        return "editable_project_bundle" if any(token in lowered for token in ("project", "source", "editable")) else "archive"
    if suffix in {".md", ".txt", ".json", ".csv", ".html", ".xml"}:
        return "document"
    return "file"


def _normalize_deliverable(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        name = _relative_name(value)
        return {
            "name": name,
            "kind": _infer_kind(name),
            "required": True,
            "media_type": None,
            "platforms": [],
            "acceptance": {},
            "editable": False,
            "description": "",
        }
    if not isinstance(value, Mapping):
        raise MediaJobContractError("each deliverable must be a filename or an object")
    unknown = sorted(set(value) - {
        "name", "kind", "required", "media_type", "platform", "platforms",
        "acceptance", "editable", "description", "format",
    })
    if unknown:
        raise MediaJobContractError(f"deliverable has unsupported fields: {unknown}")
    name = _relative_name(value.get("name"))
    kind = str(value.get("kind") or _infer_kind(name)).strip().casefold()
    if kind not in DELIVERABLE_KINDS:
        raise MediaJobContractError(f"unsupported deliverable kind for {name}: {kind}")
    required = value.get("required", True)
    editable = value.get("editable", kind == "editable_project_bundle")
    if not isinstance(required, bool) or not isinstance(editable, bool):
        raise MediaJobContractError(f"deliverable required/editable flags must be boolean: {name}")
    media_type = value.get("media_type")
    if media_type is not None:
        media_type = _text(media_type, f"deliverable[{name}].media_type")
    acceptance = value.get("acceptance", {})
    if not isinstance(acceptance, Mapping):
        raise MediaJobContractError(f"deliverable acceptance must be an object: {name}")
    platform_values = value.get("platforms")
    if platform_values is None and value.get("platform") is not None:
        platform_values = [value["platform"]]
    platforms = list(_string_list(platform_values, f"deliverable[{name}].platforms"))
    description = value.get("description", "")
    if not isinstance(description, str):
        raise MediaJobContractError(f"deliverable description must be a string: {name}")
    output = {
        "name": name,
        "kind": kind,
        "required": required,
        "media_type": media_type,
        "platforms": platforms,
        "acceptance": dict(acceptance),
        "editable": editable,
        "description": description.strip(),
    }
    if value.get("format") is not None:
        if not isinstance(value["format"], Mapping):
            raise MediaJobContractError(f"deliverable format must be an object: {name}")
        output["format"] = dict(value["format"])
    return output


def _validate_format(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise MediaJobContractError("format must be an object")
    result = dict(value)
    duration = result.get("duration_seconds")
    if duration is not None:
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
            raise MediaJobContractError("format.duration_seconds must be a positive number")
    fps = result.get("frame_rate")
    if fps is not None:
        if isinstance(fps, bool) or not isinstance(fps, (int, float)) or fps <= 0:
            raise MediaJobContractError("format.frame_rate must be a positive number")
    resolution = result.get("resolution")
    if resolution is not None and not _RESOLUTION.fullmatch(str(resolution)):
        raise MediaJobContractError("format.resolution must use WIDTHxHEIGHT")
    if result.get("aspect_ratio") is not None:
        _text(result["aspect_ratio"], "format.aspect_ratio")
    for field in ("platforms", "language"):
        if field == "platforms" and field in result:
            _string_list(result[field], "format.platforms")
        if field == "language" and result[field] is not None and not isinstance(result[field], (str, list)):
            raise MediaJobContractError("format.language must be a string or an array")
    return result


def _validate_policy(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise MediaJobContractError(f"{label} must be an object")
    return dict(value)


@dataclass(frozen=True)
class MediaJobSpec:
    schema_version: int
    title: str
    goal: str
    audience: str
    production_family: str
    deliverables: tuple[dict[str, Any], ...]
    format: dict[str, Any]
    content_contract: Any
    craft_contract: Any
    hard_constraints: tuple[str, ...]
    preferences: tuple[str, ...]
    examples: tuple[str, ...]
    unknowns: tuple[str, ...]
    success_criteria: tuple[str, ...]
    cost_policy: dict[str, Any]
    rights_policy: dict[str, Any]
    release_policy: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MediaJobSpec":
        if not isinstance(payload, Mapping):
            raise MediaJobContractError("media job must be a JSON object")
        goal = _text(payload.get("goal"), "goal")
        audience = _text(payload.get("audience"), "audience")
        raw_deliverables = payload.get("deliverables")
        if not isinstance(raw_deliverables, list) or not raw_deliverables:
            raise MediaJobContractError("deliverables must be a non-empty array")
        deliverables = tuple(_normalize_deliverable(item) for item in raw_deliverables)
        names = [item["name"].casefold() for item in deliverables]
        if len(names) != len(set(names)):
            raise MediaJobContractError("deliverable names must be unique, including case-insensitive duplicates")

        family = str(payload.get("production_family") or "custom").strip().casefold()
        if family not in PRODUCTION_FAMILIES:
            raise MediaJobContractError(f"unsupported production_family: {family}")

        content_contract = payload.get("content_contract", {})
        craft_contract = payload.get("craft_contract", {})
        if not isinstance(content_contract, (Mapping, str)) or not isinstance(craft_contract, (Mapping, str)):
            raise MediaJobContractError("content_contract and craft_contract must be objects or strings")

        cost_policy = _validate_policy(payload.get("cost_policy"), "cost_policy")
        paid = cost_policy.get("paid_actions_authorized", False)
        if not isinstance(paid, bool):
            raise MediaJobContractError("cost_policy.paid_actions_authorized must be boolean")
        max_spend = cost_policy.get("max_spend")
        if max_spend is not None and (
            isinstance(max_spend, bool) or not isinstance(max_spend, (int, float)) or max_spend < 0
        ):
            raise MediaJobContractError("cost_policy.max_spend must be a non-negative number")
        cost_policy.setdefault("paid_actions_authorized", False)

        rights_policy = _validate_policy(payload.get("rights_policy"), "rights_policy")
        require_rights = rights_policy.get("require_clearance", True)
        if not isinstance(require_rights, bool):
            raise MediaJobContractError("rights_policy.require_clearance must be boolean")
        statuses = rights_policy.get("required_rights_statuses")
        if statuses is not None:
            allowed_statuses = _string_list(statuses, "rights_policy.required_rights_statuses")
            invalid = sorted(set(allowed_statuses) - RIGHTS_STATUSES)
            if invalid:
                raise MediaJobContractError(f"unsupported rights statuses: {invalid}")
            rights_policy["required_rights_statuses"] = list(allowed_statuses)
        rights_policy.setdefault("require_clearance", True)

        release_policy = _validate_policy(payload.get("release_policy"), "release_policy")
        for field in ("required_review_rubrics", "required_evidence_refs", "required_artifact_names", "required_asset_names"):
            if field in release_policy:
                release_policy[field] = list(_string_list(release_policy[field], f"release_policy.{field}"))
        if release_policy.get("auto_publish", False) is not False:
            raise MediaJobContractError("auto_publish is forbidden; publication requires a separate owner action")

        schema_version = payload.get("schema_version", payload.get("media_job_schema_version", 1))
        if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version < 1:
            raise MediaJobContractError("schema_version must be a positive integer")

        return cls(
            schema_version=schema_version,
            title=str(payload.get("title") or goal).strip(),
            goal=goal,
            audience=audience,
            production_family=family,
            deliverables=deliverables,
            format=_validate_format(payload.get("format")),
            content_contract=dict(content_contract) if isinstance(content_contract, Mapping) else content_contract,
            craft_contract=dict(craft_contract) if isinstance(craft_contract, Mapping) else craft_contract,
            hard_constraints=_string_list(payload.get("hard_constraints"), "hard_constraints"),
            preferences=_string_list(payload.get("preferences"), "preferences"),
            examples=_string_list(payload.get("examples"), "examples"),
            unknowns=_string_list(payload.get("unknowns"), "unknowns"),
            success_criteria=_string_list(payload.get("success_criteria"), "success_criteria"),
            cost_policy=cost_policy,
            rights_policy=rights_policy,
            release_policy=release_policy,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "title": self.title,
            "goal": self.goal,
            "audience": self.audience,
            "production_family": self.production_family,
            "deliverables": [dict(item) for item in self.deliverables],
            "format": dict(self.format),
            "content_contract": self.content_contract,
            "craft_contract": self.craft_contract,
            "hard_constraints": list(self.hard_constraints),
            "preferences": list(self.preferences),
            "examples": list(self.examples),
            "unknowns": list(self.unknowns),
            "success_criteria": list(self.success_criteria),
            "cost_policy": dict(self.cost_policy),
            "rights_policy": dict(self.rights_policy),
            "release_policy": dict(self.release_policy),
        }


def validate_media_job(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize and validate a media brief without mutating the caller's payload."""
    return MediaJobSpec.from_dict(payload).to_dict()
