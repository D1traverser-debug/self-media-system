from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ..engine import StudioEngine, StudioError
from .contracts import ProductionContractError, RenderSpec
from .delivery import create_delivery_package
from .ffmpeg_assembler import FfmpegAssembler


class ProductionTaskError(StudioError):
    pass


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProductionContractError(f"{label} must be an object")
    return value


def _output_payload(path: Path, *, kind: str, media_type: str, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise ProductionTaskError(f"production executor output is missing or empty: {path.name}")
    return {
        "path": str(path), "kind": kind, "media_type": media_type,
        "rights_status": "NOT_APPLICABLE", "metadata": dict(metadata or {}),
    }


def run_claimed_production_task(
    engine: StudioEngine, project_id: str, task_id: str, worker_id: str, claim_token: str,
) -> dict[str, Any]:
    packet = engine.claimed_packet(project_id, task_id, worker_id, claim_token)
    task = packet["task"]
    if task.get("executor") != "tool":
        raise ProductionContractError("production executor only accepts tasks declared with executor=tool")
    config = _mapping(task.get("requirements", {}).get("production"), "task.requirements.production")
    operation = str(config.get("operation", "")).strip()
    attempt = int(task.get("attempt", 1))
    output_dir = engine._project_dir(project_id) / "artifacts" / "production" / task_id / f"attempt-{attempt}"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = set(task.get("outputs", []))

    try:
        if operation == "ffmpeg_assemble":
            spec_name = str(config.get("render_spec_input", "")).strip()
            spec_artifact = packet["input_artifacts"].get(spec_name)
            if not spec_artifact:
                raise ProductionContractError(f"render spec is not a declared task input: {spec_name}")
            spec = RenderSpec.from_dict(json.loads(Path(str(spec_artifact["path"])).read_text(encoding="utf-8")))
            result = FfmpegAssembler().render(
                spec, input_artifacts=packet["input_artifacts"], output_dir=output_dir, expected_outputs=outputs,
            )
            artifact_outputs = {
                spec.video_output: _output_payload(
                    Path(result["video_path"]), kind="video", media_type="video/mp4",
                    metadata={"production_executor": operation, "candidate_only": True, "render_receipt_ref": spec.receipt_output},
                ),
                spec.audio_output: _output_payload(
                    Path(result["audio_path"]), kind="audio", media_type="audio/wav",
                    metadata={"production_executor": operation, "master_mix": True, "sample_rate": 48000, "bit_depth": 24},
                ),
                spec.receipt_output: _output_payload(
                    Path(result["receipt_path"]), kind="evidence", media_type="application/json",
                    metadata={"production_executor": operation, "media_sha256": result["receipt"]["output"]["sha256"]},
                ),
            }
            completion = engine.complete_task(
                project_id, task_id, worker_id, claim_token, artifact_outputs,
                {"production_executor": operation, "candidate_only": True, "render_receipt": result["receipt"]},
            )
            return {"operation": operation, "completion": completion}

        if operation == "delivery_package":
            package_map = _mapping(config.get("package_map"), "package_map")
            expected_types = _mapping(config.get("expected_types", {}), "expected_types")
            required = config.get("required_artifacts", [])
            if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
                raise ProductionContractError("required_artifacts must be an array of artifact names")
            missing = sorted(set(required) - set(packet["input_artifacts"]))
            if missing:
                raise ProductionContractError(f"delivery package is missing required input artifacts: {missing}")
            if not set(required).issubset(set(package_map)):
                raise ProductionContractError("package_map must include every required_artifact")
            package_output = str(config.get("package_output", "delivery-package"))
            manifest_output = str(config.get("manifest_output", "delivery-manifest"))
            if outputs != {package_output, manifest_output}:
                raise ProductionContractError("delivery task outputs must exactly match package_output and manifest_output")
            result = create_delivery_package(
                input_artifacts=packet["input_artifacts"],
                package_map={str(k): str(v) for k, v in package_map.items()},
                package_path=output_dir / f"{package_output}.zip",
                manifest_path=output_dir / f"{manifest_output}.json",
                project_id=project_id,
                expected_types=expected_types,
            )
            artifact_outputs = {
                package_output: _output_payload(
                    Path(result["package_path"]), kind="archive", media_type="application/zip",
                    metadata={"production_executor": operation, "artifact_count": result["manifest"]["artifact_count"], "package_sha256": result["manifest"]["package_sha256"]},
                ),
                manifest_output: _output_payload(
                    Path(result["manifest_path"]), kind="evidence", media_type="application/json",
                    metadata={"production_executor": operation, "package_sha256": result["manifest"]["package_sha256"]},
                ),
            }
            completion = engine.complete_task(
                project_id, task_id, worker_id, claim_token, artifact_outputs,
                {"production_executor": operation, "package_manifest": result["manifest"]},
            )
            return {"operation": operation, "completion": completion}

        raise ProductionContractError(f"no production executor registered for operation: {operation or '<empty>'}")
    except Exception as exc:
        try:
            engine.fail_task(
                project_id, task_id, worker_id, claim_token,
                {"failure_type": "PRODUCTION_EXECUTOR_FAILURE", "operation": operation, "error_type": type(exc).__name__, "message": str(exc)},
                retryable=bool(config.get("retryable", False)),
            )
        except Exception:
            pass
        if isinstance(exc, StudioError):
            raise
        raise ProductionTaskError(f"production task {task_id} failed in {operation or 'unknown operation'}: {exc}") from exc
