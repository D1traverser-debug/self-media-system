from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from social_media_studio.review_execution import (
    ReviewExecutionError,
    ReviewExecutionTrustRegistry,
    build_review_packet,
    build_review_statement,
    digest_json,
    review_contract_digest,
    sign_review_statement,
)


def sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def fixture_receipt(*, blind: bool = True, media_mode: str | None = None):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    now = datetime.now(timezone.utc)
    input_digests = {"final-video": sha("final-video"), "rights-clearance": sha("rights")}
    expected = {
        "review_task_id": "review-cold-read",
        "review_contract_digest": sha("contract"),
        "reviewer_id": "human-reviewer-01",
        "reviewer_kind": "HUMAN",
        "execution_mode": "INDEPENDENT_COLD_READ",
        "packet_digest": sha("packet"),
        "result_digest": sha("review-report"),
        "input_digests": input_digests,
        "blind_review": blind,
        "required_media_inspection": media_mode,
        "reviewed_artifact_sha256": sha("final-video"),
        "review_result_sha256": sha("review-report"),
        "executor_id": "isolated-review-runtime-01",
        "media_inspection": None,
    }
    media_inspection = {}
    if media_mode:
        media_inspection = {
            "mode": media_mode,
            "method": "CONTINUOUS_PLAYBACK",
            "artifact_sha256": sha("final-video"),
            "coverage_fraction": 1,
            "inspected_duration_seconds": 30,
            "source_duration_seconds": 30,
            "coverage_intervals": [[0, 30]],
        }
        media_inspection["trace_sha256"] = digest_json({
            "artifact_sha256": media_inspection["artifact_sha256"],
            "mode": media_inspection["mode"],
            "method": media_inspection["method"],
            "source_duration_seconds": media_inspection["source_duration_seconds"],
            "coverage_intervals": media_inspection["coverage_intervals"],
        })
        expected["media_inspection"] = media_inspection
    predicate = {
        "executor_id": "isolated-review-runtime-01",
        "issued_at": (now - timedelta(seconds=5)).isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "nonce": uuid.uuid4().hex,
        "execution_id": "execution-01",
        "review_task_id": expected["review_task_id"],
        "review_contract_digest": expected["review_contract_digest"],
        "reviewer_id": expected["reviewer_id"],
        "reviewer_kind": expected["reviewer_kind"],
        "execution_mode": expected["execution_mode"],
        "packet_digest": expected["packet_digest"],
        "result_digest": expected["result_digest"],
        "input_digests": input_digests,
        "observed_input_digests": list(input_digests.values()),
        "context_id": "isolated-context-01",
        "isolation_mode": "ephemeral-container-no-network",
        "blind_review": blind,
        "sibling_verdicts_visible": False if blind else True,
        "provider": "test-provider",
        "model": "reviewer-v1",
        "media_inspection": media_inspection,
    }
    statement = build_review_statement(
        reviewed_artifact_sha256=sha("final-video"),
        review_result_sha256=sha("review-report"),
        predicate=predicate,
    )
    envelope = sign_review_statement(
        statement, key_id="review-key-01", private_key=private_key,
    )
    config = {
        "schema_version": 1,
        "policy": {"max_receipt_age_seconds": 3600},
        "trusted_executors": {
            "isolated-review-runtime-01": {
                "status": "ACTIVE",
                "key_id": "review-key-01",
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "issuer": "test-fixture",
                "isolation_mechanism": "ephemeral-container-no-network",
                "reviewer_kinds": ["HUMAN"],
                "execution_modes": ["INDEPENDENT_COLD_READ"],
                "reviewer_ids": ["human-reviewer-01"],
                "providers": ["test-provider"],
                "models": ["reviewer-v1"],
                "media_inspection_modes": ["FULL_VIDEO"] if media_mode else [],
                "media_inspection_methods": ["CONTINUOUS_PLAYBACK"] if media_mode else [],
            }
        },
    }
    return envelope, expected, config, private_key, statement, now


def test_valid_signed_review_execution_receipt_verifies():
    envelope, expected, config, *_ = fixture_receipt()
    result = ReviewExecutionTrustRegistry(config=config).verify(envelope, expected=expected)
    assert result["verified"] is True
    assert result["verification"] == "ED25519_DSSE_IN_TOTO_VERIFIED"
    assert result["review_task_id"] == "review-cold-read"


def test_empty_registry_fails_closed():
    envelope, expected, *_ = fixture_receipt()
    registry = ReviewExecutionTrustRegistry(config={"trusted_executors": {}})
    with pytest.raises(ReviewExecutionError, match="not trusted"):
        registry.verify(envelope, expected=expected)


