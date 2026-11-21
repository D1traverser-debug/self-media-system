"""Adversarial regression: native Video never claims CAOS-governed work with missing/stale parent context.

Tests assert structural admission and brief-binding, NOT real ChatGPT Skill
selection or independent cognition. The latter require first-party traces.
"""
from copy import deepcopy
import hashlib
import json

import pytest

from video_studio.engine import ContractError, GateError, StudioEngine


def brief(governed=True):
    value = {
        "goal": "Evaluate an externally linked clip workflow for legitimate video work.",
        "audience": "Creator researching possible techniques",
        "deliverables": ["evidence.json"],
        "success_criteria": ["Evidence-based reusable decision", "Independent checks"],
    }
    if governed:
        value["governance"] = {
            "mode": "CAOS_PARENT", "parent_system": "cognition-agent-os",
            "allowed_effects": ["PUBLIC_READ", "ISOLATED_LOCAL_WRITE"],
        }
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def handoff(project, b):
    return {
        "schema_version": 1, "parent_system": "cognition-agent-os",
        "child_system": "video-growth-agent", "project_id": project,
        "brief_sha256": digest(b),
        "owner_goal_ref": "owner-message:2026-11-21",
        "goal": b["goal"],
        "owner_corrections": ["Do not substitute Video-native task flow for CAOS cognition"],
        "source_refs": ["x-original-post:2123903235467387381", "github:video-growth-agent/STUDIO_ENTRY.md"],
        "decision": {
            "question": "How should this claim be handled?",
            "hypotheses": [
                {"id": "entry_lapse", "discriminator": "Native invocation trace"},
                {"id": "method_lapse", "discriminator": "Direct Video claims bypass parent admission"},
            ],
            "alternatives": [{"id": "a"}, {"id": "b"}],
            "selected_option": "b",
            "falsifier": "Actual owner result fails after the method",
            "rollback": "Revert branch and retain immutable evidence",
        },
        "allowed_effects": ["PUBLIC_READ", "ISOLATED_LOCAL_WRITE"],
        "verification": {
            "owner_outcomes": ["Complete owner-requested result"],
            "independent_evidence": ["Real artifact digest and independent check"],
        },
        "unknowns": ["Native ChatGPT Skill invocation trace unknown"],
    }


def task():
    return {
        "task_id": "research", "title": "Review candidate sources",
        "kind": "editorial_research", "executor": "agent",
        "depends_on": [], "inputs": [], "outputs": ["evidence"],
        "acceptance": {"evidence": "Sources and counterevidence required"},
        "requirements": {"effect_class": "ISOLATED_LOCAL_WRITE"},
    }


def studio(tmp_path, project="case", governed=True):
    engine = StudioEngine(tmp_path)
    b = brief(governed)
    engine.create_project(project, project, b)
    engine.add_tasks(project, [task()])
    return engine, b


def test_governed_claim_fails_closed_until_admitted(tmp_path):
    engine, b = studio(tmp_path)
    assert engine.status("case")["parent_handoff"]["reason"] == "PARENT_HANDOFF_MISSING"
    with pytest.raises(GateError, match="PARENT_HANDOFF_MISSING"):
        engine.claim_next("case", "worker")
    assert engine.list_tasks("case")[0]["status"] == "READY"
    result = engine.admit_parent_handoff("case", handoff("case", b))
    assert result["admitted"] is True
    assert "NOT_NATIVE_CAOS_SELECTION" in result["assurance_limit"]
    assert engine.claim_next("case", "worker")["task"]["task_id"] == "research"


def test_standalone_not_forced_through_caos(tmp_path):
    engine, b = studio(tmp_path, governed=False)
    assert engine.parent_handoff_status("case")["mode"] == "VIDEO_STANDALONE"
    assert engine.claim_next("case", "worker")["task"]["task_id"] == "research"
    with pytest.raises(GateError):
        engine.admit_parent_handoff("case", handoff("case", b))


@pytest.mark.parametrize("change", [
    lambda r: r.update({"project_id": "other"}),
    lambda r: r.update({"brief_sha256": "0" * 64}),
    lambda r: r.update({"goal": "Changed objective"}),
    lambda r: r.update({"owner_goal_ref": ""}),
    lambda r: r.update({"source_refs": []}),
    lambda r: r.update({"allowed_effects": ["NETWORK_WRITE"]}),
    lambda r: r["decision"].update({"selected_option": "unknown"}),
    lambda r: r["decision"]["hypotheses"].pop(),
    lambda r: r["verification"].update({"independent_evidence": []}),
])
def test_invalid_parent_handoff_denied(tmp_path, change):
    engine, b = studio(tmp_path)
    r = handoff("case", b)
    change(r)
    with pytest.raises(ContractError):
        engine.admit_parent_handoff("case", r)
    with pytest.raises(GateError, match="PARENT_HANDOFF_MISSING"):
        engine.claim_next("case", "worker")


def test_brief_revision_invalidates_admission_without_revoking_unrelated_tasks(tmp_path):
    engine, b = studio(tmp_path)
    engine.admit_parent_handoff("case", handoff("case", b))
    updated = deepcopy(b)
    updated["goal"] = "New owner goal that requires renewed parent analysis."
    engine.revise_brief("case", updated, reason="New owner correction", affected_task_ids=[])
    assert engine.status("case")["parent_handoff"]["reason"] == "PARENT_HANDOFF_STALE"
    with pytest.raises(GateError, match="PARENT_HANDOFF_STALE"):
        engine.claim_next("case", "worker")
    with pytest.raises(ContractError, match="stale"):
        engine.admit_parent_handoff("case", handoff("case", b))
    engine.admit_parent_handoff("case", handoff("case", updated))
    assert engine.claim_next("case", "worker")["task"]["task_id"] == "research"


