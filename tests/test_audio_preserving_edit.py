from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import pytest

from social_media_studio.production.audio_preserve import (
    AudioIdentityError, VideoOnlyEditSpec, AudioPreservingVideoEditor, verify_audio_packet_identity,
)
from social_media_studio.production.ffmpeg_assembler import sha256_file
from social_media_studio.production.registry import PRODUCTION_EXECUTORS

def source_clip(root: Path) -> Path:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("real ffmpeg/ffprobe required")
    source=root/"source.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-v","error","-y",
        "-f","lavfi","-i","color=c=blue:s=160x120:d=3:r=15",
        "-f","lavfi","-i","sine=frequency=440:duration=3:sample_rate=48000",
        "-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
        "-shortest",str(source)],check=True,capture_output=True,timeout=60)
    return source

def spec(mode: str, **fields) -> VideoOnlyEditSpec:
    return VideoOnlyEditSpec.from_dict({"schema_version":"1.0","audio_promise":"BITSTREAM_IDENTITY",
        "source_input":"source","mode":mode,"video_output":"result","receipt_output":"proof",**fields})

def test_true_ffmpeg_cropped_video_keeps_all_audio_payload_packets(tmp_path):
    source=source_clip(tmp_path)
    for mode,options in (("PASSTHROUGH",{}),
                         ("CROP",{"crop":{"width":120,"height":80,"x":20,"y":20}})):
        obj=AudioPreservingVideoEditor().render(spec(mode,**options),source=source,
            source_sha256=sha256_file(source),output_dir=tmp_path/mode,
            expected_outputs={"result","proof"})
        receipt=obj["receipt"]
        assert receipt["audio_identity"]["promise"]=="BITSTREAM_IDENTITY"
        assert receipt["audio_identity"]["packet_count_source"]==receipt["audio_identity"]["packet_count_output"]
        assert receipt["owner_outcome_verified"] is False
        assert Path(obj["video_path"]).is_file()
        if mode=="CROP":
            assert (receipt["output_width"],receipt["output_height"])==(120,80)

def test_true_shortened_video_preserves_encoded_audio_prefix(tmp_path):
    source=source_clip(tmp_path)
    obj=AudioPreservingVideoEditor().render(spec("TRIM_END_ONLY",end_seconds=1.6),
        source=source,source_sha256=sha256_file(source),output_dir=tmp_path/"short",
        expected_outputs={"result","proof"})
    proof=obj["receipt"]["audio_identity"]
    assert proof["promise"]=="ORIGINAL_AUDIO_PREFIX_ONLY"
    assert 0 < proof["packet_count_output"] < proof["packet_count_source"]

def test_actual_audio_reencode_is_detected_not_passed_as_original(tmp_path):
    source=source_clip(tmp_path)
    changed=tmp_path/"transcoded.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-v","error","-y","-i",str(source),
                    "-map","0:v:0","-map","0:a:0","-c:v","copy",
                    "-c:a","aac","-b:a","64k",str(changed)],
                   check=True,capture_output=True,timeout=60)
    with pytest.raises(AudioIdentityError,match="packet identity"):
        verify_audio_packet_identity(source,changed)

def test_disallowed_edit_and_untrusted_source_are_blocked(tmp_path):
    assert PRODUCTION_EXECUTORS.supports("ffmpeg_video_audio_copy")
    for fields in [
        {"mode":"AI_BLOOD_REMOVAL"},
        {"mode":"ENHANCE_4K"},
        {"mode":"CROP","crop":{"width":119,"height":80,"x":20,"y":20}},
        {"mode":"TRIM_END_ONLY","end_seconds":0},
        {"mode":"PASSTHROUGH","audio_promise":"PERCEPTUAL_SIMILARITY"},
    ]:
        with pytest.raises(AudioIdentityError):
            VideoOnlyEditSpec.from_dict({"schema_version":"1.0","audio_promise":"BITSTREAM_IDENTITY",
                "source_input":"source","video_output":"result","receipt_output":"proof",**fields})
    source=source_clip(tmp_path)
    with pytest.raises(AudioIdentityError,match="digest changed"):
        AudioPreservingVideoEditor().render(spec("PASSTHROUGH"),source=source,
            source_sha256="0"*64,output_dir=tmp_path/"bad",
            expected_outputs={"result","proof"})


