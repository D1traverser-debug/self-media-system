import json
from pathlib import Path

import pytest

from social_media_studio.domain.contracts import (
    ContentContractError, DELIVERABLE_TYPES, MediaShape, inspect_declared_deliverables,
)
from social_media_studio.scope import bind_owner_brief, resolve_intake

ROOT = Path(__file__).resolve().parents[1]


def test_every_architecture_scenario_has_a_typed_route_without_effect(tmp_path):
    matrix = json.loads((ROOT / "docs/SOCIAL_MEDIA_STUDIO_ARCH_ACCEPTANCE_V2.json").read_text(encoding="utf-8"))
    assert len(matrix["scenarios"]) >= 28
    for scenario in matrix["scenarios"]:
        assert scenario["forbidden_implicit_effect"] and scenario["owner_outcome_oracle"]
        item = {"id": "result", "type": scenario["deliverable_type"]}
        if item["type"] == "MULTI_ASPECT_IMAGE_SET":
            shapes = scenario.get("requested_shapes") or [
                {"width": 1080, "height": 1440, "orientation": "PORTRAIT"},
                {"width": 1440, "height": 1080, "orientation": "LANDSCAPE"},
            ]
            item["variants"] = [
                {"id": f"variant-{index}", "shape": shape}
                for index, shape in enumerate(shapes)
            ]
        elif scenario.get("requested_ratio"):
            item["shape"] = MediaShape.from_ratio(
                scenario["requested_ratio"], ratio_order=scenario["ratio_convention"],
                long_edge_pixels=scenario["long_edge_pixels"],
            ).as_dict()
        elif scenario.get("canonical_shape"):
            item["shape"] = scenario["canonical_shape"]
        preview = resolve_intake(tmp_path, {
            "mode": "NEW", "goal": scenario["demand"], "deliverable_specs": [item]})
        assert preview["project_id"] is None
        assert preview["selected_task_graph"] is None
        assert preview["effect_authorized"] is False
        assert preview["typed_deliverables"]["deliverables"][0]["type"] in DELIVERABLE_TYPES
        assert preview["typed_deliverables"]["quality_verified"] is False
        assert preview["typed_deliverables"]["native_caos_activation"] == "NOT_VERIFIED"
        declared = preview["typed_deliverables"]["deliverables"][0]
        if scenario.get("canonical_shape"):
            assert declared["shape"]["width"] == scenario["canonical_shape"]["width"]
            assert declared["shape"]["height"] == scenario["canonical_shape"]["height"]
            assert declared["shape"]["orientation"] == scenario["canonical_shape"]["orientation"]
        if scenario.get("requested_shapes"):
            assert [v["shape"]["orientation"] for v in declared["variants"]] == [
                shape["orientation"] for shape in scenario["requested_shapes"]
            ]


def test_ratio_and_orientation_are_explicit_not_inferred():
    landscape = MediaShape.from_mapping({"width": 1440, "height": 1080, "orientation": "LANDSCAPE"})
    portrait = MediaShape.from_mapping({"width": 1080, "height": 1440, "orientation": "PORTRAIT"})
    assert landscape.ratio == "4:3"
    assert portrait.ratio == "3:4"
    assert landscape.as_dict()["ratio_order"] == "WIDTH:HEIGHT"
    assert MediaShape.from_mapping(landscape.as_dict()) == landscape
    # The user's explicit 4:3 height:width request normalizes to 3:4 width:height.
    assert MediaShape.from_ratio("4:3", ratio_order="HEIGHT:WIDTH", long_edge_pixels=1440) == portrait
    assert MediaShape.from_ratio("4:3", ratio_order="WIDTH:HEIGHT", long_edge_pixels=1440) == landscape
    for bad_order in ("UNKNOWN", "", None):
        with pytest.raises(ContentContractError):
            MediaShape.from_ratio("4:3", ratio_order=bad_order, long_edge_pixels=1440)
    for dimensions in (
        {"width": 1440, "height": 1080, "orientation": "PORTRAIT"},
        {"width": 1080, "height": 1440, "orientation": "LANDSCAPE"},
        {"width": True, "height": 1080, "orientation": "LANDSCAPE"},
        {"width": 0, "height": 1080, "orientation": "PORTRAIT"},
    ):
        with pytest.raises(ContentContractError):
            MediaShape.from_mapping(dimensions)


