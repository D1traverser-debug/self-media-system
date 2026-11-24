import json
from pathlib import Path

import pytest

from video_studio.engine import StudioEngine
from video_studio.scope import EPOCH, bind_owner_brief, resolve_intake


def test_new_request_is_not_a_default_task_and_does_not_mutate(tmp_path):
    root = tmp_path / "not-created"
    for goal in ("Write a title only", "Edit source video without touching audio", "Design an original cover"):
        route = resolve_intake(root, {"mode": "NEW", "goal": goal})
        assert route["goal"] == goal
        assert route["project_id"] is None
        assert route["selected_task_graph"] is None
        assert route["native_activation"] == "NOT_VERIFIED_BY_RUNTIME"
        assert route["effect_authorized"] is False
        assert "professional_aesthetic_judgment" in route["architecture"]["continuous_responsibilities"]
    assert not root.exists()


def test_retired_and_unmarked_work_cannot_resume(tmp_path):
    engine = StudioEngine(tmp_path)
    brief = {"goal": "old", "audience": "test", "deliverables": ["old"]}
    engine.create_project("old-local", "old", brief)
    for name in ("ai-self-media-commercialization", "pilot-001", "pilot-002", "old-local", "unknown"):
        with pytest.raises(ValueError):
            resolve_intake(tmp_path, {"mode": "RESUME", "project_id": name})
    with pytest.raises(ValueError):
        resolve_intake(tmp_path, {"mode": "RESUME"})


def test_fresh_owner_task_can_be_one_node_and_resume_by_exact_id(tmp_path):
    engine = StudioEngine(tmp_path)
    brief = bind_owner_brief("fresh", {"goal": "Write one original caption", "audience": "test", "deliverables": ["caption"]})
    engine.create_project("fresh", "fresh", brief)
    task = {"task_id": "write", "outputs": ["caption"], "acceptance": {"quality": "original concise caption"},
            "requirements": {"deliverable_refs": ["caption"]}}
    engine.add_tasks("fresh", [task])
    assert engine.status("fresh")["task_counts"] == {"READY": 1}
    route = resolve_intake(tmp_path, {"mode": "RESUME", "project_id": "fresh"})
    assert route["brief"]["scope_epoch"] == EPOCH
    assert route["goal"] == brief["goal"]
    assert route["selected_task_graph"] is None
    # The plan is structurally ready but not authorized by a current local decision.
    assert engine.claim_next("fresh", "writer") is None
    task["requirements"]["decision_id"] = "write-decision"
    engine.revise_task("fresh", "write", {"requirements": task["requirements"]}, reason="bind the current decision")
    engine.reopen("fresh", "write", "decision binding prepared")
    engine.record_decision("fresh", decision_receipt("write", "write-decision"))
    assert engine.claim_next("fresh", "writer")["task"]["task_id"] == "write"


def test_stale_or_unrelated_task_binding_fails_without_state_mutation(tmp_path):
    engine = StudioEngine(tmp_path)
    brief = bind_owner_brief("fresh", {"goal": "Write one caption", "audience": "test", "deliverables": ["caption"]})
    engine.create_project("fresh", "fresh", brief)
    bad = {"task_id": "old-task", "outputs": ["old"], "acceptance": {"quality": "old"},
           "requirements": {"deliverable_refs": ["old deliverable"]}}
    with pytest.raises(ValueError):
        engine.add_tasks("fresh", [bad])
    assert engine.list_tasks("fresh") == []
    task = {"task_id": "write", "outputs": ["caption"], "acceptance": {"quality": "original"},
            "requirements": {"deliverable_refs": ["caption"]}}
    engine.add_tasks("fresh", [task])
    with pytest.raises(ValueError):
        engine.revise_task("fresh", "write", {"requirements": {"deliverable_refs": ["old"]}}, reason="test")
    assert engine.list_tasks("fresh")[0]["requirements"]["deliverable_refs"] == ["caption"]


