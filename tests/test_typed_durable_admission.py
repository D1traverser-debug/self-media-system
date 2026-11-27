"""Typed durable admission and delivery use the same professional contract as intake."""
import copy
from pathlib import Path

import pytest

from social_media_studio.engine import StudioEngine, GateError
from social_media_studio.scope import bind_owner_brief, resolve_intake


def make_engine(tmp_path, specs):
    engine = StudioEngine(tmp_path)
    brief = bind_owner_brief("fresh", {
        "goal": "Deliver the requested current artifacts", "audience": "owner",
        "deliverables": [s["id"] for s in specs], "deliverable_specs": specs,
    })
    engine.create_project("fresh", "fresh", brief)
    return engine


def receipt(task_id, decision_id):
    return {"task_id": task_id, "decision_id": decision_id, "question": "Select a method",
            "scope": "fixture", "source_refs": ["fixture-owner"],
            "hypotheses": [{"id": "a", "discriminator": "test A"}, {"id": "b", "discriminator": "test B"}],
            "alternatives": [{"id": "a"}, {"id": "b"}], "selected_option": "a",
            "falsifier": "fixture result fails", "rollback": "revise"}


def task(name, ref, demand, *, executor="agent", output_binding=True):
    requirements = {"deliverable_refs": [ref], "decision_id": "d-" + name,
                    "professional_demands": {ref: [demand]}}
    if output_binding:
        requirements["deliverable_outputs"] = {name: {"deliverable_id": ref, "variant_id": ref}}
    return {"task_id": name, "outputs": [name], "executor": executor,
            "acceptance": {"quality": "inspect actual result"}, "requirements": requirements}


def test_typed_admission_rejects_wrong_tool_and_unknown_variant(tmp_path):
    engine = make_engine(tmp_path, [{"id": "caption", "type": "SHORT_COPY"}])
    valid = task("write", "caption", "short_form_copy")
    for wrong in (
        {**valid, "executor": "tool"},
        {**valid, "requirements": {**valid["requirements"], "professional_demands": {"caption": ["video_generation"]}}},
        {**valid, "requirements": {**valid["requirements"], "deliverable_outputs": {
            "write": {"deliverable_id": "caption", "variant_id": "nonexistent"}}}},
        {**valid, "requirements": {k: v for k, v in valid["requirements"].items() if k != "professional_demands"}},
    ):
        with pytest.raises(ValueError):
            engine.add_tasks("fresh", [wrong])
    wrong = task("wrong", "caption", "research_and_fact_check", executor="tool", output_binding=False)
    wrong["requirements"]["production"] = {"operation": "ffmpeg_video_audio_copy"}
    with pytest.raises(ValueError):
        engine.add_tasks("fresh", [wrong])
    engine.add_tasks("fresh", [valid])
    with pytest.raises(ValueError):
        engine.revise_task("fresh", "write", {"requirements": wrong["requirements"]}, reason="wrong route")


def test_typed_route_decision_becomes_stale_when_selected_contract_changes(tmp_path, monkeypatch):
    from social_media_studio import scope

    engine = make_engine(tmp_path, [{"id": "caption", "type": "SHORT_COPY"}])
    engine.add_tasks("fresh", [task("write", "caption", "short_form_copy")])
    result = engine.record_decision("fresh", receipt("write", "d-write"))
    assert result["payload"]["action_binding"]["professional_route_binding"]["sha256"]
    original = scope.capability_lookup

    def changed(*args, **kwargs):
        current = copy.deepcopy(original(*args, **kwargs))
        if kwargs.get("demand_id") == "short_form_copy":
            current["groups"][0]["selected_operation_contract"]["scope"] += " changed"
        return current

    monkeypatch.setattr(scope, "capability_lookup", changed)
    with pytest.raises(GateError, match="professional route"):
        engine.claim_next("fresh", "worker", task_id="write")