def test_audio_promise_does_not_silently_substitute_reencoded_audio():
    result = inspect_declared_deliverables([{
        "id": "edited", "type": "MEDIA_TRANSFORM",
        "constraints": {"original_audio_promise": "BITSTREAM_IDENTITY"},
    }])
    assert result["deliverables"][0]["constraints"]["original_audio_promise"] == "BITSTREAM_IDENTITY"
    assert result["quality_verified"] is False
    with pytest.raises(ContentContractError):
        inspect_declared_deliverables([{
            "id": "edited", "type": "MEDIA_TRANSFORM",
            "constraints": {"original_audio_promise": "EQUIVALENT_SOUND"},
        }])
    with pytest.raises(ContentContractError):
        inspect_declared_deliverables([{
            "id": "post", "type": "SHORT_COPY",
            "constraints": {"original_audio_promise": "BITSTREAM_IDENTITY"},
        }])


def test_current_project_binding_has_single_deliverable_identity():
    brief = {"goal": "two covers", "audience": "mobile", "deliverables": ["cover-a", "cover-b"],
             "deliverable_specs": [
                 {"id": "cover-a", "type": "STATIC_IMAGE",
                  "shape": {"width": 1080, "height": 1440, "orientation": "PORTRAIT"}},
                 {"id": "cover-b", "type": "STATIC_IMAGE",
                  "shape": {"width": 1440, "height": 1080, "orientation": "LANDSCAPE"}},
             ]}
    bound = bind_owner_brief("new-cover-task", brief)
    assert [x["id"] for x in bound["deliverable_specs"]] == brief["deliverables"]
    with pytest.raises(ContentContractError):
        bind_owner_brief("new-cover-task", {**brief, "deliverables": ["cover-b", "cover-a"]})


def test_contract_rejects_fabricated_fields_duplicate_ids_and_video_defaults():
    for specs in (
        [{"id": "a", "type": "UNKNOWN"}],
        [{"id": "a", "type": "SHORT_COPY", "director": "mandatory"}],
        [{"id": "a", "type": "STATIC_IMAGE"}, {"id": "a", "type": "STATIC_IMAGE"}],
        [{"id": "text", "type": "SHORT_COPY",
          "shape": {"width": 100, "height": 50, "orientation": "LANDSCAPE"}}],
    ):
        with pytest.raises(ContentContractError):
            inspect_declared_deliverables(specs)
    route = inspect_declared_deliverables([{"id": "one-line", "type": "SHORT_COPY", "locale": "en-US"}])
    assert route["deliverables"][0]["shape"] is None
    assert route["selected_task_graph"] is None


def test_prompt_spec_is_an_independent_non_generation_deliverable(tmp_path):
    route = resolve_intake(tmp_path, {
        "mode": "NEW", "goal": "Refine this prompt only; do not generate an image",
        "deliverable_specs": [{"id": "prompt", "type": "PROMPT_SPEC",
                               "prohibitions": ["No image generation without a new request"],
                               "acceptance": {"goal": "clear model-applicable prompt"}}]})
    assert route["typed_deliverables"]["deliverables"][0]["type"] == "PROMPT_SPEC"
    assert route["typed_deliverables"]["deliverables"][0]["shape"] is None
    assert route["typed_deliverables"]["effect_authorized"] is False
    assert route["selected_task_graph"] is None


def test_multi_aspect_variants_keep_separate_identity_and_composition():
    item = {"id": "covers", "type": "MULTI_ASPECT_IMAGE_SET",
            "variants": [
                {"id": "tall", "shape": {"width": 1080, "height": 1440, "orientation": "PORTRAIT"}},
                {"id": "wide", "shape": {"width": 1440, "height": 1080, "orientation": "LANDSCAPE"}},
            ]}
    preview = inspect_declared_deliverables([item])
    variants = preview["deliverables"][0]["variants"]
    assert [v["id"] for v in variants] == ["tall", "wide"]
    assert [v["shape"]["aspect_ratio"] for v in variants] == ["3:4", "4:3"]
    with pytest.raises(ContentContractError):
        inspect_declared_deliverables([{"id": "covers", "type": "MULTI_ASPECT_IMAGE_SET"}])
    with pytest.raises(ContentContractError):
        inspect_declared_deliverables([{**item, "variants": [item["variants"][0], item["variants"][0]]}])
    with pytest.raises(ContentContractError):
        inspect_declared_deliverables([{"id": "covers", "type": "MULTI_ASPECT_IMAGE_SET",
                                       "variants": [item["variants"][0],
                                                    {"id": "other", "shape": item["variants"][0]["shape"]}]}])


