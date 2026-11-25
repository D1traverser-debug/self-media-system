"""Canonical owner-scope migration revokes old execution authority without losing history."""
import json
from contextlib import closing

import pytest

from social_media_studio.engine import StudioEngine
from social_media_studio.scope import EPOCH, resolve_intake
from social_media_studio.scope_migration import PRIOR_EPOCH, migrate_owner_scope


def _task(tid):
    return {
        "task_id": tid, "title": tid, "kind": "editorial",
        "executor": "agent", "depends_on": [], "inputs": [], "outputs": [tid + "-out"],
        "acceptance": {"deliverable": "Concrete output required"},
    }


def test_canonical_scope_and_controlled_upgrade_preserves_history(tmp_path):
    assert EPOCH.startswith("SOCIAL_MEDIA_")
    engine = StudioEngine(tmp_path)
    brief = {"goal": "Continue exact owner deliverables", "audience": "Owner",
             "deliverables": ["one", "two"]}
    engine.create_project("owner", "Original current owner project", brief)
    with closing(engine._connect("owner")) as conn:
        old = {**brief, "scope_epoch": PRIOR_EPOCH}
        conn.execute("UPDATE projects SET brief_json=? WHERE project_id=?",
                     (json.dumps(old), "owner"))
        conn.commit()
    engine.add_tasks("owner", [_task("running"), _task("ready")])
    engine.record_decision("owner", {
        "decision_id": "old-decision", "question": "Original choice", "scope": "owner",
        "source_refs": ["current goal"], "hypotheses": [
            {"id": "h1", "discriminator": "test 1"},
            {"id": "h2", "discriminator": "test 2"}],
        "alternatives": [{"id": "a1"}, {"id": "a2"}],
        "selected_option": "a1", "falsifier": "new evidence", "rollback": "replan",
    })
    claim = engine.claim_next("owner", "worker", task_id="running")
    assert claim is not None
    with pytest.raises(ValueError, match="retired"):
        resolve_intake(tmp_path, {"mode": "RESUME", "project_id": "owner"})

    migrated = migrate_owner_scope(engine, "owner", reason="Owner requests unified social-media scope")
    assert migrated["scope_epoch"] == EPOCH
    assert migrated["leases_revoked"] == ["running"]
    assert migrated["decisions_superseded"] == 1
    assert any(e["event_type"] == "DECISION_SUPERSEDED_BY_SCOPE_UPGRADE" for e in engine.events("owner"))
    assert migrated["historical_records_deleted"] is False
    assert resolve_intake(tmp_path, {"mode": "RESUME", "project_id": "owner"})["scope_epoch"] == EPOCH
    task_state = {item["task_id"]: item["status"] for item in engine.list_tasks("owner")}
    assert task_state["running"] == "STALE"
    assert task_state["ready"] == "READY"
    assert "ready" in engine.status("owner")["decision_blocked_tasks"]
    assert any(e["event_type"] == "PROJECT_BRIEF_REVISED" for e in engine.events("owner"))
    before = engine.status("owner")["event_count"]
    assert migrate_owner_scope(engine, "owner", reason="Recheck")["already_current"]
    assert engine.status("owner")["event_count"] == before


def test_scope_upgrade_fails_closed_on_unmarked_history(tmp_path):
    engine = StudioEngine(tmp_path)
    engine.create_project("unmarked", "Old fixture", {
        "goal": "A historical fixture", "audience": "test", "deliverables": ["out"],
    })
    with pytest.raises(ValueError, match="unmarked history"):
        migrate_owner_scope(engine, "unmarked", reason="Do not upgrade")
