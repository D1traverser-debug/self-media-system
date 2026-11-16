from __future__ import annotations

from typing import Any, Callable, Mapping

from .context import ProductionTaskContext
from .handlers import (
    execute_delivery_package,
    execute_ffmpeg_assemble,
    execute_ffprobe_media_qa,
    execute_python_frame_render,
)


Executor = Callable[[ProductionTaskContext], dict[str, Any]]


class ProductionExecutorRegistry:
    def __init__(self) -> None:
        self._executors: dict[str, Executor] = {}

    def register(self, name: str, executor: Executor) -> None:
        if not name or name in self._executors:
            raise ValueError(f"production executor name is empty or already registered: {name!r}")
        self._executors[name] = executor

    def supports(self, name: str) -> bool:
        return name in self._executors

    def operations(self) -> tuple[str, ...]:
        return tuple(sorted(self._executors))

    def operation_for_task(self, task: Mapping[str, Any]) -> str | None:
        if task.get("kind") == "technical_measurement":
            requirements = task.get("requirements", {})
            if requirements.get("tool") == "ffprobe" or "ffprobe" in requirements.get("tools", []):
                return "ffprobe_media_qa"
        operation = task.get("requirements", {}).get("production", {}).get("operation")
        return str(operation) if isinstance(operation, str) and self.supports(operation) else None

    def execute(self, operation: str, context: ProductionTaskContext) -> dict[str, Any]:
        executor = self._executors.get(operation)
        if executor is None:
            raise ValueError(f"no registered production executor: {operation}")
        return executor(context)


PRODUCTION_EXECUTORS = ProductionExecutorRegistry()
PRODUCTION_EXECUTORS.register("python_frame_render", execute_python_frame_render)
PRODUCTION_EXECUTORS.register("ffmpeg_assemble", execute_ffmpeg_assemble)
PRODUCTION_EXECUTORS.register("delivery_package", execute_delivery_package)
PRODUCTION_EXECUTORS.register("ffprobe_media_qa", execute_ffprobe_media_qa)
