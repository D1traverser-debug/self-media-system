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
