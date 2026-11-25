"""Authenticated execution receipts for high-assurance Social Media Studio reviews.

The registry is deliberately empty in production until an executor has been
independently assessed and explicitly registered. Provider run IDs and caller
supplied booleans are correlation data, not execution proof.
"""
from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://social-media-studio.dev/attestation/review-execution/v1"
PAYLOAD_TYPE = "application/vnd.in-toto+json"


class ReviewExecutionError(ValueError):
    """A review execution receipt is absent, untrusted, malformed or stale."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def dsse_pae(payload_type: str, payload: bytes) -> bytes:
    """DSSE pre-authentication encoding (PAE), version 1."""
    return (
        b"DSSEv1 "
        + str(len(payload_type.encode("utf-8"))).encode("ascii")
        + b" " + payload_type.encode("utf-8")
        + b" " + str(len(payload)).encode("ascii")
        + b" " + payload
    )


def build_review_statement(
    *, reviewed_artifact_sha256: str, review_result_sha256: str,
    predicate: dict[str, Any],
) -> dict[str, Any]:
    for value, label in (
        (reviewed_artifact_sha256, "reviewed artifact digest"),
        (review_result_sha256, "review result digest"),
    ):
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ReviewExecutionError(f"{label} must be a lowercase SHA-256 digest")
    if not isinstance(predicate, dict):
        raise ReviewExecutionError("review execution predicate must be an object")
    return {
        "_type": STATEMENT_TYPE,
        "subject": [
            {"name": "reviewed-artifact", "digest": {"sha256": reviewed_artifact_sha256}},
            {"name": "review-result", "digest": {"sha256": review_result_sha256}},
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": predicate,
    }


def sign_review_statement(statement: dict[str, Any], *, key_id: str, private_key: Any) -> dict[str, Any]:
    """Create a DSSE envelope. The private key must remain in the trusted executor."""
    if not isinstance(key_id, str) or not key_id.strip():
        raise ReviewExecutionError("signing key ID is required")
    payload = canonical_json(statement)
    signature = private_key.sign(dsse_pae(PAYLOAD_TYPE, payload))
    return {
        "payloadType": PAYLOAD_TYPE,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [{
            "keyid": key_id,
            "sig": base64.b64encode(signature).decode("ascii"),
        }],
    }


def _parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ReviewExecutionError(f"{label} is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewExecutionError(f"{label} is not RFC3339") from exc
    if parsed.tzinfo is None:
        raise ReviewExecutionError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


class ReviewExecutionTrustRegistry:
    """Verifies signed, digest-bound review execution receipts against pinned trust roots."""

    def __init__(
        self, config_path: Path | None = None, *, config: dict[str, Any] | None = None,
    ):
        if config is not None:
            self.config = config
        else:
            path = config_path or Path(__file__).with_name("data") / "review_executors.json"
            try:
                self.config = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ReviewExecutionError(f"cannot load review executor trust registry: {exc}") from exc
        if not isinstance(self.config, dict):
            raise ReviewExecutionError("review executor trust registry must be an object")
        if self.config.get("schema_version") != 1:
            raise ReviewExecutionError("unsupported review executor trust registry schema version")
        if not isinstance(self.config.get("trusted_executors", {}), dict):
            raise ReviewExecutionError("trusted_executors must be an object")
        if not isinstance(self.config.get("policy", {}), dict):
            raise ReviewExecutionError("review executor trust policy must be an object")

    def verify(
        self, envelope: dict[str, Any], *, expected: dict[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        if not isinstance(envelope, dict) or envelope.get("payloadType") != PAYLOAD_TYPE:
            raise ReviewExecutionError("review execution receipt must be an in-toto DSSE envelope")
        try:
            payload = base64.b64decode(envelope["payload"], validate=True)
            statement = json.loads(payload.decode("utf-8"))
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReviewExecutionError("review execution receipt payload is malformed") from exc
        if not isinstance(statement, dict) or statement.get("_type") != STATEMENT_TYPE:
            raise ReviewExecutionError("review execution receipt has an unsupported statement type")
        if statement.get("predicateType") != PREDICATE_TYPE:
            raise ReviewExecutionError("review execution receipt has an unsupported predicate type")
        subjects = statement.get("subject")
        if not isinstance(subjects, list):
            raise ReviewExecutionError("review execution receipt subjects are missing")
        subject_map = {
            item.get("name"): item.get("digest", {}).get("sha256")
            for item in subjects if isinstance(item, dict) and isinstance(item.get("digest"), dict)
        }
        if subject_map.get("reviewed-artifact") != expected.get("reviewed_artifact_sha256"):
            raise ReviewExecutionError("reviewed artifact digest does not match the review contract")
        if subject_map.get("review-result") != expected.get("review_result_sha256"):
            raise ReviewExecutionError("review result digest does not match the registered report artifact")

        signatures = envelope.get("signatures")
        if not isinstance(signatures, list) or not signatures:
            raise ReviewExecutionError("review execution receipt has no signature")
        predicate = statement.get("predicate")
        if not isinstance(predicate, dict):
            raise ReviewExecutionError("review execution predicate is missing")
        executor_id = predicate.get("executor_id")
        if not isinstance(executor_id, str) or not executor_id:
            raise ReviewExecutionError("review execution executor identity is missing")
        executor = self.config.get("trusted_executors", {}).get(executor_id)
        if not isinstance(executor, dict) or executor.get("status") != "ACTIVE":
            raise ReviewExecutionError(f"review executor is not trusted: {executor_id}")
        required_registry_fields = (
            "key_id", "public_key", "issuer", "isolation_mechanism",
            "reviewer_kinds", "execution_modes", "reviewer_ids", "providers", "models",
        )
        missing_registry_fields = [
            field for field in required_registry_fields
            if executor.get(field) in (None, "", [])
        ]
        if missing_registry_fields:
            raise ReviewExecutionError(
                f"trusted executor registration is incomplete: {missing_registry_fields}"
            )
        for field in ("reviewer_kinds", "execution_modes", "reviewer_ids", "providers", "models"):
            values = executor.get(field)
            if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
                raise ReviewExecutionError(f"trusted executor registration field is malformed: {field}")

        key_id = executor.get("key_id")
        signature_entry = next(
            (item for item in signatures if isinstance(item, dict) and item.get("keyid") == key_id),
            None,
        )
        if signature_entry is None:
            raise ReviewExecutionError("review execution signature key is not registered")
        try:
            public_key_bytes = base64.b64decode(executor["public_key"], validate=True)
            signature_bytes = base64.b64decode(signature_entry["sig"], validate=True)
            Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
                signature_bytes, dsse_pae(PAYLOAD_TYPE, payload),
            )
        except (KeyError, TypeError, ValueError, InvalidSignature) as exc:
            raise ReviewExecutionError("review execution signature verification failed") from exc

        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        issued_at = _parse_time(predicate.get("issued_at"), "issued_at")
        expires_at = _parse_time(predicate.get("expires_at"), "expires_at")
        clock_skew = int(self.config.get("policy", {}).get("clock_skew_seconds", 120))
        if clock_skew < 0 or clock_skew > 600:
            raise ReviewExecutionError("review executor clock-skew policy is invalid")
        if issued_at > current + timedelta(seconds=clock_skew):
            raise ReviewExecutionError("review execution receipt is from the future")
        if expires_at <= current or expires_at <= issued_at:
            raise ReviewExecutionError("review execution receipt is expired or has an invalid validity window")
        max_age = int(self.config.get("policy", {}).get("max_receipt_age_seconds", 86400))
        if (current - issued_at).total_seconds() > max_age:
            raise ReviewExecutionError("review execution receipt exceeds the maximum age")

        required_fields = (
            "nonce", "execution_id", "provider_run_id", "trace_id", "provider", "model",
            "review_task_id", "review_contract_digest", "reviewer_id", "reviewer_kind",
            "execution_mode", "packet_digest", "result_digest", "input_digests",
            "context_id", "isolation_mode",
        )
        missing = [field for field in required_fields if predicate.get(field) in (None, "", {})]
        if missing:
            raise ReviewExecutionError(f"review execution predicate is missing fields: {missing}")
        for field in (
            "review_task_id", "review_contract_digest", "reviewer_id", "reviewer_kind",
            "execution_mode", "packet_digest", "result_digest", "input_digests",
        ):
            if predicate.get(field) != expected.get(field):
                raise ReviewExecutionError(f"review execution {field} does not match the current contract")
        observed = predicate.get("observed_input_digests")
        expected_input_digests = expected.get("input_digests", {})
        if not isinstance(expected_input_digests, dict) or not all(
            isinstance(name, str) and isinstance(digest, str) for name, digest in expected_input_digests.items()
        ):
            raise ReviewExecutionError("review contract input digest map is malformed")
        required = set(expected_input_digests.values())
        if not isinstance(observed, list) or not all(isinstance(item, str) for item in observed):
            raise ReviewExecutionError("review executor observed-input digest list is malformed")
        if set(observed) != required:
            raise ReviewExecutionError("review executor did not attest observing exactly every declared input digest")
        if predicate.get("blind_review") is not expected.get("blind_review"):
            raise ReviewExecutionError("review execution blind-review mode does not match the contract")
        if expected.get("blind_review") and predicate.get("sibling_verdicts_visible") is not False:
            raise ReviewExecutionError("blind review receipt does not prove sibling verdicts were withheld")

        allowed_kinds = executor.get("reviewer_kinds", [])
        allowed_modes = executor.get("execution_modes", [])
        allowed_media_modes = executor.get("media_inspection_modes", [])
        if expected.get("executor_id") and executor_id != expected.get("executor_id"):
            raise ReviewExecutionError("review executor does not match the registered task-output producer")
        if predicate.get("reviewer_kind") not in allowed_kinds:
            raise ReviewExecutionError("reviewer kind is not authorized for this executor")
        if predicate.get("execution_mode") not in allowed_modes:
            raise ReviewExecutionError("review execution mode is not authorized for this executor")
        if predicate.get("isolation_mode") != executor.get("isolation_mechanism"):
            raise ReviewExecutionError("review isolation mechanism does not match the registered executor")

        media = predicate.get("media_inspection", {})
        required_media_mode = expected.get("required_media_inspection")
        if required_media_mode:
            if not isinstance(media, dict) or media.get("mode") != required_media_mode:
                raise ReviewExecutionError("review media inspection mode does not satisfy the contract")
            if media != expected.get("media_inspection"):
                raise ReviewExecutionError("signed media inspection does not match the registered review report")
            if media.get("artifact_sha256") != expected.get("reviewed_artifact_sha256"):
                raise ReviewExecutionError("review media inspection is not bound to the reviewed artifact")
            if required_media_mode not in allowed_media_modes:
                raise ReviewExecutionError("executor is not authorized for the required media inspection mode")
            allowed_methods = executor.get("media_inspection_methods", [])
            method = media.get("method")
            if method not in allowed_methods:
                raise ReviewExecutionError("executor is not authorized for the declared media inspection method")
            if required_media_mode == "FULL_VIDEO":
                if media.get("coverage_fraction") != 1:
                    raise ReviewExecutionError("video review does not cover the full source")
                source_duration = media.get("source_duration_seconds")
                inspected_duration = media.get("inspected_duration_seconds")
                if (
                    not isinstance(source_duration, (int, float)) or isinstance(source_duration, bool)
                    or not math.isfinite(source_duration) or source_duration <= 0
                    or not isinstance(inspected_duration, (int, float)) or isinstance(inspected_duration, bool)
                    or not math.isfinite(inspected_duration) or inspected_duration <= 0
                ):
                    raise ReviewExecutionError("full-video review must attest finite positive source and inspected durations")
                tolerance = max(0.05, source_duration * 0.001)
                if abs(inspected_duration - source_duration) > tolerance:
                    raise ReviewExecutionError("video review duration does not cover the complete source")
                intervals = media.get("coverage_intervals")
                if not isinstance(intervals, list) or not intervals:
                    raise ReviewExecutionError("full-video review requires timestamped coverage intervals")
                normalized: list[tuple[float, float]] = []
                for interval in intervals:
                    if not isinstance(interval, list) or len(interval) != 2:
                        raise ReviewExecutionError("video review coverage interval is malformed")
                    start, end = interval
                    if (
                        not isinstance(start, (int, float)) or isinstance(start, bool)
                        or not math.isfinite(start)
                        or not isinstance(end, (int, float)) or isinstance(end, bool)
                        or not math.isfinite(end)
                        or start < 0 or end <= start or end > source_duration + tolerance
                    ):
                        raise ReviewExecutionError("video review coverage interval is outside the source duration")
                    normalized.append((float(start), float(end)))
                normalized.sort()
                cursor = 0.0
                for start, end in normalized:
                    if start > cursor + tolerance:
                        raise ReviewExecutionError("video review coverage trace contains an uninspected gap")
                    cursor = max(cursor, end)
                if cursor < source_duration - tolerance:
                    raise ReviewExecutionError("video review coverage trace does not reach the end of the source")
                trace_payload = {
                    "artifact_sha256": media.get("artifact_sha256"),
                    "mode": media.get("mode"),
                    "method": media.get("method"),
                    "source_duration_seconds": source_duration,
                    "coverage_intervals": media.get("coverage_intervals"),
                }
                if media.get("trace_sha256") != digest_json(trace_payload):
                    raise ReviewExecutionError("video review coverage trace digest is missing or invalid")

        allowed_providers = executor.get("providers", [])
        if predicate.get("provider") not in allowed_providers:
            raise ReviewExecutionError("review provider is not authorized for this executor")
        allowed_models = executor.get("models", [])
        if predicate.get("model") not in allowed_models:
            raise ReviewExecutionError("review model is not authorized for this executor")
        allowed_reviewers = executor.get("reviewer_ids", [])
        if predicate.get("reviewer_id") not in allowed_reviewers:
            raise ReviewExecutionError("reviewer identity is not authorized for this executor")

        return {
            "verified": True,
            "executor_id": executor_id,
            "key_id": key_id,
            "issuer": executor.get("issuer"),
            "signature_sha256": hashlib.sha256(signature_bytes).hexdigest(),
            "statement_sha256": hashlib.sha256(payload).hexdigest(),
            "nonce": predicate["nonce"],
            "execution_id": predicate["execution_id"],
            "provider_run_id": predicate["provider_run_id"],
            "trace_id": predicate["trace_id"],
            "provider": predicate["provider"],
            "model": predicate["model"],
            "issued_at": predicate["issued_at"],
            "expires_at": predicate["expires_at"],
            "review_task_id": predicate["review_task_id"],
            "review_contract_digest": predicate["review_contract_digest"],
            "packet_digest": predicate["packet_digest"],
            "result_digest": predicate["result_digest"],
            "reviewer_id": predicate["reviewer_id"],
            "reviewer_kind": predicate["reviewer_kind"],
            "execution_mode": predicate["execution_mode"],
            "context_id": predicate["context_id"],
            "isolation_mode": predicate["isolation_mode"],
            "sibling_verdicts_visible": predicate.get("sibling_verdicts_visible"),
            "media_inspection": media,
            "verification": "ED25519_DSSE_IN_TOTO_VERIFIED",
        }
