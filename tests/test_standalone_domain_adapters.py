from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from video_growth_agent.media_graph import (
    AssetRef,
    AssetVersion,
    ContextRecord,
    DecisionRecord,
    EvidenceRecord,
    MediaGraph,
)
from video_growth_agent.timeline import TimelineClip, TimelineSpec
from video_studio.adapters import (
    assess_shot_continuity,
    editorial_plan_from_dict,
    outcome_metrics,
    route_shot,
    run_claimed_domain_adapter,
    timeline_spec_from_dict,
)
from video_studio.cli import build_parser
from video_studio.engine import StudioEngine


def _editorial_payload():
    return {
        "intent": {
            "episode_id": "E001",
            "series_id": "systems-explained",
            "audience_contract": "Explain one system without faking certainty.",
            "editorial_question": "Why does inference move toward the edge?",
            "primary_platform": "BILIBILI",
            "target_duration_seconds": 120,
            "evidence_refs": ["research://edge-inference"],
            "desired_outcomes": ["qualified_watch_time"],
            "success_metric_semantics": {"qualified_watch_time": "minutes from target viewers"},
        },
        "claims": [
            {"claim_id": "C1", "statement": "This is an analytical framing.", "claim_class": "ANALYSIS", "risk": "MEDIUM"},
        ],
        "beats": [
            {"beat_id": "B1", "episode_id": "E001", "narrative_job": "Open the mechanism", "audience_function": "Create curiosity", "target_duration_seconds": 20, "claim_ids": ["C1"]},
        ],
        "shots": [
            {"shot_id": "S1", "beat_id": "B1", "visual_job": "Show the inference path", "target_duration_seconds": 2, "truth_mode": "SYNTHETIC", "risk": "LOW", "source_claim_ids": ["C1"], "allowed_production_modes": ["PROGRAMMATIC_GRAPHICS"]},
        ],
        "plan_version": "v1",
    }


def _brief():
    return {
        "goal": "Create and independently validate one short visual candidate.",
        "audience": "Technology viewers.",
        "deliverables": ["candidate.mp4", "render-receipt.json"],
        "success_criteria": ["The exact candidate and receipt are registered with immutable lineage."],
    }


def test_editorial_plan_adapter_validates_claim_beat_shot_traceability():
    plan = editorial_plan_from_dict(_editorial_payload())
    assert plan.plan_ref == "editorial-plan://E001@v1"
    assert len(plan.claims) == len(plan.beats) == len(plan.shots) == 1
    broken = _editorial_payload()
    broken["shots"][0]["beat_id"] = "missing-beat"
    with pytest.raises(ValueError, match="missing beat"):
        editorial_plan_from_dict(broken)


def test_timeline_adapter_reconstructs_refs_and_requires_promoted_graph_assets():
    graph = MediaGraph()
    graph.add_context(ContextRecord("program", "PROGRAM"))
    graph.add_context(ContextRecord("episode", "EPISODE", "program"))
    ref = AssetRef("take-01", "v1")
    graph.add_asset(AssetVersion(ref, "episode", "VIDEO", "asset://take-01", "sha256:take"))
    graph.add_evidence(EvidenceRecord("ev-01", "ASSET_VERSION", ref.key(), "REVIEW", ("review://take-01",), "2026-11-16T00:00:00Z"))
    graph.add_decision(DecisionRecord("dec-01", "PROMOTION", "director", (ref.key(),), ("criteria://shot",), ("ev-01",), "PROMOTE", "2026-11-16T00:01:00Z"))
    graph.promote_asset(ref, decision_id="dec-01")
    payload = {
        "timeline_id": "master", "version_id": "v1", "context_id": "episode",
        "clips": [{
            "clip_id": "clip-01", "asset_ref": {"asset_id": "take-01", "version_id": "v1"},
            "track_id": "V1", "timeline_start_seconds": 0, "source_start_seconds": 0,
            "duration_seconds": 5,
        }],
    }
    timeline = timeline_spec_from_dict(payload)
    timeline.validate_against_graph(graph)
    assert timeline.duration_seconds == 5
    graph.asset_state_overrides[ref] = "CANDIDATE"
    with pytest.raises(ValueError, match="not promoted"):
        timeline.validate_against_graph(graph)


