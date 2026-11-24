"""Social Media Studio's nested IPOS boundary: classify intent, never duplicate canonical identity state.

This module does not read the private IPOS library, run a render or establish approval.
The existing IPOS Video Identity Bundle adapters remain the *only downstream
approved-canon consumer*. No owner action is inferred from a source reference.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import ContentContractError


IDENTITY_MODES = frozenset({
    "TEMPORARY_CHARACTER", "PERSISTENT_IDENTITY_DESIGN",
    "APPROVED_CANON_USE", "IDENTITY_DERIVATIVE", "NO_IDENTITY",
})
_NON_CANON_OUTPUTS = frozenset({"STATIC_IMAGE", "MULTI_ASPECT_IMAGE_SET", "PROMPT_SPEC",
                                "IDENTITY_ASSET", "ORIGINAL_VIDEO"})
_CANON_OUTPUTS = _NON_CANON_OUTPUTS | {"MEDIA_TRANSFORM", "PLATFORM_PACKAGE", "LONG_ARTICLE"}


def validate_identity_constraints(deliverable_type: str, constraints: Mapping[str, Any]) -> None:
    """Validate explicit mode only; does not infer identity from title or text."""
    if not isinstance(constraints, Mapping):
        raise ContentContractError("identity constraints must be an object")
    mode = constraints.get("identity_mode")
    if mode is None:
        return  # unresolved persistent identity intent is not assumed from words
    if mode not in IDENTITY_MODES:
        raise ContentContractError("unknown identity_mode")
    if mode == "TEMPORARY_CHARACTER" and deliverable_type not in _NON_CANON_OUTPUTS:
        raise ContentContractError("temporary character does not belong to this deliverable type")
    if mode == "PERSISTENT_IDENTITY_DESIGN" and deliverable_type not in {
        "IDENTITY_ASSET", "PROMPT_SPEC", "ANALYSIS_REPORT",
    }:
        raise ContentContractError("persistent identity design requires a design deliverable")
    if mode in {"APPROVED_CANON_USE", "IDENTITY_DERIVATIVE"} and deliverable_type not in _CANON_OUTPUTS:
        raise ContentContractError("approved identity use requires an identity-capable deliverable")
    if mode in {"APPROVED_CANON_USE", "IDENTITY_DERIVATIVE"}:
        if constraints.get("canon_approved") is True or constraints.get("identity_approval") == "APPROVED":
            raise ContentContractError("caller cannot self-attest approved canon in deliverable constraints")


def identity_route(deliverables: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Return an explicit, non-authorizing, task-neutral content-system route."""
    results = []
    for item in deliverables:
        kind = item["type"]
        constraints = item.get("constraints", {})
        validate_identity_constraints(kind, constraints)
        mode = constraints.get("identity_mode")
        if mode is None:
            mode = "UNSPECIFIED_IDENTITY_DESIGN" if kind == "IDENTITY_ASSET" else "NO_IDENTITY"
        specialist = mode == "PERSISTENT_IDENTITY_DESIGN"
        consuming = mode in {"APPROVED_CANON_USE", "IDENTITY_DERIVATIVE"}
        results.append({
            "deliverable_id": item["id"],
            "identity_mode": mode,
            "product_context": "SOCIAL_MEDIA_STUDIO/ORIGINAL_IDENTITY_IPOS" if specialist else (
                "SOCIAL_MEDIA_STUDIO/IDENTITY_CONSUMER" if consuming else "SOCIAL_MEDIA_STUDIO/GENERAL_CREATIVE"
            ),
            "specialist_source": "CURRENT_IPOS_SKILL_AND_OWNER_CANONICAL_STATE"
                if specialist else None,
            "approval_check": "EXACT_IPOS_EXPORT_AND_OWNER_RIGHTS_READBACK_REQUIRED"
                if consuming else ("OWNER_ONLY_FOR_PERMANENT_IDENTITY" if specialist else "NOT_APPLICABLE"),
            "canon_use_admitted": False,
            "effect_authorized": False,
            "current_owner_ipos_state_loaded": False,
            "requires_current_canon_bundle": consuming,
            "historical_project_snapshot_authority": False,
            "status": "CURRENT_EXPORT_UNVERIFIED" if consuming else (
                "INTERNAL_SPECIALIST_TEXT_WORK_ALLOWED_SCOPED_EFFECTS_SEPARATE" if specialist else (
                    "IDENTITY_SCOPE_UNRESOLVED" if mode == "UNSPECIFIED_IDENTITY_DESIGN"
                    else "NO_PERSISTENT_CANON_DEPENDENCY"
                )
            ),
        })
    return {
        "routes": results,
        "overall": "NON_AUTHORIZING_ROUTE_PREVIEW",
        "canon_authority": "OWNER_APPROVED_IPOS_SOURCE_ONLY",
        "ip_studio_business_membership": "NESTED_SOCIAL_MEDIA_STUDIO_SUBSYSTEM",
        "current_source_custody": "SEPARATELY_MAINTAINED_PRIVATE_IPOS_STATE",
        "selected_task_graph": None,
    }
