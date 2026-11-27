"""Pure, read-only release coverage projection across owner-declared variants.

A project with one accepted artifact has not thereby satisfied every deliverable.
No new state, approvals, inferred content quality, side effects or scheduler.
"""
from __future__ import annotations

from typing import Any


def variant_release_coverage(variants: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize *current, digest-checked* candidates already projected by engine.

    The source engine alone decides currency and exact bytes, and only its
    existing release transaction may mark an artifact ACCEPTED. This projection
    never promotes a candidate or represents independent owner acceptance.
    """
    identities: set[tuple[str, str]] = set()
    missing_candidates: list[dict[str, str]] = []
    unreleased_variants: list[dict[str, str]] = []
    accepted_variants: list[dict[str, str]] = []
    ambiguous_release_variants: list[dict[str, str]] = []
    for entry in variants:
        key = (entry["deliverable_id"], entry["variant_id"])
        if key in identities:
            raise ValueError(f"duplicate deliverable variant in outcome projection: {key}")
        identities.add(key)
        record = {"deliverable_id": key[0], "variant_id": key[1]}
        candidates = entry["candidates"]
        if not candidates:
            missing_candidates.append(record)
        accepted_count = sum(c.get("artifact_status") == "ACCEPTED" for c in candidates)
        if accepted_count == 1:
            accepted_variants.append(record)
        else:
            if accepted_count > 1:
                ambiguous_release_variants.append(record)
            unreleased_variants.append(record)
    release_complete = bool(variants) and not unreleased_variants
    return {
        "declared_variant_count": len(variants),
        "individually_released_variant_count": len(accepted_variants),
        "missing_candidate_variants": missing_candidates,
        "unreleased_variants": unreleased_variants,
        "ambiguous_release_variants": ambiguous_release_variants,
        "artifact_release_coverage_complete": release_complete,
        "owner_outcome_verified": False,
        "external_publication_authorized": False,
        "whole_demand_accepted": False,
        "release_coverage_scope": "CURRENT_VARIANT_ARTIFACT_RELEASES_ONLY",
        "next_required_boundary": (
            "INDEPENDENT_OWNER_OUTCOME_AND_QUALITY_REVIEW"
            if release_complete else "COMPLETE_MISSING_VARIANTS_AND_ARTIFACT_RELEASE_CHECKS"
        ),
    }
