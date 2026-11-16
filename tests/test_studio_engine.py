from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import threading

import pytest

from video_studio.engine import ClaimError, ContractError, StudioEngine


def brief():
    return {
        "goal": "Produce a publishable 60-second technology explainer.",
        "audience": "Technology-curious viewers aged 20-40.",
        "deliverables": ["final.mp4", "cover.png", "publish-copy.md"],
        "release_policy": {
            "required_evidence_refs": ["platform-format-review"],
            "required_review_rubrics": ["editorial", "craft", "technical"],
        },
    }


def make_engine(tmp_path: Path) -> StudioEngine:
    engine = StudioEngine(tmp_path / "workspace")
    engine.create_project("demo", "Demo", brief())
    return engine


def task(task_id, *, deps=(), inputs=(), outputs=None, priority=0):
    return {
        "task_id": task_id,
        "title": task_id,
        "kind": "production",
        "executor": "agent",
        "depends_on": list(deps),
        "inputs": list(inputs),
        "outputs": outputs or [f"{task_id}-artifact"],
        "acceptance": {"observable": "A concrete artifact exists and satisfies the brief."},
        "priority": priority,
    }


def complete(engine, tmp_path, task_id, worker="worker"):
    packet = engine.claim_next("demo", worker)
    assert packet is not None
    assert packet["task"]["task_id"] == task_id
    artifact_name = packet["task"]["outputs"][0]
    output = engine._project_dir("demo") / "artifacts" / f"{artifact_name}.txt"
    output.write_text(f"artifact for {task_id}", encoding="utf-8")
    result = engine.complete_task(
        "demo", task_id, worker, packet["claim"]["claim_token"],
        {artifact_name: {"path": str(output), "kind": "document", "media_type": "text/plain", "rights_status": "OWNED"}},
    )
    return result["artifacts"][artifact_name]


def test_project_requires_outcome_contract_and_has_standalone_identity(tmp_path):
    engine = StudioEngine(tmp_path)
    with pytest.raises(ContractError):
        engine.create_project("bad", "Bad", {"goal": "x"})
    created = engine.create_project("good", "Good", brief())
    assert created["project_id"] == "good"
    assert Path(created["workspace"]).is_dir()
    assert (Path(created["workspace"]) / "studio.sqlite3").is_file()


def test_dynamic_dag_runs_independent_tasks_in_parallel_then_unlocks_dependency(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("research"), task("visual"), task("edit", deps=["research", "visual"], inputs=["research-artifact", "visual-artifact"])])

    # Two workers can claim two independent tasks; no fixed stage order is imposed.
    first = engine.claim_next("demo", "worker-a")
    second = engine.claim_next("demo", "worker-b")
    assert {first["task"]["task_id"], second["task"]["task_id"]} == {"research", "visual"}
    assert engine.claim_next("demo", "worker-c") is None

    for packet in (first, second):
        task_id = packet["task"]["task_id"]
        output_name = packet["task"]["outputs"][0]
        output = engine._project_dir("demo") / "artifacts" / f"{task_id}.txt"
        output.write_text(task_id, encoding="utf-8")
        engine.complete_task("demo", task_id, packet["claim"]["worker_id"], packet["claim"]["claim_token"], {
            output_name: {"path": str(output), "kind": "document", "media_type": "text/plain", "rights_status": "OWNED"}
        })

    edit = engine.claim_next("demo", "editor")
    assert edit["task"]["task_id"] == "edit"
    assert set(edit["input_artifacts"]) == {"research-artifact", "visual-artifact"}


def test_concurrent_claim_is_atomic_and_single_task_has_one_owner(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("only")])
    barrier = threading.Barrier(2)

    def claim(worker):
        barrier.wait()
        return engine.claim_next("demo", worker)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, ["worker-a", "worker-b"]))
    claimed = [item for item in results if item is not None]
    assert len(claimed) == 1
    assert claimed[0]["task"]["task_id"] == "only"


def test_missing_input_waits_until_asset_is_imported(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("edit", inputs=["source-video"])])
    assert engine.list_tasks("demo")[0]["status"] == "WAITING_INPUT"
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source bytes")
    imported = engine.import_asset("demo", "source-video", source, kind="video", media_type="video/mp4", rights_status="AUTHORIZED")
    assert imported["sha256"] == hashlib.sha256(b"source bytes").hexdigest()
    assert engine.list_tasks("demo")[0]["status"] == "READY"


