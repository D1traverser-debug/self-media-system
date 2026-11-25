"""A bounded self-media operation cycle: real local effects and explicit handoffs.

CAOS remains external parent governance, not a Python runtime dependency.
No automatic agent/human impersonation, external paid calls, release or learning
promotion. Project-specific task graphs and current decision admission are read
from the single StudioEngine ledger.
"""
from __future__ import annotations

from typing import Any
from contextlib import closing

from .engine import StudioEngine, GateError
from .production.executors import tool_executor_for_task
from .production.worker_pool import run_ready_tool_tasks


def _snapshot(engine: StudioEngine, project_id: str) -> dict[str, Any]:
    admission = engine.status(project_id)
    tasks = engine.list_tasks(project_id)
    admitted = set(admission["admitted_ready_tasks"])
    decision_blocked = admission["decision_blocked_tasks"]
    retry_exhausted = admission["retry_exhausted_tasks"]
    parallel: dict[str, list[str]] = {"tool": [], "agent": [], "human": [], "external": []}
    blocked: list[dict[str, Any]] = []
    handoff_packets: dict[str, list[dict[str, Any]]] = {"agent": [], "human": [], "external": []}
    for task in tasks:
        task_id = task["task_id"]
        status = task["status"]
        executor = task.get("executor", "unknown")
        if status == "READY":
            if task_id in retry_exhausted:
                reason = "RETRY_BUDGET_EXHAUSTED"
            elif task_id in decision_blocked:
                reason = "DECISION_REQUIRED"
            elif executor == "tool" and tool_executor_for_task(task) is None:
                reason = "UNREGISTERED_EXECUTOR"
            else:
                parallel.setdefault(executor, []).append(task_id)
                continue
        elif status in {"RUNNING", "COMPLETED"}:
            continue
        elif status == "FAILED":
            reason = "ROOT_CAUSE_REPLAN_REQUIRED"
        elif status == "WAITING_INPUT":
            reason = "INPUT_OR_EXTERNAL_DEPENDENCY"
        elif status == "STALE":
            reason = "INVALIDATED_UPSTREAM"
        else:
            reason = "DEPENDENCIES_NOT_SATISFIED"
        blocked.append({
            "task_id": task_id, "status": status, "reason": reason,
            "depends_on": task.get("depends_on", []),
        })
    # A real, read-only task packet has exact current input artifact hashes.
    # It does NOT claim a task or authorize an Agent, human or external effect.
    with closing(engine._connect(project_id)) as connection:
        for executor in ("agent", "human", "external"):
            for task_id in list(parallel[executor]):
                row = connection.execute(
                    "SELECT * FROM tasks WHERE project_id=? AND task_id=? AND status='READY'",
                    (project_id, task_id),
                ).fetchone()
                if row is None:
                    continue  # readiness changed while projecting; a claim must recheck
                try:
                    packet = engine._work_packet(connection, project_id, row)
                except GateError as exc:
                    parallel[executor].remove(task_id)
                    blocked.append({"task_id": task_id, "status": "READY",
                                    "reason": "INPUT_PROVENANCE_INVALID",
                                    "detail": str(exc)})
                    continue
                if packet["missing_inputs"]:
                    parallel[executor].remove(task_id)
                    blocked.append({"task_id": task_id, "status": "READY",
                                    "reason": "INPUT_OR_EXTERNAL_DEPENDENCY",
                                    "detail": packet["missing_inputs"]})
                    continue
                handoff_packets[executor].append({
                    "task": packet["task"],
                    "input_artifacts": packet["input_artifacts"],
                    "missing_inputs": packet["missing_inputs"],
                    "instructions": packet["instructions"],
                    "claimed": False,
                    "effect_authorized": False,
                    "requires_fresh_claim_and_decision_recheck": True,
                })
    return {
        "handoff_packets": handoff_packets,
        "task_counts": admission["task_counts"],
        "open_failures": admission["open_failures"],
        "parallel_ready_lanes": {key: sorted(values) for key, values in parallel.items()},
        "blocked_tasks": sorted(blocked, key=lambda item: item["task_id"]),
        "all_tasks_complete": bool(tasks) and all(t["status"] == "COMPLETED" for t in tasks),
        "event_count": admission["event_count"],
    }


def run_work_cycle(
    engine: StudioEngine, project_id: str, *, execute_tools: bool = True,
    max_workers: int = 2, max_rounds: int = 50,
) -> dict[str, Any]:
    """Dispatch only admitted local tools, then reconcile the real project state."""
    if not 1 <= max_workers <= 16 or not 1 <= max_rounds <= 500:
        raise ValueError("max_workers must be 1..16 and max_rounds must be 1..500")
    before = _snapshot(engine, project_id)
    execution = (
        run_ready_tool_tasks(engine, project_id, max_workers=max_workers, max_rounds=max_rounds)
        if execute_tools else None
    )
    after = _snapshot(engine, project_id)
    candidates = sorted(
        item["learning_id"] for item in engine.list_learning(project_id)
        if item["status"] == "CANDIDATE"
    )
    reasons = {item["reason"] for item in after["blocked_tasks"]}
    lanes = after["parallel_ready_lanes"]
    next_actions: list[str] = []
    if "ROOT_CAUSE_REPLAN_REQUIRED" in reasons or (execution and execution["failed"]):
        next_actions.append("Diagnose root causes, challenge the method, repair and independently replay.")
    if "DECISION_REQUIRED" in reasons or "RETRY_BUDGET_EXHAUSTED" in reasons:
        next_actions.append("Bind a current CAOS-governed decision or revise exhausted contracts.")
    if "UNREGISTERED_EXECUTOR" in reasons:
        next_actions.append("Verify and register the exact local executor before claiming this task.")
    if lanes["agent"]:
        next_actions.append("Dispatch admitted agent work packets with current input digests.")
    if lanes["human"]:
        next_actions.append("Obtain actual human review or authorization; do not self-approve.")
    if lanes["external"]:
        next_actions.append("Verify external operation, cost, rights and owner authorization.")
    if "INPUT_PROVENANCE_INVALID" in reasons:
        next_actions.append("Audit tampered or missing input bytes; invalidate affected descendants before retry.")
    if "INPUT_OR_EXTERNAL_DEPENDENCY" in reasons:
        next_actions.append("Import required verified input and refresh the dependency graph.")
    if "INVALIDATED_UPSTREAM" in reasons:
        next_actions.append("Reopen invalidated work only after the earliest cause is repaired.")
    if lanes["tool"]:
        next_actions.append("Execute admitted local tool tasks in the next bounded cycle.")
    if after["all_tasks_complete"]:
        next_actions.append("Independently inspect final artifacts and run exact-digest release-check.")
    if candidates:
        next_actions.append("Replay learning candidates with independent evidence before promotion.")
    if not next_actions:
        next_actions.append("Inspect the outcome and dependency ledger; no effect is authorized.")
    return {
        "project_id": project_id, "cycle": "BOUNDED_OPERATIONAL_LOOP",
        "before": before, "execution": execution, "after": after,
        "learning_candidates": candidates, "next_actions": next_actions,
        "tool_execution_performed": execute_tools,
        "caos_native_activation_verified": False,
        "release_authorized": False, "learning_promoted": False,
        "independent_acceptance_verified": False,
    }
