"""Optional article-specific evidence dependency inspection.

No scheduler, ledger, source authentication, semantic evaluator or release grant.
Inputs are declarations by an editor, not proof of actual research or review.
"""
from __future__ import annotations

import hashlib
import json
from collections import deque
from typing import Any, Mapping


def article_digest(article: Mapping[str, Any]) -> str:
    """Bind the trace to the exact JSON article contract, excluding the trace."""
    payload = {k: v for k, v in article.items() if k != "editorial_trace"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _rows(value: Any, field: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(v, Mapping) for v in value):
        raise ValueError(f"{field} must be a list of objects")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value


def _refs(value: Any, field: str) -> set[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    values = [_text(v, field) for v in value]
    if len(set(values)) != len(values):
        raise ValueError(f"{field} contains duplicate references")
    return set(values)


def inspect_editorial_trace(article: Mapping[str, Any]) -> dict[str, Any]:
    """Check declared evidence coverage and reopen affected descendants.

    A finding targets the earliest known contradicted premise, not a fixed
    stage. Different article types may declare different dependency graphs.
    Callers must revalidate external source revisions independently and submit
    changed_node_ids; this function cannot observe external changes.
    """
    trace = article.get("editorial_trace")
    digest = article_digest(article)
    out = {
        "article_sha256": digest, "semantic_quality_verified": False,
        "source_authenticity_verified": False, "independent_review_verified": False,
        "owner_outcome_verified": False, "publication_authorized": False,
        "method_promoted": False,
    }
    if trace is None:
        return {**out, "status": "TRACE_NOT_SUPPLIED"}
    if not isinstance(trace, Mapping) or trace.get("schema_version") != "1.0":
        raise ValueError("editorial_trace requires schema_version 1.0")
    if trace.get("article_sha256") != digest:
        return {**out, "status": "STALE_ARTICLE_TRACE",
                "action": "rebind and reassess against the current article; do not reuse old review"}
    claims = {row["claim_id"] for row in article.get("factual_claims", [])}
    sections = {row["section_id"] for row in article.get("sections", [])}
    nodes = {}
    covered_claims, covered_sections = set(), set()
    for row in _rows(trace.get("nodes"), "nodes"):
        key = _text(row.get("id"), "node id")
        if key in nodes:
            raise ValueError("duplicate editorial node")
        _text(row.get("purpose"), "node purpose")
        state = row.get("state")
        if state not in ("OPEN", "CANDIDATE", "SUPPORTED", "CONTRADICTED"):
            raise ValueError("unknown editorial node state")
        deps = _refs(row.get("depends_on", []), "depends_on")
        evidence = _refs(row.get("evidence_refs", []), "evidence_refs")
        if state == "SUPPORTED" and not evidence:
            raise ValueError("SUPPORTED declaration requires evidence references")
        c = _refs(row.get("claim_ids", []), "claim_ids")
        s = _refs(row.get("section_ids", []), "section_ids")
        if not c <= claims or not s <= sections:
            raise ValueError("node references unknown article claim or section")
        covered_claims.update(c)
        covered_sections.update(s)
        nodes[key] = (state, deps)
    if not nodes:
        raise ValueError("editorial trace requires at least one relevant node")
    children = {key: set() for key in nodes}
    remaining = {}
    for key, (_, deps) in nodes.items():
        if not deps <= nodes.keys():
            raise ValueError("unresolved editorial dependency")
        remaining[key] = len(deps)
        for dep in deps:
            children[dep].add(key)
    ready = deque(k for k, n in remaining.items() if not n)
    visited = 0
    while ready:
        key = ready.popleft()
        visited += 1
        for child in children[key]:
            remaining[child] -= 1
            if not remaining[child]:
                ready.append(child)
    if visited != len(nodes):
        raise ValueError("cyclic editorial dependency")
    changed = _refs(trace.get("changed_node_ids", []), "changed_node_ids")
    if not changed <= nodes.keys():
        raise ValueError("unknown changed node")
    roots = changed | {k for k, (s, _) in nodes.items() if s != "SUPPORTED"}
    findings, advisory = set(), []
    for row in _rows(trace.get("findings", []), "findings"):
        key = _text(row.get("id"), "finding id")
        if key in findings:
            raise ValueError("duplicate editorial finding")
        findings.add(key)
        target = _text(row.get("target_id"), "finding target")
        if target not in nodes:
            raise ValueError("finding targets unknown node")
        _text(row.get("problem"), "finding problem")
        if not _refs(row.get("evidence_refs", []), "finding evidence_refs"):
            raise ValueError("finding needs an evidence reference")
        state, severity = row.get("state"), row.get("severity")
        if state not in ("OPEN", "RESOLVED") or severity not in ("BLOCKING", "ADVISORY"):
            raise ValueError("invalid finding state or severity")
        if state == "RESOLVED":
            _text(row.get("resolution_ref"), "resolution_ref")
        elif severity == "BLOCKING":
            roots.add(target)
        else:
            advisory.append(key)
    affected = set(roots)
    pending = deque(roots)
    while pending:
        for child in children[pending.popleft()]:
            if child not in affected:
                affected.add(child)
                pending.append(child)
    # Optional observations bind a method revision to a material decision in
    # this article. They remain editor declarations, never proof of use/effect.
    applications = []
    seen_applications = set()
    for row in _rows(trace.get("method_observations", []), "method_observations"):
        key = _text(row.get("id"), "method observation id")
        if key in seen_applications:
            raise ValueError("duplicate method observation")
        seen_applications.add(key)
        target = _text(row.get("target_id"), "method target")
        if target not in nodes:
            raise ValueError("method observation targets unknown node")
        method_ref = _text(row.get("method_ref"), "method_ref")
        revision = _text(row.get("method_sha256"), "method_sha256")
        if len(revision) != 64 or any(ch not in "0123456789abcdef" for ch in revision):
            raise ValueError("method_sha256 must be a lowercase SHA-256 digest")
        disposition = row.get("disposition")
        if disposition not in ("CONSULTED_ONLY", "CHANGE_DECLARED", "RETAINED_AFTER_TEST", "REJECTED"):
            raise ValueError("invalid method observation disposition")
        reason = _text(row.get("reason"), "method observation reason")
        refs = _refs(row.get("evidence_refs", []), "method evidence_refs")
        if not refs:
            raise ValueError("method observation requires evidence references")
        if disposition in ("CHANGE_DECLARED", "RETAINED_AFTER_TEST"):
            before = _text(row.get("before"), "method decision before")
            after = _text(row.get("after"), "method decision after")
            _text(row.get("result_ref"), "method result_ref")
            if disposition == "CHANGE_DECLARED" and before.strip() == after.strip():
                raise ValueError("declared method change requires different before and after")
            if disposition == "RETAINED_AFTER_TEST" and before.strip() != after.strip():
                raise ValueError("retained decision requires matching before and after")
            if disposition == "RETAINED_AFTER_TEST":
                _text(row.get("test_ref"), "method test_ref")
        applications.append({
            "id": key, "target_id": target, "method_ref": method_ref,
            "method_sha256": revision, "disposition": disposition,
            "status": "REOPEN_REQUIRED" if target in affected else "DECLARED_ONLY",
            "method_bytes_verified": False, "application_verified": False,
            "improvement_verified": False,
        })
    missing_claims = sorted(claims - covered_claims)
    missing_sections = sorted(sections - covered_sections)
    return {
        **out,
        "status": ("REOPEN_REQUIRED" if affected or missing_claims or missing_sections
                   else "DECLARED_TRACE_CONSISTENT_REVIEW_PENDING"),
        "reopen_roots": sorted(roots), "affected_nodes": sorted(affected),
        "unaffected_nodes": sorted(nodes.keys() - affected),
        "unmapped_declared_claim_ids": missing_claims,
        "unmapped_declared_section_ids": missing_sections,
        "open_advisory_finding_ids": sorted(advisory),
        "method_observations": applications,
        "coverage_limit": "Only declared claims/sections and dependencies checked; no semantic completeness proof.",
    }