def test_complete_graph_does_not_mean_complete_delivery(tmp_path):
    engine = make_engine(tmp_path, [{"id": "caption", "type": "SHORT_COPY"},
                                    {"id": "article", "type": "LONG_ARTICLE"}])
    engine.add_tasks("fresh", [task("write", "caption", "short_form_copy")])
    engine.record_decision("fresh", receipt("write", "d-write"))
    packet = engine.claim_next("fresh", "worker", task_id="write")
    workspace = Path(engine.project("fresh")["workspace"])
    output = workspace / "caption.txt"
    output.write_text("A sample fixture caption.", encoding="utf-8")
    completed = engine.complete_task("fresh", "write", "worker", packet["claim"]["claim_token"],
                                     {"write": {"path": str(output), "kind": "text",
                                                "media_type": "text/plain", "rights_status": "OWNED"}})
    artifact_id = completed["artifacts"]["write"]["artifact_id"]
    resumed = engine.resume("fresh")
    assert resumed["project_status"] == "TASK_GRAPH_COMPLETE"
    progress = resumed["deliverable_progress"]
    assert progress["candidate_coverage_complete"] is False
    assert progress["artifact_release_coverage_complete"] is False
    assert progress["individually_released_variant_count"] == 0
    assert {v["deliverable_id"] for v in progress["unreleased_variants"]} == {"caption", "article"}
    assert progress["whole_demand_accepted"] is False
    assert progress["owner_outcome_verified"] is False
    by_id = {v["deliverable_id"]: v for v in progress["variants"]}
    assert by_id["caption"]["candidates"][0]["artifact_id"] == artifact_id
    assert by_id["caption"]["candidates"][0]["format_and_quality_verified"] is False
    assert by_id["article"]["candidates"] == []
    assert "lack bound candidates" in resumed["next_action"]
    from social_media_studio.production.worker_pool import run_ready_tool_tasks
    from social_media_studio.operation_cycle import run_work_cycle

    worker = run_ready_tool_tasks(engine, "fresh", max_workers=1)
    assert worker["scheduler_status"] == "DELIVERABLE_CANDIDATES_INCOMPLETE"
    assert worker["deliverable_progress"] == progress
    assert worker["next_action"] == resumed["next_action"]
    cycle = run_work_cycle(engine, "fresh", execute_tools=True)
    assert cycle["after"]["deliverable_progress"] == progress
    assert resumed["next_action"] in cycle["next_actions"]
    assert cycle["tool_execution_requested"] is True
    assert cycle["tool_execution_performed"] is False
    assert cycle["release_authorized"] is False
    output.write_text("Changed bytes.", encoding="utf-8")
    progress = engine.status("fresh")["deliverable_progress"]
    assert progress["variants"][0]["candidates"] == []
    assert progress["rejected_bindings"][0]["reason"] == "ARTIFACT_BYTES_MISSING_OR_CHANGED"


def test_intermediate_output_not_a_deliverable_even_if_task_completed(tmp_path):
    engine = make_engine(tmp_path, [{"id": "caption", "type": "SHORT_COPY"}])
    engine.add_tasks("fresh", [task("notes", "caption", "research_and_fact_check", output_binding=False)])
    engine.record_decision("fresh", receipt("notes", "d-notes"))
    packet = engine.claim_next("fresh", "worker", task_id="notes")
    output = Path(engine.project("fresh")["workspace"]) / "notes.txt"
    output.write_text("Intermediate notes", encoding="utf-8")
    completed = engine.complete_task("fresh", "notes", "worker", packet["claim"]["claim_token"],
                                     {"notes": {"path": str(output), "kind": "text",
                                                "media_type": "text/plain", "rights_status": "OWNED"}})
    progress = engine.status("fresh")["deliverable_progress"]
    assert not progress["candidate_coverage_complete"]
    result = engine.release_check("fresh", completed["artifacts"]["notes"]["artifact_id"], required_rubrics=["fixture-independent-review"])
    assert "artifact_not_bound_to_current_deliverable_variant" in result["failures"]
    assert result["owner_outcome_verified"] is False


def test_local_support_route_can_be_declared_without_claiming_semantic_execution(tmp_path):
    engine = make_engine(tmp_path, [{"id": "caption", "type": "SHORT_COPY"}])
    node = task("research", "caption", "research_and_fact_check", executor="tool", output_binding=False)
    node["requirements"]["production"] = {"operation": "source_evidence_audit"}
    engine.add_tasks("fresh", [node])
    result = engine.record_decision("fresh", receipt("research", "d-research"))
    binding = result["payload"]["action_binding"]["professional_route_binding"]
    assert binding["local_dispatch"] == "production:source_evidence_audit"
    assert binding["assurance"] == "STRUCTURAL_SCOPE_ONLY_NOT_METHOD_OR_OUTCOME_VERIFIED"


def test_local_evidence_routes_support_their_own_requested_report_not_unrelated_outputs(tmp_path):
    from social_media_studio.scope import capability_lookup
    for key, operation in (
        ("programmatic_motion_graphics", "python_frame_render"),
        ("video_assembly", "ffmpeg_assemble"),
        ("original_audio_preservation", "ffmpeg_video_audio_copy"),
        ("technical_media_qa", "ffprobe_media_qa"),
    ):
        group = capability_lookup(demand_id=key)["groups"][0]
        route = group["selected_operation_contract"]
        assert "ANALYSIS_REPORT" in route["deliverable_types"]
        assert operation in route["local_support_operations"]
        assert "SHORT_COPY" not in route["deliverable_types"]
        assert not group["executor_routes"]["actual_executor_verified"]
        view = resolve_intake(tmp_path, {"mode": "NEW", "goal": "Inspect operation evidence",
            "deliverable_specs": [{"id": "report", "type": "ANALYSIS_REPORT"}]},
            selection={"deliverables": {"report": [key]}})["demand_composition"]
        assert view["deliverables"][0]["proposed_professional_routes"][0]["demand_id"] == key
        assert view["effect_authorized"] is False
