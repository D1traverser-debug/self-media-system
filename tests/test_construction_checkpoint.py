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