def test_real_owner_scoped_studio_claim_dispatch_complete_and_audio_receipt(tmp_path):
    import json
    from social_media_studio.engine import StudioEngine
    from social_media_studio.scope import bind_owner_brief
    from social_media_studio.production.worker_pool import run_ready_tool_tasks

    project="audio-crop-demand"
    engine=StudioEngine(tmp_path/"workspace")
    brief=bind_owner_brief(project, {
        "goal":"Crop original video without modifying encoded audio",
        "audience":"original owner","deliverables":["edited-video","audio-identity-report"],
        "deliverable_specs":[
            {"id":"edited-video","type":"MEDIA_TRANSFORM",
             "constraints":{"original_audio_promise":"BITSTREAM_IDENTITY"}},
            {"id":"audio-identity-report","type":"ANALYSIS_REPORT"},
        ]})
    engine.create_project(project,project,brief)
    video=source_clip(tmp_path)
    specfile=tmp_path/"edit.json"
    specfile.write_text(json.dumps({
        "schema_version":"1.0","source_input":"source-clip",
        "mode":"CROP","crop":{"width":120,"height":80,"x":20,"y":20},
        "audio_promise":"BITSTREAM_IDENTITY",
        "video_output":"edited-video","receipt_output":"audio-identity-report",
    }),encoding="utf-8")
    engine.import_asset(project,"source-clip",video,kind="video",
        media_type="video/mp4",rights_status="OWNED")
    engine.import_asset(project,"edit-spec",specfile,kind="document",
        media_type="application/json",rights_status="NOT_APPLICABLE")
    engine.add_tasks(project,[{
        "task_id":"crop-video-only","title":"Crop while retaining encoded audio",
        "kind":"media_transform","executor":"tool",
        "inputs":["source-clip","edit-spec"],
        "outputs":["edited-video","audio-identity-report"],
        "requirements":{"deliverable_refs":["edited-video","audio-identity-report"],
            "professional_demands":{"edited-video":["video_reframe","original_audio_preservation"],
                                    "audio-identity-report":["original_audio_preservation"]},
            "deliverable_outputs":{"edited-video":{"deliverable_id":"edited-video","variant_id":"edited-video"},
                                   "audio-identity-report":{"deliverable_id":"audio-identity-report","variant_id":"audio-identity-report"}},
            "decision_id":"crop-decision",
            "production":{"operation":"ffmpeg_video_audio_copy","edit_spec_input":"edit-spec"}},
        "acceptance":{"audio":"exact original encoded packet payloads","video":"crop to declared geometry"},
    }])
    assert set(engine.status(project)["decision_blocked_tasks"])=={"crop-video-only"}
    engine.record_decision(project,{
        "task_id":"crop-video-only","decision_id":"crop-decision",
        "question":"How to crop video without changing audio?",
        "scope":"actual video-only edit","source_refs":["source-clip","edit-spec"],
        "hypotheses":[{"id":"h1","discriminator":"reencoded audio would change packet hash"},
                      {"id":"h2","discriminator":"stream copy should preserve packet hash"}],
        "alternatives":[{"id":"copy"},{"id":"reencode"}],"selected_option":"copy",
        "falsifier":"any payload mismatch or stream loss",
        "rollback":"do not promote edited candidate; reopen source method",
    })
    outcome=run_ready_tool_tasks(engine,project,max_workers=1)
    assert outcome["failed"]==[],outcome
    assert len(outcome["completed"])==1,outcome
    assert engine.status(project)["task_counts"]=={"COMPLETED":1}
    finish=engine.list_tasks(project)[0]["result"]
    assert finish["production_executor"]=="ffmpeg_video_audio_copy"
    assert finish["identity_receipt"]["audio_identity"]["promise"]=="BITSTREAM_IDENTITY"
    assert finish["identity_receipt"]["owner_outcome_verified"] is False
    assert finish["identity_receipt"]["candidate_only"] is True
    progress=engine.status(project)["deliverable_progress"]
    assert progress["candidate_coverage_complete"] is True
    assert progress["owner_outcome_verified"] is False
    candidates={v["deliverable_id"]:v["candidates"] for v in progress["variants"]}
    assert candidates["edited-video"][0]["media_type"]=="video/mp4"
    assert candidates["audio-identity-report"][0]["media_type"]=="application/json"
    assert candidates["edited-video"][0]["artifact_id"] != candidates["audio-identity-report"][0]["artifact_id"]

