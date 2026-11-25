import hashlib
import json
from pathlib import Path

import pytest

from social_media_studio.engine import StudioEngine
from social_media_studio.scope import EPOCH, bind_owner_brief, resolve_intake





def adoption_packet(brief, *, source_refs=None, source_coverage="CURRENT_CHAT_ONLY"):
    refs = source_refs or [{
        "source_ref": "current-chat-context",
        "source_type": "CHAT_CONTEXT",
        "role": "OWNER_GOAL",
        "verification": "CONVERSATION_CONTEXT_ONLY",
    }]
    return {
        "schema_version": "1.0",
        "kind": "SOCIAL_MEDIA_STUDIO_ADOPTION_PACKET",
        "source_coverage": source_coverage,
        "coverage_notes": "Only the declared source material was inspected; no unlisted chat history is claimed.",
        "source_refs": refs,
        "goal": {
            "original_user_goal": "Start an original content project.",
            "current_goal": brief["goal"],
            "deliverables": brief["deliverables"],
            "hard_constraints": ["Preserve every explicit owner correction."],
            "preferences": ["Use the simplest method that meets the target quality."],
            "prohibitions": ["Do not import unrelated task images."],
            "corrections": [{"order": 1, "text": "The final deliverable must remain original.", "source_ref": refs[0]["source_ref"]}],
        },
        "completed_work": [{
            "description": "Initial discussion and concept exploration.",
            "status": "CLAIMED_UNVERIFIED",
            "evidence_refs": [],
        }],
        "prior_decisions": [{
            "question": "Which creative direction should be used?",
            "choice": "Use the owner-corrected direction.",
            "status": "REQUIRES_REVALIDATION",
        }],
        "open_items": ["Inspect actual source files before creating the execution graph."],
        "failure_history": [{
            "symptom": "An earlier image attempt inherited unrelated references.",
            "status": "RESOLVED_UNVERIFIED",
            "evidence_refs": [],
        }],
        "next_action": "Verify imported source material and plan only the remaining work.",
        "context_boundary": {
            "mode": "DECLARED_INPUTS_PLUS_PROJECT_BRIEF",
            "allowed_input_names": [],
            "excluded_context_refs": ["unrelated-prior-image-set"],
            "allow_prior_conversation": False,
            "allow_sibling_task_context": False,
            "isolated_chat_required": False,
        },
    }


def test_manifest_owner_scope_epoch_matches_runtime():
    from social_media_studio.scope import contract
    assert contract()["task_admission"]["scope_epoch"] == EPOCH


def test_runtime_owner_scope_operations_fail_closed_on_manifest_epoch_drift(monkeypatch, tmp_path):
    import social_media_studio.scope as scope
    stale = {"task_admission": {"scope_epoch": "VIDEO_TASK_NEUTRAL_20261124", "retired_project_ids": []}}
    monkeypatch.setattr(scope, "contract", lambda: stale)
    with pytest.raises(ValueError, match="owner scope epoch mismatch"):
        scope.bind_owner_brief("fresh", {"goal": "caption", "audience": "test", "deliverables": ["caption"]})
    with pytest.raises(ValueError, match="owner scope epoch mismatch"):
        scope.resolve_intake(tmp_path, {"mode": "NEW", "goal": "caption"})
    with pytest.raises(ValueError, match="owner scope epoch mismatch"):
        scope.validate_task_binding(
            {"scope_epoch": EPOCH, "deliverables": ["caption"]},
            {"requirements": {"deliverable_refs": ["caption"]}},
        )


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