def test_governance_downgrade_is_not_silent(tmp_path):
    engine, b = studio(tmp_path)
    with pytest.raises(GateError, match="downgrade"):
        engine.revise_brief("case", brief(False), reason="Attempt bypass")
    assert engine.project("case")["brief"]["governance"]["mode"] == "CAOS_PARENT"


def test_admission_is_idempotent(tmp_path):
    engine, b = studio(tmp_path)
    r = handoff("case", b)
    engine.admit_parent_handoff("case", r)
    before = engine.status("case")["event_count"]
    engine.admit_parent_handoff("case", r)
    assert engine.status("case")["event_count"] == before




def test_claim_remains_stale_after_new_handoff_if_it_started_before_revision(tmp_path):
    engine, b = studio(tmp_path)
    engine.admit_parent_handoff("case", handoff("case", b))
    packet = engine.claim_next("case", "worker")
    newer = deepcopy(b)
    newer["goal"] = "Changed owner goal"
    engine.revise_brief("case", newer, reason="New goal", affected_task_ids=[])
    engine.admit_parent_handoff("case", handoff("case", newer))
    with pytest.raises(GateError, match="CLAIM_STALE"):
        engine.claimed_packet("case", "research", "worker", packet["claim"]["claim_token"])
    with pytest.raises(GateError, match="CLAIM_STALE"):
        engine.heartbeat("case", "research", "worker", packet["claim"]["claim_token"])


def test_unadmitted_effect_class_does_not_block_legal_peer(tmp_path):
    engine = StudioEngine(tmp_path)
    b = brief()
    engine.create_project("case", "case", b)
    forbidden = task()
    forbidden["task_id"] = "external"
    forbidden["outputs"] = ["external_output"]
    forbidden["requirements"] = {"effect_class": "PRODUCTION_RELEASE"}
    forbidden["priority"] = 100
    permitted = task()
    permitted["priority"] = 1
    engine.add_tasks("case", [forbidden, permitted])
    engine.admit_parent_handoff("case", handoff("case", b))
    assert engine.claim_next("case", "worker")["task"]["task_id"] == "research"


def test_unadmitted_effect_class_fails_closed(tmp_path):
    engine, b = studio(tmp_path)
    engine.admit_parent_handoff("case", handoff("case", b))
    engine.revise_task("case", "research",
                       {"requirements": {"effect_class": "PRODUCTION_RELEASE"}},
                       reason="Probe forbidden effect")
    with pytest.raises(GateError, match="EFFECT_SCOPE_UNADMITTED"):
        engine.claim_next("case", "worker")



def test_asset_import_is_blocked_until_local_write_scope_admitted(tmp_path):
    engine, b = studio(tmp_path)
    source = tmp_path / "source.txt"
    source.write_text("Authorized test content", encoding="utf-8")
    with pytest.raises(GateError, match="PARENT_HANDOFF_MISSING"):
        engine.import_asset("case", "sample", source, kind="source", media_type="text/plain",
                            rights_status="OWNED")
    limited = handoff("case", b)
    limited["allowed_effects"] = ["PUBLIC_READ"]
    engine.admit_parent_handoff("case", limited)
    with pytest.raises(GateError, match="ASSET_IMPORT_EFFECT_NOT_ALLOWED"):
        engine.import_asset("case", "sample", source, kind="source", media_type="text/plain",
                            rights_status="OWNED")
    engine.admit_parent_handoff("case", handoff("case", b))
    artifact = engine.import_asset("case", "sample", source, kind="source",
                                   media_type="text/plain", rights_status="OWNED")
    assert artifact["name"] == "sample"


def test_replaced_parent_decision_invalidates_running_lease(tmp_path):
    engine, b = studio(tmp_path)
    first = handoff("case", b)
    engine.admit_parent_handoff("case", first)
    packet = engine.claim_next("case", "worker")
    second = deepcopy(first)
    second["unknowns"].append("New material contrary evidence")
    engine.admit_parent_handoff("case", second)
    with pytest.raises(GateError, match="CLAIM_STALE"):
        engine.claimed_packet("case", "research", "worker", packet["claim"]["claim_token"])



def test_real_cli_admission_before_claim(tmp_path):
    import json
    from video_studio.cli import main

    workspace = tmp_path / "studio"
    b = brief()
    bfile = tmp_path / "brief.json"
    tasks_file = tmp_path / "tasks.json"
    receipt_file = tmp_path / "receipt.json"
    bfile.write_text(json.dumps(b), encoding="utf-8")
    tasks_file.write_text(json.dumps([task()]), encoding="utf-8")
    receipt_file.write_text(json.dumps(handoff("case", b)), encoding="utf-8")
    root_args = ["--root", str(workspace)]
    assert main(root_args + ["init", "case", "--brief", str(bfile)]) == 0
    assert main(root_args + ["plan", "case", str(tasks_file)]) == 0
    assert main(root_args + ["claim", "case", "--worker", "worker"]) == 2
    assert main(root_args + ["admit-parent-handoff", "case", str(receipt_file)]) == 0
    assert main(root_args + ["claim", "case", "--worker", "worker"]) == 0

def test_invalid_governed_brief_denied(tmp_path):
    engine = StudioEngine(tmp_path)
    b = brief()
    del b["governance"]["allowed_effects"]
    with pytest.raises(ContractError, match="allowed_effects"):
        engine.create_project("case", "case", b)