def test_shot_router_adapter_uses_operation_capability_quality_and_evidence_gates():
    decision = route_shot({
        "request": {
            "shot_id": "S1", "required_capabilities": ["i2v", "image_reference"],
            "duration_seconds": 4, "minimum_quality": 4.0, "lane": "production", "risk": "hero",
        },
        "engines": [
            {"engine_id": "cheap", "capabilities": ["i2v", "image_reference"], "measured_quality": 4.1,
             "available": True, "output_cost_usd_per_second": 0.05,
             "quality_evidence_refs": ["benchmark://cheap"], "pricing_evidence_refs": ["pricing://cheap"]},
            {"engine_id": "premium", "capabilities": ["i2v", "image_reference"], "measured_quality": 4.8,
             "available": True, "premium": True, "output_cost_usd_per_second": 0.50,
             "quality_evidence_refs": ["benchmark://premium"], "pricing_evidence_refs": ["pricing://premium"]},
        ],
    })
    assert decision["selected_engine_id"] == "premium"
    assert all(item["eligible"] for item in decision["assessments"])


def test_business_metrics_adapter_preserves_objective_vector_without_global_score():
    result = outcome_metrics({
        "episode_id": "E001",
        "platform_receipts": [{
            "platform": "BILIBILI", "variant_id": "master-v1",
            "raw_metrics": {"play": 1000, "follow_conversion": 0.03},
            "metric_semantics": {"play": "platform play count", "follow_conversion": "play-to-follow"},
            "evidence_refs": ["platform://receipt"], "observed_at": "2026-11-16T00:00:00Z",
        }],
        "production": {
            "published_minutes": 2, "cash_cost_usd": 10, "creator_minutes": 60,
            "generated_video_seconds": 20, "premium_video_seconds": 5,
            "generation_attempts": 4, "rejected_generation_attempts": 1,
            "accepted_generated_assets": 3, "reused_asset_uses": 2,
        },
        "commercial": {
            "revenue_usd": 100, "direct_cost_usd": 20, "rights_revenue_usd": 5,
            "repeat_buy_signal": "UNKNOWN", "evidence_refs": ["commercial://receipt"],
        },
    })
    assert result["derived_metrics"]["cost_per_published_minute"] == 5
    assert result["derived_metrics"]["commercial_gross_margin_usd"] == 85
    assert "score" not in result["objective_vector"]


def test_cli_exposes_domain_adapter_execution_inside_standalone_runtime():
    args = build_parser().parse_args([
        "run-adapter", "demo", "render", "--worker", "renderer", "--token", "lease-token",
    ])
    assert args.command == "run-adapter"
    assert args.project_id == "demo"


def test_programmatic_graphic_adapter_executes_and_registers_candidate_with_lineage(tmp_path):
    font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe") or not font.is_file():
        pytest.skip("FFmpeg/ffprobe/DejaVuSans are required for local graphic rendering")

    engine = StudioEngine(tmp_path)
    engine.create_project("demo", "Adapter integration", _brief())

    plan_path = tmp_path / "editorial-plan.json"
    plan_path.write_text(json.dumps(_editorial_payload()), encoding="utf-8")
    shot_path = tmp_path / "shot-contract.json"
    shot_path.write_text(json.dumps({
        "shot_id": "S1", "sequence_id": "sequence-01", "narrative_job": "Show the inference path",
        "duration_seconds": 2, "truth_mode": "SYNTHETIC", "risk": "LOW",
        "allowed_modes": ["PROGRAMMATIC_GRAPHICS"], "required_capabilities": ["ffmpeg.drawtext"],
        "quality_targets": {"readability": 4}, "disclosure_required": True,
        "editorial_plan_ref": "editorial-plan://E001@v1", "beat_id": "B1", "source_claim_ids": ["C1"],
    }), encoding="utf-8")
    spec_path = tmp_path / "graphic-spec.json"
    spec_path.write_text(json.dumps({
        "spec_id": "spec-01", "kind": "TITLE_CARD", "title": "Inference moves closer",
        "subtitle": "A synthetic explanatory visual", "duration_seconds": 2,
        "width": 640, "height": 640, "fps": 24,
    }), encoding="utf-8")
    rights_path = tmp_path / "rights-clearance.txt"
    rights_path.write_text("The local font is licensed for this use.", encoding="utf-8")

    engine.import_asset("demo", "editorial-plan", plan_path, kind="document", media_type="application/json", rights_status="NOT_APPLICABLE")
    engine.import_asset("demo", "shot-contract", shot_path, kind="document", media_type="application/json", rights_status="NOT_APPLICABLE")
    engine.import_asset("demo", "graphic-spec", spec_path, kind="document", media_type="application/json", rights_status="NOT_APPLICABLE")
    engine.import_asset("demo", "font-asset", font, kind="font", media_type="font/ttf", rights_status="LICENSED")
    engine.import_asset("demo", "rights-clearance", rights_path, kind="document", media_type="text/plain", rights_status="OWNED")

    engine.add_tasks("demo", [{
        "task_id": "render", "title": "Render one programmatic graphic candidate",
        "kind": "domain_adapter", "executor": "tool", "depends_on": [],
        "inputs": ["editorial-plan", "shot-contract", "graphic-spec", "font-asset", "rights-clearance"],
        "outputs": ["graphic-candidate", "graphic-render-receipt"],
        "requirements": {"domain_adapter": {
            "name": "programmatic_graphic_render",
            "editorial_plan_input": "editorial-plan",
            "shot_contract_input": "shot-contract",
            "graphic_spec_input": "graphic-spec",
            "font_input": "font-asset",
            "rights_evidence_input": "rights-clearance",
            "video_output": "graphic-candidate",
            "receipt_output": "graphic-render-receipt",
        }},
        "acceptance": {"candidate": "The rendered output is a candidate only; it is not promoted or released."},
        "priority": 100,
    }])
    packet = engine.claim_next("demo", "renderer")
    assert packet["task"]["task_id"] == "render"
    result = run_claimed_domain_adapter(
        engine, "demo", "render", "renderer", packet["claim"]["claim_token"],
    )
    assert result["status"] == "COMPLETED"
    artifacts = result["completion"]["artifacts"]
    video = artifacts["graphic-candidate"]
    receipt = artifacts["graphic-render-receipt"]
    assert Path(video["path"]).is_file()
    assert video["metadata"]["candidate_only"] is True
    assert video["metadata"]["promotion_authorized"] is False
    assert video["metadata"]["rights_evidence_refs"] == ["rights-clearance"]
    receipt_payload = json.loads(Path(receipt["path"]).read_text(encoding="utf-8"))
    assert receipt_payload["candidate_only"] is True
    assert receipt_payload["release_authorized"] is False
    with engine._connect("demo") as connection:
        lineage = connection.execute(
            "SELECT COUNT(*) FROM artifact_inputs WHERE project_id='demo' AND output_artifact_id=?",
            (video["artifact_id"],),
        ).fetchone()[0]
    assert lineage == 5
    assert engine.audit("demo")["pass"] is True


