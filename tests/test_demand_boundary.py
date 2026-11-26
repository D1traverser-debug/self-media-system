import copy

import pytest

from social_media_studio.domain.contracts import ContentContractError
from social_media_studio.engine import StudioEngine
from social_media_studio.scope import bind_owner_brief, resolve_intake


def brief():
    return {
        "goal": "Edit the video, preserve audio", "audience": "mobile",
        "deliverables": ["edit"],
        "deliverable_specs": [{"id": "edit", "type": "MEDIA_TRANSFORM",
                               "constraints": {"original_audio_promise": "BITSTREAM_IDENTITY"}}],
        "demand_contract": {
            "schema_version": 1, "owner_source_refs": ["owner-message"],
            "clauses": [
                {"id": "audio", "kind": "HARD_CONSTRAINT", "text": "Preserve original audio",
                 "source_ref": "owner-message", "deliverable_refs": ["edit"]},
                {"id": "publish", "kind": "AUTHORIZATION_LIMIT", "text": "Do not publish",
                 "source_ref": "owner-message", "deliverable_refs": []},
            ],
        },
    }


def test_direct_and_durable_share_declaration_without_grant(tmp_path):
    root = tmp_path / "not-created"
    route = resolve_intake(root, {"mode": "NEW", **brief()})
    assert not root.exists()
    assert route["demand"]["contract_status"] == "DECLARED_UNVERIFIED"
    assert route["demand"]["clauses"][0]["deliverable_refs"] == ["edit"]
    assert route["demand"]["clauses"][1]["deliverable_refs"] == []
    assert not route["demand"]["source_authenticity_verified"]
    assert not route["demand"]["semantic_completeness_verified"]
    assert not route["effect_authorized"]
    assert route["selected_task_graph"] is None
    engine = StudioEngine(root)
    engine.create_project("fresh", "fresh", bind_owner_brief("fresh", brief()))
    resumed = resolve_intake(root, {"mode": "RESUME", "project_id": "fresh"})
    assert resumed["demand"] == route["demand"]


@pytest.mark.parametrize("field,value", [
    ("source_ref", "unknown"), ("deliverable_refs", ["other"]),
    ("kind", "GRANT"), ("id", "bad id"), ("text", ""),
])
def test_invalid_clauses_rejected_on_both_surfaces(tmp_path, field, value):
    data = brief()
    data["demand_contract"]["clauses"][0][field] = value
    with pytest.raises(ContentContractError):
        resolve_intake(tmp_path / "absent", {"mode": "NEW", **data})
    with pytest.raises(ContentContractError):
        bind_owner_brief("fresh", data)
    assert not (tmp_path / "absent").exists()


def test_revision_cannot_bypass_shared_boundary_or_drop_declarations(tmp_path):
    engine = StudioEngine(tmp_path)
    original = bind_owner_brief("fresh", brief())
    engine.create_project("fresh", "fresh", original)
    snapshot = engine.project("fresh")
    history = engine.brief_history("fresh")
    for field in ("deliverable_specs", "demand_contract"):
        changed = copy.deepcopy(original)
        changed.pop(field)
        with pytest.raises(ContentContractError):
            engine.revise_brief("fresh", changed, reason="fixture")
    changed = copy.deepcopy(original)
    changed["deliverable_specs"][0]["id"] = "other"
    with pytest.raises(ContentContractError):
        engine.revise_brief("fresh", changed, reason="fixture")
    changed = copy.deepcopy(original)
    changed["demand_contract"]["clauses"][0]["source_ref"] = "unknown"
    with pytest.raises(ContentContractError):
        engine.revise_brief("fresh", changed, reason="fixture")
    assert engine.project("fresh") == snapshot
    assert engine.brief_history("fresh") == history
    changed = copy.deepcopy(original)
    changed["goal"] = "Owner corrected the video edit"
    changed["demand_contract"]["owner_source_refs"].append("owner-correction")
    changed["demand_contract"]["clauses"][0]["source_ref"] = "owner-correction"
    changed["demand_contract"]["amendments"] = [
        {"id": "correct-goal", "target": "@brief", "action": "REVISE",
         "source_ref": "owner-correction", "reason": "owner changed the goal"},
        {"id": "correct-audio", "target": "audio", "action": "REVISE",
         "source_ref": "owner-correction", "reason": "bind audio constraint to correction"},
    ]
    result = engine.revise_brief("fresh", changed, reason="fixture correction")
    assert result["project"]["brief"] == changed
    assert resolve_intake(tmp_path, {"mode": "RESUME", "project_id": "fresh"})["goal"] == changed["goal"]


