from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..engine import StudioEngine, StudioError
from .context import ProductionTaskContext
from .contracts import ProductionContractError
from .registry import PRODUCTION_EXECUTORS


class ProductionTaskError(StudioError):
    pass


def run_claimed_tool_task(
    engine: StudioEngine, project_id: str, task_id: str, worker_id: str, claim_token: str,
) -> dict[str, Any]:
    packet = engine.claimed_packet(project_id, task_id, worker_id, claim_token)
    task = packet["task"]
    config: Mapping[str, Any] = {}
    operation = ""
    try:
        if task.get("executor") != "tool":
            raise ProductionContractError("local production registry only accepts tasks declared with executor=tool")
        requirements = task.get("requirements", {})
        raw_config = requirements.get("production", {})
        if raw_config is not None and not isinstance(raw_config, Mapping):
            raise ProductionContractError("task.requirements.production must be an object")
        config = raw_config or {}
        operation = PRODUCTION_EXECUTORS.operation_for_task(task) or ""
        if not operation:
            raise ProductionContractError("task has no registered local tool executor")
        attempt = int(task.get("attempt", 1))
        output_dir = engine._project_dir(project_id) / "artifacts" / "production" / task_id / f"attempt-{attempt}"
        output_dir.mkdir(parents=True, exist_ok=True)
        context = ProductionTaskContext(
            engine=engine, packet=packet, project_id=project_id, task_id=task_id,
            worker_id=worker_id, claim_token=claim_token, config=config, output_dir=output_dir,
        )
        return PRODUCTION_EXECUTORS.execute(operation, context)
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
        raise ProductionTaskError(f"tool task {task_id} failed in {operation or 'unregistered operation'}: {exc}") from exc


def run_claimed_production_task(
    engine: StudioEngine, project_id: str, task_id: str, worker_id: str, claim_token: str,
) -> dict[str, Any]:
    """Compatibility name for a claimed task dispatched through the production registry."""
    return run_claimed_tool_task(engine, project_id, task_id, worker_id, claim_token)