def test_cli_rejects_legacy_workspace_on_all_owner_paths_and_requires_explicit_owner_scope(tmp_path, capsys):
    from social_media_studio.cli import main
    workspace = tmp_path / "workspace"
    engine = StudioEngine(workspace)
    engine.create_project("old-local", "old", {"goal": "old", "audience": "test", "deliverables": ["old"]})
    assert main(["--root", str(workspace), "status", "old-local"]) == 2
    assert main(["--root", str(workspace), "claim", "old-local", "--worker", "w"]) == 2
    # A fixture flag cannot adopt an existing unmarked owner/history workspace.
    assert main(["--root", str(workspace), "--offline-fixture", "status", "old-local"]) == 2
    assert main(["--root", str(workspace), "--offline-fixture", "init", "fixture", "--brief", str(tmp_path / "missing.json")]) == 2

    brief = tmp_path / "brief.json"
    brief.write_text(json.dumps({"goal": "new", "audience": "test", "deliverables": ["caption"]}))
    # Owner scope is opt-in; the old no-op flag now gates creation.
    assert main(["--root", str(workspace), "init", "fresh", "--brief", str(brief)]) == 2
    assert main(["--root", str(workspace), "init", "fresh", "--brief", str(brief), "--owner-task"]) == 0
    assert resolve_intake(workspace, {"mode": "RESUME", "project_id": "fresh"})["scope_epoch"] == EPOCH
    assert main(["--root", str(workspace), "status", "fresh"]) == 0

    fixture_root = tmp_path / "fixture-workspace"
    assert main(["--offline-fixture", "--root", str(fixture_root), "init", "fixture", "--brief", str(brief)]) == 0
    assert (fixture_root / ".sms-offline-fixture.json").is_file()
    assert main(["--offline-fixture", "--root", str(fixture_root), "status", "fixture"]) == 0
    # Owner mode cannot open fixture data, and fixture mode cannot create owner scope.
    assert main(["--root", str(fixture_root), "status", "fixture"]) == 2
    assert main(["--offline-fixture", "--root", str(fixture_root), "init", "bad", "--brief", str(brief), "--owner-task"]) == 2
    # A workspace with prior bytes cannot be retroactively labelled as a fixture.
    assert main(["--offline-fixture", "--root", str(workspace), "init", "fixture2", "--brief", str(brief)]) == 2


def test_workspace_mode_marker_is_root_bound_and_modes_are_mutually_exclusive(tmp_path):
    from social_media_studio.scope import validate_workspace_mode
    owner_root = tmp_path / "owner"
    owner_root.mkdir()
    fixture_root = tmp_path / "fixture"
    resolved = validate_workspace_mode(
        fixture_root, offline_fixture=True, initialize=True, owner_root=owner_root,
    )
    assert resolved == fixture_root.resolve()
    with pytest.raises(ValueError):
        validate_workspace_mode(fixture_root, offline_fixture=False, owner_root=owner_root)
    with pytest.raises(ValueError):
        validate_workspace_mode(owner_root, offline_fixture=True, initialize=True, owner_root=owner_root)

    occupied_root = tmp_path / "occupied"
    occupied_root.mkdir()
    (occupied_root / "projects").mkdir()
    with pytest.raises(ValueError):
        validate_workspace_mode(
            occupied_root, offline_fixture=True, initialize=True, owner_root=owner_root,
        )

    copied_root = tmp_path / "copied"
    copied_root.mkdir()
    (copied_root / ".sms-offline-fixture.json").write_bytes(
        (fixture_root / ".sms-offline-fixture.json").read_bytes()
    )
    with pytest.raises(ValueError):
        validate_workspace_mode(copied_root, offline_fixture=True, owner_root=owner_root)


def test_knowledge_lookup_only_selects_active_reference_and_binds_source_bytes():
    from social_media_studio.scope import knowledge_lookup
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
    from social_media_studio.engine import GateError
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
    assert engine.status("fresh")["admitted_ready_tasks"] == ["b"]
    assert set(engine.status("fresh")["decision_blocked_tasks"]) == {"a"}
    assert engine.claim_next("fresh", "worker")["task"]["task_id"] == "b"
    engine.record_decision("fresh", decision_receipt("a", "d-a"))
    assert engine.claim_next("fresh", "worker")["task"]["task_id"] == "a"
    engine.revise_brief("fresh", {**brief, "goal": "new owner correction"}, reason="goal changed")
    engine.reopen("fresh", "a", "reconsider")
    with pytest.raises(GateError):
        engine.claim_next("fresh", "new-worker", task_id="a")


def test_goal_reversion_does_not_restore_old_decision_authority(tmp_path):
    from social_media_studio.engine import GateError
    engine = StudioEngine(tmp_path)
    brief = bind_owner_brief("fresh", {"goal": "caption", "audience": "a", "deliverables": ["a"]})
    engine.create_project("fresh", "fresh", brief)
    engine.add_tasks("fresh", [{"task_id": "a", "outputs": ["a"], "acceptance": {"quality": "clear"},
                               "requirements": {"deliverable_refs": ["a"], "decision_id": "d-a"}}])
    engine.record_decision("fresh", decision_receipt("a", "d-a"))
    engine.revise_brief("fresh", {**brief, "goal": "different"}, reason="owner changes scope")
    engine.revise_brief("fresh", brief, reason="owner restores text")
    engine.reopen("fresh", "a", "new decision required")
    with pytest.raises(GateError):
        engine.claim_next("fresh", "writer", task_id="a")