def test_claim_token_and_lease_prevent_stale_worker_completion(tmp_path, monkeypatch):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render")])
    packet = engine.claim_next("demo", "worker-a", lease_seconds=30)
    token = packet["claim"]["claim_token"]
    # Simulate an expired lease in the durable store, without sleeping.
    with engine._connect("demo") as connection:
        connection.execute("UPDATE tasks SET lease_until='2000-01-01T00:00:00Z' WHERE task_id='render'")
        connection.commit()
    reclaimed = engine.claim_next("demo", "worker-b", lease_seconds=30)
    assert reclaimed["claim"]["worker_id"] == "worker-b"
    output = tmp_path / "render.txt"
    output.write_text("done", encoding="utf-8")
    with pytest.raises(ClaimError):
        engine.complete_task("demo", "render", "worker-a", token, {
            "render-artifact": {"path": str(output), "rights_status": "OWNED"}
        })


def test_task_completion_requires_exact_declared_outputs_and_stores_digest(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render", outputs=["master-video", "cover"])])
    packet = engine.claim_next("demo", "worker")
    master = engine._project_dir("demo") / "artifacts" / "master.mp4"
    cover = engine._project_dir("demo") / "artifacts" / "cover.png"
    master.write_bytes(b"mp4")
    cover.write_bytes(b"png")
    with pytest.raises(ContractError):
        engine.complete_task("demo", "render", "worker", packet["claim"]["claim_token"], {
            "master-video": {"path": str(master), "rights_status": "OWNED"}
        })
    result = engine.complete_task("demo", "render", "worker", packet["claim"]["claim_token"], {
        "master-video": {"path": str(master), "kind": "video", "media_type": "video/mp4", "rights_status": "OWNED"},
        "cover": {"path": str(cover), "kind": "image", "media_type": "image/png", "rights_status": "OWNED"},
    })
    assert result["artifacts"]["master-video"]["sha256"] == hashlib.sha256(b"mp4").hexdigest()
    assert engine.audit("demo")["pass"] is True


def test_artifact_path_cannot_escape_project_workspace(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render")])
    packet = engine.claim_next("demo", "worker")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    with pytest.raises(ContractError):
        engine.complete_task("demo", "render", "worker", packet["claim"]["claim_token"], {
            "render-artifact": {"path": str(outside), "rights_status": "OWNED"}
        })


def test_decision_receipt_requires_competing_causes_alternatives_and_falsifier(tmp_path):
    engine = make_engine(tmp_path)
    with pytest.raises(ContractError):
        engine.record_decision("demo", {"question": "which method?"})
    receipt = engine.record_decision("demo", {
        "question": "Why did the opening fail?",
        "scope": "episode-01/opening",
        "source_refs": ["asset://rough-cut-v1", "review://cold-read-v1"],
        "hypotheses": [
            {"id": "H1", "claim": "the hook is unclear", "discriminator": "cold-read viewers cannot state the promise"},
            {"id": "H2", "claim": "the visual promise is weak", "discriminator": "visual-only preview does not communicate the premise"},
        ],
        "alternatives": [
            {"id": "A", "plan": "rewrite hook", "counterevidence": "could worsen pacing"},
            {"id": "B", "plan": "replace opening visual", "counterevidence": "may not fix unclear premise"},
        ],
        "selected_option": "A",
        "falsifier": "a blind cold-read can accurately paraphrase the original promise",
        "rollback": "restore opening v1 and preserve its asset lineage",
    })
    assert receipt["status"] == "ACTIVE"


def test_failure_cannot_close_without_independent_verification_and_regression(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render")])
    failure = engine.record_failure("demo", {
        "task_id": "render",
        "symptom": "generated clips repeatedly break object continuity",
        "hypotheses": [
            {"id": "H1", "claim": "reference binding is insufficient", "discriminator": "compare same prompt with and without locked reference"},
            {"id": "H2", "claim": "motion request exceeds model capability", "discriminator": "test a lower-motion control with the same reference"},
        ],
        "selected_root_cause": "H2",
        "method_challenge": "the current benchmark did not isolate motion complexity",
        "repair_plan": "split the move into two controlled shots",
        "falsifier": "a matched test with the original motion succeeds consistently",
        "rollback": "restore the original shot plan and retain rejected takes",
        "evidence_refs": ["take://failed-1", "benchmark://motion-control"],
    })
    with pytest.raises(ContractError):
        engine.resolve_failure("demo", failure["failure_id"], {"verification_refs": ["qa://1"]})
    engine.resolve_failure("demo", failure["failure_id"], {
        "verification_refs": ["review://new-cut"],
        "regression_refs": ["replay://continuity-fixture"],
        "result": "PASS",
    })
    assert engine.status("demo")["open_failures"] == 0


def test_reviews_are_bound_to_exact_digest_and_independent_reviewer(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render")])
    artifact = complete(engine, tmp_path, "render", "artist")
    with pytest.raises(ContractError):
        engine.record_review("demo", artifact["artifact_id"], reviewer_id="artist", rubric_id="craft", outcome="PASS", dimensions={"visual": 4}, evidence_refs=["frame://1"])
    review = engine.record_review("demo", artifact["artifact_id"], reviewer_id="reviewer", rubric_id="craft", outcome="PASS", dimensions={"visual": 4}, evidence_refs=["frame://1", "frame://2"])
    assert review["artifact_digest"] == artifact["sha256"]


def test_release_check_requires_all_reviews_rights_and_platform_evidence(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render", outputs=["final-video"])])
    packet = engine.claim_next("demo", "artist")
    output = engine._project_dir("demo") / "artifacts" / "final-video.mp4"
    output.write_bytes(b"verified final video bytes")
    result = engine.complete_task("demo", "render", "artist", packet["claim"]["claim_token"], {
        "final-video": {"path": str(output), "kind": "video", "media_type": "video/mp4", "rights_status": "OWNED"}
    })
    artifact = result["artifacts"]["final-video"]
    for rubric in ("editorial", "craft", "technical"):
        engine.record_review("demo", artifact["artifact_id"], reviewer_id=f"reviewer-{rubric}", rubric_id=rubric, outcome="PASS", dimensions={"score": 4}, evidence_refs=[f"evidence://{rubric}"])
    blocked = engine.release_check("demo", artifact["artifact_id"], required_rubrics=["editorial", "craft", "technical"], evidence_refs=[])
    assert blocked["pass"] is False
    assert any(item.startswith("release_evidence_missing") for item in blocked["failures"])
    passed = engine.release_check("demo", artifact["artifact_id"], required_rubrics=["editorial", "craft", "technical"], evidence_refs=["platform-format-review"])
    assert passed["pass"] is True


def test_invalidation_only_marks_target_and_dependency_descendants_stale(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("research"), task("visual"), task("edit", deps=["research", "visual"]), task("cover", deps=["visual"])])
    # Complete independent nodes and descendants in dependency order.
    complete(engine, tmp_path, "research", "w1")
    complete(engine, tmp_path, "visual", "w2")
    complete(engine, tmp_path, "cover", "w3")
    complete(engine, tmp_path, "edit", "w4")
    result = engine.invalidate("demo", "visual", "visual direction changed")
    assert set(result["invalidated_tasks"]) == {"visual", "edit", "cover"}
    states = {item["task_id"]: item["status"] for item in engine.list_tasks("demo")}
    assert states["research"] == "COMPLETED"
    assert states["visual"] == states["edit"] == states["cover"] == "STALE"
    reopened = engine.reopen("demo", "visual", "new visual direction approved")
    assert set(reopened) == {"visual", "edit", "cover"}
    states = {item["task_id"]: item["status"] for item in engine.list_tasks("demo")}
    assert states["visual"] == "READY"
    assert states["edit"] == states["cover"] == "PENDING"


def test_learning_stays_candidate_until_independent_replay_and_counterexample_trials(tmp_path):
    engine = make_engine(tmp_path)
    candidate = engine.record_learning("demo", {
        "method": "use a locked camera and one object transform for product reveal shots",
        "applicability": ["static product hero shots"],
        "counterexamples": ["handheld documentary movement"],
        "failure_conditions": ["camera motion is part of the story"],
        "evidence_refs": ["pilot://001-shot-04"],
        "replay_refs": ["fixture://product-reveal"],
        "independent_replay_pass": True,
    })
    assert candidate["status"] == "CANDIDATE"
    validated = engine.record_learning("demo", {
        "method": "use a locked camera and one object transform for product reveal shots",
        "applicability": ["static product hero shots"],
        "counterexamples": ["handheld documentary movement"],
        "failure_conditions": ["camera motion is part of the story"],
        "evidence_refs": ["pilot://001-shot-04", "pilot://002-shot-03"],
        "replay_refs": ["fixture://product-reveal-v1", "fixture://product-reveal-v2"],
        "independent_replay_pass": True,
        "validation_evidence_refs": ["review://method-review"],
        "counterexample_trials": ["fixture://handheld-documentary"],
    })
    assert validated["status"] == "VALIDATED"


def test_cli_exposes_standalone_entry_without_caos_import(tmp_path):
    source = (Path(__file__).parents[1] / "video_studio" / "engine.py").read_text(encoding="utf-8")
    assert "import caos" not in source.lower()
    assert "caos_runtime" not in source.lower()
    from video_studio.cli import main
    brief_file = tmp_path / "brief.json"
    brief_file.write_text(json.dumps(brief()), encoding="utf-8")
    assert main(["--root", str(tmp_path / "ws"), "init", "cli-demo", "--brief", str(brief_file)]) == 0
    assert main(["--root", str(tmp_path / "ws"), "audit", "cli-demo"]) == 0


def test_graph_rejects_cycles_and_multiple_output_producers(tmp_path):
    engine = make_engine(tmp_path)
    with pytest.raises(ContractError, match="cycle"):
        engine.add_tasks("demo", [task("a", deps=["b"]), task("b", deps=["a"])])
    with pytest.raises(ContractError, match="one producer"):
        engine.add_tasks("demo", [task("a", outputs=["shared"]), task("b", outputs=["shared"])])


def test_failure_retry_is_bounded_by_declared_attempt_budget(tmp_path):
    engine = make_engine(tmp_path)
    spec = task("unstable")
    spec["max_attempts"] = 2
    engine.add_tasks("demo", [spec])
    first = engine.claim_next("demo", "worker-a")
    retry = engine.fail_task("demo", "unstable", "worker-a", first["claim"]["claim_token"], {"symptom": "transient"}, retryable=True)
    assert retry == {"task_id": "unstable", "status": "READY", "retry_scheduled": True}
    second = engine.claim_next("demo", "worker-b")
    assert second["claim"]["attempt"] == 2
    final = engine.fail_task("demo", "unstable", "worker-b", second["claim"]["claim_token"], {"symptom": "still failing"}, retryable=True)
    assert final == {"task_id": "unstable", "status": "FAILED", "retry_scheduled": False}
    assert engine.claim_next("demo", "worker-c") is None


def test_artifact_paths_are_immutable_and_audit_detects_post_registration_mutation(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render", priority=10), task("another")])
    packet = engine.claim_next("demo", "artist")
    output = engine._project_dir("demo") / "artifacts" / "master.mp4"
    output.write_bytes(b"first render")
    result = engine.complete_task("demo", "render", "artist", packet["claim"]["claim_token"], {
        "render-artifact": {"path": str(output), "kind": "video", "media_type": "video/mp4", "rights_status": "OWNED"}
    })
    second = engine.claim_next("demo", "artist-2")
    assert second["task"]["task_id"] == "another"
    with pytest.raises(ContractError, match="immutable"):
        engine.complete_task("demo", "another", "artist-2", second["claim"]["claim_token"], {
            "another-artifact": {"path": str(output), "kind": "video", "media_type": "video/mp4", "rights_status": "OWNED"}
        })
    output.write_bytes(b"silently replaced")
    audit = engine.audit("demo")
    assert audit["pass"] is False
    assert any("digest_mismatch" in item for item in audit["failures"])
    with pytest.raises(ContractError, match="bytes changed"):
        engine.record_review("demo", result["artifacts"]["render-artifact"]["artifact_id"], reviewer_id="reviewer", rubric_id="craft", outcome="PASS", dimensions={"visual": 4}, evidence_refs=["frame://1"])


def test_release_check_rehashes_final_artifact_before_acceptance(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render")])
    artifact = complete(engine, tmp_path, "render", "artist")
    engine.record_review("demo", artifact["artifact_id"], reviewer_id="reviewer", rubric_id="craft", outcome="PASS", dimensions={"visual": 4}, evidence_refs=["frame://1"])
    output = Path(artifact["path"])
    output.write_text("modified after review", encoding="utf-8")
    result = engine.release_check("demo", artifact["artifact_id"], required_rubrics=["craft"], evidence_refs=["platform-format-review"])
    assert result["pass"] is False
    assert any(item.startswith("final_artifact_bytes_missing_or_digest_changed") for item in result["failures"])


def test_builtin_ffprobe_qa_measures_real_media_and_completes_a_claimed_task(tmp_path):
    import shutil
    import subprocess

    from video_studio.media import run_claimed_media_qa

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg/ffprobe are not installed")
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("technical-qa", inputs=["final-candidate"], outputs=["technical-qa-receipt"])])
    media = tmp_path / "sample.mp4"
    subprocess.run([
        "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1:r=25",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=1", "-c:v", "libx264",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-y", str(media),
    ], check=True, capture_output=True)
    engine.import_asset("demo", "final-candidate", media, kind="video", media_type="video/mp4", rights_status="OWNED")
    # Recreate task with the explicit measurement contract before claiming.
    # The task is already waiting for the input; update the declared tool requirements in its task contract.
    with engine._connect("demo") as connection:
        connection.execute(
            "UPDATE tasks SET kind='technical_measurement',requirements_json=? WHERE project_id='demo' AND task_id='technical-qa'",
            (json.dumps({"tool": "ffprobe", "resolution": "320x240", "frame_rate": 25, "duration_min_seconds": 0.8, "duration_max_seconds": 1.2, "audio_required": True}),),
        )
        connection.commit()
    packet = engine.claim_next("demo", "qa-worker")
    result = run_claimed_media_qa(engine, "demo", "technical-qa", "qa-worker", packet["claim"]["claim_token"], "final-candidate")
    assert result["report"]["hard_pass"] is True
    assert result["report"]["summary"]["width"] == 320
    assert result["report"]["summary"]["frame_rate"] == 25
    assert result["task_completion"]["status"] == "COMPLETED"
    assert engine.audit("demo")["pass"] is True


def test_event_history_and_decision_review_receipts_are_database_immutable(tmp_path):
    import sqlite3

    engine = make_engine(tmp_path)
    with engine._connect("demo") as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE events SET event_type='TAMPERED' WHERE project_id='demo'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM events WHERE project_id='demo'")
        connection.rollback()


def test_brief_revision_records_history_and_invalidates_only_affected_descendants(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("research", priority=20), task("visual", priority=10), task("edit", deps=["research"]), task("cover", deps=["visual"])])
    complete(engine, tmp_path, "research", "w1")
    complete(engine, tmp_path, "visual", "w2")
    complete(engine, tmp_path, "cover", "w3")
    complete(engine, tmp_path, "edit", "w4")
    revised = brief()
    revised["goal"] = "Produce a 60-second cinematic explainer with a stronger human story."
    result = engine.revise_brief("demo", revised, reason="owner changed the editorial promise", affected_task_ids=["visual"])
    assert set(result["invalidated_tasks"]) == {"visual", "cover"}
    states = {item["task_id"]: item["status"] for item in engine.list_tasks("demo")}
    assert states["research"] == states["edit"] == "COMPLETED"
    assert states["visual"] == states["cover"] == "STALE"
    history = engine.brief_history("demo")
    assert len(history) == 2
    assert history[-1]["payload"]["brief"]["goal"] == revised["goal"]
    assert engine.project("demo")["revision"] > 1


def test_task_contract_revision_revokes_claim_and_invalidates_only_descendants(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("research", priority=20), task("visual", priority=10), task("edit", deps=["research"]), task("cover", deps=["visual"])])
    complete(engine, tmp_path, "research", "w1")
    complete(engine, tmp_path, "visual", "w2")
    complete(engine, tmp_path, "cover", "w3")
    complete(engine, tmp_path, "edit", "w4")
    revised = engine.revise_task("demo", "visual", {"acceptance": {"visual": "The exact material and motion must match the approved reference."}}, reason="visual review found an untested continuity constraint")
    assert revised["task"]["status"] == "READY"
    assert revised["invalidated_descendants"] == ["cover"]
    states = {item["task_id"]: item["status"] for item in engine.list_tasks("demo")}
    assert states["research"] == states["edit"] == "COMPLETED"
    assert states["visual"] == "READY" and states["cover"] == "STALE"


def test_task_contract_revision_rejects_dependency_cycles_without_mutating_state(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("a"), task("b", deps=["a"])])
    before = engine.list_tasks("demo")
    with pytest.raises(ContractError, match="cycle"):
        engine.revise_task("demo", "a", {"depends_on": ["b"]}, reason="invalid experiment")
    after = engine.list_tasks("demo")
    assert [(x["task_id"], x["depends_on"]) for x in before] == [(x["task_id"], x["depends_on"]) for x in after]


def test_release_check_blocks_conflicting_review_outcomes_for_same_rubric(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("render")])
    artifact = complete(engine, tmp_path, "render", "artist")
    engine.record_review("demo", artifact["artifact_id"], reviewer_id="reviewer-pass", rubric_id="craft", outcome="PASS", dimensions={"visual": 4}, evidence_refs=["frame://pass"])
    engine.record_review("demo", artifact["artifact_id"], reviewer_id="reviewer-fail", rubric_id="craft", outcome="FAIL", dimensions={"visual": 1}, evidence_refs=["frame://fail"])
    result = engine.release_check("demo", artifact["artifact_id"], required_rubrics=["craft"], evidence_refs=["platform-format-review"])
    assert result["pass"] is False
    assert any(item.startswith("required_review_missing_or_conflicting:craft") for item in result["failures"])

