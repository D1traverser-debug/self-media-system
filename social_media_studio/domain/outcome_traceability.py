"""Trace actual owner obligations through declared deliverables, not task guesses.

A trace is a verification agenda tied to current briefing bytes, not signed
source authenticity, independent craft review or an owner's acceptance.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .assurance import CRITERIA
from .demand import inspect_demand


def trace_owner_requirements(brief: Mapping[str, Any], observed_variants: list[dict[str, Any]]) -> dict[str, Any]:
    source = dict(brief)
    demand = inspect_demand(source, durable=True)
    typed = demand["typed_deliverables"]
    if typed is None:
        return {"status": "UNTYPED_NOT_TRACEABLE", "owner_outcome_verified": False}
    declared = {d["id"]: d for d in typed["deliverables"]}
    expected = {(d["id"], v["id"]) for d in declared.values()
                for v in (d["variants"] or [{"id": d["id"]}])}
    observed_keys = [(v["deliverable_id"], v["variant_id"]) for v in observed_variants]
    if len(set(observed_keys)) != len(observed_keys):
        raise ValueError("duplicate delivered variant in owner requirement trace")
    if set(observed_keys) != expected:
        raise ValueError("owner requirement trace cannot drop or invent declared variants")

    rows = []
    for variant in observed_variants:
        owner_id = variant["deliverable_id"]
        spec = declared[owner_id]
        applicable_clauses = [
            {"clause_id": clause["id"], "kind": clause["kind"],
             "source_ref": clause["source_ref"], "required_text": clause["text"],
             "verification": "INDEPENDENT_SEMANTIC_REVIEW_PENDING"}
            for clause in demand["clauses"]
            if not clause["deliverable_refs"] or owner_id in clause["deliverable_refs"]
        ]
        quality_dimensions = [
            {"criterion_id": dimension, "verification": "ACTUAL_RESULT_REVIEW_PENDING"}
            for dimension in CRITERIA[spec["type"]]
        ]
        observed_digests = [
            {"artifact_id": item["artifact_id"], "sha256": item["sha256"],
             "technical_status": item["conformance"]["status"]}
            for item in variant.get("candidates", [])
        ]
        rows.append({
            "deliverable_id": owner_id, "variant_id": variant["variant_id"],
            "type": spec["type"],
            "source_refs": list(spec["source_refs"]),
            "owner_clauses": applicable_clauses,
            "declared_acceptance": dict(spec["acceptance"]),
            "declared_constraints": dict(spec["constraints"]),
            "declared_prohibitions": list(spec["prohibitions"]),
            "communication_intent": spec.get("communication_intent"),
            "professional_criteria": quality_dimensions,
            "actual_artifact_bindings": observed_digests,
            "independent_result_review_verified": False,
            "owner_acceptance_verified": False,
        })

    raw = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    unresolved = [c["id"] for c in demand["clauses"] if c["kind"] == "UNRESOLVED_QUESTION"]
    return {
        "status": "DECLARED_OBLIGATIONS_MAPPED_NOT_VERIFIED",
        "brief_sha256": hashlib.sha256(raw).hexdigest(),
        "owner_source_contract_status": demand["contract_status"],
        "owner_original_source_authenticated": False,
        "semantic_completeness_verified": False,
        "current_declared_variant_count": len(expected),
        "mapped_variant_count": len(rows),
        "outstanding_unresolved_clause_ids": unresolved,
        "owner_amendments_for_reconciliation": demand["amendments"],
        "obligations": rows,
        "every_variant_receives_source_scoped_obligations": True,
        "independent_quality_review_verified": False,
        "owner_outcome_verified": False,
        "external_publication_authorized": False,
    }
