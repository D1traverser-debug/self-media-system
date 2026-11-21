from __future__ import annotations

import copy

import pytest

from video_studio.engine import ContractError, StudioEngine
from video_studio.job_contract import MediaJobContractError, MediaJobSpec, validate_media_job


def _brief():
    return {
        "goal": "Produce a short cinematic explainer.",
        "audience": "Technology-curious viewers.",
        "production_family": "cinematic_explainer",
        "deliverables": [
            {"name": "final.mp4", "kind": "video", "media_type": "video/mp4", "acceptance": {"playback": "pass"}},
            {"name": "audio-master.wav", "kind": "audio", "media_type": "audio/wav"},
            {"name": "captions.srt", "kind": "subtitle"},
            {"name": "source-project.zip", "kind": "editable_project_bundle", "editable": True},
        ],
        "format": {"duration_seconds": 60, "aspect_ratio": "9:16", "resolution": "1080x1920", "frame_rate": 30},
        "hard_constraints": ["No fabricated factual claims."],
        "cost_policy": {"max_spend": 0},
        "release_policy": {"required_review_rubrics": ["editorial", "craft", "technical"], "auto_publish": False},
    }


def test_legacy_filename_deliverables_are_normalized_without_mutating_input():
    brief = {
        "goal": "Create a social video.",
        "audience": "General viewers.",
        "deliverables": ["final.mp4", "cover.png", "captions.srt", "publish-copy.md"],
    }
    before = copy.deepcopy(brief)
    normalized = validate_media_job(brief)
    assert [item["kind"] for item in normalized["deliverables"]] == ["video", "image", "subtitle", "document"]
    assert brief == before
    assert normalized["cost_policy"]["paid_actions_authorized"] is False
    assert normalized["rights_policy"]["require_clearance"] is True


def test_typed_media_job_preserves_per_deliverable_acceptance_and_editable_bundle():
    normalized = validate_media_job(_brief())
    final = normalized["deliverables"][0]
    bundle = normalized["deliverables"][3]
    assert final["acceptance"] == {"playback": "pass"}
    assert final["media_type"] == "video/mp4"
    assert bundle["kind"] == "editable_project_bundle"
    assert bundle["editable"] is True
    assert normalized["production_family"] == "cinematic_explainer"


@pytest.mark.parametrize("name", ["../escape.mp4", "/absolute/final.mp4", "nested/../../escape.mp4", "bad\\path.mp4"])
def test_deliverable_paths_must_be_safe_relative_paths(name):
    brief = _brief()
    brief["deliverables"][0]["name"] = name
    with pytest.raises(MediaJobContractError, match="relative|traverse|safe"):
        validate_media_job(brief)


def test_case_insensitive_duplicate_deliverables_are_rejected():
    brief = _brief()
    brief["deliverables"].append({"name": "FINAL.MP4", "kind": "video"})
    with pytest.raises(MediaJobContractError, match="unique"):
        validate_media_job(brief)


def test_invalid_resolution_and_paid_policy_are_rejected():
    brief = _brief()
    brief["format"]["resolution"] = "wide"
    with pytest.raises(MediaJobContractError, match="WIDTHxHEIGHT"):
        validate_media_job(brief)
    brief = _brief()
    brief["cost_policy"]["paid_actions_authorized"] = "yes"
    with pytest.raises(MediaJobContractError, match="boolean"):
        validate_media_job(brief)


def test_auto_publish_is_never_a_default_or_implicit_permission():
    brief = _brief()
    brief["release_policy"]["auto_publish"] = True
    with pytest.raises(MediaJobContractError, match="auto_publish is forbidden"):
        validate_media_job(brief)


def test_engine_accepts_typed_media_job_and_rejects_invalid_brief(tmp_path):
    engine = StudioEngine(tmp_path)
    project = engine.create_project("typed-job", "Typed job", _brief())
    assert project["brief"]["deliverables"][0]["name"] == "final.mp4"
    invalid = _brief()
    invalid["deliverables"][0]["name"] = "../outside.mp4"
    with pytest.raises(ContractError, match="deliverable"):
        engine.create_project("invalid-job", "Invalid job", invalid)
