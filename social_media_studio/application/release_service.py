"""Artifact-scoped release assurance application service.

Owns the existing release transaction without creating a second database,
scheduler, publication authority or owner-acceptance ledger. The StudioEngine
facade still supplies one project's persistence, provenance and event methods.
"""
from __future__ import annotations

from contextlib import closing
import json
import math
import sqlite3
from typing import Any

from ..domain.release_policy import resolve_release_guards
from ..engine_support import (
    ContractError, ProjectNotFound, RIGHTS_ALLOWED, _loads, _sha256,
)
from ..review_execution import (
    ReviewExecutionError, build_review_packet, digest_json, review_contract_digest,
)


class ReleaseAssuranceService:
    """Transactional single-artifact check; never whole-project user approval."""

    def __init__(self, engine: Any) -> None:
        self._engine = engine

    def release_check(
        self, project_id: str, artifact_id: str, *, required_rubrics: list[str],
        evidence_refs: list[str] | None = None, require_rights: bool = True,
    ) -> dict[str, Any]:
        with closing(self._engine._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._engine._refresh_cross_project_transfers_in_tx(connection, project_id)
            self._engine._refresh_in_tx(connection, project_id)
            artifact = connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?", (project_id, artifact_id)
            ).fetchone()
            if artifact is None:
                raise ProjectNotFound(artifact_id)
            failures: list[str] = []
            artifact_path = self._engine._project_dir(project_id) / artifact["relative_path"]
            if not artifact_path.is_file() or _sha256(artifact_path) != artifact["sha256"]:
                failures.append("artifact_bytes_missing_or_digest_changed")
            if artifact["status"] not in {"CURRENT", "ACCEPTED"}:
                failures.append(f"artifact_not_current:{artifact['status']}")

            brief = _loads(self._engine._project_row(connection, project_id)["brief_json"], {})
            release_policy = brief.get("release_policy", {})
            progress = self._engine._deliverable_progress_in_tx(connection, project_id)
            deliverable_binding = None
            if progress["status"] == "CANDIDATE_COVERAGE_ONLY":
                for variant in progress["variants"]:
                    if any(c["artifact_id"] == artifact_id for c in variant["candidates"]):
                        deliverable_binding = {"deliverable_id": variant["deliverable_id"],
                                               "variant_id": variant["variant_id"]}
                        break
                if deliverable_binding is None:
                    failures.append("artifact_not_bound_to_current_deliverable_variant")
            release_guards = resolve_release_guards(
                release_policy, artifact_kind=artifact["kind"],
                media_type=artifact["media_type"],
                allowed_rights=release_policy.get("required_rights_statuses", sorted(RIGHTS_ALLOWED)),
                caller_require_rights=require_rights,
            )
            failures.extend(release_guards.disallowed_relaxations)
            effective_require_rights = release_guards.require_rights
            allowed_rights = set(release_guards.allowed_rights)
            require_rights_evidence = release_guards.require_rights_evidence
            if effective_require_rights and artifact["rights_status"] not in allowed_rights:
                failures.append(f"rights_not_cleared:{artifact['rights_status']}")

            lineage, lineage_failures = self._engine._artifact_lineage_rows(connection, project_id, artifact_id)
            failures.extend(lineage_failures)
            checked_lineage: list[dict[str, Any]] = []
            rights_evidence_verified_asset_ids: set[str] = set()

            def verify_rights_evidence_bindings(
                source: sqlite3.Row, *, failure_prefix: str,
            ) -> list[dict[str, Any]]:
                metadata = _loads(source["metadata_json"], {})
                refs = metadata.get("rights_evidence_refs", []) if isinstance(metadata, dict) else []
                if not isinstance(refs, list) or not refs:
                    return []
                source_label = f"{source['name']}:{source['artifact_id']}"
                event_row = connection.execute(
                    """SELECT payload_json FROM events
                       WHERE project_id=? AND entity_type='ARTIFACT' AND entity_id=?
                         AND event_type IN ('ASSET_IMPORTED','ARTIFACT_CREATED')
                       ORDER BY event_no DESC LIMIT 1""",
                    (project_id, source["artifact_id"]),
                ).fetchone()
                event_payload = _loads(event_row["payload_json"], {}) if event_row else {}
                event_metadata = event_payload.get("metadata", {}) if isinstance(event_payload, dict) else {}
                if (
                    not isinstance(event_metadata, dict)
                    or event_payload.get("artifact_id") != source["artifact_id"]
                    or event_payload.get("version") != source["version"]
                    or event_payload.get("sha256") != source["sha256"]
                    or event_metadata.get("rights_evidence_refs") != refs
                ):
                    failures.append(f"{failure_prefix}_metadata_event_mismatch:{source_label}")
                    return []
                stored_bindings = metadata.get("rights_evidence_bindings")
                event_bindings = event_metadata.get("rights_evidence_bindings")
                if stored_bindings != event_bindings:
                    failures.append(f"{failure_prefix}_digest_binding_metadata_mismatch:{source_label}")
                    return []
                # Legacy compatibility is limited to event-recorded external URLs.
                # They are references, not authenticated copies of remote content.
                if event_bindings is None:
                    if all(
                        isinstance(ref, str) and ref.startswith(("https://", "http://"))
                        for ref in refs
                    ):
                        return [{
                            "reference": ref,
                            "verification": "EXTERNAL_REFERENCE_NOT_FETCHED",
                        } for ref in refs]
                    failures.append(f"{failure_prefix}_digest_bindings_missing:{source_label}")
                    return []
                if (
                    not isinstance(event_bindings, dict)
                    or event_bindings.get("schema_version") != 1
                    or event_bindings.get("binding_mode") != "ARTIFACT_CREATION_EVENT_ID_VERSION_SHA256_SNAPSHOT"
                ):
                    failures.append(f"{failure_prefix}_digest_bindings_invalid:{source_label}")
                    return []
                items = event_bindings.get("items")
                if not isinstance(items, list) or len(items) != len(refs):
                    failures.append(f"{failure_prefix}_digest_bindings_incomplete:{source_label}")
                    return []

                receipts: list[dict[str, Any]] = []
                for index, reference in enumerate(refs):
                    binding = items[index]
                    if not isinstance(binding, dict) or binding.get("reference") != reference:
                        failures.append(f"{failure_prefix}_ref_unresolved:{source['name']}:{reference}")
                        continue
                    if isinstance(reference, str) and reference.startswith(("https://", "http://")):
                        if binding.get("reference_type") != "EXTERNAL_URI" or binding.get("resolved") is not True:
                            failures.append(f"{failure_prefix}_ref_unresolved:{source['name']}:{reference}")
                            continue
                        receipts.append({
                            "reference": reference,
                            "verification": "EXTERNAL_REFERENCE_NOT_FETCHED",
                        })
                        continue
                    if binding.get("reference_type") != "ARTIFACT" or binding.get("resolved") is not True:
                        reason = binding.get("reason")
                        if reason == "BYTES_MISSING_OR_DIGEST_CHANGED":
                            failures.append(f"{failure_prefix}_bytes_missing_or_digest_changed:{source['name']}:{reference}")
                        else:
                            failures.append(f"{failure_prefix}_ref_unresolved:{source['name']}:{reference}")
                        continue
                    evidence_id = binding.get("artifact_id")
                    if not isinstance(evidence_id, str) or not evidence_id or evidence_id == source["artifact_id"]:
                        failures.append(f"{failure_prefix}_ref_unresolved:{source['name']}:{reference}")
                        continue
                    evidence_row = connection.execute(
                        "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                        (project_id, evidence_id),
                    ).fetchone()
                    if evidence_row is None or evidence_row["status"] not in {"CURRENT", "ACCEPTED"}:
                        failures.append(f"{failure_prefix}_ref_unresolved:{source['name']}:{reference}")
                        continue
                    if (
                        int(evidence_row["version"]) != binding.get("version")
                        or evidence_row["sha256"] != binding.get("sha256")
                        or evidence_row["producer_id"] != binding.get("producer_id")
                    ):
                        failures.append(f"{failure_prefix}_bytes_missing_or_digest_changed:{source['name']}:{reference}")
                        continue
                    evidence_path = self._engine._project_dir(project_id) / evidence_row["relative_path"]
                    if not evidence_path.is_file() or _sha256(evidence_path) != evidence_row["sha256"]:
                        failures.append(f"{failure_prefix}_bytes_missing_or_digest_changed:{source['name']}:{reference}")
                        continue
                    receipts.append({
                        "reference": reference,
                        "artifact_id": evidence_id,
                        "name": evidence_row["name"],
                        "version": int(evidence_row["version"]),
                        "sha256": evidence_row["sha256"],
                        "kind": evidence_row["kind"],
                        "media_type": evidence_row["media_type"],
                        "producer_id": evidence_row["producer_id"],
                        "verification": "LOCAL_ARTIFACT_ID_VERSION_SHA256_RECHECKED",
                    })
                return receipts

            for source in lineage:
                rights_evidence_bindings: list[dict[str, Any]] = []
                source_path = self._engine._project_dir(project_id) / source["relative_path"]
                if not source_path.is_file() or _sha256(source_path) != source["sha256"]:
                    failures.append(f"lineage_bytes_missing_or_changed:{source['artifact_id']}")
                if effective_require_rights and self._engine._is_media_artifact(source):
                    if source["rights_status"] not in allowed_rights:
                        failures.append(f"lineage_rights_not_cleared:{source['name']}:{source['artifact_id']}:{source['rights_status']}")
                    if require_rights_evidence:
                        metadata = _loads(source["metadata_json"], {})
                        refs = metadata.get("rights_evidence_refs", []) if isinstance(metadata, dict) else []
                        if not isinstance(refs, list) or not refs:
                            failures.append(f"lineage_rights_evidence_missing:{source['name']}:{source['artifact_id']}")
                        else:
                            rights_evidence_bindings = verify_rights_evidence_bindings(
                                source, failure_prefix="lineage_rights_evidence",
                            )
                            rights_evidence_verified_asset_ids.add(source["artifact_id"])
                    else:
                        rights_evidence_bindings = []
                else:
                    rights_evidence_bindings = []
                checked_lineage.append({
                    "artifact_id": source["artifact_id"], "name": source["name"],
                    "sha256": source["sha256"], "rights_status": source["rights_status"],
                    "rights_evidence": rights_evidence_bindings,
                })

            review_rows = connection.execute(
                "SELECT * FROM reviews WHERE project_id=? AND artifact_id=? AND artifact_digest=?",
                (project_id, artifact_id, artifact["sha256"]),
            ).fetchall()
            by_rubric: dict[str, list[sqlite3.Row]] = {}
            for review in review_rows:
                by_rubric.setdefault(review["rubric_id"], []).append(review)
            effective_rubrics = sorted(set(required_rubrics or []) | set(release_policy.get("required_review_rubrics", [])))
            if not effective_rubrics:
                raise ContractError("release_check requires at least one review rubric in the brief or command")

            review_contracts = release_policy.get("review_contracts", {})
            review_summary: dict[str, Any] = {}
            for rubric in effective_rubrics:
                rows = by_rubric.get(rubric, [])
                outcomes = [row["outcome"] for row in rows]
                if not outcomes or any(outcome != "PASS" for outcome in outcomes):
                    failures.append(f"required_review_missing_or_conflicting:{rubric}:{outcomes}")
                contract = review_contracts.get(rubric, {}) if isinstance(review_contracts, dict) else {}
                attestations: list[dict[str, Any]] = []
                reviewer_ids: set[str] = set()
                context_ids: set[str] = set()
                evidence_receipts: list[dict[str, Any]] = []
                def verify_review_evidence_binding(
                    binding: Any, reference: Any, *, rubric: str, review_id: str,
                    unresolved_code: str, digest_code: str,
                    failure_detail: str | None = None,
                ) -> dict[str, Any] | None:
                    detail = failure_detail or f"{rubric}:{review_id}:{reference}"
                    if (
                        not isinstance(binding, dict)
                        or binding.get("reference") != reference
                        or binding.get("resolved") is not True
                    ):
                        reason = binding.get("reason") if isinstance(binding, dict) else None
                        if reason == "BYTES_MISSING_OR_DIGEST_CHANGED":
                            failures.append(f"{digest_code}:{detail}")
                        else:
                            failures.append(f"{unresolved_code}:{detail}")
                        return None
                    evidence_id = binding.get("artifact_id")
                    if not isinstance(evidence_id, str) or not evidence_id:
                        failures.append(f"{unresolved_code}:{detail}")
                        return None
                    evidence_artifact = connection.execute(
                        "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                        (project_id, evidence_id),
                    ).fetchone()
                    if evidence_artifact is None or evidence_artifact["status"] not in {"CURRENT", "ACCEPTED"}:
                        failures.append(f"{unresolved_code}:{detail}")
                        return None
                    if (
                        evidence_artifact["version"] != binding.get("version")
                        or evidence_artifact["sha256"] != binding.get("sha256")
                        or evidence_artifact["producer_id"] != binding.get("producer_id")
                    ):
                        failures.append(f"{digest_code}:{detail}")
                        return None
                    evidence_path = self._engine._project_dir(project_id) / evidence_artifact["relative_path"]
                    if not evidence_path.is_file() or _sha256(evidence_path) != evidence_artifact["sha256"]:
                        failures.append(f"{digest_code}:{detail}")
                        return None
                    return {
                        "reference": reference,
                        "artifact_id": evidence_id,
                        "name": evidence_artifact["name"],
                        "version": int(evidence_artifact["version"]),
                        "sha256": evidence_artifact["sha256"],
                        "kind": evidence_artifact["kind"],
                        "media_type": evidence_artifact["media_type"],
                        "producer_id": evidence_artifact["producer_id"],
                        "verified_at_release": True,
                    }

                def review_event_payload(review_id: str) -> dict[str, Any]:
                    event_row = connection.execute(
                        """SELECT payload_json FROM events
                           WHERE project_id=? AND entity_type='REVIEW' AND entity_id=?
                             AND event_type='REVIEW_RECORDED'
                           ORDER BY event_no DESC LIMIT 1""",
                        (project_id, review_id),
                    ).fetchone()
                    event_payload = _loads(event_row["payload_json"], {}) if event_row else {}
                    return event_payload if isinstance(event_payload, dict) else {}

                for review in rows:
                    reviewer_ids.add(review["reviewer_id"])
                    dimensions = _loads(review["dimensions_json"], {})
                    review_evidence_receipts: list[dict[str, Any]] = []
                    finding_evidence_receipts: list[dict[str, Any]] = []
                    event_payload = review_event_payload(review["review_id"])
                    event_bindings = event_payload.get("evidence_bindings", {})
                    if not isinstance(event_bindings, dict):
                        event_bindings = {}
                    if contract.get("require_resolvable_evidence_refs"):
                        review_evidence = _loads(review["evidence_refs_json"], [])
                        review_snapshots = event_bindings.get("review_evidence", [])
                        if not isinstance(review_evidence, list) or not review_evidence:
                            failures.append(f"review_evidence_missing:{rubric}:{review['review_id']}")
                        elif not isinstance(review_snapshots, list) or len(review_snapshots) != len(review_evidence):
                            failures.append(f"review_evidence_digest_bindings_missing:{rubric}:{review['review_id']}")
                        else:
                            for index, reference in enumerate(review_evidence):
                                verified_binding = verify_review_evidence_binding(
                                    review_snapshots[index], reference, rubric=rubric,
                                    review_id=review["review_id"],
                                    unresolved_code="review_evidence_unresolved",
                                    digest_code="review_evidence_bytes_missing_or_digest_changed",
                                )
                                if verified_binding is not None:
                                    review_evidence_receipts.append(verified_binding)
                    attestation: dict[str, Any] = {}
                    if self._engine._review_contract_requires_execution(contract):
                        receipt = event_payload.get("execution_receipt")
                        expected = event_payload.get("execution_expected")
                        review_task_id = event_payload.get("review_task_id")
                        result_artifact_id = event_payload.get("review_result_artifact_id")
                        if not isinstance(receipt, dict) or not isinstance(expected, dict) or not review_task_id or not result_artifact_id:
                            failures.append(f"review_execution_attestation_missing:{rubric}:{review['review_id']}")
                        else:
                            task = connection.execute(
                                "SELECT * FROM tasks WHERE project_id=? AND task_id=?",
                                (project_id, review_task_id),
                            ).fetchone()
                            result_artifact = connection.execute(
                                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                                (project_id, result_artifact_id),
                            ).fetchone()
                            if (
                                task is None or task["kind"] != "review" or task["status"] != "COMPLETED"
                                or result_artifact is None or result_artifact["status"] not in {"CURRENT", "ACCEPTED"}
                                or result_artifact["produced_by_task"] != review_task_id
                                or result_artifact["kind"] != "review_report"
                                or result_artifact["media_type"] != "application/json"
                                or result_artifact["producer_id"] == artifact["producer_id"]
                            ):
                                failures.append(f"review_execution_task_or_report_stale:{rubric}:{review['review_id']}")
                            else:
                                result_path = self._engine._project_dir(project_id) / result_artifact["relative_path"]
                                if not result_path.is_file() or _sha256(result_path) != result_artifact["sha256"]:
                                    failures.append(f"review_execution_report_bytes_changed:{rubric}:{review['review_id']}")
                                else:
                                    task_result = _loads(task["result_json"], {})
                                    task_requirements = _loads(task["requirements_json"], {})
                                    task_contract = task_requirements.get("review_contract") if isinstance(task_requirements, dict) else None
                                    current_rubric_contracts = release_policy.get("review_contracts", {})
                                    current_rubric = current_rubric_contracts.get(rubric, {}) if isinstance(current_rubric_contracts, dict) else {}
                                    output_ids = task_result.get("outputs", {}) if isinstance(task_result, dict) else {}
                                    if not isinstance(output_ids, dict) or result_artifact_id not in set(output_ids.values()):
                                        failures.append(f"review_execution_report_not_task_output:{rubric}:{review['review_id']}")
                                    input_bindings = task_result.get("input_bindings", []) if isinstance(task_result, dict) else []
                                    declared_inputs = _loads(task["inputs_json"], [])
                                    if (
                                        not isinstance(input_bindings, list)
                                        or len(input_bindings) != len(declared_inputs)
                                        or not all(isinstance(item, dict) for item in input_bindings)
                                        or [item.get("name") for item in input_bindings] != declared_inputs
                                    ):
                                        failures.append(f"review_execution_task_inputs_do_not_match_claim:{rubric}:{review['review_id']}")
                                    try:
                                        report_payload = json.loads(result_path.read_text(encoding="utf-8"))
                                    except (OSError, json.JSONDecodeError):
                                        report_payload = None
                                    expected_report = {
                                        "schema_version": 1,
                                        "outcome": review["outcome"],
                                        "dimensions": _loads(review["dimensions_json"], {}),
                                        "evidence_refs": _loads(review["evidence_refs_json"], []),
                                        "notes": review["notes"],
                                    }
                                    if isinstance(current_rubric, dict) and current_rubric.get("required_media_inspection"):
                                        expected_report["media_inspection"] = (
                                            report_payload.get("media_inspection")
                                            if isinstance(report_payload, dict) else None
                                        )
                                    if report_payload != expected_report:
                                        failures.append(f"review_execution_report_review_record_mismatch:{rubric}:{review['review_id']}")
                                    input_bindings = task_result.get("input_bindings", []) if isinstance(task_result, dict) else []
                                    input_digests: dict[str, str] = {}
                                    inputs_current = isinstance(input_bindings, list) and bool(input_bindings)
                                    if isinstance(input_bindings, list):
                                        for binding in input_bindings:
                                            if not isinstance(binding, dict):
                                                inputs_current = False
                                                continue
                                            bound = connection.execute(
                                                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                                                (project_id, binding.get("artifact_id")),
                                            ).fetchone()
                                            if (
                                                bound is None or bound["status"] not in {"CURRENT", "ACCEPTED"}
                                                or bound["name"] != binding.get("name")
                                                or int(bound["version"]) != binding.get("version")
                                                or bound["sha256"] != binding.get("sha256")
                                            ):
                                                inputs_current = False
                                                continue
                                            bound_path = self._engine._project_dir(project_id) / bound["relative_path"]
                                            if not bound_path.is_file() or _sha256(bound_path) != bound["sha256"]:
                                                inputs_current = False
                                                continue
                                            input_digests[binding["name"]] = binding["sha256"]
                                    subject_binding = next(
                                        (item for item in input_bindings if isinstance(item, dict) and item.get("name") == artifact["name"]),
                                        None,
                                    ) if isinstance(input_bindings, list) else None
                                    if (
                                        not inputs_current or not isinstance(subject_binding, dict)
                                        or subject_binding.get("artifact_id") != artifact["artifact_id"]
                                        or subject_binding.get("sha256") != artifact["sha256"]
                                    ):
                                        failures.append(f"review_execution_inputs_stale_or_incomplete:{rubric}:{review['review_id']}")
                                    try:
                                        if not isinstance(task_contract, dict) or not isinstance(current_rubric, dict):
                                            raise ReviewExecutionError("current owner review contract is missing")
                                        if (
                                            task_contract.get("rubric_id") != rubric
                                            or task_contract.get("reviewer_id") != review["reviewer_id"]
                                            or task_contract.get("subject_artifact") != artifact["name"]
                                        ):
                                            raise ReviewExecutionError("review task identity no longer matches the reviewed artifact and reviewer")
                                        for field in ("reviewer_kind", "execution_mode", "blind_review", "required_media_inspection"):
                                            if task_contract.get(field) != current_rubric.get(field):
                                                raise ReviewExecutionError(f"review task {field} no longer matches the owner rubric")
                                        expected_executors = {
                                            "HUMAN": {"human"}, "AI": {"agent", "external"}, "TOOL": {"tool"},
                                        }.get(current_rubric.get("reviewer_kind"))
                                        if (
                                            current_rubric.get("reviewer_kind") not in {"HUMAN", "AI", "TOOL"}
                                            or not isinstance(current_rubric.get("execution_mode"), str)
                                            or not current_rubric.get("execution_mode")
                                            or (expected_executors and task["executor"] not in expected_executors)
                                        ):
                                            raise ReviewExecutionError("review task executor is not authorized by the current owner rubric")
                                        packet = build_review_packet(
                                            project_id=project_id, task_id=review_task_id,
                                            task_contract=task_contract, rubric_contract=current_rubric,
                                            input_bindings=input_bindings,
                                        )
                                        recomputed_expected = {
                                            "review_task_id": review_task_id,
                                            "review_contract_digest": review_contract_digest(task_contract, current_rubric),
                                            "reviewer_id": review["reviewer_id"],
                                            "reviewer_kind": current_rubric.get("reviewer_kind"),
                                            "execution_mode": current_rubric.get("execution_mode"),
                                            "packet_digest": digest_json(packet),
                                            "result_digest": result_artifact["sha256"],
                                            "input_digests": input_digests,
                                            "blind_review": bool(current_rubric.get("blind_review", False)),
                                            "required_media_inspection": current_rubric.get("required_media_inspection"),
                                            "media_inspection": report_payload.get("media_inspection") if current_rubric.get("required_media_inspection") and isinstance(report_payload, dict) else None,
                                            "reviewed_artifact_sha256": artifact["sha256"],
                                            "review_result_sha256": result_artifact["sha256"],
                                            "executor_id": result_artifact["producer_id"],
                                        }
                                        if expected != recomputed_expected:
                                            raise ReviewExecutionError("review execution expectation no longer matches current task, rubric, subject and input versions")
                                        verified_execution = self._engine.review_trust_registry.verify(
                                            receipt, expected=recomputed_expected,
                                        )
                                        nonce_row = connection.execute(
                                            "SELECT review_id FROM review_execution_nonces WHERE project_id=? AND nonce=?",
                                            (project_id, verified_execution["nonce"]),
                                        ).fetchone()
                                        if nonce_row is None or nonce_row["review_id"] != review["review_id"]:
                                            failures.append(f"review_execution_nonce_binding_invalid:{rubric}:{review['review_id']}")
                                        else:
                                            attestation = {
                                                "reviewer_kind": verified_execution["reviewer_kind"],
                                                "execution_mode": verified_execution["execution_mode"],
                                                "blind_review": bool(current_rubric.get("blind_review", False)),
                                                "inspected_artifact_digest": artifact["sha256"],
                                                "context_id": verified_execution["context_id"],
                                                "verified_execution": verified_execution,
                                            }
                                            context_ids.add(verified_execution["context_id"])
                                    except ReviewExecutionError as exc:
                                        failures.append(f"review_execution_attestation_invalid:{rubric}:{review['review_id']}:{exc}")
                    attestations.append(attestation)
                    required_kind = contract.get("reviewer_kind")
                    if required_kind and attestation.get("reviewer_kind") != required_kind:
                        failures.append(f"reviewer_kind_mismatch:{rubric}:{review['review_id']}:{attestation.get('reviewer_kind')}")
                    required_mode = contract.get("execution_mode")
                    if required_mode and attestation.get("execution_mode") != required_mode:
                        failures.append(f"review_execution_mode_mismatch:{rubric}:{review['review_id']}:{attestation.get('execution_mode')}")
                    if contract.get("blind_review") and attestation.get("blind_review") is not True:
                        failures.append(f"blind_review_attestation_missing:{rubric}:{review['review_id']}")
                    if contract.get("require_digest_attestation") and attestation.get("inspected_artifact_digest") != artifact["sha256"]:
                        failures.append(f"review_inspected_digest_mismatch:{rubric}:{review['review_id']}")
                    if contract.get("require_context_id") and not attestation.get("context_id"):
                        failures.append(f"review_context_id_missing:{rubric}:{review['review_id']}")
                    scorecard = dimensions.get("scorecard", dimensions.get("scores", {})) if isinstance(dimensions, dict) else {}
                    if not isinstance(scorecard, dict):
                        scorecard = {}
                    for dimension, floor in contract.get("dimension_floors", {}).items():
                        try:
                            score = float(scorecard[dimension])
                        except (KeyError, TypeError, ValueError):
                            failures.append(f"review_score_missing:{rubric}:{dimension}:{review['review_id']}")
                            continue
                        if not math.isfinite(score):
                            failures.append(f"review_score_not_finite:{rubric}:{dimension}:{review['review_id']}")
                            continue
                        try:
                            floor_value = float(floor)
                        except (TypeError, ValueError):
                            failures.append(f"review_floor_invalid:{rubric}:{dimension}")
                            continue
                        if not math.isfinite(floor_value):
                            failures.append(f"review_floor_not_finite:{rubric}:{dimension}")
                            continue
                        if score < floor_value:
                            failures.append(f"review_score_below_floor:{rubric}:{dimension}:{score:g}<{floor_value:g}")
                    score_dimensions = contract.get("score_dimensions", [])
                    if score_dimensions:
                        try:
                            values = [float(scorecard[name]) for name in score_dimensions]
                            if not all(math.isfinite(value) for value in values):
                                failures.append(f"review_scorecard_not_finite:{rubric}:{review['review_id']}")
                            else:
                                average = sum(values) / len(values)
                                minimum_average = float(contract.get("min_average", 0))
                                if not math.isfinite(minimum_average):
                                    failures.append(f"review_minimum_average_not_finite:{rubric}:{review['review_id']}")
                                elif average < minimum_average:
                                    failures.append(f"review_average_below_floor:{rubric}:{average:.2f}<{minimum_average:g}")
                        except (KeyError, TypeError, ValueError, ZeroDivisionError):
                            failures.append(f"review_scorecard_incomplete:{rubric}:{review['review_id']}")
                    min_findings = int(contract.get("min_findings", 0))
                    findings = dimensions.get("findings", []) if isinstance(dimensions, dict) else []
                    if min_findings and (not isinstance(findings, list) or len(findings) < min_findings):
                        failures.append(f"review_findings_below_minimum:{rubric}:{len(findings) if isinstance(findings, list) else 0}<{min_findings}")
                    # Validate every supplied finding even when the minimum count is not met.
                    # A short Red Team report must not hide unresolved or untraceable evidence.
                    if isinstance(findings, list):
                        for index, finding in enumerate(findings):
                            if not isinstance(finding, dict) or not finding.get("finding"):
                                failures.append(f"review_finding_incomplete:{rubric}:{index}")
                                continue
                            if contract.get("require_evidence_per_finding") and not finding.get("evidence_ref"):
                                failures.append(f"review_finding_evidence_missing:{rubric}:{index}")
                            if contract.get("require_resolvable_evidence_refs") and finding.get("evidence_ref"):
                                finding_snapshots = event_bindings.get("finding_evidence", [])
                                snapshot = next(
                                    (item for item in finding_snapshots
                                     if isinstance(item, dict) and item.get("finding_index") == index),
                                    None,
                                ) if isinstance(finding_snapshots, list) else None
                                verified_binding = verify_review_evidence_binding(
                                    snapshot, finding["evidence_ref"], rubric=rubric,
                                    review_id=review["review_id"],
                                    unresolved_code="review_finding_evidence_unresolved",
                                    digest_code="review_finding_evidence_bytes_missing_or_digest_changed",
                                    failure_detail=f"{rubric}:{index}:{finding['evidence_ref']}",
                                )
                                if verified_binding is not None:
                                    finding_evidence_receipts.append({
                                        "finding_index": index,
                                        **verified_binding,
                                    })
                            if contract.get("require_disposition_per_finding") and finding.get("disposition") not in {
                                "UNRESOLVED", "MITIGATED", "ACCEPTED", "NOT_APPLICABLE",
                            }:
                                failures.append(f"review_finding_disposition_missing:{rubric}:{index}")
                            severity = str(finding.get("severity", "MEDIUM")).upper()
                            disposition = finding.get("disposition")
                            if disposition == "UNRESOLVED" and severity in {"CRITICAL", "HIGH"} and review["outcome"] == "PASS":
                                failures.append(f"red_team_unresolved_high_risk:{rubric}:{index}")
                    evidence_receipts.append({
                        "review_id": review["review_id"],
                        "review_evidence": review_evidence_receipts,
                        "finding_evidence": finding_evidence_receipts,
                    })
                if contract.get("min_reviewers", 0) and len(reviewer_ids) < int(contract["min_reviewers"]):
                    failures.append(f"reviewer_quorum_missing:{rubric}:{len(reviewer_ids)}<{int(contract['min_reviewers'])}")
                if contract.get("distinct_contexts") and len(context_ids) < len(rows):
                    failures.append(f"review_contexts_not_independent:{rubric}")
                review_summary[rubric] = {
                    "review_ids": [row["review_id"] for row in rows],
                    "reviewer_ids": sorted(reviewer_ids),
                    "outcomes": outcomes,
                    "attestations": attestations,
                    "evidence_receipts": evidence_receipts,
                }

            supplied_evidence = set(evidence_refs or [])
            required_evidence = set(release_policy.get("required_evidence_refs", []))
            missing_evidence = sorted(required_evidence - supplied_evidence)
            if missing_evidence:
                failures.append(f"release_evidence_missing:{missing_evidence}")

            for evidence_name in release_policy.get("required_evidence_artifact_names", []):
                evidence_artifact = self._engine._artifact_by_name(connection, project_id, evidence_name)
                if evidence_artifact is None:
                    failures.append(f"required_evidence_artifact_missing:{evidence_name}")
                    continue
                evidence_path = self._engine._project_dir(project_id) / evidence_artifact["relative_path"]
                if not evidence_path.is_file() or _sha256(evidence_path) != evidence_artifact["sha256"]:
                    failures.append(f"required_evidence_artifact_bytes_changed:{evidence_name}")
                if evidence_artifact["kind"] not in {"evidence", "document", "rights_record", "qa_report", "review_report", "decision", "timeline", "domain_state"}:
                    failures.append(f"required_evidence_artifact_wrong_kind:{evidence_name}:{evidence_artifact['kind']}")

            required_artifacts = list(release_policy.get("required_artifact_names", []))
            for required_name in required_artifacts:
                required_artifact = self._engine._artifact_by_name(connection, project_id, required_name)
                if required_artifact is None:
                    failures.append(f"required_deliverable_missing:{required_name}")
                else:
                    required_path = self._engine._project_dir(project_id) / required_artifact["relative_path"]
                    if not required_path.is_file() or _sha256(required_path) != required_artifact["sha256"]:
                        failures.append(f"required_deliverable_bytes_changed:{required_name}")
                    if (
                        effective_require_rights
                        and required_artifact["rights_status"] != "NOT_APPLICABLE"
                        and required_artifact["rights_status"] not in allowed_rights
                    ):
                        failures.append(f"required_deliverable_rights_not_cleared:{required_name}:{required_artifact['rights_status']}")

            required_assets = list(release_policy.get("required_asset_names", []))
            for asset_name in required_assets:
                source_asset = self._engine._artifact_by_name(connection, project_id, asset_name)
                if source_asset is None:
                    failures.append(f"required_source_asset_missing:{asset_name}")
                else:
                    source_path = self._engine._project_dir(project_id) / source_asset["relative_path"]
                    if not source_path.is_file() or _sha256(source_path) != source_asset["sha256"]:
                        failures.append(f"required_source_asset_bytes_changed:{asset_name}")
                    if effective_require_rights and source_asset["rights_status"] not in allowed_rights:
                        failures.append(f"required_source_asset_rights_not_cleared:{asset_name}:{source_asset['rights_status']}")
                    if source_asset["artifact_id"] not in {row["artifact_id"] for row in lineage}:
                        failures.append(f"required_source_asset_not_in_final_lineage:{asset_name}")
                    if require_rights_evidence:
                        metadata = _loads(source_asset["metadata_json"], {})
                        refs = metadata.get("rights_evidence_refs", []) if isinstance(metadata, dict) else []
                        if not isinstance(refs, list) or not refs:
                            failures.append(f"required_source_asset_rights_evidence_missing:{asset_name}")
                        elif source_asset["artifact_id"] not in rights_evidence_verified_asset_ids:
                            verify_rights_evidence_bindings(
                                source_asset, failure_prefix="required_source_asset_rights_evidence",
                            )
                            rights_evidence_verified_asset_ids.add(source_asset["artifact_id"])

            qa_receipt: dict[str, Any] | None = None
            requires_technical_qa = release_guards.require_technical_qa
            if requires_technical_qa:
                qa_name = release_policy.get("technical_qa_artifact_name", "technical-qa-receipt")
                qa_artifact = self._engine._artifact_by_name(connection, project_id, qa_name)
                if qa_artifact is None:
                    failures.append(f"technical_qa_receipt_missing:{qa_name}")
                else:
                    qa_path = self._engine._project_dir(project_id) / qa_artifact["relative_path"]
                    try:
                        qa_payload = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path.is_file() else {}
                    except (OSError, json.JSONDecodeError):
                        qa_payload = {}
                    if not qa_path.is_file() or _sha256(qa_path) != qa_artifact["sha256"]:
                        failures.append("technical_qa_receipt_bytes_missing_or_changed")
                    if not isinstance(qa_payload, dict):
                        qa_payload = {}
                    if qa_artifact["kind"] != "qa_report":
                        failures.append(f"technical_qa_artifact_wrong_kind:{qa_artifact['kind']}")
                    qa_metadata = qa_payload.get("metadata", {})
                    if not isinstance(qa_metadata, dict):
                        qa_metadata = {}
                    if qa_metadata.get("checker") != "ffmpeg-ffprobe-v1.0":
                        failures.append("technical_qa_checker_unrecognized")
                    if qa_payload.get("hard_pass") is not True or qa_payload.get("hard_failures"):
                        failures.append("technical_qa_hard_pass_missing")
                    if qa_payload.get("media_sha256") != artifact["sha256"]:
                        failures.append("technical_qa_target_digest_mismatch")
                    if qa_payload.get("input_artifact_id") != artifact_id:
                        failures.append("technical_qa_target_artifact_id_mismatch")
                    checks = qa_payload.get("checks", [])
                    if not isinstance(checks, list):
                        checks = []
                    check_statuses = {item.get("check_id"): item.get("status") for item in checks if isinstance(item, dict)}
                    required_check_ids = {
                        "video_stream", "stream_duration_match", "true_peak", "black_frames", "full_decode",
                    } | set(release_policy.get("technical_qa_required_check_ids", []))
                    missing_checks = sorted(required_check_ids - set(check_statuses))
                    failed_checks = sorted(key for key, status in check_statuses.items() if status != "PASS")
                    if missing_checks:
                        failures.append(f"technical_qa_checks_missing:{missing_checks}")
                    if failed_checks:
                        failures.append(f"technical_qa_checks_failed:{failed_checks}")
                    metadata = _loads(qa_artifact["metadata_json"], {})
                    if metadata.get("hard_pass") is not True or metadata.get("media_sha256") != artifact["sha256"]:
                        failures.append("technical_qa_artifact_metadata_mismatch")
                    qa_receipt = {
                        "artifact_id": qa_artifact["artifact_id"], "sha256": qa_artifact["sha256"],
                        "media_sha256": qa_payload.get("media_sha256"), "hard_pass": qa_payload.get("hard_pass"),
                        "checks": check_statuses,
                    }

            rubric_contracts = release_policy.get("review_contracts", {})
            if not isinstance(rubric_contracts, dict):
                rubric_contracts = {}
            high_assurance_rubrics = [
                rubric for rubric in effective_rubrics
                if self._engine._review_contract_requires_execution(rubric_contracts.get(rubric, {}))
            ]
            high_assurance_reviews = [
                attestation
                for rubric in high_assurance_rubrics
                for attestation in review_summary.get(rubric, {}).get("attestations", [])
            ]
            high_assurance_review_count = sum(
                len(review_summary.get(rubric, {}).get("review_ids", []))
                for rubric in high_assurance_rubrics
            )
            high_assurance_verified_count = sum(
                1 for attestation in high_assurance_reviews
                if isinstance(attestation, dict)
                and isinstance(attestation.get("verified_execution"), dict)
                and attestation["verified_execution"].get("verified") is True
            )
            if not high_assurance_rubrics:
                high_assurance_status = "NOT_REQUIRED"
            elif (
                high_assurance_review_count > 0
                and high_assurance_verified_count == high_assurance_review_count
                and all(review_summary.get(rubric, {}).get("review_ids") for rubric in high_assurance_rubrics)
            ):
                high_assurance_status = "VERIFIED"
            else:
                high_assurance_status = "BLOCKED"

            receipt = {
                "artifact_id": artifact_id, "artifact_digest": artifact["sha256"],
                "deliverable_binding": deliverable_binding,
                "acceptance_scope": "INDIVIDUAL_ARTIFACT_ONLY",
                "external_publication_authorized": False,
                "whole_demand_accepted": False,
                "owner_outcome_verified": False,
                "required_rubrics": effective_rubrics, "review_summary": review_summary,
                "required_artifacts": required_artifacts,
                "required_assets": required_assets,
                "required_evidence_artifacts": list(release_policy.get("required_evidence_artifact_names", [])),
                "evidence_refs": sorted(supplied_evidence),
                "rights_status": artifact["rights_status"],
                "artifact_lineage": checked_lineage,
                "technical_qa": qa_receipt,
                "rights_evidence_required": require_rights_evidence,
                "failures": failures, "pass": not failures,
                "review_attestation_limit": "Low-assurance reviews retain metadata-only identity; high-assurance rubrics require a signed DSSE/in-toto Ed25519 execution receipt verified at recording and release.",
                "review_execution_verification": {
                    "high_assurance": high_assurance_status,
                    "ordinary_review": "LOW_ASSURANCE_METADATA_ONLY",
                    "trusted_executor_count": len(self._engine.review_trust_registry.config.get("trusted_executors", {})),
                    "high_assurance_review_count": high_assurance_review_count,
                    "high_assurance_verified_count": high_assurance_verified_count,
                },
            }
            if not failures:
                connection.execute("UPDATE artifacts SET status='ACCEPTED' WHERE project_id=? AND artifact_id=?", (project_id, artifact_id))
                self._engine._event(connection, project_id, "ARTIFACT", artifact_id, "ARTIFACT_RELEASE_ACCEPTED", receipt)
            else:
                self._engine._event(connection, project_id, "ARTIFACT", artifact_id, "ARTIFACT_RELEASE_BLOCKED", receipt)
            connection.commit()
            return receipt

