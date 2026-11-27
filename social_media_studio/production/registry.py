from __future__ import annotations

from typing import Any, Callable, Mapping

from .context import ProductionTaskContext
from ..domain.effects import LOCAL_DETERMINISTIC, RISK_CLASSES, TRUSTED_CODE_UNSANDBOXED
from .effect_gate import admit_registered_effect
from .handlers import (
    execute_delivery_package,
    execute_ffmpeg_assemble,
    execute_ffmpeg_video_audio_copy,
    execute_ffprobe_media_qa,
    execute_python_frame_render,
    execute_source_evidence_audit,
)


Executor = Callable[[ProductionTaskContext], dict[str, Any]]


class ProductionExecutorRegistry:
    def __init__(self) -> None:
        self._executors: dict[str, Executor] = {}
        self._effect_risks: dict[str, str] = {}

    def register(self, name: str, executor: Executor, *, effect_risk: str) -> None:
        if not name or name in self._executors:
            raise ValueError(f"production executor name is empty or already registered: {name!r}")
        if effect_risk not in RISK_CLASSES:
            raise ValueError(f"production executor must declare a known effect risk: {name!r}")
        self._executors[name] = executor
        self._effect_risks[name] = effect_risk

    def effect_risk(self, name: str) -> str:
        if name not in self._effect_risks:
            raise ValueError(f"unknown registered production effect: {name}")
        return self._effect_risks[name]

    def supports(self, name: str) -> bool:
        return name in self._executors

    def operations(self) -> tuple[str, ...]:
        return tuple(sorted(self._executors))

    def operation_for_task(self, task: Mapping[str, Any]) -> str | None:
        requirements = task.get("requirements", {})
        if not isinstance(requirements, Mapping):
            return None
        if task.get("kind") == "technical_measurement":
            tools = requirements.get("tools", [])
            if requirements.get("tool") == "ffprobe" or (isinstance(tools, list) and "ffprobe" in tools):
                return "ffprobe_media_qa"
        production = requirements.get("production", {})
        if not isinstance(production, Mapping):
            return None
        operation = production.get("operation")
        return str(operation) if isinstance(operation, str) and self.supports(operation) else None

    def execute(self, operation: str, context: ProductionTaskContext) -> dict[str, Any]:
        executor = self._executors.get(operation)
        if executor is None:
            raise ValueError(f"no registered production executor: {operation}")
        admit_registered_effect(self._effect_risks[operation], context)
        return executor(context)


PRODUCTION_EXECUTORS = ProductionExecutorRegistry()
PRODUCTION_EXECUTORS.register("python_frame_render", execute_python_frame_render, effect_risk=TRUSTED_CODE_UNSANDBOXED)
PRODUCTION_EXECUTORS.register("ffmpeg_assemble", execute_ffmpeg_assemble, effect_risk=LOCAL_DETERMINISTIC)
PRODUCTION_EXECUTORS.register("delivery_package", execute_delivery_package, effect_risk=LOCAL_DETERMINISTIC)
PRODUCTION_EXECUTORS.register("ffprobe_media_qa", execute_ffprobe_media_qa, effect_risk=LOCAL_DETERMINISTIC)

PRODUCTION_EXECUTORS.register("ffmpeg_video_audio_copy", execute_ffmpeg_video_audio_copy, effect_risk=LOCAL_DETERMINISTIC)

PRODUCTION_EXECUTORS.register("source_evidence_audit", execute_source_evidence_audit, effect_risk=LOCAL_DETERMINISTIC)
