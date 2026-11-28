"""Construction continuity checks, not evidence of product readiness."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_construction_checkpoint_covers_current_architecture_and_acceptance():
    plan = load("docs/SMS_CONSTRUCTION_CHECKPOINT.json")
    catalog = load(plan["authority"]["catalog"])
    matrix = load(plan["authority"]["acceptance"])
    tasks = plan["tasks"]
    ids = {task["id"] for task in tasks}
    assert len(ids) == len(tasks)
    subsystems = [s for t in tasks for s in t["subsystems"]]
    scenarios = [s for t in tasks for s in t["scenario_ids"]]
    assert len(subsystems) == len(set(subsystems))
    assert set(subsystems) == {s["id"] for s in catalog["subsystems"]}
    assert len(scenarios) == len(set(scenarios))
    assert set(scenarios) == {s["id"] for s in matrix["scenarios"]}
    by_id = {t["id"]: t for t in tasks}
    def visit(key, ancestors):
        assert key not in ancestors, f"cycle: {key}"
        for dep in by_id[key]["depends_on"]:
            assert dep in by_id
            visit(dep, ancestors | {key})
    for task in tasks:
        assert task["goal"] and task["acceptance"] and task["next_action"]
        assert task["status"] in {"OPEN", "IN_PROGRESS", "BLOCKED", "VERIFIED"}
        assert len(task["depends_on"]) == len(set(task["depends_on"]))
        if task["status"] == "BLOCKED":
            assert task["blocker"]
        if task["status"] == "VERIFIED":
            assert task["evidence"]
            assert all(by_id[d]["status"] == "VERIFIED" for d in task["depends_on"])
        visit(task["id"], set())
    assert "docs/SMS_CONSTRUCTION_CHECKPOINT.json" in (ROOT / "STUDIO_ENTRY.md").read_text(encoding="utf-8")
    assert plan["authority"]["private_owner_original_precedes_this_checkpoint"] is True


def test_checkpoint_ci_receipt_is_consistent_and_not_a_live_head_oracle():
    plan = load("docs/SMS_CONSTRUCTION_CHECKPOINT.json")
    integration = plan["integration"]
    by_id = {task["id"]: task for task in plan["tasks"]}
    b00 = by_id["B00"]

    assert integration["observed_head"]
    assert integration["observed_ci"] == "PASS"
    assert integration["observed_ci_run"] is not None
    assert integration["last_known_green_sha"] == integration["observed_head"]
    assert integration["last_known_green_pr_run"] == integration["observed_ci_run"]
    assert integration["push_ci_for_observed_head"] == "NOT_VERIFIED"

    semantics = integration["observed_head_semantics"].lower()
    assert "last verified" in semantics
    assert "not the live branch head" in semantics
    assert "re-query" in semantics

    assert b00["status"] == "VERIFIED"
    assert any(
        integration["observed_head"] in evidence
        and str(integration["observed_ci_run"]) in evidence
        for evidence in b00["evidence"]
    )
    assert "live PR head" in b00["next_action"]
    assert "re-run" in b00["next_action"]
