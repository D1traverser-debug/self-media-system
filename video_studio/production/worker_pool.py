from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from ..engine import StudioEngine
from .executors import run_claimed_tool_task
from .registry import PRODUCTION_EXECUTORS


def run_ready_tool_tasks(
    engine: StudioEngine, project_id: str, *, worker_prefix: str = "local-tool",
    max_workers: int = 2, lease_seconds: int = 900, max_rounds: int = 50,
) -> dict[str, Any]:
    """Run registered local tool tasks concurrently, then refresh and schedule downstream ready rounds."""
    if not 1 <= max_workers <= 16:
        raise ValueError("max_workers must be between 1 and 16")
    if not 1 <= max_rounds <= 500:
        raise ValueError("max_rounds must be between 1 and 500")
    completed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    claimed_total: list[dict[str, Any]] = []
    unregistered_by_id: dict[str, dict[str, Any]] = {}
    rounds = 0

    for round_number in range(1, max_rounds + 1):
        rounds = round_number
        tasks = engine.list_tasks(project_id)
        ready = [item for item in tasks if item.get("status") == "READY" and item.get("executor") == "tool"]
        candidates = [item for item in ready if PRODUCTION_EXECUTORS.operation_for_task(item)]
        for item in ready:
            if not PRODUCTION_EXECUTORS.operation_for_task(item):
                unregistered_by_id[item["task_id"]] = {
                    "task_id": item["task_id"], "title": item.get("title"),
                    "kind": item.get("kind"), "requirements": item.get("requirements", {}),
                }
        if not candidates:
            break

        claims: list[dict[str, Any]] = []
        for index, task in enumerate(candidates[:max_workers], start=1):
            worker_id = f"{worker_prefix}-{round_number}-{index}"
            packet = engine.claim_next(project_id, worker_id, lease_seconds, executor="tool", task_id=task["task_id"])
            if packet:
                claims.append(packet)
                claimed_total.append({"task_id": task["task_id"], "worker_id": worker_id})
        if not claims:
            break

        with ThreadPoolExecutor(max_workers=len(claims), thread_name_prefix="vga-tool") as pool:
            futures = {
                pool.submit(
                    run_claimed_tool_task, engine, project_id, packet["task"]["task_id"],
                    packet["claim"]["worker_id"], packet["claim"]["claim_token"],
                ): packet for packet in claims
            }
            for future in as_completed(futures):
                packet = futures[future]
                try:
                    completed.append({"task_id": packet["task"]["task_id"], "result": future.result()})
                except Exception as exc:
                    failed.append({"task_id": packet["task"]["task_id"], "error_type": type(exc).__name__, "error": str(exc)})

    return {
        "project_id": project_id, "rounds": rounds, "max_workers": max_workers,
        "claimed": claimed_total, "completed": completed, "failed": failed,
        "ready_tool_tasks_without_registered_executor": list(unregistered_by_id.values()),
        "scheduler_status": (
            "COMPLETED_WITH_FAILURES" if failed else
            "PARTIAL_UNREGISTERED_EXECUTORS" if unregistered_by_id else
            "COMPLETED"
        ),
    }
