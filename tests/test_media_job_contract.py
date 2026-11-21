from __future__ import annotations

import copy
from pathlib import Path

import pytest

from video_studio.engine import ContractError, StudioEngine
from video_studio.job_contract import (
    MediaJobContractError,
    MediaJobSpec,
    validate_deliverable_output,
    validate_media_job,
    validate_media_job_artifacts,
)


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
    assert [item["artifact_name"] for item in normalized["deliverables"]] == [
        "final.mp4", "cover.png", "captions.srt", "publish-copy.md"
    ]
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


@pytest.mark.parametrize("name", ["../escape.mp4", "/absolute/final.mp4", "nested/../../escape.mp4", "bad\\path.mp4", "folder/", "nested//final.mp4"])
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


def test_nested_deliverable_paths_map_to_unique_safe_artifact_names():
    brief = _brief()
    brief["deliverables"][0]["name"] = "exports/final.mp4"
    normalized = validate_media_job(brief)
    assert normalized["deliverables"][0]["artifact_name"] == "final.mp4"

    brief["deliverables"].append({"name": "backup/final.mp4", "kind": "video"})
    with pytest.raises(MediaJobContractError, match="artifact_name values must be unique"):
        validate_media_job(brief)


def test_explicit_artifact_name_is_supported_for_task_graph_mapping():
    brief = _brief()
    brief["deliverables"][0]["artifact_name"] = "master-video"
    normalized = validate_media_job(brief)
    assert normalized["deliverables"][0]["artifact_name"] == "master-video"


def test_deliverable_output_checks_actual_bytes_mime_and_defers_craft_review(tmp_path):
    brief = _brief()
    deliverable = validate_media_job(brief)["deliverables"][0]
    output_path = tmp_path / "final.mp4"
    output_path.write_bytes(b"real file bytes")
    report = validate_deliverable_output(
        deliverable,
        {"path": str(output_path), "media_type": "video/mp4", "metadata": {}},
    )
    assert report["status"] == "MECHANICAL_PASS"
    assert report["size_bytes"] == len(b"real file bytes")
    assert report["deferred_acceptance"] == ["playback"]
    assert report["qualitative_review_required"] is True


def test_deliverable_output_rejects_wrong_media_type_and_missing_metadata(tmp_path):
    brief = _brief()
    deliverable = validate_media_job(brief)["deliverables"][0]
    output_path = tmp_path / "final.mp4"
    output_path.write_bytes(b"video bytes")
    with pytest.raises(MediaJobContractError, match="media_type mismatch"):
        validate_deliverable_output(
            deliverable,
            {"path": str(output_path), "media_type": "image/png"},
        )

    deliverable["acceptance"] = {"required_metadata": ["provider_receipt"]}
    with pytest.raises(MediaJobContractError, match="required output metadata missing"):
        validate_deliverable_output(
            deliverable,
            {"path": str(output_path), "media_type": "video/mp4", "metadata": {}},
        )


def test_media_job_artifact_gate_requires_every_required_output_and_rights(tmp_path):
    brief = _brief()
    output_path = tmp_path / "final.mp4"
    output_path.write_bytes(b"video bytes")
    record = {
        "status": "CURRENT",
        "sha256": "abc123",
        "size_bytes": output_path.stat().st_size,
        "rights_status": "OWNED",
        "media_type": "video/mp4",
        "path": str(output_path),
        "metadata": {},
    }
    report = validate_media_job_artifacts(brief, {"final.mp4": record})
    assert report["status"] == "BLOCKED"
    assert "required_deliverable_missing:audio-master.wav" in report["failures"]
    assert "required_deliverable_missing:captions.srt" in report["failures"]
    assert "required_deliverable_missing:source-project.zip" in report["failures"]


def test_engine_checks_deliverable_output_and_release_package_completeness(tmp_path):
    brief = {
        "goal": "Produce a short video package.",
        "audience": "General viewers.",
        "deliverables": [
            {"name": "final.mp4", "kind": "video", "media_type": "video/mp4"},
            {"name": "audio-master.wav", "kind": "audio", "media_type": "audio/wav"},
        ],
        "release_policy": {"required_review_rubrics": ["craft"], "auto_publish": False},
    }
    engine = StudioEngine(tmp_path)
    engine.create_project("output-contract", "Output contract", brief)
    engine.add_tasks("output-contract", [{
        "task_id": "render-final",
        "title": "Render final master",
        "kind": "production",
        "executor": "tool",
        "depends_on": [],
        "inputs": [],
        "outputs": ["final.mp4"],
        "acceptance": {"file": "A non-empty MP4 master exists."},
        "requirements": {},
    }])
    packet = engine.claim_next("output-contract", "renderer")
    claim = packet["claim"]
    workspace = Path(engine.project("output-contract")["workspace"])
    output_path = workspace / "artifacts" / "final.mp4"
    output_path.write_bytes(b"test mp4 bytes")

    with pytest.raises(ContractError, match="media_type mismatch"):
        engine.complete_task(
            "output-contract", "render-final", "renderer", claim["claim_token"],
            {"final.mp4": {"path": "artifacts/final.mp4", "media_type": "image/png", "rights_status": "OWNED"}},
        )

    completed = engine.complete_task(
        "output-contract", "render-final", "renderer", claim["claim_token"],
        {"final.mp4": {"path": "artifacts/final.mp4", "media_type": "video/mp4", "rights_status": "OWNED"}},
    )
    assert completed["result"]["deliverable_output_checks"]["final.mp4"]["status"] == "MECHANICAL_PASS"

    receipt = engine.release_check(
        "output-contract",
        completed["artifacts"]["final.mp4"]["artifact_id"],
        required_rubrics=["craft"],
    )
    assert receipt["pass"] is False
    assert "required_deliverable_missing:audio-master.wav" in receipt["failures"]
    assert receipt["media_job_acceptance"]["status"] == "BLOCKED"
