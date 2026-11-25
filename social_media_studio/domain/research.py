"""Deterministic source evidence inspection, not semantic truth certification.

Inputs are current, artifact-bound text sources. A verified quoted passage
proves only that those exact bytes occur in a registered source version.
The caller's SUPPORTS/CONTRADICTS label is not an independent factual verdict.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping


def inspect_research_evidence(
    bundle: Mapping[str, Any], inputs: Mapping[str, Mapping[str, Any]], *,
    manifest_input: str,
) -> dict[str, Any]:
    if bundle.get("schema_version") != "1.0" or not isinstance(bundle.get("claims"), list) or not bundle["claims"]:
        raise ValueError("research bundle requires schema_version 1.0 and non-empty claims")
    checks: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in bundle["claims"]:
        if not isinstance(item, Mapping) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("every research claim needs an exact id")
        if item["id"] in ids:
            raise ValueError("duplicate research claim id")
        ids.add(item["id"])
        if not isinstance(item.get("statement"), str) or not item["statement"].strip():
            raise ValueError("research claim statement must be non-empty")
        kind = item.get("kind")
        if kind not in {"FACT", "ESTIMATE", "OPINION", "SATIRE", "FICTION"}:
            raise ValueError("claim kind must distinguish fact/estimate/opinion/satire/fiction")
        records = item.get("evidence", [])
        if not isinstance(records, list):
            raise ValueError("claim evidence must be a list")
        sources: list[dict[str, Any]] = []
        issues: list[str] = []
        for evidence in records:
            if not isinstance(evidence, Mapping):
                raise ValueError("evidence record must be an object")
            name = evidence.get("source_input")
            excerpt = evidence.get("excerpt")
            stance = evidence.get("stance")
            if not isinstance(name, str) or name == manifest_input or name not in inputs:
                issues.append("SOURCE_NOT_DECLARED_AS_SEPARATE_INPUT")
                continue
            if stance not in {"SUPPORTS", "CONTRADICTS", "CONTEXT"}:
                issues.append("UNSUPPORTED_STANCE_LABEL")
                continue
            if not isinstance(excerpt, str) or not excerpt.strip() or len(excerpt) > 5000:
                issues.append("INVALID_SOURCE_EXCERPT")
                continue
            source = inputs[name]
            path = Path(str(source["path"]))
            if not path.is_file() or path.stat().st_size > 2_000_000:
                issues.append("SOURCE_MISSING_OR_TOO_LARGE_FOR_TEXT_INSPECTION")
                continue
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != source.get("sha256"):
                issues.append("SOURCE_DIGEST_MISMATCH")
                continue
            try:
                body = raw.decode("utf-8")
            except UnicodeDecodeError:
                issues.append("SOURCE_IS_NOT_VERIFIABLE_UTF8_TEXT")
                continue
            if excerpt not in body:
                issues.append("QUOTED_EXCERPT_NOT_IN_SOURCE")
                continue
            sources.append({
                "source_input": name, "artifact_id": source["artifact_id"],
                "sha256": source["sha256"], "reported_stance": stance,
                "byte_excerpt_match": True, "source_truth_independently_verified": False,
            })
        supporting = [s for s in sources if s["reported_stance"] == "SUPPORTS"]
        opposing = [s for s in sources if s["reported_stance"] == "CONTRADICTS"]
        if kind in {"FACT", "ESTIMATE"} and not supporting:
            issues.append("FACT_OR_ESTIMATE_MISSING_GROUNDED_SUPPORT")
        checks.append({
            "claim_id": item["id"], "kind": kind,
            "evidence": sources, "issues": sorted(set(issues)),
            "source_label_conflict": bool(supporting and opposing),
            "source_quote_coverage": bool(supporting) if kind in {"FACT", "ESTIMATE"} else not issues,
            "factual_truth_verified": False,
        })
    return {
        "schema_version": "1.0",
        "assurance": "SOURCE_BYTES_AND_QUOTED_EXCERPT_VERIFIED_ONLY",
        "claims": checks,
        "evidence_coverage_pass": all(not x["issues"] for x in checks),
        "semantic_fact_check_performed": False,
        "external_search_performed": False,
        "independent_owner_acceptance": False,
        "method_promotion_authorized": False,
    }
