"""Single pure declaration boundary for current owner demands.

The existing brief is the authority and the existing project event history is
the revision ledger. No inferred intent, permission grant or new scheduler.
"""
from __future__ import annotations

import re
from typing import Any

from .contracts import ContentContractError, inspect_declared_deliverables

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
CLAUSE_KINDS = frozenset({
    "OUTCOME", "HARD_CONSTRAINT", "PREFERENCE", "PROHIBITION",
    "ACCEPTANCE", "AUTHORIZATION_LIMIT", "UNRESOLVED_QUESTION",
})


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContentContractError(f"{label} must be nonempty text")
    return value


def _strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ContentContractError(f"{label} must be an array")
    result = [_text(item, label) for item in value]
    if len(result) != len(set(result)):
        raise ContentContractError(f"{label} must not contain duplicates")
    return result


def inspect_demand(brief: dict[str, Any], *, durable: bool = False) -> dict[str, Any]:
    """Inspect explicit declarations only; partial direct demands remain valid."""
    if not isinstance(brief, dict):
        raise ContentContractError("demand must be an object")
    goal = _text(brief.get("goal"), "exact current owner goal")
    ids = _strings(brief["deliverables"], "deliverables") if "deliverables" in brief else None
    if durable and not ids:
        raise ContentContractError("durable demand requires explicit deliverables")
    typed = None
    if "deliverable_specs" in brief:
        typed = inspect_declared_deliverables(brief["deliverable_specs"], expected_ids=ids)
    if ids is None and typed:
        ids = typed["deliverable_ids"]
    clauses = []
    sources = []
    amendments = []
    if "demand_contract" in brief:
        declaration = brief["demand_contract"]
        if (not isinstance(declaration, dict)
                or not {"schema_version", "owner_source_refs", "clauses"}.issubset(declaration)
                or set(declaration) - {"schema_version", "owner_source_refs", "clauses", "amendments"}
                or type(declaration["schema_version"]) is not int
                or declaration["schema_version"] != 1):
            raise ContentContractError("demand_contract must use exact schema version 1")
        sources = _strings(declaration["owner_source_refs"], "owner_source_refs")
        if not sources:
            raise ContentContractError("demand_contract requires owner source references")
        raw = declaration["clauses"]
        if not isinstance(raw, list) or not raw:
            raise ContentContractError("demand_contract requires explicit clauses")
        seen = set()
        for clause in raw:
            if not isinstance(clause, dict) or set(clause) != {
                    "id", "kind", "text", "source_ref", "deliverable_refs"}:
                raise ContentContractError("invalid demand clause fields")
            identifier = _text(clause["id"], "clause id")
            if not _ID.fullmatch(identifier) or identifier in seen:
                raise ContentContractError("clause id must be safe and unique")
            seen.add(identifier)
            kind = _text(clause["kind"], "clause kind")
            if kind not in CLAUSE_KINDS:
                raise ContentContractError("unsupported demand clause kind")
            source = _text(clause["source_ref"], "clause source_ref")
            if source not in sources:
                raise ContentContractError("clause source_ref must be declared")
            refs = _strings(clause["deliverable_refs"], "clause deliverable_refs")
            if any(ref not in (ids or []) for ref in refs):
                raise ContentContractError("clause references unknown deliverable")
            clauses.append({"id": identifier, "kind": kind,
                            "text": _text(clause["text"], "clause text"),
                            "source_ref": source, "deliverable_refs": refs})
        amendments_raw = declaration.get("amendments", [])
        if not isinstance(amendments_raw, list):
            raise ContentContractError("amendments must be an array")
        amendment_ids = set()
        for amendment in amendments_raw:
            if not isinstance(amendment, dict) or set(amendment) != {
                    "id", "target", "action", "source_ref", "reason"}:
                raise ContentContractError("invalid demand amendment fields")
            amendment_id = _text(amendment["id"], "amendment id")
            if not _ID.fullmatch(amendment_id) or amendment_id in amendment_ids:
                raise ContentContractError("amendment IDs must be unique and safe")
            amendment_ids.add(amendment_id)
            target = _text(amendment["target"], "amendment target")
            if target != "@brief" and not _ID.fullmatch(target):
                raise ContentContractError("invalid amendment target")
            action = amendment["action"]
            if not isinstance(action, str) or action not in {"ADD", "REVISE", "RETIRE"}:
                raise ContentContractError("invalid amendment action")
            source = _text(amendment["source_ref"], "amendment source_ref")
            if source not in sources:
                raise ContentContractError("amendment source must be declared")
            amendments.append({"id": amendment_id, "target": target, "action": action,
                               "source_ref": source, "reason": _text(amendment["reason"], "amendment reason")})
    return {
        "goal": goal, "deliverable_ids": ids, "typed_deliverables": typed,
        "contract_status": "DECLARED_UNVERIFIED" if "demand_contract" in brief else "UNSTRUCTURED",
        "owner_source_refs": sources, "clauses": clauses, "amendments": amendments,
        "source_authenticity_verified": False, "semantic_completeness_verified": False,
        "effect_authorized": False, "selected_task_graph": None,
    }