def test_unstructured_direct_request_stays_read_only(tmp_path):
    root = tmp_path / "absent"
    route = resolve_intake(root, {"mode": "NEW", "goal": "One caption only"})
    assert route["demand"]["contract_status"] == "UNSTRUCTURED"
    assert route["demand"]["clauses"] == []
    assert route["selected_task_graph"] is None
    assert not root.exists()

def test_cannot_silently_delete_a_prohibition_or_rewrite_the_goal(tmp_path):
    engine = StudioEngine(tmp_path)
    original = bind_owner_brief("fresh", brief())
    engine.create_project("fresh", "fresh", original)
    changed = copy.deepcopy(original)
    changed["goal"] = "Something different"
    with pytest.raises(ContentContractError, match="explicit new amendment"):
        engine.revise_brief("fresh", changed, reason="unproven change")
    changed = copy.deepcopy(original)
    changed["demand_contract"]["clauses"] = changed["demand_contract"]["clauses"][:1]
    with pytest.raises(ContentContractError, match="explicit new amendment"):
        engine.revise_brief("fresh", changed, reason="silently remove no-publish")
    assert engine.project("fresh")["brief"] == original


def test_explicit_retirement_requires_fresh_correction_source(tmp_path):
    engine = StudioEngine(tmp_path)
    original = bind_owner_brief("fresh", brief())
    engine.create_project("fresh", "fresh", original)
    changed = copy.deepcopy(original)
    contract = changed["demand_contract"]
    contract["clauses"].pop()
    contract["amendments"] = [
        {"id": "retire-publish", "target": "publish", "action": "RETIRE",
         "source_ref": "owner-message", "reason": "owner correction"}
    ]
    with pytest.raises(ContentContractError, match="newly declared"):
        engine.revise_brief("fresh", changed, reason="spoofed correction")
    contract["owner_source_refs"].append("owner-message-correction-2")
    contract["amendments"][0]["source_ref"] = "owner-message-correction-2"
    engine.revise_brief("fresh", changed, reason="explicit correction")
    current = engine.project("fresh")["brief"]
    assert current["demand_contract"]["amendments"][0]["action"] == "RETIRE"
    assert "publish" not in {c["id"] for c in current["demand_contract"]["clauses"]}
    with pytest.raises(ContentContractError, match="append-only"):
        again = copy.deepcopy(current)
        again["demand_contract"]["amendments"] = []
        engine.revise_brief("fresh", again, reason="erase history")


def test_resume_rejects_unapplied_owner_correction(tmp_path):
    engine = StudioEngine(tmp_path)
    engine.create_project("fresh", "fresh", bind_owner_brief("fresh", brief()))
    for bad in ({"goal": "Different goal"}, {"owner_correction": "No longer edit audio"},
                {"deliverable_specs": []}, {"demand_contract": {}}):
        with pytest.raises(ValueError, match="cannot apply owner corrections"):
            resolve_intake(tmp_path, {"mode": "RESUME", "project_id": "fresh", **bad})
    assert resolve_intake(tmp_path, {"mode": "RESUME", "project_id": "fresh"})["goal"] == brief()["goal"]

def test_malformed_amendment_action_fails_with_contract_error(tmp_path):
    for action in ([], {}, None, 3):
        candidate = brief()
        candidate["demand_contract"]["amendments"] = [
            {"id": "bad-action", "target": "@brief", "action": action,
             "source_ref": "owner-message", "reason": "test"}
        ]
        with pytest.raises(ContentContractError, match="invalid amendment action"):
            bind_owner_brief("fresh", candidate)
