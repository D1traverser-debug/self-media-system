import copy
import json
from pathlib import Path

import pytest

from video_studio.scope import capability_lookup, resolve_intake


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
    profile = json.loads((ROOT / "video_growth_agent/data/capabilities.json").read_text())
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
    data = json.loads((ROOT / "video_growth_agent/data/coordination-policy.json").read_text())
    assert data["governance_binding"]["entrypoint"] == "STUDIO_ENTRY.md"


def test_identity_capability_is_nested_and_on_demand():
    from video_studio.scope import capability_lookup
    identity = capability_lookup("identity_collaboration")
    item = identity["groups"][0]
    assert "persistent_identity_design" in item["demands"]
    assert "identity_derivative_production" in item["demands"]
    assert item["activation"] == "DEMAND_SELECTED_ONLY"
    assert len([x for x in item["adapters"] if x.startswith("ipos_")]) == 5
    assert identity["effect_authorized"] is False