def validate_demand_revision(previous: dict[str, Any], current: dict[str, Any]) -> None:
    """Prevent a revision from silently downgrading an already typed boundary.

    Actual owner correction authority and semantic conflicts still require CAOS.
    The existing brief revision event preserves prior declarations.
    """
    before = inspect_demand(previous, durable=True)
    after = inspect_demand(current, durable=True)
    for field in ("deliverable_specs", "demand_contract"):
        if field in previous and field not in current:
            raise ContentContractError(f"owner revision cannot silently drop {field}")
    if before["contract_status"] != "DECLARED_UNVERIFIED":
        return  # first opt-in admission of structured declarations
    if after["contract_status"] != "DECLARED_UNVERIFIED":
        raise ContentContractError("structured demand cannot be silently removed")
    old_sources, new_sources = before["owner_source_refs"], after["owner_source_refs"]
    if new_sources[:len(old_sources)] != old_sources:
        raise ContentContractError("prior owner source references must be retained in order")
    old_amendments, new_amendments = before["amendments"], after["amendments"]
    if new_amendments[:len(old_amendments)] != old_amendments:
        raise ContentContractError("prior demand amendments are append-only")
    old_clauses = {c["id"]: c for c in before["clauses"]}
    current_clauses = {c["id"]: c for c in after["clauses"]}
    changed = {}
    for clause_id in old_clauses.keys() | current_clauses.keys():
        if clause_id not in old_clauses:
            changed[clause_id] = "ADD"
        elif clause_id not in current_clauses:
            changed[clause_id] = "RETIRE"
        elif old_clauses[clause_id] != current_clauses[clause_id]:
            changed[clause_id] = "REVISE"
    envelope = lambda brief: {k: v for k, v in brief.items()
                              if k not in {"demand_contract", "scope_epoch"}}
    if envelope(previous) != envelope(current):
        changed["@brief"] = "REVISE"
    delta = new_amendments[len(old_amendments):]
    expected = {(key, action) for key, action in changed.items()}
    observed = [(a["target"], a["action"]) for a in delta]
    if len(observed) != len(expected) or set(observed) != expected:
        raise ContentContractError("every demand change needs one exact, explicit new amendment")
    fresh_sources = set(new_sources[len(old_sources):])
    for amendment in delta:
        if amendment["source_ref"] not in fresh_sources:
            raise ContentContractError("new amendment requires a newly declared owner correction source")
        target = amendment["target"]
        if target != "@brief" and amendment["action"] in {"ADD", "REVISE"}:
            if current_clauses[target]["source_ref"] != amendment["source_ref"]:
                raise ContentContractError("updated clause must cite its amendment source")
