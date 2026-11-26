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
    if "demand_contract" in brief:
        declaration = brief["demand_contract"]
        if (not isinstance(declaration, dict)
                or set(declaration) != {"schema_version", "owner_source_refs", "clauses"}
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
    return {
        "goal": goal, "deliverable_ids": ids, "typed_deliverables": typed,
        "contract_status": "DECLARED_UNVERIFIED" if "demand_contract" in brief else "UNSTRUCTURED",
        "owner_source_refs": sources, "clauses": clauses,
        "source_authenticity_verified": False, "semantic_completeness_verified": False,
        "effect_authorized": False, "selected_task_graph": None,
    }


def validate_demand_revision(previous: dict[str, Any], current: dict[str, Any]) -> None:
    """Prevent a revision from silently downgrading an already typed boundary.

    Actual owner correction authority and semantic conflicts still require CAOS.
    The existing brief revision event preserves prior declarations.
    """
    inspect_demand(current, durable=True)
    for field in ("deliverable_specs", "demand_contract"):
        if field in previous and field not in current:
            raise ContentContractError(f"owner revision cannot silently drop {field}")
