"""Structural conformance uses observed bytes and never grants owner approval."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from social_media_studio.application.outcome_inspection import _probe
from social_media_studio.cli import build_parser
from social_media_studio.domain.conformance import assess_observation
from social_media_studio.engine import StudioEngine
from social_media_studio.scope import bind_owner_brief


def test_fake_png_with_truthy_mime_cannot_satisfy_visual_shape(tmp_path):
    fake = tmp_path / "fake.png"
    fake.write_bytes(b"not a PNG file")
    observation = _probe(fake, deliverable_type="STATIC_IMAGE", declared_media_type="image/png")
    result = assess_observation(
        deliverable_type="STATIC_IMAGE", declared_media_type="image/png",
        expected_shape={"width": 1200, "height": 900}, observation=observation,
    )
    assert result["status"] == "MISMATCH"
    assert not result["creative_quality_verified"]


def test_actual_image_dimensions_must_match_declared_shape_and_real_format(tmp_path):
    img = tmp_path / "really-jpeg.png"
    Image.new("RGB", (1200, 900), "white").save(img, format="JPEG")
    obs = _probe(img, deliverable_type="STATIC_IMAGE", declared_media_type="image/png")
    verdict = assess_observation(deliverable_type="STATIC_IMAGE", declared_media_type="image/png",
                                 expected_shape={"width": 1200, "height": 900}, observation=obs)
    assert verdict["status"] == "MISMATCH"
    assert "MEDIA_TYPE_DECLARATION_CONFLICTS_WITH_BYTES" in verdict["failures"]
    img2 = tmp_path / "wrong-size.png"
    Image.new("RGB", (1200, 900)).save(img2, format="PNG")
    verdict2 = assess_observation(
        deliverable_type="STATIC_IMAGE", declared_media_type="image/png",
        expected_shape={"width": 900, "height": 1200},
        observation=_probe(img2, deliverable_type="STATIC_IMAGE", declared_media_type="image/png"),
    )
    assert verdict2["status"] == "MISMATCH"
    assert "DECLARED_PIXEL_SHAPE_MISMATCH" in verdict2["failures"]


def test_real_shape_matches_only_structural_contract(tmp_path):
    img = tmp_path / "portrait.png"
    Image.new("RGB", (900, 1200)).save(img)
    outcome = assess_observation(
        deliverable_type="STATIC_IMAGE", declared_media_type="image/png",
        expected_shape={"width": 900, "height": 1200},
        observation=_probe(img, deliverable_type="STATIC_IMAGE", declared_media_type="image/png"),
    )
    assert outcome["status"] == "MATCH"
    assert outcome["observed"]["width"] == 900
    assert outcome["creative_quality_verified"] is False
    assert outcome["owner_outcome_verified"] is False


def test_document_claim_cannot_relabel_binary_or_invalid_json(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"\x00unexpected binary")
    assert _probe(bad, deliverable_type="SHORT_COPY", declared_media_type="text/plain")["error"]
    bad.write_text("{not-json}", encoding="utf-8")
    assert _probe(bad, deliverable_type="PLATFORM_PACKAGE", declared_media_type="application/json")["error"]


def _receipt(task_id):
    return {
        "task_id": task_id, "decision_id": "dec-" + task_id,
        "question": "Create exact requested deliverable variant", "scope": "owner fixture",
        "source_refs": ["owner-fixture"],
        "hypotheses": [{"id": "a", "discriminator": "correct ratio"},
                       {"id": "b", "discriminator": "wrong ratio"}],
        "alternatives": [{"id": "a"}, {"id": "b"}],
        "selected_option": "a", "falsifier": "measured ratio fails", "rollback": "revise",
    }


def test_durable_two_variant_outcome_inspection_uses_current_artifact_bytes(tmp_path):
    specs = [{"id": "cover", "type": "MULTI_ASPECT_IMAGE_SET", "variants": [
        {"id": "portrait", "shape": {"width": 900, "height": 1200, "orientation": "PORTRAIT"}},
        {"id": "landscape", "shape": {"width": 1600, "height": 900, "orientation": "LANDSCAPE"}},
    ]}]
    engine = StudioEngine(tmp_path / "workspace")
    brief = bind_owner_brief("fresh", {
        "goal": "Produce both actual cover variants", "audience": "owner",
        "deliverables": ["cover"], "deliverable_specs": specs,
    })
    engine.create_project("fresh", "fresh", brief)
    tasks = []
    for name in ("portrait", "landscape"):
        task_id = "render-" + name
        tasks.append({
            "task_id": task_id, "title": task_id, "executor": "agent",
            "kind": "production", "outputs": [task_id], "depends_on": [],
            "requirements": {
                "deliverable_refs": ["cover"], "decision_id": "dec-" + task_id,
                "professional_demands": {"cover": ["cover_design"]},
                "deliverable_outputs": {task_id: {"deliverable_id": "cover", "variant_id": name}},
            }, "acceptance": {"observable": "Measured pixel dimensions match exact requested variant"},
        })
    engine.add_tasks("fresh", tasks)
    for name in ("portrait", "landscape"):
        tid = "render-" + name
        engine.record_decision("fresh", _receipt(tid))
        packet = engine.claim_next("fresh", "worker", task_id=tid)
        assert packet and packet["task"]["task_id"] == tid
        path = engine._project_dir("fresh") / "artifacts" / (name + ".png")
        size = (900, 1200) if name == "portrait" else (900, 1600)
        Image.new("RGB", size).save(path)
        engine.complete_task("fresh", tid, "worker", packet["claim"]["claim_token"], {
            tid: {"path": str(path), "kind": "image", "media_type": "image/png", "rights_status": "OWNED"},
        })
    result = engine.inspect_outcome("fresh")
    by_id = {v["variant_id"]: v for v in result["variants"]}
    assert result["status"] == "OBSERVED_ONLY_NOT_OWNER_ACCEPTANCE"
    assert result["observed_conformance_complete"] is False
    assert by_id["portrait"]["observable_conformance"] == "MATCH"
    assert by_id["landscape"]["observable_conformance"] == "MISMATCH"
    assert result["owner_outcome_verified"] is False
    assert result["whole_demand_accepted"] is False
    assert result["artifact_release_coverage_complete"] is False
    parser = build_parser()
    assert parser.parse_args(["inspect-outcome", "fresh"]).project_id == "fresh"


def test_historical_untyped_scope_never_infers_format_acceptance(tmp_path):
    engine = StudioEngine(tmp_path)
    engine.create_project("old", "old", {
        "goal": "one caption", "audience": "owner", "deliverables": ["caption"],
    })
    result = engine.inspect_outcome("old")
    assert result["status"] == "UNTYPED_OR_HISTORICAL"
    assert result["observed_conformance_complete"] is False
    assert result["whole_demand_accepted"] is False


def test_two_current_covers_are_ambiguous_not_a_final_choice():
    from social_media_studio.domain.conformance import select_variant_candidate
    candidates = [
        {"artifact_id": "good", "artifact_status": "CURRENT", "conformance": {"status": "MATCH"}},
        {"artifact_id": "bad", "artifact_status": "CURRENT", "conformance": {"status": "MISMATCH"}},
    ]
    choice = select_variant_candidate(candidates)
    assert choice["status"] == "AMBIGUOUS"
    assert choice["selected_artifact_id"] is None
    assert choice["owner_selection_verified"] is False


def test_single_individually_released_artifact_is_selectable_but_not_owner_approved():
    from social_media_studio.domain.conformance import select_variant_candidate
    choice = select_variant_candidate([
        {"artifact_id": "rejected-draft", "artifact_status": "CURRENT"},
        {"artifact_id": "released", "artifact_status": "ACCEPTED"},
    ])
    assert choice["status"] == "SELECTED_INDIVIDUAL_RELEASE"
    assert choice["selected_artifact_id"] == "released"
    assert choice["owner_selection_verified"] is False
    assert select_variant_candidate([
        {"artifact_id": "one", "artifact_status": "ACCEPTED"},
        {"artifact_id": "two", "artifact_status": "ACCEPTED"},
    ])["status"] == "AMBIGUOUS"


def test_nonempty_text_is_a_minimum_for_actual_short_copy_bytes(tmp_path):
    empty = tmp_path / "blank.txt"
    empty.write_text("  \n\t\n", encoding="utf-8")
    observed = _probe(empty, deliverable_type="SHORT_COPY", declared_media_type="text/plain")
    finding = assess_observation(
        deliverable_type="SHORT_COPY", declared_media_type="text/plain",
        expected_shape=None, observation=observed,
    )
    assert finding["status"] == "MISMATCH"
    assert "DOCUMENT_CONTAINS_NO_NONWHITESPACE_TEXT" in finding["failures"]


def test_audio_preservation_promise_cannot_be_self_proved_by_container_and_dimensions():
    no_audio = assess_observation(
        deliverable_type="MEDIA_TRANSFORM", declared_media_type="video/mp4",
        expected_shape={"width": 1920, "height": 1080},
        constraints={"original_audio_promise": "BITSTREAM_IDENTITY"},
        observation={"kind": "VIDEO", "media_type": "video/mp4",
                     "width": 1920, "height": 1080, "has_audio_stream": False},
    )
    assert no_audio["status"] == "MISMATCH"
    assert "AUDIO_PROMISE_OUTPUT_HAS_NO_AUDIO_STREAM" in no_audio["failures"]
    has_audio = assess_observation(
        deliverable_type="MEDIA_TRANSFORM", declared_media_type="video/mp4",
        expected_shape={"width": 1920, "height": 1080},
        constraints={"original_audio_promise": "PCM_IDENTITY"},
        observation={"kind": "VIDEO", "media_type": "video/mp4",
                     "width": 1920, "height": 1080, "has_audio_stream": True},
    )
    assert has_audio["status"] == "UNVERIFIED"
    assert has_audio["audio_preservation_verified"] is False
    assert "ORIGINAL_AUDIO_PROMISE_NEEDS_SOURCE_BOUND_QA_PROOF" in has_audio["limitations"]


def test_current_multiple_alternative_cover_artifacts_are_not_silently_counted_as_complete(tmp_path):
    engine = StudioEngine(tmp_path / "workspace")
    brief = bind_owner_brief("alternatives", {
        "goal": "Deliver the actually selected portrait cover, not any one proposal",
        "audience": "owner", "deliverables": ["cover"],
        "deliverable_specs": [{"id": "cover", "type": "STATIC_IMAGE",
            "shape": {"width": 900, "height": 1200, "orientation": "PORTRAIT"}}],
    })
    engine.create_project("alternatives", "alternatives", brief)
    tasks = []
    for label in ("valid", "invalid"):
        tid = "render-" + label
        tasks.append({"task_id": tid, "title": tid, "executor": "agent",
            "kind": "production", "outputs": [tid], "depends_on": [],
            "requirements": {
                "deliverable_refs": ["cover"], "decision_id": "dec-" + tid,
                "professional_demands": {"cover": ["cover_design"]},
                "deliverable_outputs": {tid: {"deliverable_id": "cover", "variant_id": "cover"}},
            }, "acceptance": {"observable": "A specific actual output is measured"}})
    engine.add_tasks("alternatives", tasks)
    for label in ("valid", "invalid"):
        tid = "render-" + label
        engine.record_decision("alternatives", _receipt(tid))
        packet = engine.claim_next("alternatives", "worker", task_id=tid)
        assert packet
        actual = engine._project_dir("alternatives") / "artifacts" / (label + ".png")
        Image.new("RGB", (900, 1200) if label == "valid" else (1600, 900)).save(actual)
        engine.complete_task("alternatives", tid, "worker", packet["claim"]["claim_token"], {
            tid: {"path": str(actual), "kind": "image", "media_type": "image/png",
                  "rights_status": "OWNED"},
        })
    inspected = engine.inspect_outcome("alternatives")
    assert inspected["observed_conformance_complete"] is False
    assert inspected["variants"][0]["observable_conformance"] == "AMBIGUOUS"
    assert inspected["variants"][0]["candidate_selection"]["selected_artifact_id"] is None
    assert {c["conformance"]["status"] for c in inspected["variants"][0]["candidates"]} == {
        "MATCH", "MISMATCH",
    }
    assert inspected["whole_demand_accepted"] is False


def test_outcome_inspection_refuses_mixed_brief_revision_if_owner_changes_scope_mid_probe(tmp_path, monkeypatch):
    engine = StudioEngine(tmp_path / "current-scope")
    brief = bind_owner_brief("rev", {
        "goal": "Owner can revise cover ratio while a review is in flight",
        "audience": "owner", "deliverables": ["cover"],
        "deliverable_specs": [{"id": "cover", "type": "STATIC_IMAGE",
                               "shape": {"width": 900, "height": 1200, "orientation": "PORTRAIT"}}],
    })
    engine.create_project("rev", "rev", brief)
    original_status = engine.status
    calls = [0]

    def raced_status(project_id):
        status = original_status(project_id)
        calls[0] += 1
        if calls[0] == 2:
            status["project"] = dict(status["project"], revision=status["project"]["revision"] + 1)
        return status

    monkeypatch.setattr(engine, "status", raced_status)
    report = engine.inspect_outcome("rev")
    assert calls[0] == 2
    assert report["status"] == "INSPECTION_SNAPSHOT_CHANGED_RETRY"
    assert report["discarded_mixed_revision_observations"] is True
    assert report["observed_conformance_complete"] is False
    assert report["owner_outcome_verified"] is False


def test_inspection_rejects_candidate_changes_between_start_and_end_readback(tmp_path, monkeypatch):
    engine = StudioEngine(tmp_path / "current-scope")
    brief = bind_owner_brief("candidate-drift", {
        "goal": "Observe an exact current final variant",
        "audience": "owner", "deliverables": ["post"],
        "deliverable_specs": [{"id": "post", "type": "SHORT_COPY"}],
    })
    engine.create_project("candidate-drift", "candidate-drift", brief)
    original_status = engine.status
    calls = [0]

    def raced_status(project_id):
        status = original_status(project_id)
        calls[0] += 1
        if calls[0] == 2:
            status["deliverable_progress"] = dict(
                status["deliverable_progress"], rejected_bindings=[{"reason": "changed while observing"}],
            )
        return status

    monkeypatch.setattr(engine, "status", raced_status)
    result = engine.inspect_outcome("candidate-drift")
    assert result["status"] == "INSPECTION_SNAPSHOT_CHANGED_RETRY"
    assert result["observed_conformance_complete"] is False
    assert result["whole_demand_accepted"] is False
