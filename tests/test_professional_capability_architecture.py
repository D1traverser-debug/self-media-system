import copy
import json
from pathlib import Path

import pytest

from social_media_studio.scope import capability_lookup, resolve_intake


ROOT = Path(__file__).resolve().parents[1]


def test_professional_coverage_is_separate_from_business_and_tasks(tmp_path):
    coverage = capability_lookup()
    groups = {g["id"]: g for g in coverage["groups"]}
    assert len(groups) == 9
    demands = {d for g in groups.values() for d in g["demands"]}
    assert {"long_form_editorial", "platform_title", "image_prompt_design", "original_audio_preservation", "video_generation", "avatar_design"} <= demands
    assert coverage["selected_task_graph"] is None
    assert not coverage["effect_authorized"]
    assert not coverage["business_outcome_verified"]
    for goal in ("one English caption", "repair audio only", "design an avatar", "long article"):
        route = resolve_intake(tmp_path, {"mode": "NEW", "goal": goal})
        assert route["selected_task_graph"] is None
        assert route["project_id"] is None
        assert route["architecture"]["recursive_governance"]["coverage"] == "ALL_LEVELS_ALL_MATERIAL_DECISIONS_AND_EFFECTS"
    assert capability_lookup("media_transform")["groups"][0]["operations"] == ["ffmpeg_video_audio_copy"]
    assert "ffmpeg_video_audio_copy" not in groups["verification_delivery"]["operations"]
    assert "original_audio_preservation" in groups["media_transform"]["demands"]


def test_no_fake_registered_route_or_ambiguous_capability():
    profile = json.loads((ROOT / "social_media_studio/legacy/data/capabilities.json").read_text())
    for mutation in ("invent", "omit", "duplicate", "permanent"):
        bad = copy.deepcopy(profile)
        groups = bad["professional_capability_groups"]
        if mutation == "invent":
            groups[0]["operations"].append("imaginary_image_generator")
        elif mutation == "omit":
            groups[1]["adapters"].clear()
        elif mutation == "duplicate":
            groups[1]["demands"].append(groups[0]["demands"][0])
        else:
            groups[0]["activation"] = "ALWAYS_RUN"
        with pytest.raises(ValueError):
            capability_lookup(profile=bad)
    with pytest.raises(ValueError):
        capability_lookup("unknown")
    old = next(x for x in capability_lookup()["legacy_capabilities"] if x["capability_id"] == "media_business_program_orchestration")
    assert old["current_route"]["status"] == "LEGACY_REFERENCE"
    assert "projects/" not in old["invocation_path"]


def test_coordination_points_to_live_entry():
    data = json.loads((ROOT / "social_media_studio/legacy/data/coordination-policy.json").read_text())
    assert data["governance_binding"]["entrypoint"] == "STUDIO_ENTRY.md"


def test_identity_capability_is_nested_and_on_demand():
    from social_media_studio.scope import capability_lookup
    identity = capability_lookup("identity_collaboration")
    item = identity["groups"][0]
    assert "persistent_identity_design" in item["demands"]
    assert "identity_derivative_production" in item["demands"]
    assert item["activation"] == "DEMAND_SELECTED_ONLY"
    assert len([x for x in item["adapters"] if x.startswith("ipos_")]) == 5
    assert identity["effect_authorized"] is False



def test_exact_demand_lookup_returns_scoped_resources_without_authorizing_execution():
    short = capability_lookup("editorial_writing", demand_id="short_form_copy")
    assert short["selected_demand_id"] == "short_form_copy"
    assert short["demand_resolution"] == "EXACT_DEMAND_PROFILE"
    assert short["effect_authorized"] is False
    assert short["selected_task_graph"] is None
    assert short["groups"][0]["executor_routes"]["route_scope"] == (
        "EXACT_DEMAND_SUPPORT_CANDIDATES__NOT_EXECUTOR_ADMISSION"
    )

    profile = json.loads((ROOT / "social_media_studio/legacy/data/capabilities.json").read_text())
    next(g for g in profile["professional_capability_groups"] if g["id"] == "motion_production")["demand_profiles"].pop("video_generation")
    fallback = capability_lookup("motion_production", demand_id="video_generation", profile=profile)
    assert fallback["demand_resolution"] == "GROUP_LEVEL_FALLBACK"
    assert fallback["effect_authorized"] is False


def test_complete_exact_profiles_select_resources_without_group_inheritance():
    overview = capability_lookup()
    count = 0
    for group in overview["groups"]:
        assert set(group["demands"]) == set(group["demand_profiles"])
        for demand_id, profile in group["demand_profiles"].items():
            exact = capability_lookup(group["id"], demand_id=demand_id)["groups"][0]
            assert exact["demand_resolution"] == "EXACT_DEMAND_PROFILE"
            assert exact["resource_selection_scope"] == "EXACT_PROFILE_ONLY"
            assert [x["id"] for x in exact["knowledge_resources"]] == profile["knowledge_refs"]
            assert [x["id"] for x in exact["methods"]] == profile["method_ids"]
            assert [x["id"] for x in exact["professional_roles"]] == profile["role_ids"]
            assert exact["skill_sections"] == profile["skill_sections"]
            assert profile["avoid_when"] and profile["selection_notes"]
            assert not exact["executor_routes"]["actual_executor_verified"]
            count += 1
    assert count == 54
    simple = capability_lookup(demand_id="image_enhancement")["groups"][0]
    assert not simple["methods"]
    assert "storyboard_artist" not in [x["id"] for x in simple["professional_roles"]]
    trim = capability_lookup(demand_id="video_trim")["groups"][0]
    assert not trim["methods"]
    assert "visual-development" not in [x["id"] for x in trim["knowledge_resources"]]
    prompt = capability_lookup(demand_id="image_prompt_design")["groups"][0]
    assert not prompt["executor_routes"]["domain_adapters"]
    assert not prompt["executor_routes"]["production_operations"]
    assert any(x["status"] == "CANDIDATE_REQUIRES_REVALIDATION" for x in prompt["knowledge_resources"])
