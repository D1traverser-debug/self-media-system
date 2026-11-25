from __future__ import annotations

from pathlib import Path

from social_media_studio.engine import ContractError, StudioEngine


def _produce_and_review(
    tmp_path: Path, *, project_id: str, deliverable: str, kind: str,
    media_type: str, rubric_id: str,
):
    engine = StudioEngine(tmp_path / project_id)
    brief = {
        "goal": f"Produce one {deliverable} for publication.",
        "audience": "The intended platform audience.",
        "deliverables": [deliverable],
        "release_policy": {
            "require_rights": False,
            "require_rights_evidence": False,
            "no_auto_publish": True,
            "required_review_rubrics": [rubric_id],
            "review_contracts": {
                rubric_id: {
                    "min_reviewers": 1,
                    "require_resolvable_evidence_refs": True,
                }
            },
        },
    }
    engine.create_project(project_id, f"Cross-content fixture: {deliverable}", brief)
    evidence_path = tmp_path / f"{project_id}-review-evidence.txt"
    evidence_path.write_text("Owner-supplied review context.", encoding="utf-8")
    evidence = engine.import_asset(
        project_id, "review-context", evidence_path,
        kind="evidence", media_type="text/plain", rights_status="NOT_APPLICABLE",
    )
    engine.add_tasks(project_id, [{
        "task_id": "produce-deliverable",
        "title": f"Produce {deliverable}",
        "kind": "production",
        "executor": "agent",
        "depends_on": [],
        "inputs": [],
        "outputs": [deliverable],
        "acceptance": {"observable": f"A current {deliverable} artifact exists."},
        "requirements": {},
    }])
    packet = engine.claim_next(project_id, f"producer-{project_id}")
    assert packet is not None
    assert packet["task"]["task_id"] == "produce-deliverable"
    output_path = engine._project_dir(project_id) / "artifacts" / (
        f"{deliverable}.png" if kind == "image" else
        f"{deliverable}.mp4" if kind == "video" else
        f"{deliverable}.md"
    )
    if kind == "image":
        output_path.write_bytes(b"deterministic-image-fixture-bytes")
    elif kind == "video":
        output_path.write_bytes(b"deterministic-video-fixture-bytes")
    else:
        output_path.write_text("# A short platform-native article.\n", encoding="utf-8")
    result = engine.complete_task(
        project_id, "produce-deliverable", f"producer-{project_id}",
        packet["claim"]["claim_token"],
        {deliverable: {
            "path": str(output_path), "kind": kind, "media_type": media_type,
            "rights_status": "NOT_APPLICABLE",
        }},
    )
    artifact = result["artifacts"][deliverable]
    review = engine.record_review(
        project_id, artifact["artifact_id"],
        reviewer_id=f"reviewer-{project_id}", rubric_id=rubric_id,
        outcome="PASS", dimensions={"scorecard": {"goal_fit": 5}},
        evidence_refs=[evidence["artifact_id"]],
    )
    return engine, artifact, review


def test_x_article_and_static_image_do_not_inherit_video_only_qa_or_media_graph(tmp_path):
    cases = [
        {
            "project_id": "x-article",
            "deliverable": "final-x-article",
            "kind": "document",
            "media_type": "text/markdown",
            "rubric_id": "editorial",
        },
        {
            "project_id": "static-image",
            "deliverable": "final-static-image",
            "kind": "image",
            "media_type": "image/png",
            "rubric_id": "visual",
        },
    ]
    for case in cases:
        engine, artifact, review = _produce_and_review(tmp_path, **case)
        tasks = engine.list_tasks(case["project_id"])
        assert [task["task_id"] for task in tasks] == ["produce-deliverable"]
        assert all(task["kind"] == "production" for task in tasks)
        release = engine.release_check(
            case["project_id"], artifact["artifact_id"],
            required_rubrics=[], require_rights=False,
        )
        assert release["pass"] is True, release["failures"]
        assert release["technical_qa"] is None
        assert release["review_summary"][case["rubric_id"]]["review_ids"] == [review["review_id"]]
        assert release["review_execution_verification"]["ordinary_review"] == "LOW_ASSURANCE_METADATA_ONLY"
        assert release["review_execution_verification"]["high_assurance"] == "ED25519_DSSE_IN_TOTO_VERIFIED_AT_RECORD_AND_RELEASE"


def test_video_only_technical_qa_gate_remains_scoped_to_video_artifacts(tmp_path):
    engine, artifact, _ = _produce_and_review(
        tmp_path, project_id="video-only", deliverable="final-video",
        kind="video", media_type="video/mp4", rubric_id="craft",
    )
    release = engine.release_check(
        "video-only", artifact["artifact_id"], required_rubrics=[], require_rights=False,
    )
    assert release["pass"] is False
    assert "technical_qa_receipt_missing:technical-qa-receipt" in release["failures"]
    assert release["technical_qa"] is None


def test_high_assurance_is_an_explicit_contract_choice_not_a_global_default():
    assert StudioEngine._review_contract_requires_execution({
        "min_reviewers": 1,
        "require_resolvable_evidence_refs": True,
    }) is False
    assert StudioEngine._review_contract_requires_execution({
        "reviewer_kind": "HUMAN",
        "execution_mode": "INDEPENDENT_COLD_READ",
        "blind_review": True,
    }) is True


def test_short_article_high_assurance_contract_blocks_without_a_registered_executor(tmp_path):
    engine = StudioEngine(tmp_path / "high-assurance-article")
    brief = {
        "goal": "Produce a short X Article.",
        "audience": "Technology readers.",
        "deliverables": ["final-article"],
        "release_policy": {
            "require_rights": False,
            "require_rights_evidence": False,
            "required_review_rubrics": ["human-cold-read"],
            "review_contracts": {
                "human-cold-read": {
                    "reviewer_kind": "HUMAN",
                    "execution_mode": "INDEPENDENT_COLD_READ",
                    "blind_review": True,
                    "require_execution_attestation": True,
                }
            },
        },
    }
    engine.create_project("high-assurance-article", "Short article high-assurance fixture", brief)
    source = tmp_path / "high-assurance-source.txt"
    source.write_text("Review context.", encoding="utf-8")
    evidence = engine.import_asset(
        "high-assurance-article", "review-context", source,
        kind="evidence", media_type="text/plain", rights_status="NOT_APPLICABLE",
    )
    output = engine._project_dir("high-assurance-article") / "artifacts" / "final-article.md"
    output.write_text("# Article\n", encoding="utf-8")
    engine.import_asset(
        "high-assurance-article", "final-article", output,
        kind="document", media_type="text/markdown", rights_status="NOT_APPLICABLE",
    )
    with pytest.raises(ContractError, match="completed review task"):
        engine.record_review(
            "high-assurance-article", engine._artifact_by_name(
                engine._connect("high-assurance-article"), "high-assurance-article", "final-article"
            )["artifact_id"],
            reviewer_id="human-reviewer", rubric_id="human-cold-read",
            outcome="PASS", dimensions={}, evidence_refs=[evidence["artifact_id"]],
        )
