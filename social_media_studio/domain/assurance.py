"""Non-executing craft criteria by real deliverable type and variant."""
from __future__ import annotations
from typing import Any
from .contracts import DELIVERABLE_TYPES, inspect_declared_deliverables

CRITERIA = {
    "SHORT_COPY": ("owner_intent", "natural_language", "hook_and_value", "no_redundancy"),
    "LONG_ARTICLE": ("thesis", "fact_provenance", "causal_argument", "counterargument",
                     "original_insight", "reader_value", "emotional_progression"),
    "PLATFORM_PACKAGE": ("platform_voice", "current_platform_spec",
                         "distinct_title_description_cover_roles", "tags_and_locale", "media_meaning"),
    "PROMPT_SPEC": ("intended_visual_story", "explicit_reference_roles", "model_applicability",
                    "composition", "render_falsifier"),
    "STATIC_IMAGE": ("one_glance_story", "focal_hierarchy", "composition", "typography",
                     "reference_fidelity", "mobile_thumbnail"),
    "MULTI_ASPECT_IMAGE_SET": ("shared_intent", "different_per_ratio_compositions",
                               "per_ratio_typography", "per_ratio_safe_zone", "per_ratio_pixel_review"),
    "MEDIA_TRANSFORM": ("changes_only", "source_integrity", "audio_promise",
                        "stream_and_duration_sync", "real_visual_inspection"),
    "ORIGINAL_VIDEO": ("director_story", "visual_coherence", "shot_and_motion_craft",
                       "sound_and_edit", "full_playback", "media_integrity"),
    "IDENTITY_ASSET": ("identity_scope", "canon_approval_if_persistent",
                       "identity_consistency", "visual_character", "version_and_rights"),
    "ANALYSIS_REPORT": ("source_coverage", "competing_explanations", "reasoned_conclusion",
                        "limitations_and_uncertainty", "owner_value"),
}
if set(CRITERIA) != DELIVERABLE_TYPES:
    raise RuntimeError("quality contract missing a deliverable type")

def build_quality_plan(specs: Any) -> dict[str, Any]:
    declared = inspect_declared_deliverables(specs)
    plans = []
    for item in declared["deliverables"]:
        kind = item["type"]
        variants = item["variants"]
        acceptance = dict(item["acceptance"])
        acceptance_present = bool(acceptance)
        plan = {
            "deliverable_id": item["id"], "type": kind, "criteria": list(CRITERIA[kind]),
            "locale": item["locale"], "platform": item["platform"],
            "shape": item["shape"], "source_refs": list(item["source_refs"]),
            "prohibitions": list(item["prohibitions"]),
            "owner_acceptance": acceptance,
            "owner_acceptance_status": "DECLARED" if acceptance_present else "MISSING",
            "blocking_gaps": [] if acceptance_present else ["OWNER_ACCEPTANCE_NOT_DECLARED"],
            "declared_constraints": dict(item["constraints"]),
            "output_variant_ids": [v["id"] for v in variants] if variants else [item["id"]],
            "proof_required": ["actual output examined", "exact version and source",
                               "observed criterion-specific findings",
                               "negative evidence and unresolved blockers",
                               "independence verified where material"],
            "quality_verified": False, "independent_review_verified": False,
            "owner_outcome_verified": False, "release_authorized": False,
        }
        if kind == "MULTI_ASPECT_IMAGE_SET":
            plan["per_variant_review"] = [
                {"id": v["id"], "shape": v["shape"],
                 "pixels_reviewed": False, "composition_verified": False,
                 "text_at_mobile_size_verified": False} for v in variants]
        if kind == "MEDIA_TRANSFORM":
            plan["audio_promise"] = item["constraints"].get("original_audio_promise")
            plan["audio_identity_verified"] = False
        if kind == "IDENTITY_ASSET":
            plan["owner_approved_ipos_canon_verified"] = False
        plans.append(plan)
    return {"plans": plans, "status": "PLAN_ONLY_NOT_AN_EVALUATION",
            "native_caos_activation": "NOT_VERIFIED",
            "actual_artifacts_inspected": False, "release_authorized": False}