def test_continuity_adapter_distinguishes_hard_identity_from_allowed_location_change():
    report = assess_shot_continuity({
        "before": {"shot_id": "S1", "dimensions": {"face": "approved-face", "wardrobe": "blue", "location": "office"}},
        "after": {"shot_id": "S2", "dimensions": {"face": "generic-face", "wardrobe": "blue", "location": "street"}},
        "link": {
            "from_shot_id": "S1", "to_shot_id": "S2",
            "rules": [
                {"dimension": "face", "severity": "HARD", "mode": "PRESERVE", "reason": "Identity must remain stable."},
                {"dimension": "wardrobe", "severity": "HARD", "mode": "PRESERVE"},
                {"dimension": "location", "severity": "SOFT", "mode": "ALLOW_CHANGE"},
            ],
        },
        "evidence_refs": ["frame://S1", "frame://S2"],
    })
    assert report["hard_pass"] is False
    violations = report["assessment"]["violations"]
    assert len(violations) == 1
    assert violations[0]["dimension"] == "face"
    assert violations[0]["severity"] == "HARD"


def test_extended_media_qa_adapter_records_loudness_and_silence_analysis(tmp_path):
    import subprocess

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg/ffprobe are required for extended media QA")
    engine = StudioEngine(tmp_path)
    engine.create_project("audio", "Extended QA", _brief())
    media = tmp_path / "audio-video.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-v", "error",
        "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1:r=25",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-y", str(media),
    ], check=True, capture_output=True)
    engine.import_asset("audio", "final-candidate", media, kind="video", media_type="video/mp4", rights_status="OWNED")
    engine.add_tasks("audio", [{
        "task_id": "extended-qa", "title": "Run supplementary loudness and silence QA",
        "kind": "domain_adapter", "executor": "tool", "depends_on": [],
        "inputs": ["final-candidate"], "outputs": ["extended-audio-qa"],
        "requirements": {"domain_adapter": {
            "name": "extended_media_qa", "media_input": "final-candidate", "output_name": "extended-audio-qa",
        }},
        "acceptance": {"qa": "Record integrated loudness, true peak, long silence and black-frame diagnostics."},
    }])
    packet = engine.claim_next("audio", "audio-qa")
    result = run_claimed_domain_adapter(engine, "audio", "extended-qa", "audio-qa", packet["claim"]["claim_token"])
    report = json.loads(Path(result["completion"]["artifacts"]["extended-audio-qa"]["path"]).read_text(encoding="utf-8"))
    check_ids = {item["check_id"] for item in report["checks"]}
    assert {"integrated_loudness", "true_peak", "long_silence", "black_frames"}.issubset(check_ids)
    assert report["metadata"]["checker"] == "ffmpeg-ffprobe-v0.2"
