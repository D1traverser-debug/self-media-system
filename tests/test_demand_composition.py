"""Cross-axis architecture regression: common seam, no per-scenario controller."""
import copy
import json
from pathlib import Path

import pytest

from social_media_studio.scope import capability_lookup, resolve_intake
from social_media_studio.domain.contracts import DELIVERABLE_TYPES

ROOT = Path(__file__).resolve().parents[1]

def spec(identifier, kind, **extra):
    return {"id": identifier, "type": kind, **extra}

def intake(tmp_path, specs, choices=None, **extra):
    return resolve_intake(tmp_path, {"mode": "NEW", "goal": "current exact owner goal",
                                   "deliverable_specs": specs, **extra}, selection=choices)

def test_every_demand_has_exact_operation_scope_and_no_phantom_admission():
    coverage = capability_lookup()
    groups = coverage["groups"]
    seen = set()
    for g in groups:
        assert set(g["demand_routes"]) == set(g["demands"])
        assert not seen.intersection(g["demands"])
        seen.update(g["demands"])
        for demand_id, contract in g["demand_routes"].items():
            result = capability_lookup(g["id"], demand_id=demand_id)
            exact = result["groups"][0]
            assert exact["selected_operation_contract"] == contract
            assert set(contract["deliverable_types"]) <= DELIVERABLE_TYPES
            assert exact["executor_routes"]["production_operations"] == contract["local_support_operations"]
            assert {x["name"] for x in exact["executor_routes"]["domain_adapters"]} == set(contract["local_support_adapters"])
            assert not exact["executor_routes"]["actual_executor_verified"]
            assert not result["effect_authorized"]
    assert len(seen) >= 54

@pytest.mark.parametrize("demand_id", ["image_generation", "image_editing", "platform_title", "short_form_copy",
                                      "video_merge", "video_enhancement", "audio_restoration", "temporary_character"])
def test_unrelated_group_operations_are_not_inherited(demand_id):
    group = capability_lookup(demand_id=demand_id)["groups"][0]
    assert group["executor_routes"]["production_operations"] == []
    assert group["executor_routes"]["domain_adapters"] == []

def test_only_explicitly_scoped_motion_and_audio_copy_are_exposed():
    motion = capability_lookup(demand_id="programmatic_motion_graphics")["groups"][0]
    assert motion["executor_routes"]["production_operations"] == ["python_frame_render"]
    audio = capability_lookup(demand_id="original_audio_preservation")["groups"][0]
    assert audio["executor_routes"]["production_operations"] == ["ffmpeg_video_audio_copy"]
    assert "Eligible" in audio["selected_operation_contract"]["scope"]
    generation = capability_lookup(demand_id="video_generation")["groups"][0]
    assert generation["executor_routes"]["production_operations"] == []
    assert {x["name"] for x in generation["executor_routes"]["domain_adapters"]} == {"shot_route"}

def test_all_typed_outcomes_use_the_same_composition_seam(tmp_path):
    specs = [spec(kind.lower(), kind) for kind in sorted(DELIVERABLE_TYPES)]
    for item in specs:
        if item["type"] == "MULTI_ASPECT_IMAGE_SET":
            item["variants"] = [
                {"id":"horizontal","shape":{"width":1600,"height":900,"orientation":"LANDSCAPE"}},
                {"id":"vertical","shape":{"width":900,"height":1200,"orientation":"PORTRAIT"}}]
    result = intake(tmp_path, specs)
    composition = result["demand_composition"]
    assert {i["deliverable_contract"]["type"] for i in composition["deliverables"]} == DELIVERABLE_TYPES
    assert composition["selected_task_graph"] is None
    assert composition["surface_proposed"] is None
    assert not composition["business_domains_proposed"]
    assert not composition["effect_authorized"]
    assert not tmp_path.joinpath("projects").exists()
    for d in composition["deliverables"]:
        assert d["quality_plan"]["deliverable_id"] == d["deliverable_id"]
        assert d["internal_ownership"]["deliverable_id"] == d["deliverable_id"]
        assert d["identity_scope"]["deliverable_id"] == d["deliverable_id"]
        assert d["selection_status"] == "UNSELECTED"
        assert not d["proposed_professional_routes"]
        assert d["candidate_demands_not_selected"]

