from __future__ import annotations

import json
from pathlib import Path

from social_media_studio.domain.contracts import DELIVERABLE_TYPES
from social_media_studio.domain.editorial import PLATFORMS
from social_media_studio.domain_adapters.registry import DOMAIN_ADAPTERS
from social_media_studio.production.registry import PRODUCTION_EXECUTORS
from social_media_studio.scope import capability_lookup

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_user_need_business_domains_are_exactly_separate_from_execution_order():
    manifest = _json("social_media_studio/data/studio_manifest.json")
    model = manifest["architecture"]["user_need_model"]
    assert model["business_domains"] == {
        "CONTENT_CREATION_AND_PRODUCTION": "PRODUCTION_SYSTEM",
        "ACCOUNT_OPERATIONS_AND_GROWTH": "MEDIA_GROWTH",
        "ORIGINAL_IP_AND_BRAND": "ORIGINAL_DIGITAL_IP",
        "COMMERCIALIZATION": "COMMERCIALIZATION",
    }
    assert set(model["business_domains"].values()) == set(manifest["business_workstreams"])
    assert model["composition"] == "DYNAMIC_CROSS_AXIS_COMPOSITION__NO_FIXED_PIPELINE"
    assert manifest["architecture"]["layers_semantics"].startswith("RESPONSIBILITY_LEVELS_NOT_SEQUENTIAL_STAGES")


def test_professional_capability_axis_resolves_knowledge_methods_skills_roles_and_real_executors():
    manifest = _json("social_media_studio/data/studio_manifest.json")
    model = manifest["architecture"]["user_need_model"]["professional_capabilities"]
    for key in ("knowledge", "methods", "skills", "roles"):
        assert (ROOT / model[key]).is_file(), (key, model[key])
    assert all((ROOT / path).is_file() for path in model["local_executors"])
    assert model["selection"] == "DEMAND_SELECTED_ONLY__CURRENT_AVAILABILITY_AND_GAPS_MUST_BE_CHECKED"

    raw_profile = _json("social_media_studio/legacy/data/capabilities.json")
    knowledge_ids = {item["id"] for item in _json("social_media_studio/data/knowledge_catalog.json")["entries"]}
    method_ids = {item["id"] for item in _json("social_media_studio/legacy/data/techniques.json")["techniques"]}
    role_ids = set(_json("social_media_studio/legacy/data/roles.json")["roles"])
    skill_text = (ROOT / "skills/social-media-studio/SKILL.md").read_text(encoding="utf-8")
    for group in raw_profile["professional_capability_groups"]:
        assert set(group["knowledge_refs"]) <= knowledge_ids
        assert set(group["method_ids"]) <= method_ids
        assert set(group["role_ids"]) <= role_ids
        assert all(f"## {section}" in skill_text for section in group["skill_sections"])

    profile = capability_lookup()
    assert all("knowledge_resources" in group and "methods" in group
               and "professional_roles" in group and "executor_routes" in group
               for group in profile["groups"])
    assert len(profile["groups"]) == 9
    assert set(DOMAIN_ADAPTERS) == {name for group in profile["groups"] for name in group["adapters"]}
    assert set(PRODUCTION_EXECUTORS.operations()) == {name for group in profile["groups"] for name in group["operations"]}
    assert len(profile["legacy_capabilities"]) == 24
    assert profile["effect_authorized"] is False
    assert profile["business_outcome_verified"] is False

    catalog = _json("social_media_studio/data/subsystem_catalog.json")
    assert len(catalog["subsystems"]) == 16
    assert len(DOMAIN_ADAPTERS) == 17
    assert len(PRODUCTION_EXECUTORS.operations()) == 6


def test_deliverable_axis_has_typed_contracts_and_complete_ownership():
    manifest = _json("social_media_studio/data/studio_manifest.json")
    catalog = _json("social_media_studio/data/subsystem_catalog.json")
    model = manifest["architecture"]["user_need_model"]["deliverables"]
    assert model["types"] == "social_media_studio.domain.contracts.DELIVERABLE_TYPES"
    assert set(catalog["deliverable_ownership"]) == set(DELIVERABLE_TYPES)
    assert model["ownership"] == "social_media_studio/data/subsystem_catalog.json#deliverable_ownership"
    assert "NO_DEFAULT_VIDEO_FINAL" in model["semantics"]


def test_platform_axis_is_a_variant_dimension_not_a_fixed_stage():
    manifest = _json("social_media_studio/data/studio_manifest.json")
    model = manifest["architecture"]["user_need_model"]["platform_adaptation"]
    assert model["variant_schema"] == "social_media_studio.domain.contracts.DeliverableVariant"
    assert model["platform_registry"] == "social_media_studio.domain.editorial.PLATFORMS"
    assert set(model["dimensions"]) == {
        "locale", "platform", "shape.width", "shape.height", "shape.orientation", "shape.aspect_ratio"
    }
    assert "OTHER" in PLATFORMS
    assert "NO_HARDCODED_LIMITS" in model["semantics"]


def test_five_loops_are_triggered_by_conditions_not_serialized_as_one_pipeline():
    manifest = _json("social_media_studio/data/studio_manifest.json")
    loops = manifest["architecture"]["control_loops"]
    assert set(loops) == {
        "coordination", "decision", "execution", "requirement_feedback", "failure_root_cause", "learning", "owner"
    }
    assert loops["coordination"] == "EVENT_OR_CONDITION_TRIGGERED__NOT_SERIAL_STAGES"
    assert manifest["architecture"]["recursive_governance"]["decision_reentry"] == "EARLIEST_CONTRADICTED_PREMISE_AND_DEPENDENTS"
    assert "INVALIDATE_ONLY_AFFECTED_DEPENDENTS" in loops["requirement_feedback"]
    assert "INDEPENDENT_VERIFICATION" in loops["failure_root_cause"]
    assert "CAOS_OWNER_ACCEPTANCE" in loops["learning"]


def test_data_lifecycle_and_acceptance_keep_mutable_state_immutable_evidence_and_owner_outcome_separate():
    manifest = _json("social_media_studio/data/studio_manifest.json")
    arch = manifest["architecture"]
    data = arch["data_lifecycle"]
    assert data["store"] == "SQLite_WAL_PER_PROJECT"
    assert "events" in data["append_only_evidence"]
    assert "decisions" in data["append_only_evidence"]
    assert "reviews" in data["append_only_evidence"]
    assert "SHA256" in data["artifact_identity"]
    assert "PRESERVE_PRIOR_HISTORY" in data["revision"]
    assert "NO_GENERIC_PHYSICAL_DELETE" in data["deletion"]

    acceptance = arch["acceptance_model"]
    assert "SOCIAL_MEDIA_STUDIO" in acceptance["professional"]
    assert "CAOS" in acceptance["owner_outcome"]
    assert "ARE_DISTINCT_STATES" in acceptance["separation"]
    surfaces = arch["execution_surfaces"]
    assert "NO_MANDATORY_LEDGER" in surfaces["DIRECT_SESSION"]
    assert "VERSIONED_TASKS" in surfaces["DURABLE_STUDIO"]
