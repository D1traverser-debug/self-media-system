from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest
from PIL import Image

from video_studio.engine import StudioEngine
from video_studio.production.worker_pool import run_ready_tool_tasks


def _brief():
    return {
        "goal": "Assemble and package a short audiovisual production master from declared shot and audio assets.",
        "audience": "Video production operators.",
        "deliverables": [
            "final-video", "audio-master", "captions", "cover", "reproducible-project-source-bundle",
            "publish-copy", "rights-manifest", "technical-qa", "delivery-package",
        ],
    }


def _ffmpeg(path: Path, *args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", *args, "-y", str(path)],
        check=True, capture_output=True, text=True,
    )


def _source_assets(root: Path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg and FFprobe are required for production execution tests")
    shot1 = root / "shot-01.mp4"
    shot2 = root / "shot-02.mp4"
    audio = root / "audio-mix.wav"
    _ffmpeg(shot1, "-f", "lavfi", "-i", "color=c=blue:s=320x568:d=2:r=10", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an")
    _ffmpeg(shot2, "-f", "lavfi", "-i", "color=c=red:s=320x568:d=2:r=10", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an")
    _ffmpeg(audio, "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "2")
    captions = root / "captions.srt"
    captions.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nFirst shot\n\n"
        "2\n00:00:02,000 --> 00:00:04,000\nSecond shot\n",
        encoding="utf-8",
    )
    cover = root / "cover.png"
    Image.new("RGB", (320, 568), "navy").save(cover)
    publish = root / "publish-copy.md"
    publish.write_text("# A short production demo\n\nA deterministic local render test.\n", encoding="utf-8")
    rights = root / "rights-manifest.json"
    rights.write_text(json.dumps({"sources": ["owner-created test assets"], "cleared": True}), encoding="utf-8")
    timeline = root / "production-timeline.json"
    timeline.write_text(json.dumps({
        "schema_version": "1.0",
        "project_id": "delivery-demo",
        "archetype": "CINEMATIC_EXPLAINER",
        "width": 320,
        "height": 568,
        "fps": 10,
        "duration_seconds": 4,
        "clips": [
            {"input_name": "shot-01", "source_start_seconds": 0, "duration_seconds": 2, "fit": "cover"},
            {"input_name": "shot-02", "source_start_seconds": 0, "duration_seconds": 2, "fit": "cover"},
        ],
        "audio_tracks": [
            {"input_name": "audio-mix", "start_seconds": 0, "duration_seconds": 4, "gain_db": -6, "role": "MIX"},
        ],
        "audio_required": True,
        "captions_input": "captions",
        "burn_captions": False,
        "video_output": "final-video",
        "audio_output": "audio-master",
        "receipt_output": "render-receipt",
    }, indent=2), encoding="utf-8")
    return {
        "shot-01": (shot1, "video", "video/mp4", "OWNED"),
        "shot-02": (shot2, "video", "video/mp4", "OWNED"),
        "audio-mix": (audio, "audio", "audio/wav", "OWNED"),
        "captions": (captions, "subtitle", "application/x-subrip", "OWNED"),
        "cover": (cover, "image", "image/png", "OWNED"),
        "publish-copy": (publish, "document", "text/markdown", "OWNED"),
        "rights-manifest": (rights, "evidence", "application/json", "NOT_APPLICABLE"),
        "timeline-spec": (timeline, "document", "application/json", "NOT_APPLICABLE"),
    }


def test_end_to_end_production_render_qa_and_delivery_package(tmp_path):
    engine = StudioEngine(tmp_path / "workspace")
    engine.create_project("delivery-demo", "Production delivery demo", _brief())
    assets = _source_assets(tmp_path)
    for name, (path, kind, media_type, rights) in assets.items():
        engine.import_asset("delivery-demo", name, path, kind=kind, media_type=media_type, rights_status=rights)

    package_map = {
        "final-video": "deliverables/final-video.mp4",
        "audio-master": "deliverables/audio-master.wav",
        "captions": "deliverables/captions.srt",
        "cover": "deliverables/cover.png",
        "publish-copy": "publish/publish-copy.md",
        "rights-manifest": "rights/rights-manifest.json",
        "timeline-spec": "project/production-timeline.json",
        "shot-01": "project/assets/shot-01.mp4",
        "shot-02": "project/assets/shot-02.mp4",
        "audio-mix": "project/assets/audio-mix.wav",
        "render-receipt": "evidence/render-receipt.json",
        "technical-qa": "evidence/technical-qa.json",
    }
    required = list(package_map)
    engine.add_tasks("delivery-demo", [
        {
            "task_id": "render-master",
            "title": "Assemble the exact audiovisual master and separate audio master",
            "kind": "production_render",
            "executor": "tool",
            "depends_on": [],
            "inputs": ["timeline-spec", "shot-01", "shot-02", "audio-mix", "captions"],
            "outputs": ["final-video", "audio-master", "render-receipt"],
            "requirements": {"production": {"operation": "ffmpeg_assemble", "render_spec_input": "timeline-spec"}},
            "acceptance": {"render": "Produce a non-empty MP4, 24-bit WAV master and digest-bound render receipt."},
        },
        {
            "task_id": "technical-qa",
            "title": "Measure the exact rendered master",
            "kind": "technical_measurement",
            "executor": "tool",
            "depends_on": ["render-master"],
            "inputs": ["final-video"],
            "outputs": ["technical-qa"],
            "requirements": {
                "tools": ["ffprobe"],
                "resolution": "320x568",
                "frame_rate": 10,
                "duration_min_seconds": 3.9,
                "duration_max_seconds": 4.1,
                "audio_required": True,
            },
            "acceptance": {"qa": "The exact final candidate has the requested streams, dimensions, frame rate and duration."},
        },
        {
            "task_id": "package-delivery",
            "title": "Package all requested outputs and editable source dependencies",
            "kind": "delivery_package",
            "executor": "tool",
            "depends_on": ["technical-qa"],
            "inputs": required,
            "outputs": ["delivery-package", "delivery-manifest"],
            "requirements": {"production": {
                "operation": "delivery_package",
                "required_artifacts": required,
                "package_map": package_map,
                "package_output": "delivery-package",
                "manifest_output": "delivery-manifest",
                "expected_types": {
                    "final-video": {"kind": "video", "media_type": "video/mp4"},
                    "audio-master": {"kind": "audio", "media_type": "audio/wav"},
                    "captions": {"kind": "subtitle", "media_type": "application/x-subrip"},
                    "cover": {"kind": "image", "media_type": "image/png"},
                    "publish-copy": {"kind": "document", "media_type": "text/markdown"},
                    "rights-manifest": {"kind": "evidence", "media_type": "application/json"},
                    "timeline-spec": {"kind": "document", "media_type": "application/json"},
                    "shot-01": {"kind": "video", "media_type": "video/mp4"},
                    "shot-02": {"kind": "video", "media_type": "video/mp4"},
                    "audio-mix": {"kind": "audio", "media_type": "audio/wav"},
                    "render-receipt": {"kind": "evidence", "media_type": "application/json"},
                    "technical-qa": {"kind": "qa_report", "media_type": "application/json"}
                }
            }},
            "acceptance": {"delivery": "Every required deliverable and source dependency is present with exact artifact identity and digest."},
        },
    ])

    result = run_ready_tool_tasks(engine, "delivery-demo", worker_prefix="test-renderer", max_workers=2)
    assert result["scheduler_status"] == "COMPLETED", result
    assert [item["task_id"] for item in result["completed"]] == ["render-master", "technical-qa", "package-delivery"]
    assert result["failed"] == []
    assert result["ready_tool_tasks_without_registered_executor"] == []

    tasks = {item["task_id"]: item for item in engine.list_tasks("delivery-demo")}
    assert {key: value["status"] for key, value in tasks.items()} == {
        "render-master": "COMPLETED",
        "technical-qa": "COMPLETED",
        "package-delivery": "COMPLETED",
    }

    assert engine.audit("delivery-demo")["pass"] is True
    artifact_path = next(
        path for path in (engine._project_dir("delivery-demo") / "artifacts" / "production" / "package-delivery").rglob("delivery-package.zip")
    )
    assert artifact_path.is_file()
    with zipfile.ZipFile(artifact_path) as archive:
        names = set(archive.namelist())
    assert set(package_map.values()).issubset(names)
    assert "delivery-manifest.json" in names
    assert engine.audit("delivery-demo")["pass"] is True


def test_local_tool_pool_claims_independent_render_tasks_in_the_same_round(tmp_path):
    engine = StudioEngine(tmp_path / "parallel-workspace")
    engine.create_project("parallel-demo", "Parallel render demo", _brief())
    assets = _source_assets(tmp_path)
    for name, (path, kind, media_type, rights) in assets.items():
        engine.import_asset("parallel-demo", name, path, kind=kind, media_type=media_type, rights_status=rights)

    tasks = []
    for index in (1, 2):
        spec_name = f"timeline-{index}"
        spec = json.loads((tmp_path / "production-timeline.json").read_text(encoding="utf-8"))
        spec["project_id"] = "parallel-demo"
        spec["video_output"] = f"final-video-{index}"
        spec["audio_output"] = f"audio-master-{index}"
        spec["receipt_output"] = f"render-receipt-{index}"
        spec_path = tmp_path / f"{spec_name}.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        engine.import_asset("parallel-demo", spec_name, spec_path, kind="document", media_type="application/json", rights_status="NOT_APPLICABLE")
        tasks.append({
            "task_id": f"render-{index}",
            "title": f"Render independent candidate {index}",
            "kind": "production_render",
            "executor": "tool",
            "depends_on": [],
            "inputs": [spec_name, "shot-01", "shot-02", "audio-mix", "captions"],
            "outputs": [f"final-video-{index}", f"audio-master-{index}", f"render-receipt-{index}"],
            "requirements": {"production": {"operation": "ffmpeg_assemble", "render_spec_input": spec_name}},
            "acceptance": {"render": "Produce a digest-bound audiovisual candidate."},
        })
    engine.add_tasks("parallel-demo", tasks)
    result = run_ready_tool_tasks(engine, "parallel-demo", worker_prefix="parallel-renderer", max_workers=2)
    assert result["scheduler_status"] == "COMPLETED", result
    assert {item["task_id"] for item in result["claimed"]} == {"render-1", "render-2"}
    assert {item["task_id"] for item in result["completed"]} == {"render-1", "render-2"}
    assert len({item["worker_id"] for item in result["claimed"]}) == 2
    assert all(task["status"] == "COMPLETED" for task in engine.list_tasks("parallel-demo"))



def test_trusted_python_frame_renderer_produces_a_real_motion_shot(tmp_path):
    from video_studio.production.contracts import FrameRenderSpec, ProductionContractError

    engine = StudioEngine(tmp_path / "motion-workspace")
    engine.create_project("motion-demo", "Trusted motion renderer demo", _brief())
    renderer = tmp_path / "renderer.py"
    renderer.write_text(
        "from PIL import Image, ImageDraw\n"
        "def render_frame(t, width, height, assets, params):\n"
        "    image = Image.new('RGB', (width, height), tuple(params['background']))\n"
        "    draw = ImageDraw.Draw(image)\n"
        "    x = int((0.1 + 0.8 * t / params['duration']) * width)\n"
        "    y = height // 2\n"
        "    radius = max(3, min(width, height) // 12)\n"
        "    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=tuple(params['accent']))\n"
        "    draw.text((8, 8), params['title'], fill=(255, 255, 255))\n"
        "    return image\n",
        encoding="utf-8",
    )
    frame_spec = tmp_path / "frame-render-spec.json"
    frame_spec.write_text(json.dumps({
        "schema_version": "1.0",
        "project_id": "motion-demo",
        "renderer_input": "renderer-script",
        "entrypoint": "render_frame",
        "width": 160,
        "height": 284,
        "fps": 5,
        "duration_seconds": 2,
        "asset_inputs": [],
        "params": {"duration": 2, "title": "Motion test", "background": [7, 17, 35], "accent": [0, 220, 255]},
        "trusted_code_execution": True,
        "video_output": "shot-candidate",
        "receipt_output": "shot-render-receipt",
    }, indent=2), encoding="utf-8")
    engine.import_asset("motion-demo", "renderer-script", renderer, kind="source_code", media_type="text/x-python", rights_status="OWNED")
    engine.import_asset("motion-demo", "frame-render-spec", frame_spec, kind="document", media_type="application/json", rights_status="NOT_APPLICABLE")
    engine.add_tasks("motion-demo", [{
        "task_id": "render-motion-shot",
        "title": "Render a project-owned animated scene with explicit code execution approval",
        "kind": "production_render",
        "executor": "tool",
        "depends_on": [],
        "inputs": ["renderer-script", "frame-render-spec"],
        "outputs": ["shot-candidate", "shot-render-receipt"],
        "requirements": {"production": {
            "operation": "python_frame_render",
            "render_spec_input": "frame-render-spec",
            "trusted_code_execution": True,
        }},
        "acceptance": {"render": "Produce exactly 10 frames and a digest-bound candidate receipt."},
    }])

    result = run_ready_tool_tasks(engine, "motion-demo", worker_prefix="motion-renderer", max_workers=1)
    assert result["scheduler_status"] == "COMPLETED", result
    assert result["failed"] == []
    task = engine.list_tasks("motion-demo")[0]
    assert task["status"] == "COMPLETED"
    output_dir = engine._project_dir("motion-demo") / "artifacts" / "production" / "render-motion-shot" / "attempt-1"
    shot = output_dir / "shot-candidate.mp4"
    receipt = json.loads((output_dir / "shot-render-receipt.json").read_text(encoding="utf-8"))
    assert shot.is_file() and shot.stat().st_size > 0
    assert receipt["renderer"] == "python-frame-renderer-v1"
    assert receipt["trusted_project_code_execution"] is True
    assert receipt["candidate_only"] is True
    assert receipt["frame_count"] == 10
    assert engine.audit("motion-demo")["pass"] is True

    invalid = json.loads(frame_spec.read_text(encoding="utf-8"))
    invalid["trusted_code_execution"] = False
    invalid_spec = FrameRenderSpec.from_dict(invalid)
    with pytest.raises(ProductionContractError, match="trusted_code_execution=true"):
        invalid_spec.validate_inputs({"renderer-script"})



def test_executor_registry_reports_unknown_tool_tasks_without_claiming_them(tmp_path):
    from video_studio.production.registry import PRODUCTION_EXECUTORS

    assert set(PRODUCTION_EXECUTORS.operations()) == {
        "python_frame_render", "ffmpeg_assemble", "delivery_package", "ffprobe_media_qa",
    }
    engine = StudioEngine(tmp_path / "unknown-tool-workspace")
    engine.create_project("unknown-tool", "Unregistered tool demo", _brief())
    engine.add_tasks("unknown-tool", [{
        "task_id": "unknown-local-tool",
        "title": "A tool task with no registered executor",
        "kind": "unknown_tool_operation",
        "executor": "tool",
        "depends_on": [],
        "inputs": [],
        "outputs": ["unproduced-output"],
        "requirements": {"tool_name": "not-installed"},
        "acceptance": {"execution": "Must not be silently claimed or marked complete."},
    }])
    result = run_ready_tool_tasks(engine, "unknown-tool", max_workers=2)
    assert result["scheduler_status"] == "PARTIAL_UNREGISTERED_EXECUTORS"
    assert result["claimed"] == []
    assert result["completed"] == []
    assert result["ready_tool_tasks_without_registered_executor"][0]["task_id"] == "unknown-local-tool"
    assert engine.list_tasks("unknown-tool")[0]["status"] == "READY"