def test_unrelated_decision_does_not_authorize_task_and_caller_binding_rejected(tmp_path):
    from social_media_studio.engine import ContractError, GateError
    engine = StudioEngine(tmp_path)
    brief = bind_owner_brief("fresh", {"goal": "caption", "audience": "a", "deliverables": ["a"]})
    engine.create_project("fresh", "fresh", brief)
    engine.add_tasks("fresh", [{"task_id": "a", "outputs": ["a"], "acceptance": {"quality": "clear"},
                               "requirements": {"deliverable_refs": ["a"], "decision_id": "d-a"}}])
    receipt = decision_receipt("a", "d-a")
    with pytest.raises(ContractError):
        engine.record_decision("fresh", {**receipt, "action_binding": {"fake": True}})
    with pytest.raises(ContractError):
        engine.record_decision("fresh", {**receipt, "decision_id": "d-wrong"})
    assert engine.claim_next("fresh", "writer") is None


def test_x_article_and_one_time_avatar_dispatch_are_typed_internal_routes(tmp_path):
    new = resolve_intake(tmp_path, {
        "mode": "NEW", "goal": "Write an English X Article with one illustration",
        "deliverable_specs": [
            {"id":"article","type":"LONG_ARTICLE","locale":"en-US"},
            {"id":"illustration","type":"STATIC_IMAGE"},
        ]})
    picked = new["internal_subsystem_routing"]["routes"]
    assert [p["primary_internal_subsystem"] for p in picked] == [
        "editorial_and_language", "visual_and_static_design"]
    assert new["internal_subsystem_routing"]["peer_system_task_authority_inherited"] is False
    assert new["selected_task_graph"] is None
    assert new["effect_authorized"] is False


def test_adopt_intake_is_read_only_and_creates_no_task_graph(tmp_path):
    brief = {"goal": "Finish an original technology explainer", "audience": "curious viewers",
             "deliverables": ["final-video", "cover", "publish-copy"]}
    packet = adoption_packet(brief)
    route = resolve_intake(tmp_path, {
        "mode": "ADOPT", "project_id": "adopted-explainer",
        "brief": brief, "adoption_packet": packet,
    })
    assert route["mode"] == "ADOPT"
    assert route["project_id"] == "adopted-explainer"
    assert route["task_graph_created"] is False
    assert route["selected_task_graph"] is None
    assert route["effect_authorized"] is False
    assert not (tmp_path / "projects" / "adopted-explainer").exists()


def test_adopt_rejects_existing_project_and_unverified_full_export(tmp_path):
    brief = {"goal": "Write one original article", "audience": "readers", "deliverables": ["article"]}
    engine = StudioEngine(tmp_path)
    engine.create_project("already-here", "Existing", bind_owner_brief("already-here", brief))
    with pytest.raises(ValueError, match="new project_id"):
        resolve_intake(tmp_path, {
            "mode": "ADOPT", "project_id": "already-here",
            "brief": brief, "adoption_packet": adoption_packet(brief),
        })
    invalid = adoption_packet(brief, source_coverage="FULL_SOURCE_EXPORT", source_refs=[{
        "source_ref": "chat-export.json", "source_type": "CHAT_EXPORT",
        "role": "OWNER_GOAL", "verification": "EXACT_BYTES_HASHED",
        "sha256": "a" * 64,
    }])
    with pytest.raises(ValueError, match="artifact_name"):
        resolve_intake(tmp_path, {
            "mode": "ADOPT", "project_id": "new-adoption",
            "brief": brief, "adoption_packet": invalid,
        })


