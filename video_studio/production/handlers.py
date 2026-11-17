from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ..media import run_claimed_media_qa
from .context import ProductionTaskContext
from .contracts import FrameRenderSpec, ProductionContractError, RenderSpec
from .delivery import create_delivery_package
from .ffmpeg_assembler import FfmpegAssembler
from .python_frame_renderer import PythonFrameRenderer


def _output_payload(path: Path, *, kind: str, media_type: str, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise ProductionContractError(f"production executor output is missing or empty: {path.name}")
    return {
        "path": str(path), "kind": kind, "media_type": media_type,
        "rights_status": "NOT_APPLICABLE", "metadata": dict(metadata or {}),
    }


def execute_python_frame_render(context: ProductionTaskContext) -> dict[str, Any]:
    if context.config.get("trusted_code_execution") is not True:
        raise ProductionContractError("task config must explicitly authorize trusted_code_execution=true")
    spec_name = str(context.config.get("render_spec_input", "")).strip()
    spec_artifact = context.inputs.get(spec_name)
    if not spec_artifact:
        raise ProductionContractError(f"frame render spec is not a declared task input: {spec_name}")
    spec = FrameRenderSpec.from_dict(json.loads(Path(str(spec_artifact["path"])).read_text(encoding="utf-8")))
    result = PythonFrameRenderer().render(
        spec, input_artifacts=context.inputs, output_dir=context.output_dir,
        expected_outputs=context.outputs, project_root=context.engine._project_dir(context.project_id),
    )
    outputs = {
        spec.video_output: _output_payload(
            Path(result["video_path"]), kind="video", media_type="video/mp4",
            metadata={"production_executor": "python_frame_render", "candidate_only": True, "render_receipt_ref": spec.receipt_output},
        ),
        spec.receipt_output: _output_payload(
            Path(result["receipt_path"]), kind="evidence", media_type="application/json",
            metadata={"production_executor": "python_frame_render", "frame_count": spec.frame_count, "media_sha256": result["receipt"]["output"]["sha256"]},
        ),
    }
    completion = context.engine.complete_task(
        context.project_id, context.task_id, context.worker_id, context.claim_token, outputs,
        {"production_executor": "python_frame_render", "candidate_only": True, "render_receipt": result["receipt"]},
    )
    return {"operation": "python_frame_render", "completion": completion}


def execute_ffmpeg_assemble(context: ProductionTaskContext) -> dict[str, Any]:
    spec_name = str(context.config.get("render_spec_input", "")).strip()
    spec_artifact = context.inputs.get(spec_name)
    if not spec_artifact:
        raise ProductionContractError(f"render spec is not a declared task input: {spec_name}")
    spec = RenderSpec.from_dict(json.loads(Path(str(spec_artifact["path"])).read_text(encoding="utf-8")))
    result = FfmpegAssembler().render(
        spec, input_artifacts=context.inputs, output_dir=context.output_dir, expected_outputs=context.outputs,
    )
    outputs = {
        spec.video_output: _output_payload(
            Path(result["video_path"]), kind="video", media_type="video/mp4",
            metadata={"production_executor": "ffmpeg_assemble", "candidate_only": True, "render_receipt_ref": spec.receipt_output},
        ),
        spec.audio_output: _output_payload(
            Path(result["audio_path"]), kind="audio", media_type="audio/wav",
            metadata={"production_executor": "ffmpeg_assemble", "master_mix": True, "sample_rate": 48000, "bit_depth": 24},
        ),
        spec.receipt_output: _output_payload(
            Path(result["receipt_path"]), kind="evidence", media_type="application/json",
            metadata={"production_executor": "ffmpeg_assemble", "media_sha256": result["receipt"]["output"]["sha256"]},
        ),
    }
    completion = context.engine.complete_task(
        context.project_id, context.task_id, context.worker_id, context.claim_token, outputs,
        {"production_executor": "ffmpeg_assemble", "candidate_only": True, "render_receipt": result["receipt"]},
    )
    return {"operation": "ffmpeg_assemble", "completion": completion}


def execute_delivery_package(context: ProductionTaskContext) -> dict[str, Any]:
    package_map = context.config.get("package_map")
    if not isinstance(package_map, Mapping):
        raise ProductionContractError("package_map must be an object")
    expected_types = context.config.get("expected_types", {})
    if not isinstance(expected_types, Mapping):
        raise ProductionContractError("expected_types must be an object")
    required = context.config.get("required_artifacts", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise ProductionContractError("required_artifacts must be an array of artifact names")
    missing = sorted(set(required) - set(context.inputs))
    if missing:
        raise ProductionContractError(f"delivery package is missing required input artifacts: {missing}")
    if not set(required).issubset(set(package_map)):
        raise ProductionContractError("package_map must include every required_artifact")
    package_output = str(context.config.get("package_output", "delivery-package"))
    manifest_output = str(context.config.get("manifest_output", "delivery-manifest"))
    if context.outputs != {package_output, manifest_output}:
        raise ProductionContractError("delivery task outputs must exactly match package_output and manifest_output")
    result = create_delivery_package(
        input_artifacts=context.inputs,
        package_map={str(k): str(v) for k, v in package_map.items()},
        package_path=context.output_dir / f"{package_output}.zip",
        manifest_path=context.output_dir / f"{manifest_output}.json",
        project_id=context.project_id,
        expected_types=expected_types,
    )
    outputs = {
        package_output: _output_payload(
            Path(result["package_path"]), kind="archive", media_type="application/zip",
            metadata={"production_executor": "delivery_package", "artifact_count": result["manifest"]["artifact_count"], "package_sha256": result["manifest"]["package_sha256"]},
        ),
        manifest_output: _output_payload(
            Path(result["manifest_path"]), kind="evidence", media_type="application/json",
            metadata={"production_executor": "delivery_package", "package_sha256": result["manifest"]["package_sha256"]},
        ),
    }
    completion = context.engine.complete_task(
        context.project_id, context.task_id, context.worker_id, context.claim_token, outputs,
        {"production_executor": "delivery_package", "package_manifest": result["manifest"]},
    )
    return {"operation": "delivery_package", "completion": completion}


def execute_ffprobe_media_qa(context: ProductionTaskContext) -> dict[str, Any]:
    return run_claimed_media_qa(
        context.engine, context.project_id, context.task_id, context.worker_id, context.claim_token,
    )
