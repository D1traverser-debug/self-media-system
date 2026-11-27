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
