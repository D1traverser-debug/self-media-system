"""Demand composition across existing business, craft, artifact and execution axes.

Selection is an assistant proposal, not an owner requirement or permission. The
current brief is the source of truth; no scheduler, side effect or new ledger.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

_SURFACES = {"DIRECT_SESSION", "DURABLE_STUDIO"}
_CANON_USE = {"approved_identity_use", "identity_continuity", "identity_derivative_production"}

def _unique_strings(value: Any, label: str) -> list[str]:
    if (not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value)
            or len(value) != len(set(value))):
        raise ValueError(f"{label} must be a unique list of nonempty strings")
    return value

def compose_demand(demand, *, mode, selection, quality, ownership, identity, manifest, lookup):
    """Compose one read-only proposal per current deliverable, without implicit work."""
    if selection is None:
        selection = {}
    if not isinstance(selection, dict) or set(selection) - {"business_domains", "surface", "deliverables"}:
        raise ValueError("composition selection must contain only business_domains, surface, deliverables")
    allowed_business = set(manifest["architecture"]["user_need_model"]["business_domains"])
    business = _unique_strings(selection.get("business_domains", []), "business_domains")
    if not set(business) <= allowed_business:
        raise ValueError("unknown business domain")
    surface = selection.get("surface")
    if surface is not None and (not isinstance(surface, str) or surface not in _SURFACES):
        raise ValueError("unknown execution surface")
    if mode == "RESUME":
        if surface == "DIRECT_SESSION":
            raise ValueError("cannot substitute a direct session for explicit durable resume")
        surface = "DURABLE_STUDIO"
    selected = selection.get("deliverables", {})
    if not isinstance(selected, dict):
        raise ValueError("deliverable selections must be an object keyed by exact deliverable ID")
    typed = demand["typed_deliverables"]
    items = typed["deliverables"] if typed else []
    ids = {item["id"] for item in items}
    if set(selected) - ids:
        raise ValueError("composition references unknown current typed deliverable")
    groups = lookup()["groups"] if items else []
    demand_index = {key: (group["id"], route) for group in groups
                    for key, route in group["demand_routes"].items()}
    quality_by_id = {item["deliverable_id"]: item for item in quality["plans"]} if quality else {}
    owners_by_id = {item["deliverable_id"]: item for item in ownership["routes"]} if ownership else {}
    identity_by_id = {item["deliverable_id"]: item for item in identity["routes"]} if identity else {}
    result = []
    for item in items:
        identifier, kind = item["id"], item["type"]
        identity_mode = identity_by_id[identifier]["identity_mode"]
        def applicable(key, route):
            if kind not in route["deliverable_types"]:
                return False
            if key in _CANON_USE:
                return identity_mode in {"APPROVED_CANON_USE", "IDENTITY_DERIVATIVE"}
            if key == "persistent_identity_design":
                return identity_mode == "PERSISTENT_IDENTITY_DESIGN"
            if key == "temporary_character":
                return identity_mode == "TEMPORARY_CHARACTER"
            return True
        candidates = sorted(key for key, (_, route) in demand_index.items() if applicable(key, route))
        demands = _unique_strings(selected.get(identifier, []), f"deliverable {identifier} demand selection")
        if not set(demands) <= set(candidates):
            raise ValueError(f"{identifier}: operation does not match current deliverable type or identity scope")
        routes = []
        for key in demands:
            group_id, _ = demand_index[key]
            resolved = lookup(group_id, demand_id=key)["groups"][0]
            routes.append({
                "demand_id": key, "group_id": group_id,
                "operation_contract": resolved["selected_operation_contract"],
                "resource_resolution": resolved["demand_resolution"],
                "knowledge_resources": resolved["knowledge_resources"],
                "methods": resolved["methods"], "professional_roles": resolved["professional_roles"],
                "skill_sections": resolved["skill_sections"],
                "executor_routes": resolved["executor_routes"],
                "actual_executor_verified": False,
            })
        clauses = [c for c in demand["clauses"] if not c["deliverable_refs"] or identifier in c["deliverable_refs"]]
        result.append({
            "deliverable_id": identifier, "deliverable_contract": item,
            "owner_clauses": clauses, "internal_ownership": owners_by_id[identifier],
            "identity_scope": identity_by_id[identifier], "quality_plan": quality_by_id[identifier],
            "candidate_demands_not_selected": [key for key in candidates if key not in demands],
            "proposed_professional_routes": routes,
            "selection_status": "PROPOSED_REQUIRES_CAOS_METHOD_AND_EFFECT_CHECK" if routes else "UNSELECTED",
        })
    # Bind the proposal to the actual normalized source and the chosen route, not
    # to an ID alone. This is a locator, not a signed decision or revision grant.
    payload = {"demand": demand, "selection": selection, "mode": mode}
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                      separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        "status": "COMPOSITION_PREVIEW_NOT_EXECUTION" if items else "INTERPRET_CURRENT_GOAL_NO_TYPED_ROUTE",
        "proposal_sha256": digest, "business_domains_proposed": business,
        "surface_proposed": surface, "deliverables": result,
        "owner_source_authenticity_verified": False, "semantic_completeness_verified": False,
        "selected_task_graph": None, "effect_authorized": False,
        "actual_executor_verified": False, "owner_outcome_verified": False,
        "native_caos_activation": "NOT_VERIFIED",
    }
