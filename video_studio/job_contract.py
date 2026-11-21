from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
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
_ARTIFACT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_MEDIA_TYPE = re.compile(r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$")

_KIND_MEDIA_PREFIXES = {
    "video": ("video/",),
    "image": ("image/",),
    "image_set": ("image/", "application/zip", "application/x-tar"),
    "audio": ("audio/",),
    "subtitle": ("text/", "application/x-subrip", "application/ttml+xml"),
    "cover": ("image/",),
    "social_copy": ("text/", "application/json"),
    "editable_project_bundle": ("application/zip", "application/x-tar", "application/gzip", "application/x-7z-compressed"),
    "evidence": ("text/", "application/json", "application/pdf"),
    "document": ("text/", "application/json", "application/pdf", "application/xml"),
    "archive": ("application/zip", "application/x-tar", "application/gzip", "application/x-7z-compressed"),
}


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
    raw_parts = name.split("/")
    path = PurePosixPath(name)
    if name.endswith("/") or path.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
        raise MediaJobContractError(f"deliverable name must be a safe relative file path without traversal: {name!r}")
    return name


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
        value = {"name": value}
    if not isinstance(value, Mapping):
        raise MediaJobContractError("each deliverable must be a filename or an object")
    unknown = sorted(set(value) - {
        "name", "artifact_name", "kind", "required", "media_type", "platform", "platforms",
        "acceptance", "editable", "description", "format",
    })
    if unknown:
        raise MediaJobContractError(f"deliverable has unsupported fields: {unknown}")
    name = _relative_name(value.get("name"))
    raw_artifact_name = value.get("artifact_name")
    if raw_artifact_name is None:
        raw_artifact_name = PurePosixPath(name).name
        if not _ARTIFACT_NAME.fullmatch(str(raw_artifact_name)):
            raw_artifact_name = re.sub(r"[^A-Za-z0-9._-]+", "-", str(raw_artifact_name)).strip("-.")
    artifact_name = _text(raw_artifact_name, f"deliverable[{name}].artifact_name")
    if not _ARTIFACT_NAME.fullmatch(artifact_name):
        raise MediaJobContractError(
            f"deliverable artifact_name must be a safe Video artifact identifier: {artifact_name!r}"
        )
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
        if not _MEDIA_TYPE.fullmatch(media_type):
            raise MediaJobContractError(f"deliverable[{name}].media_type must use type/subtype MIME syntax")
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
        "artifact_name": artifact_name,
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
        if field == "language" and result.get(field) is not None and not isinstance(result.get(field), (str, list)):
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
        artifact_names = [item["artifact_name"].casefold() for item in deliverables]
        if len(artifact_names) != len(set(artifact_names)):
            raise MediaJobContractError(
                "deliverable artifact_name values must be unique, including case-insensitive duplicates"
            )

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


def _kind_accepts_media_type(kind: str, media_type: str) -> bool:
    if kind == "file":
        return True
    prefixes = _KIND_MEDIA_PREFIXES.get(kind, ())
    lowered = media_type.casefold()
    return any(lowered.startswith(prefix.casefold()) for prefix in prefixes)


def validate_deliverable_output(
    deliverable: Mapping[str, Any],
    output: Mapping[str, Any],
    *,
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Validate actual output bytes and type; craft/semantic checks remain separate."""
    item = _normalize_deliverable(deliverable)
    if not isinstance(output, Mapping):
        raise MediaJobContractError("deliverable output must be an object")
    raw_path = path if path is not None else output.get("path")
    if not isinstance(raw_path, (str, Path)) or not str(raw_path).strip():
        raise MediaJobContractError(f"{item['artifact_name']}: output path is required")
    output_path = Path(raw_path)
    if not output_path.is_file():
        raise MediaJobContractError(f"{item['artifact_name']}: output file does not exist: {output_path}")
    size_bytes = output_path.stat().st_size
    acceptance = item["acceptance"]

    min_bytes = acceptance.get("min_bytes", 1)
    if isinstance(min_bytes, bool) or not isinstance(min_bytes, int) or min_bytes < 0:
        raise MediaJobContractError(f"{item['name']}: acceptance.min_bytes must be a non-negative integer")
    if size_bytes < min_bytes:
        raise MediaJobContractError(
            f"{item['artifact_name']}: output is too small ({size_bytes} bytes < {min_bytes})"
        )
    max_bytes = acceptance.get("max_bytes")
    if max_bytes is not None:
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < min_bytes:
            raise MediaJobContractError(f"{item['name']}: acceptance.max_bytes must be an integer >= min_bytes")
        if size_bytes > max_bytes:
            raise MediaJobContractError(
                f"{item['artifact_name']}: output is too large ({size_bytes} bytes > {max_bytes})"
            )

    media_type = _text(output.get("media_type"), f"{item['artifact_name']}.media_type")
    if item["media_type"] is not None and media_type.casefold() != item["media_type"].casefold():
        raise MediaJobContractError(
            f"{item['artifact_name']}: media_type mismatch; expected {item['media_type']}, got {media_type}"
        )
    if not _kind_accepts_media_type(item["kind"], media_type):
        raise MediaJobContractError(
            f"{item['artifact_name']}: media_type {media_type} is incompatible with deliverable kind {item['kind']}"
        )

    allowed_extensions = acceptance.get("allowed_extensions")
    if allowed_extensions is not None:
        extensions = _string_list(allowed_extensions, f"{item['name']}.acceptance.allowed_extensions")
        normalized_extensions = {extension.casefold() for extension in extensions}
        if any(not extension.startswith(".") for extension in normalized_extensions):
            raise MediaJobContractError(f"{item['name']}: allowed_extensions entries must start with a dot")
        if output_path.suffix.casefold() not in normalized_extensions:
            raise MediaJobContractError(
                f"{item['artifact_name']}: extension {output_path.suffix!r} is not allowed"
            )

    required_metadata = acceptance.get("required_metadata")
    if required_metadata is not None:
        required = _string_list(required_metadata, f"{item['name']}.acceptance.required_metadata")
        metadata = output.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise MediaJobContractError(f"{item['artifact_name']}: output metadata must be an object")
        missing_metadata = [key for key in required if metadata.get(key) in (None, "", [], {})]
        if missing_metadata:
            raise MediaJobContractError(
                f"{item['artifact_name']}: required output metadata missing: {missing_metadata}"
            )

    text_min = acceptance.get("min_text_chars")
    text_max = acceptance.get("max_text_chars")
    text_chars = None
    if text_min is not None or text_max is not None:
        try:
            text_content = output_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            raise MediaJobContractError(f"{item['artifact_name']}: text acceptance requires UTF-8 output") from exc
        text_chars = len(text_content)
        if text_min is not None:
            if isinstance(text_min, bool) or not isinstance(text_min, int) or text_min < 0:
                raise MediaJobContractError(f"{item['name']}: min_text_chars must be a non-negative integer")
            if text_chars < text_min:
                raise MediaJobContractError(f"{item['artifact_name']}: text is shorter than min_text_chars")
        if text_max is not None:
            if isinstance(text_max, bool) or not isinstance(text_max, int) or text_max < 0:
                raise MediaJobContractError(f"{item['name']}: max_text_chars must be a non-negative integer")
            if text_chars > text_max:
                raise MediaJobContractError(f"{item['artifact_name']}: text is longer than max_text_chars")

    mechanically_checked = {
        "min_bytes", "max_bytes", "allowed_extensions",
        "required_metadata", "min_text_chars", "max_text_chars",
    }
    deferred = sorted(set(acceptance) - mechanically_checked)
    return {
        "artifact_name": item["artifact_name"],
        "deliverable_name": item["name"],
        "kind": item["kind"],
        "status": "MECHANICAL_PASS",
        "media_type": media_type,
        "size_bytes": size_bytes,
        "text_chars": text_chars,
        "deferred_acceptance": deferred,
        "qualitative_review_required": True,
    }


def validate_task_outputs(
    brief: Mapping[str, Any],
    outputs: Mapping[str, Mapping[str, Any]],
    project_root: str | Path,
) -> dict[str, Any]:
    """Validate only task outputs mapped to owner-facing deliverables."""
    normalized = validate_media_job(brief)
    deliverables = {item["artifact_name"]: item for item in normalized["deliverables"]}
    root = Path(project_root)
    reports: dict[str, Any] = {}
    for artifact_name, payload in outputs.items():
        deliverable = deliverables.get(artifact_name)
        if deliverable is None:
            continue
        if not isinstance(payload, Mapping):
            raise MediaJobContractError(f"{artifact_name}: output declaration must be an object")
        raw_path = payload.get("path")
        if not isinstance(raw_path, (str, Path)) or not str(raw_path).strip():
            raise MediaJobContractError(f"{artifact_name}: output path is required")
        output_path = Path(raw_path)
        if not output_path.is_absolute():
            output_path = root / output_path
        reports[artifact_name] = validate_deliverable_output(deliverable, payload, path=output_path)
    return reports


def validate_media_job_artifacts(
    brief: Mapping[str, Any],
    artifacts_by_name: Mapping[str, Mapping[str, Any]],
    *,
    require_rights: bool = True,
) -> dict[str, Any]:
    """Validate all required deliverables against current registered artifacts."""
    normalized = validate_media_job(brief)
    rights_policy = normalized["rights_policy"]
    clearance_required = bool(require_rights and rights_policy.get("require_clearance", True))
    allowed_rights = set(
        rights_policy.get(
            "required_rights_statuses",
            ["OWNED", "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN"],
        )
    )
    failures: list[str] = []
    deliverable_reports: list[dict[str, Any]] = []
    required_names: list[str] = []

    for item in normalized["deliverables"]:
        artifact_name = item["artifact_name"]
        if item["required"]:
            required_names.append(artifact_name)
        record = artifacts_by_name.get(artifact_name)
        if record is None:
            status = "OPTIONAL_NOT_PRODUCED"
            if item["required"]:
                status = "MISSING_REQUIRED"
                failures.append(f"required_deliverable_missing:{artifact_name}")
            deliverable_reports.append({
                "artifact_name": artifact_name,
                "deliverable_name": item["name"],
                "status": status,
            })
            continue

        if record.get("status") not in {"CURRENT", "ACCEPTED"}:
            failures.append(f"deliverable_not_current:{artifact_name}:{record.get('status')}")
        if not record.get("sha256"):
            failures.append(f"deliverable_digest_missing:{artifact_name}")
        if clearance_required and record.get("rights_status") not in allowed_rights:
            failures.append(f"deliverable_rights_not_cleared:{artifact_name}:{record.get('rights_status')}")

        raw_path = record.get("path")
        output = {
            "path": raw_path,
            "media_type": record.get("media_type"),
            "metadata": record.get("metadata", {}),
        }
        try:
            output_report = validate_deliverable_output(item, output, path=raw_path)
        except MediaJobContractError as exc:
            failures.append(f"deliverable_output_invalid:{artifact_name}:{exc}")
            output_report = {"status": "BLOCKED", "reason": str(exc)}

        if raw_path and Path(raw_path).is_file():
            actual_size = Path(raw_path).stat().st_size
            if record.get("size_bytes") != actual_size:
                failures.append(f"deliverable_size_record_mismatch:{artifact_name}")

        deliverable_reports.append({
            "artifact_name": artifact_name,
            "deliverable_name": item["name"],
            "status": "MECHANICAL_PASS" if output_report.get("status") == "MECHANICAL_PASS" else "BLOCKED",
            "output_acceptance": output_report,
            "rights_status": record.get("rights_status"),
            "sha256": record.get("sha256"),
        })

    failures = list(dict.fromkeys(failures))
    return {
        "status": "BLOCKED" if failures else "MECHANICAL_PASS",
        "mechanical_pass": not failures,
        "required_artifact_names": required_names,
        "deliverables": deliverable_reports,
        "rights_clearance_required": clearance_required,
        "qualitative_review_required": True,
        "failures": failures,
    }
