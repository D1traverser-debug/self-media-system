"""Demand-specific execution loop: real readiness, parallelism, failure stop, learning."""
from __future__ import annotations

import pytest

from social_media_studio.engine import StudioEngine
from social_media_studio.scope import bind_owner_brief
from social_media_studio.operation_cycle import run_work_cycle
from social_media_studio.production.worker_pool import run_ready_tool_tasks
import social_media_studio.production.worker_pool as pool


def _brief():
    return {"goal": "Produce verified assets", "audience": "Reviewer", "deliverables": ["out"]}


def _task(tid, executor, requirements=None):
    return {
        "task_id": tid, "title": tid, "kind": "production_render",
        "executor": executor, "depends_on": [], "inputs": [],
        "outputs": [tid + "-out"], "requirements": requirements or {},
        "acceptance": {"observable": "A real artifact is required"},
    }


def test_cycle_plan_separates_parallel_agent_human_and_unavailable_tool(tmp_path):
    engine = StudioEngine(tmp_path)
    engine.create_project("mixed", "Mixed scope", _brief())
    engine.add_tasks("mixed", [
        _task("write", "agent"), _task("approve", "human"),
        _task("unconnected", "tool", {"production": {"operation": "not_registered"}}),
    ])
    before = engine.status("mixed")["event_count"]
    report = run_work_cycle(engine, "mixed", execute_tools=False)
    assert engine.status("mixed")["event_count"] == before
    assert report["tool_execution_performed"] is False
    assert report["execution"] is None
    assert report["after"]["parallel_ready_lanes"]["agent"] == ["write"]
    assert report["after"]["parallel_ready_lanes"]["human"] == ["approve"]
    assert report["after"]["parallel_ready_lanes"]["tool"] == []
    assert [(x["task_id"], x["reason"]) for x in report["after"]["blocked_tasks"]] == [
        ("unconnected", "UNREGISTERED_EXECUTOR")]
    assert report["release_authorized"] is False
    assert report["learning_promoted"] is False
    assert report["caos_native_activation_verified"] is False


def test_decision_blocked_tool_is_not_misreported_as_executor_gap(tmp_path):
    engine = StudioEngine(tmp_path)
    engine.create_project("active", "Governed current work", bind_owner_brief("active", _brief()))
    task = _task("needs-decision", "tool", {
        "deliverable_refs": ["out"],
        "production": {"operation": "no-such-executor"},
    })
    engine.add_tasks("active", [task])
    result = run_ready_tool_tasks(engine, "active", max_workers=2)
    assert result["scheduler_status"] == "BLOCKED_CURRENT_DECISION_REQUIRED"
    assert result["ready_tool_tasks_without_registered_executor"] == []
    report = run_work_cycle(engine, "active", execute_tools=False)
    assert report["after"]["blocked_tasks"][0]["reason"] == "DECISION_REQUIRED"


def test_tool_failure_cannot_be_blindly_retried_in_one_cycle(tmp_path, monkeypatch):
    engine = StudioEngine(tmp_path)
    engine.create_project("fails", "Failure case", _brief())
    engine.add_tasks("fails", [_task("probe", "tool", {
        "production": {"operation": "ffprobe_media_qa"},
    })])
    attempts = []

    def fails(engine, project_id, task_id, worker_id, token):
        attempts.append(task_id)
        engine.fail_task(project_id, task_id, worker_id, token,
                         {"message": "repeatable failure"}, retryable=True)
        raise RuntimeError("repeatable failure")

    monkeypatch.setattr(pool, "run_claimed_tool_task", fails)
    result = run_ready_tool_tasks(engine, "fails", max_rounds=6, max_workers=2)
    assert attempts == ["probe"], result
    assert len(result["failed"]) == 1
    assert result["scheduler_status"] == "FAILED_TASKS"
    assert result["claimed"] and len(result["claimed"]) == 1
    assert engine.status("fails")["task_counts"].get("READY", 0) == 1


def test_cycle_parameter_preflight_does_not_claim(tmp_path):
    engine = StudioEngine(tmp_path)
    engine.create_project("params", "Invalid execution capacity", _brief())
    with pytest.raises(ValueError, match="max_workers"):
        run_work_cycle(engine, "params", execute_tools=False, max_workers=0)
    assert engine.status("params")["event_count"] == 1


def test_agent_handoff_packet_binds_real_input_bytes_without_claim(tmp_path):
    import hashlib
    engine = StudioEngine(tmp_path / "workspace")
    engine.create_project("handoff", "Agent packet", _brief())
    source = tmp_path / "source.md"
    source.write_text("verified content", encoding="utf-8")
    registered = engine.import_asset("handoff", "source", source,
                                     kind="document", media_type="text/markdown",
                                     rights_status="OWNED")
    engine.add_tasks("handoff", [{
        **_task("draft", "agent"),
        "inputs": ["source"],
        "acceptance": {"output": "Use exact registered source bytes"},
    }])
    report = run_work_cycle(engine, "handoff", execute_tools=False)
    packet = report["after"]["handoff_packets"]["agent"][0]
    assert packet["task"]["task_id"] == "draft"
    assert packet["input_artifacts"]["source"]["artifact_id"] == registered["artifact_id"]
    assert packet["input_artifacts"]["source"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert packet["claimed"] is False
    assert packet["effect_authorized"] is False
    assert engine.list_tasks("handoff")[0]["status"] == "READY"
