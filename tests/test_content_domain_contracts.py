import json
from pathlib import Path

import pytest

from video_studio.domain.contracts import (
    ContentContractError, DELIVERABLE_TYPES, MediaShape, inspect_declared_deliverables,
)
from video_studio.scope import bind_owner_brief, resolve_intake

ROOT = Path(__file__).resolve().parents[1]


def test_every_architecture_scenario_has_a_typed_route_without_effect(tmp_path):
    matrix = json.loads((ROOT / "docs/CONTENT_STUDIO_ARCH_ACCEPTANCE_V2.json").read_text(encoding="utf-8"))
    assert len(matrix["scenarios"]) >= 28
    for scenario in matrix["scenarios"]:
        assert scenario["forbidden_implicit_effect"] and scenario["owner_outcome_oracle"]
        item = {"id": "result", "type": scenario["deliverable_type"]}
        preview = resolve_intake(tmp_path, {
            "mode": "NEW", "goal": scenario["demand"], "deliverable_specs": [item]})
        assert preview["project_id"] is None
        assert preview["selected_task_graph"] is None
        assert preview["effect_authorized"] is False
        assert preview["typed_deliverables"]["deliverables"][0]["type"] in DELIVERABLE_TYPES
        assert preview["typed_deliverables"]["quality_verified"] is False
        assert preview["typed_deliverables"]["native_caos_activation"] == "NOT_VERIFIED"


def test_ratio_and_orientation_are_explicit_not_inferred():
    assert MediaShape.from_mapping({"width": 1440, "height": 1080, "orientation": "LANDSCAPE"}).ratio == "4:3"
    assert MediaShape.from_mapping({"width": 1080, "height": 1440, "orientation": "PORTRAIT"}).ratio == "3:4"
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
