"""Typed deliverable structural conformance; never infers aesthetic or owner approval."""
from __future__ import annotations

from typing import Any, Mapping

_VISUAL = frozenset({"STATIC_IMAGE", "MULTI_ASPECT_IMAGE_SET"})
_VIDEO = frozenset({"ORIGINAL_VIDEO"})
_DOCUMENT = frozenset({"SHORT_COPY", "LONG_ARTICLE", "PLATFORM_PACKAGE", "PROMPT_SPEC", "ANALYSIS_REPORT"})


def assess_observation(
    *, deliverable_type: str, declared_media_type: str,
    expected_shape: Mapping[str, Any] | None, observation: Mapping[str, Any],
) -> dict[str, Any]:
    """Assess observed file evidence without calling probes or granting a release.

    UNKNOWN/UNSUPPORTED/NO_TOOL results cannot be silently promoted to PASS.
    """
    failures: list[str] = []
    limitations: list[str] = []
    error = observation.get("error")
    if error:
        available = error in {"PROBE_TOOL_UNAVAILABLE", "FILE_OVER_SIZE_LIMIT", "UNSUPPORTED_MEDIA_TYPE"}
        return {"status": "UNVERIFIED" if available else "MISMATCH",
                "failures": [] if available else [str(error)],
                "limitations": [str(error)] if available else [],
                "observed": dict(observation),
                "technical_conformance_only": True,
                "creative_quality_verified": False, "owner_outcome_verified": False}

    observed_kind = observation.get("kind")
    if deliverable_type in _VISUAL and observed_kind != "IMAGE":
        failures.append("DELIVERABLE_REQUIRES_IMAGE_BYTES")
    elif deliverable_type in _VIDEO and observed_kind != "VIDEO":
        failures.append("DELIVERABLE_REQUIRES_VIDEO_STREAM")
    elif deliverable_type in _DOCUMENT and observed_kind not in {"TEXT", "JSON"}:
        failures.append("DELIVERABLE_REQUIRES_READABLE_DOCUMENT")
    elif deliverable_type == "MEDIA_TRANSFORM" and observed_kind not in {"VIDEO", "AUDIO"}:
        failures.append("MEDIA_TRANSFORM_EXPECTED_VIDEO_OR_AUDIO")
    elif deliverable_type == "IDENTITY_ASSET" and observed_kind not in {"IMAGE", "TEXT", "JSON"}:
        failures.append("IDENTITY_ASSET_FORMAT_UNSUPPORTED")

    actual_media_type = observation.get("media_type")
    if declared_media_type.startswith(("image/", "video/", "audio/")):
        if actual_media_type != declared_media_type:
            failures.append("MEDIA_TYPE_DECLARATION_CONFLICTS_WITH_BYTES")
    elif declared_media_type == "application/json" and observed_kind != "JSON":
        failures.append("DECLARED_JSON_NOT_VALID")
    elif declared_media_type.startswith("text/") and observed_kind != "TEXT":
        failures.append("DECLARED_TEXT_NOT_VALID")

    if expected_shape is not None:
        if observed_kind not in {"IMAGE", "VIDEO"}:
            failures.append("DECLARED_SHAPE_NOT_OBSERVABLE")
        else:
            width, height = observation.get("width"), observation.get("height")
            if width != expected_shape.get("width") or height != expected_shape.get("height"):
                failures.append("DECLARED_PIXEL_SHAPE_MISMATCH")
    else:
        limitations.append("NO_EXACT_PIXEL_SHAPE_DECLARED")

    if not observed_kind:
        failures.append("NO_RECOGNIZED_FILE_FORMAT")
    return {
        "status": "MISMATCH" if failures else "MATCH",
        "failures": failures, "limitations": limitations,
        "observed": dict(observation),
        "technical_conformance_only": True,
        "creative_quality_verified": False, "owner_outcome_verified": False,
    }