def test_cli_rejects_legacy_workspace_on_all_owner_paths(tmp_path, capsys):
    from video_studio.cli import main
    workspace = tmp_path / "workspace"
    engine = StudioEngine(workspace)
    engine.create_project("old-local", "old", {"goal": "old", "audience": "test", "deliverables": ["old"]})
    assert main(["--root", str(workspace), "status", "old-local"]) == 2
    assert main(["--root", str(workspace), "claim", "old-local", "--worker", "w"]) == 2
    assert main(["--root", str(workspace), "--offline-fixture", "status", "old-local"]) == 0
    brief = tmp_path / "brief.json"
    brief.write_text(json.dumps({"goal": "new", "audience": "test", "deliverables": ["caption"]}))
    assert main(["--root", str(workspace), "init", "fresh", "--brief", str(brief)]) == 0
    assert resolve_intake(workspace, {"mode": "RESUME", "project_id": "fresh"})["scope_epoch"] == EPOCH
    assert main(["--root", str(workspace), "--offline-fixture", "status", "fresh"]) == 2
    assert main(["--root", str(workspace), "status", "fresh"]) == 0


def test_knowledge_lookup_only_selects_active_reference_and_binds_source_bytes():
    from video_studio.scope import knowledge_lookup
    root = Path(__file__).resolve().parents[1]
    active = knowledge_lookup(repo_root=root)["entries"]
    assert active and all(item["status"] == "ACTIVE_REFERENCE" for item in active)
    assert all(len(item["source_sha256"]) == 64 for item in active)
    assert all(item["execution_verified"] is False for item in active)
    assert not any(item["ref"].startswith("projects/") for item in active)
    with pytest.raises(ValueError):
        knowledge_lookup("workflow")
    historical = knowledge_lookup("workflow", include_nonactive=True, repo_root=root)["entries"][0]
    assert historical["status"] == "LEGACY_REFERENCE_ONLY"
    with pytest.raises(ValueError):
        knowledge_lookup("no-such-method")


def test_goal_change_cannot_leave_old_owner_task_current(tmp_path):
    engine = StudioEngine(tmp_path)
    brief = bind_owner_brief("fresh", {"goal": "caption", "audience": "a", "deliverables": ["caption"]})
    engine.create_project("fresh", "fresh", brief)
    tasks = [{"task_id": name, "outputs": [name], "acceptance": {"quality": "clear"},
              "requirements": {"deliverable_refs": ["caption"]}} for name in ("research", "write")]
    engine.add_tasks("fresh", tasks)
    new = {**brief, "goal": "caption with no historical claims"}
    result = engine.revise_brief("fresh", new, reason="owner correction", affected_task_ids=["write"])
    assert set(result["invalidated_tasks"]) == {"research", "write"}


def decision_receipt(task_id, decision_id):
    # Structural fixture only; no assertion that a model or CAOS actually reasoned.
    return {"task_id": task_id, "decision_id": decision_id, "question": "Select a method",
            "scope": "current task", "source_refs": ["fixture-owner-goal"],
            "hypotheses": [{"id": "h1", "discriminator": "test A"},
                           {"id": "h2", "discriminator": "test B"}],
            "alternatives": [{"id": "a"}, {"id": "b"}], "selected_option": "a",
            "falsifier": "result fails fixture criteria", "rollback": "reopen task"}


def test_independent_tasks_bind_independent_decisions_and_reject_stale_action(tmp_path):
    from video_studio.engine import GateError
    engine = StudioEngine(tmp_path)
    brief = bind_owner_brief("fresh", {"goal": "two captions", "audience": "a", "deliverables": ["a", "b"]})
    engine.create_project("fresh", "fresh", brief)
    engine.add_tasks("fresh", [
        {"task_id": name, "outputs": [name], "acceptance": {"quality": "clear"},
         "requirements": {"deliverable_refs": [name], "decision_id": f"d-{name}"}}
        for name in ("a", "b")])
    with pytest.raises(GateError):
        engine.claim_next("fresh", "worker", task_id="a")
    engine.record_decision("fresh", decision_receipt("b", "d-b"))
    assert engine.claim_next("fresh", "worker")["task"]["task_id"] == "b"
    engine.record_decision("fresh", decision_receipt("a", "d-a"))
    assert engine.claim_next("fresh", "worker")["task"]["task_id"] == "a"
    engine.revise_brief("fresh", {**brief, "goal": "new owner correction"}, reason="goal changed")
    engine.reopen("fresh", "a", "reconsider")
    with pytest.raises(GateError):
        engine.claim_next("fresh", "new-worker", task_id="a")