def test_adopt_imports_exact_hashed_chat_export_and_preserves_provenance(tmp_path):
    source_dir = tmp_path / "adoption-source"
    source_dir.mkdir()
    export = source_dir / "chat-export.txt"
    export.write_text("Original user goal. Correction: preserve the exact deliverable.", encoding="utf-8")
    digest = hashlib.sha256(export.read_bytes()).hexdigest()
    brief = {"goal": "Produce the corrected original article", "audience": "readers",
             "deliverables": ["article"]}
    packet = adoption_packet(brief, source_coverage="FULL_SOURCE_EXPORT", source_refs=[{
        "source_ref": "chat-export.txt", "source_type": "CHAT_EXPORT",
        "role": "OWNER_GOAL", "verification": "EXACT_BYTES_HASHED",
        "sha256": digest, "artifact_name": "chat-export", "media_type": "text/plain",
    }])
    packet_path = source_dir / "ADOPTION.json"
    packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
    engine = StudioEngine(tmp_path / "workspace")
    result = engine.adopt_project("article-adopted", "Adopted article", brief, packet_path)
    assert result["task_graph_created"] is False
    assert result["execution_authorized"] is False
    assert result["source_artifacts"][0]["name"] == "chat-export"
    assert result["source_artifacts"][0]["sha256"] == digest
    resume = engine.resume("article-adopted")
    assert resume["project_status"] == "NO_TASK_GRAPH"
    assert resume["adoption"]["payload"]["source_coverage"] == "FULL_SOURCE_EXPORT"
    assert {item["name"] for item in resume["current_artifacts"]} == {"chat-export", "adoption-context"}
    assert resume["adoption"]["payload"]["prior_decisions_authority"] == "REQUIRES_REVALIDATION"


def test_adopt_rejects_source_digest_mismatch_before_project_creation(tmp_path):
    source_dir = tmp_path / "adoption-source"
    source_dir.mkdir()
    export = source_dir / "chat-export.txt"
    export.write_text("A real chat export", encoding="utf-8")
    brief = {"goal": "Produce a short original video", "audience": "viewers",
             "deliverables": ["video"]}
    packet = adoption_packet(brief, source_coverage="FULL_SOURCE_EXPORT", source_refs=[{
        "source_ref": "chat-export.txt", "source_type": "CHAT_EXPORT",
        "role": "OWNER_GOAL", "verification": "EXACT_BYTES_HASHED",
        "sha256": "0" * 64, "artifact_name": "chat-export", "media_type": "text/plain",
    }])
    packet_path = source_dir / "ADOPTION.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    workspace = tmp_path / "workspace"
    engine = StudioEngine(workspace)
    from social_media_studio.engine import GateError
    with pytest.raises(GateError, match="source digest mismatch"):
        engine.adopt_project("bad-adoption", "Bad adoption", brief, packet_path)
    assert not (workspace / "projects" / "bad-adoption").exists()


def test_context_boundary_rejects_implicit_history_and_sibling_task_leakage():
    from social_media_studio.scope import validate_context_boundary
    valid = {
        "mode": "DECLARED_INPUTS_ONLY",
        "allowed_input_names": ["reference-image"],
        "excluded_context_refs": ["unrelated-image"],
        "allow_prior_conversation": False,
        "allow_sibling_task_context": False,
        "isolated_chat_required": True,
    }
    assert validate_context_boundary(valid, task_inputs=["reference-image"])["isolated_chat_required"] is True
    with pytest.raises(ValueError, match="prior conversation"):
        validate_context_boundary({**valid, "allow_prior_conversation": True}, task_inputs=["reference-image"])
    with pytest.raises(ValueError, match="sibling-task"):
        validate_context_boundary({**valid, "allow_sibling_task_context": True}, task_inputs=["reference-image"])
    with pytest.raises(ValueError, match="exactly match"):
        validate_context_boundary(valid, task_inputs=["different-image"])


def test_adopt_cli_requires_explicit_owner_scope_and_imports_packet(tmp_path, capsys):
    from social_media_studio.cli import main
    workspace = tmp_path / "owner-workspace"
    brief = {"goal": "Create a short original video", "audience": "viewers", "deliverables": ["video"]}
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(json.dumps(brief), encoding="utf-8")
    packet_path = tmp_path / "adoption.json"
    packet_path.write_text(json.dumps(adoption_packet(brief)), encoding="utf-8")
    assert main(["--root", str(workspace), "adopt", "video-adopted",
                 "--brief", str(brief_path), "--packet", str(packet_path)]) == 2
    assert main(["--root", str(workspace), "adopt", "video-adopted",
                 "--brief", str(brief_path), "--packet", str(packet_path), "--owner-task"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["task_graph_created"] is False
    assert result["project"]["project_id"] == "video-adopted"

