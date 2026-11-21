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
        "allowed_effects": ["PUBLIC_READ"],
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


def test_invalid_governed_brief_denied(tmp_path):
    engine = StudioEngine(tmp_path)
    b = brief()
    del b["governance"]["allowed_effects"]
    with pytest.raises(ContractError, match="allowed_effects"):
        engine.create_project("case", "case", b)