def test_mixed_request_preserves_owner_scope_and_independent_variants(tmp_path):
    specs = [spec("caption","SHORT_COPY",locale="zh-CN"),
             spec("cover","STATIC_IMAGE",shape={"width":900,"height":1200,"orientation":"PORTRAIT"},
                  constraints={"identity_mode":"TEMPORARY_CHARACTER"})]
    demand_contract={"schema_version":1,"owner_source_refs":["current-owner"],
                     "clauses":[{"id":"global","kind":"PROHIBITION","text":"no publication",
                                 "source_ref":"current-owner","deliverable_refs":[]},
                                {"id":"caption-only","kind":"HARD_CONSTRAINT","text":"Chinese",
                                 "source_ref":"current-owner","deliverable_refs":["caption"]}]}
    selection={"surface":"DIRECT_SESSION","business_domains":["CONTENT_CREATION_AND_PRODUCTION"],
               "deliverables":{"caption":["short_form_copy"],"cover":["cover_design","temporary_character"]}}
    route=intake(tmp_path,specs,selection,demand_contract=demand_contract)["demand_composition"]
    caption,cover=route["deliverables"]
    assert [c["id"] for c in caption["owner_clauses"]] == ["global","caption-only"]
    assert [c["id"] for c in cover["owner_clauses"]] == ["global"]
    assert caption["deliverable_contract"]["locale"] == "zh-CN"
    assert cover["deliverable_contract"]["shape"]["aspect_ratio"] == "3:4"
    assert [x["demand_id"] for x in caption["proposed_professional_routes"]] == ["short_form_copy"]
    assert "approved_identity_use" not in cover["candidate_demands_not_selected"]
    assert "persistent_identity_design" not in cover["candidate_demands_not_selected"]
    assert cover["identity_scope"]["requires_current_canon_bundle"] is False
    assert route["surface_proposed"] == "DIRECT_SESSION"
    assert route["effect_authorized"] is False
    assert not tmp_path.joinpath("projects").exists()

def test_wrong_type_identity_and_unknown_selection_rejected(tmp_path):
    caption = [spec("c","SHORT_COPY")]
    for selection in ({"deliverables":{"c":["video_generation"]}},
                      {"deliverables":{"unknown":["short_form_copy"]}},
                      {"deliverables":{"c":["short_form_copy","short_form_copy"]}},
                      {"business_domains":["invented"]},
                      {"surface":"publish"}):
        with pytest.raises(ValueError):
            intake(tmp_path,caption,selection)
    with pytest.raises(ValueError,match="identity scope"):
        intake(tmp_path,[spec("v","STATIC_IMAGE")],{"deliverables":{"v":["approved_identity_use"]}})
    with pytest.raises(ValueError,match="deliverable type"):
        intake(tmp_path,[spec("p","PROMPT_SPEC")],{"deliverables":{"p":["image_generation"]}})

def test_unstructured_direct_goal_never_requires_schema_or_project(tmp_path):
    result=resolve_intake(tmp_path,{"mode":"NEW","goal":"one short title"})
    assert result["demand_composition"]["status"] == "INTERPRET_CURRENT_GOAL_NO_TYPED_ROUTE"
    assert result["demand_composition"]["deliverables"] == []
    assert result["selected_task_graph"] is None
    assert not tmp_path.joinpath("projects").exists()

def test_missing_or_wrong_group_operation_contract_fails_closed():
    original=json.loads((ROOT/"social_media_studio/legacy/data/capabilities.json").read_text())
    for mutation in ("missing","wrong_operation","phantom_type"):
        raw=copy.deepcopy(original)
        group=next(g for g in raw["professional_capability_groups"] if g["id"]=="editorial_writing")
        if mutation=="missing":
            group["demand_routes"].pop("short_form_copy")
        elif mutation=="wrong_operation":
            group["demand_routes"]["short_form_copy"]["local_support_operations"]=["ffmpeg_assemble"]
        else:
            group["demand_routes"]["short_form_copy"]["deliverable_types"]=["FAKE"]
        with pytest.raises(ValueError):
            capability_lookup(profile=raw)
