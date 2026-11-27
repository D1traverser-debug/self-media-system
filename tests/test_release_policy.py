"""Architectural negative tests: release gates cannot be weakened by a brief or caller."""
from __future__ import annotations

import pytest

from social_media_studio.cli import build_parser
from social_media_studio.domain.release_policy import resolve_release_guards
from social_media_studio.engine import ContractError, StudioEngine


def test_release_guard_preserves_video_qa_and_media_rights_floor():
    guards = resolve_release_guards(
        {"require_rights": False, "require_rights_evidence": False,
         "require_technical_qa": False},
        artifact_kind="video", media_type="video/mp4",
        allowed_rights=["OWNED", "AUTHORIZED"], caller_require_rights=False,
    )
    assert guards.require_rights is True
    assert guards.require_rights_evidence is True
    assert guards.require_technical_qa is True
    assert set(guards.disallowed_relaxations) == {
        "release_rights_requirement_cannot_be_disabled",
        "release_media_rights_evidence_cannot_be_disabled",
        "release_video_technical_qa_cannot_be_disabled",
    }


def test_release_guard_is_artifact_type_specific_not_a_global_video_pipeline():
    guards = resolve_release_guards(
        {"require_technical_qa": False}, artifact_kind="document",
        media_type="text/plain", allowed_rights=["OWNED"],
    )
    assert guards.require_technical_qa is False
    assert guards.disallowed_relaxations == ()


@pytest.mark.parametrize("key", [
    "require_rights", "require_rights_evidence", "require_technical_qa",
])
def test_brief_rejects_ambiguous_boolean_gate_values(tmp_path, key):
    engine = StudioEngine(tmp_path / key)
    with pytest.raises(ContractError, match="must be boolean"):
        engine.create_project("demo", "demo", {
            "goal": "Produce an artifact", "audience": "viewers",
            "deliverables": ["result"],
            "release_policy": {key: "false"},
        })


def _engine_and_asset(tmp_path, *, policy, kind, media_type, rights_status="OWNED"):
    engine = StudioEngine(tmp_path / "workspace")
    engine.create_project("demo", "Release floor", {
        "goal": "Make one exact artifact", "audience": "owner",
        "deliverables": ["item"],
        "release_policy": policy,
    })
    path = tmp_path / "sample.bin"
    path.write_bytes(b"fixed fixture bytes")
    asset = engine.import_asset(
        "demo", "item", path, kind=kind, media_type=media_type,
        rights_status=rights_status,
    )
    return engine, asset


def test_video_release_downgrade_cannot_accept_without_technical_qa(tmp_path):
    engine, asset = _engine_and_asset(
        tmp_path, policy={"require_technical_qa": False, "required_review_rubrics": []},
        kind="video", media_type="video/mp4",
    )
    result = engine.release_check("demo", asset["artifact_id"], required_rubrics=[])
    assert result["pass"] is False
    assert "release_video_technical_qa_cannot_be_disabled" in result["failures"]
    assert any(x.startswith("technical_qa_receipt_missing:") for x in result["failures"])
    assert result["acceptance_scope"] == "INDIVIDUAL_ARTIFACT_ONLY"
    assert result["external_publication_authorized"] is False
    assert result["whole_demand_accepted"] is False


def test_rights_bypass_cannot_accept_unknown_rights_from_brief_or_api(tmp_path):
    engine, asset = _engine_and_asset(
        tmp_path, policy={"require_rights": False}, kind="document",
        media_type="text/plain", rights_status="UNKNOWN",
    )
    result = engine.release_check(
        "demo", asset["artifact_id"], required_rubrics=[], require_rights=False,
    )
    assert result["pass"] is False
    assert "release_rights_requirement_cannot_be_disabled" in result["failures"]
    assert "rights_not_cleared:UNKNOWN" in result["failures"]


def test_media_rights_evidence_cannot_be_disabled(tmp_path):
    engine, asset = _engine_and_asset(
        tmp_path, policy={"require_rights_evidence": False}, kind="image",
        media_type="image/png",
    )
    result = engine.release_check("demo", asset["artifact_id"], required_rubrics=[])
    assert result["pass"] is False
    assert "release_media_rights_evidence_cannot_be_disabled" in result["failures"]
    assert any(x.startswith("lineage_rights_evidence_missing:") for x in result["failures"])


def test_obsolete_cli_rights_bypass_removed():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["release-check", "demo", "item", "--allow-unknown-rights"])