def test_review_receipt_rejects_tampered_signature():
    envelope, expected, config, *_ = fixture_receipt()
    envelope["signatures"][0]["sig"] = base64.b64encode(b"not-a-valid-ed25519-signature").decode("ascii")
    with pytest.raises(ReviewExecutionError, match="signature verification failed"):
        ReviewExecutionTrustRegistry(config=config).verify(envelope, expected=expected)


def test_review_receipt_rejects_wrong_subject_digest():
    envelope, expected, config, *_ = fixture_receipt()
    expected["reviewed_artifact_sha256"] = sha("different-artifact")
    with pytest.raises(ReviewExecutionError, match="artifact digest"):
        ReviewExecutionTrustRegistry(config=config).verify(envelope, expected=expected)


def test_review_receipt_requires_every_input_digest_to_be_observed():
    envelope, expected, config, private_key, statement, _ = fixture_receipt()
    statement["predicate"]["observed_input_digests"] = [sha("final-video")]
    envelope = sign_review_statement(statement, key_id="review-key-01", private_key=private_key)
    with pytest.raises(ReviewExecutionError, match="observing every exact input digest"):
        ReviewExecutionTrustRegistry(config=config).verify(envelope, expected=expected)


def test_blind_review_rejects_visible_sibling_verdicts():
    envelope, expected, config, private_key, statement, _ = fixture_receipt(blind=True)
    statement["predicate"]["sibling_verdicts_visible"] = True
    envelope = sign_review_statement(statement, key_id="review-key-01", private_key=private_key)
    with pytest.raises(ReviewExecutionError, match="sibling verdicts were withheld"):
        ReviewExecutionTrustRegistry(config=config).verify(envelope, expected=expected)


def test_review_receipt_rejects_expired_execution():
    envelope, expected, config, private_key, statement, now = fixture_receipt()
    statement["predicate"]["issued_at"] = (now - timedelta(hours=2)).isoformat()
    statement["predicate"]["expires_at"] = (now - timedelta(hours=1)).isoformat()
    envelope = sign_review_statement(statement, key_id="review-key-01", private_key=private_key)
    with pytest.raises(ReviewExecutionError, match="expired"):
        ReviewExecutionTrustRegistry(config=config).verify(envelope, expected=expected, now=now)


def test_full_video_review_requires_complete_coverage_of_exact_source():
    envelope, expected, config, private_key, statement, _ = fixture_receipt(media_mode="FULL_VIDEO")
    media = dict(statement["predicate"]["media_inspection"])
    media["coverage_intervals"] = [[0, 6]]
    media["coverage_fraction"] = 1
    media["trace_sha256"] = digest_json({
        "artifact_sha256": media["artifact_sha256"],
        "mode": media["mode"],
        "method": media["method"],
        "source_duration_seconds": media["source_duration_seconds"],
        "coverage_intervals": media["coverage_intervals"],
    })
    statement["predicate"]["media_inspection"] = media
    expected["media_inspection"] = media
    envelope = sign_review_statement(statement, key_id="review-key-01", private_key=private_key)
    with pytest.raises(ReviewExecutionError, match="does not reach the end"):
        ReviewExecutionTrustRegistry(config=config).verify(envelope, expected=expected)


def test_review_packet_is_digest_bound_and_excludes_sibling_review_outputs():
    task_contract = {
        "rubric_id": "human-cold-read",
        "reviewer_id": "human-reviewer-01",
        "subject_artifact": "final-video",
        "blind_review": True,
    }
    rubric_contract = {"reviewer_kind": "HUMAN", "blind_review": True}
    inputs = [
        {"name": "final-video", "artifact_id": "a1", "version": 1, "sha256": sha("video"), "kind": "video"},
        {"name": "rights-clearance", "artifact_id": "a2", "version": 1, "sha256": sha("rights"), "kind": "document"},
    ]
    packet = build_review_packet(
        project_id="project-01", task_id="review-01", task_contract=task_contract,
        rubric_contract=rubric_contract, input_bindings=inputs,
    )
    assert packet["sibling_verdicts_included"] is False
    assert len(packet["inputs"]) == 2
    assert review_contract_digest(task_contract, rubric_contract) != review_contract_digest(task_contract, {**rubric_contract, "blind_review": False})
    with pytest.raises(ReviewExecutionError, match="sibling review outputs"):
        build_review_packet(
            project_id="project-01", task_id="review-01", task_contract=task_contract,
            rubric_contract=rubric_contract,
            input_bindings=inputs + [{
                "name": "other-review", "artifact_id": "a3", "version": 1,
                "sha256": sha("review"), "kind": "review_report",
            }],
        )
