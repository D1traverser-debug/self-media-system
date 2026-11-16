from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from .studio_engine import ContractError, GateError, StudioEngine


def _fraction(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        numerator, denominator = value.split("/", 1)
        denominator_value = float(denominator)
        return float(numerator) / denominator_value if denominator_value else None
    except (ValueError, ZeroDivisionError):
        try:
            return float(value)
        except ValueError:
            return None


def probe_media(path: str | Path, requirements: dict[str, Any] | None = None, *, timeout_seconds: int = 120) -> dict[str, Any]:
    """Inspect real media bytes with ffprobe; this measures technical facts only."""
    media = Path(path).resolve(strict=True)
    if not media.is_file() or media.stat().st_size == 0:
        raise ContractError("media must be a non-empty regular file")
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size,bit_rate,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels,duration",
        "-of", "json", str(media),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except FileNotFoundError as exc:
        raise GateError("ffprobe is not installed or is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise GateError(f"ffprobe timed out after {timeout_seconds}s") from exc
    if completed.returncode != 0:
        raise GateError(f"ffprobe failed: {completed.stderr.strip()[:2000]}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GateError("ffprobe returned invalid JSON") from exc

    streams = payload.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    fmt = payload.get("format", {})
    duration = float(fmt["duration"]) if fmt.get("duration") not in (None, "N/A") else None
    fps = _fraction((video or {}).get("avg_frame_rate")) or _fraction((video or {}).get("r_frame_rate"))
    req = requirements or {}
    checks: list[dict[str, Any]] = []

    def check(check_id: str, passed: bool, observed: Any, expected: Any = None, note: str = "") -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "observed": observed, "expected": expected, "note": note})

    check("video_stream", video is not None, bool(video), True)
    audio_required = bool(req.get("audio_required", True))
    check("audio_stream", audio is not None or not audio_required, bool(audio), "required" if audio_required else "optional")

    duration_min = req.get("duration_min_seconds")
    duration_max = req.get("duration_max_seconds")
    if duration_min is not None or duration_max is not None:
        duration_ok = duration is not None and (duration_min is None or duration >= float(duration_min)) and (duration_max is None or duration <= float(duration_max))
        check("duration_range", duration_ok, duration, {"min": duration_min, "max": duration_max})
    else:
        check("duration_readable", duration is not None and duration > 0, duration, "> 0 seconds")

    resolution = req.get("resolution")
    if resolution:
        try:
            expected_width, expected_height = (int(part) for part in str(resolution).lower().split("x", 1))
            observed = [video.get("width"), video.get("height")] if video else None
            check("resolution", observed == [expected_width, expected_height], observed, [expected_width, expected_height])
        except (ValueError, TypeError):
            raise ContractError("requirements.resolution must use WIDTHxHEIGHT, e.g. 1080x1920")

    fps_expected = req.get("frame_rate")
    if fps_expected is not None:
        check("frame_rate", fps is not None and abs(fps - float(fps_expected)) < 0.05, fps, float(fps_expected))

    stream_durations = [float(item["duration"]) for item in streams if item.get("duration") not in (None, "N/A")]
    if duration is not None and stream_durations:
        tolerance = float(req.get("stream_duration_tolerance_seconds", 0.25))
        delta = max(stream_durations) - min(stream_durations)
        check("stream_duration_match", delta <= tolerance, delta, f"<= {tolerance}s")

    hard_failures = [item["check_id"] for item in checks if item["status"] == "FAIL"]
    return {
        "schema_version": 1,
        "media_path": str(media),
        "media_sha256": _file_sha256(media),
        "size_bytes": media.stat().st_size,
        "format": fmt,
        "streams": streams,
        "summary": {
            "duration_seconds": duration,
            "video_codec": (video or {}).get("codec_name"),
            "width": (video or {}).get("width"),
            "height": (video or {}).get("height"),
            "frame_rate": fps,
            "audio_codec": (audio or {}).get("codec_name"),
            "audio_channels": (audio or {}).get("channels"),
        },
        "checks": checks,
        "hard_failures": hard_failures,
        "hard_pass": not hard_failures,
        "scope_warning": "Technical measurement only; it does not prove editorial quality, visual craft, humor, truth, rights or audience response.",
    }


def _file_sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_claimed_media_qa(
    engine: StudioEngine, project_id: str, task_id: str, worker_id: str,
    claim_token: str, input_name: str | None = None,
) -> dict[str, Any]:
    packet = engine.claimed_packet(project_id, task_id, worker_id, claim_token)
    task = packet["task"]
    requirements = task.get("requirements", {})
    if task.get("kind") != "technical_measurement" and requirements.get("tool") != "ffprobe":
        raise ContractError("qa-media can only execute a declared technical_measurement task")
    names = list(packet["input_artifacts"])
    selected = input_name or (names[0] if names else None)
    if selected not in packet["input_artifacts"]:
        raise ContractError(f"QA input {selected!r} is not a declared, available task input")
    if len(task["outputs"]) != 1:
        raise ContractError("qa-media task must declare exactly one output receipt")
    report = probe_media(packet["input_artifacts"][selected]["path"], requirements)
    report["project_id"] = project_id
    report["task_id"] = task_id
    report["input_artifact_id"] = packet["input_artifacts"][selected]["artifact_id"]
    output_name = task["outputs"][0]
    output_path = engine._project_dir(project_id) / "artifacts" / f"{task_id}-{report['media_sha256'][:12]}.qa.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    completed = engine.complete_task(
        project_id, task_id, worker_id, claim_token,
        {output_name: {
            "path": str(output_path), "kind": "qa_report", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"media_sha256": report["media_sha256"], "hard_pass": report["hard_pass"], "hard_failures": report["hard_failures"]},
        }},
        result={"measurement_completed": True, "hard_pass": report["hard_pass"], "hard_failures": report["hard_failures"]},
    )
    return {"report": report, "task_completion": completed}