def test_audit_detects_tampering_of_stale_historical_artifacts(tmp_path):
    engine = make_engine(tmp_path)
    engine.add_tasks("demo", [task("research"), task("edit", deps=["research"], inputs=["research-artifact"])])
    research = complete(engine, tmp_path, "research", "researcher")
    complete(engine, tmp_path, "edit", "editor")
    engine.invalidate("demo", "research", "owner changed source interpretation")
    Path(research["path"]).write_text("tampered historical evidence", encoding="utf-8")
    report = engine.audit("demo")
    assert report["pass"] is False
    assert any(
        item.startswith("artifact_digest_mismatch:")
        and research["artifact_id"] in item
        for item in report["failures"]
    )


def test_repeated_media_qa_uses_new_immutable_receipt_path(tmp_path):
    import shutil
    import subprocess

    from video_studio.media import run_claimed_media_qa

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg/ffprobe are not installed")
    engine = make_engine(tmp_path)
    engine.add_tasks(
        "demo",
        [task("technical-qa", inputs=["final-candidate"], outputs=["technical-qa-receipt"])],
    )
    media = tmp_path / "repeat.mp4"
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-f", "lavfi", "-i",
            "color=c=blue:s=320x240:d=1:r=25", "-f", "lavfi", "-i",
            "sine=frequency=1000:duration=1", "-c:v", "libx264", "-pix_fmt",
            "yuv420p", "-c:a", "aac", "-shortest", "-y", str(media),
        ],
        check=True,
        capture_output=True,
    )
    engine.import_asset(
        "demo", "final-candidate", media, kind="video",
        media_type="video/mp4", rights_status="OWNED",
    )
    with engine._connect("demo") as connection:
        connection.execute(
            "UPDATE tasks SET kind='technical_measurement',requirements_json=? "
            "WHERE project_id='demo' AND task_id='technical-qa'",
            (json.dumps({
                "tool": "ffprobe", "resolution": "320x240",
                "frame_rate": 25, "audio_required": True,
            }),),
        )
        connection.commit()
    first_packet = engine.claim_next("demo", "qa-worker-1")
    first = run_claimed_media_qa(
        engine, "demo", "technical-qa", "qa-worker-1",
        first_packet["claim"]["claim_token"], "final-candidate",
    )
    engine.invalidate("demo", "technical-qa", "re-run measurement after QA policy update")
    engine.reopen("demo", "technical-qa", "measurement retry approved")
    second_packet = engine.claim_next("demo", "qa-worker-2")
    second = run_claimed_media_qa(
        engine, "demo", "technical-qa", "qa-worker-2",
        second_packet["claim"]["claim_token"], "final-candidate",
    )
    first_path = first["task_completion"]["artifacts"]["technical-qa-receipt"]["path"]
    second_path = second["task_completion"]["artifacts"]["technical-qa-receipt"]["path"]
    assert first_path != second_path
    assert second["task_completion"]["status"] == "COMPLETED"
    assert engine.audit("demo")["pass"] is True