def test_intake_rejects_conflicting_explicit_deliverable_ids(tmp_path):
    with pytest.raises(ContentContractError):
        resolve_intake(tmp_path, {"mode": "NEW", "goal": "make a cover",
                                  "deliverables": ["something-else"],
                                  "deliverable_specs": [{"id": "cover", "type": "STATIC_IMAGE"}]})


def test_ipos_subsystem_is_internal_but_canonical_approval_is_separately_custodied(tmp_path):
    from social_media_studio.domain.contracts import ContentContractError
    context = resolve_intake(tmp_path, {
        "mode": "NEW", "goal": "Develop my permanent anonymous creator identity",
        "deliverable_specs": [{"id": "creator", "type": "IDENTITY_ASSET",
                               "constraints": {"identity_mode": "PERSISTENT_IDENTITY_DESIGN"}}]})
    route = context["identity_routing"]["routes"][0]
    assert route["product_context"] == "SOCIAL_MEDIA_STUDIO/ORIGINAL_IDENTITY_IPOS"
    assert route["status"].startswith("INTERNAL_SPECIALIST")
    assert route["canon_use_admitted"] is False
    assert route["current_owner_ipos_state_loaded"] is False
    assert context["identity_routing"]["ip_studio_business_membership"] == "NESTED_SOCIAL_MEDIA_STUDIO_SUBSYSTEM"
    assert context["selected_task_graph"] is None

    ephemeral = resolve_intake(tmp_path, {
        "mode": "NEW", "goal": "Draw a disposable avatar for this post",
        "deliverable_specs": [{"id": "avatar", "type": "STATIC_IMAGE",
                               "constraints": {"identity_mode": "TEMPORARY_CHARACTER"}}]})
    assert ephemeral["identity_routing"]["routes"][0]["product_context"] == "SOCIAL_MEDIA_STUDIO/GENERAL_CREATIVE"
    assert ephemeral["identity_routing"]["routes"][0]["requires_current_canon_bundle"] is False

    proposed = resolve_intake(tmp_path, {
        "mode": "NEW", "goal": "Use my existing character in a clip",
        "deliverable_specs": [{"id": "clip", "type": "ORIGINAL_VIDEO",
                               "constraints": {"identity_mode": "APPROVED_CANON_USE",
                                               "bundle_ref": "ipos://unverified/example"}}]})
    consumer = proposed["identity_routing"]["routes"][0]
    assert consumer["requires_current_canon_bundle"] is True
    assert consumer["status"] == "CURRENT_EXPORT_UNVERIFIED"
    assert consumer["canon_use_admitted"] is False
    assert proposed["effect_authorized"] is False

    with pytest.raises(ContentContractError):
        resolve_intake(tmp_path, {"mode": "NEW", "goal": "pretend approval",
                                  "deliverable_specs": [{"id": "clip", "type": "ORIGINAL_VIDEO",
                                    "constraints": {"identity_mode": "APPROVED_CANON_USE",
                                                    "canon_approved": True}}]})
    with pytest.raises(ContentContractError):
        resolve_intake(tmp_path, {"mode": "NEW", "goal": "invalid identity method",
                                  "deliverable_specs": [{"id": "a", "type": "SHORT_COPY",
                                    "constraints": {"identity_mode": "PERSISTENT_IDENTITY_DESIGN"}}]})


def test_unrelated_content_has_no_ipos_dependency(tmp_path):
    context = resolve_intake(tmp_path, {"mode": "NEW", "goal": "Restore a non-character video",
        "deliverable_specs": [{"id": "edit", "type": "MEDIA_TRANSFORM"}]})
    route = context["identity_routing"]["routes"][0]
    assert route["identity_mode"] == "NO_IDENTITY"
    assert route["requires_current_canon_bundle"] is False
    assert route["historical_project_snapshot_authority"] is False
