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
