"""Task-neutral routing. No parent execution, grant or native activation is fabricated."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from importlib.resources import files
from pathlib import Path
from typing import Any

EPOCH = "SOCIAL_MEDIA_OWNER_SCOPE_V2_20261125"


OFFLINE_FIXTURE_MARKER = ".sms-offline-fixture.json"


def validate_workspace_mode(
    root: str | Path, *, offline_fixture: bool, initialize: bool = False,
    owner_root: str | Path | None = None,
) -> Path:
    """Keep CLI owner ledgers and mechanical fixture workspaces mutually exclusive.

    A fixture root is initialized only when it is empty, then bound to its resolved
    path by a marker. This is an accidental-mixing guard, not an authentication system.
    """
    candidate = Path(root).expanduser()
    if offline_fixture and candidate.is_symlink():
        raise ValueError("offline fixture root cannot be a symlink")
    workspace = candidate.resolve()
    if workspace.exists() and not workspace.is_dir():
        raise ValueError("workspace root must be a directory")
    marker = workspace / OFFLINE_FIXTURE_MARKER

    def verify_marker() -> None:
        if marker.is_symlink() or not marker.is_file():
            raise ValueError("offline fixture marker is missing or invalid")
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("offline fixture marker cannot be read") from exc
        expected = {
            "schema_version": 1,
            "mode": "OFFLINE_FIXTURE",
            "authority": "MECHANICAL_REGRESSION_ONLY",
            "workspace_root": str(workspace),
        }
        if payload != expected:
            raise ValueError("offline fixture marker does not match this exact workspace")

    if offline_fixture:
        if owner_root is not None:
            owner = Path(owner_root).expanduser().resolve()
            if (workspace == owner or workspace.is_relative_to(owner)
                    or owner.is_relative_to(workspace)):
                raise ValueError("offline fixture root must be disjoint from the default owner workspace")
        if marker.exists() or marker.is_symlink():
            verify_marker()
        else:
            if not initialize:
                raise ValueError("offline fixture root is unmarked; initialize a dedicated empty root first")
            if workspace.exists() and any(workspace.iterdir()):
                raise ValueError("offline fixture root must be empty before its first initialization")
            workspace.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema_version": 1,
                "mode": "OFFLINE_FIXTURE",
                "authority": "MECHANICAL_REGRESSION_ONLY",
                "workspace_root": str(workspace),
            }
            try:
                with marker.open("x", encoding="utf-8") as stream:
                    json.dump(payload, stream, ensure_ascii=False, sort_keys=True)
                    stream.write("\n")
            except FileExistsError:
                verify_marker()
        return workspace

    if marker.exists() or marker.is_symlink():
        raise ValueError("owner mode cannot access an offline fixture workspace")
    return workspace


def contract() -> dict[str, Any]:
    return json.loads(files("social_media_studio").joinpath("data", "studio_manifest.json").read_text(encoding="utf-8"))


def assert_scope_epoch(manifest: dict[str, Any] | None = None) -> None:
    """Fail closed when runtime code and the canonical owner-scope contract drift."""
    current = manifest if manifest is not None else contract()
    declared = current.get("task_admission", {}).get("scope_epoch")
    if declared != EPOCH:
        raise ValueError(f"owner scope epoch mismatch: runtime={EPOCH!r}, manifest={declared!r}")


def _id(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value):
        raise ValueError("exact safe project_id required")
    manifest = contract()
    assert_scope_epoch(manifest)
    if value.casefold() in {item.casefold() for item in manifest["task_admission"]["retired_project_ids"]}:
        raise ValueError("retired project instance cannot be resumed or reused")
    return value


def bind_owner_brief(project_id: str, brief: dict[str, Any]) -> dict[str, Any]:
    _id(project_id)
    if not isinstance(brief, dict) or not isinstance(brief.get("goal"), str) or not brief["goal"].strip():
        raise ValueError("exact current owner goal is required")
    if brief.get("scope_epoch", EPOCH) != EPOCH:
        raise ValueError("cannot reuse a retired scope epoch")
    from .domain.demand import inspect_demand
    inspect_demand(brief, durable=True)
    return {**brief, "scope_epoch": EPOCH}


def validate_task_binding(brief: dict[str, Any], task: dict[str, Any]) -> dict[str, Any] | None:
    """Use the current composition contract at every durable admission boundary.

    Typed tasks explicitly propose professional demands for each referenced
    deliverable. Actual local dispatch must match those exact support routes.
    This is structural scope validation, not a CAOS decision or quality receipt.
    """
    assert_scope_epoch()
    if brief.get("scope_epoch") != EPOCH:
        return None  # mechanical compatibility and isolated fixture path
    requirements = task.get("requirements", {})
    if not isinstance(requirements, dict):
        raise ValueError("task requirements must be an object")
    refs = requirements.get("deliverable_refs")
    deliverables = brief.get("deliverables", [])
    if (not isinstance(refs, list) or not refs
            or any(not isinstance(ref, str) or ref not in deliverables for ref in refs)
            or len(refs) != len(set(refs))):
        raise ValueError("every governed task must reference exact current deliverables")
    if "deliverable_specs" not in brief:
        if "professional_demands" in requirements or "deliverable_outputs" in requirements:
            raise ValueError("typed professional or output bindings require current deliverable_specs")
        return None  # existing unstructured owner briefs are not silently reinterpreted
    from .domain.demand import inspect_demand
    from .application.demand_composition import demand_applies
    from .production.executors import tool_executor_for_task

    items = {item["id"]: item for item in inspect_demand(brief, durable=True)["typed_deliverables"]["deliverables"]}
    selected = requirements.get("professional_demands")
    if not isinstance(selected, dict) or set(selected) != set(refs):
        raise ValueError("typed task needs exact professional_demands for every deliverable_ref")
    executor = task.get("executor")
    if executor not in {"agent", "tool", "human", "external"}:
        raise ValueError("typed task requires a declared executor")
    adapter_config = requirements.get("domain_adapter")
    production_config = requirements.get("production")
    if "domain_adapter" in requirements and "production" in requirements:
        raise ValueError("typed task cannot combine competing local dispatcher configurations")
    if executor != "tool" and ("domain_adapter" in requirements or "production" in requirements):
        raise ValueError("local dispatcher configurations require executor=tool")
    local_route = tool_executor_for_task(task) if executor == "tool" else None
    # External high-assurance tool reviews have their own signed executor and
    # are not production registry operations. No arbitrary missing tool route.
    external_review = (executor == "tool" and task.get("kind") == "review"
                       and "domain_adapter" not in requirements and "production" not in requirements)
    if executor == "tool" and not local_route and not external_review:
        raise ValueError("typed tool task requires an exact registered local route or separate review executor")
    resolved = {}
    for ref in refs:
        demands = selected[ref]
        if (not isinstance(demands, list) or not demands
                or any(not isinstance(x, str) or not x.strip() for x in demands)
                or len(demands) != len(set(demands))):
            raise ValueError(f"{ref}: professional_demands must contain unique exact demand IDs")
        records = []
        allowed = set()
        for key in demands:
            group = capability_lookup(demand_id=key)["groups"][0]
            route = group["selected_operation_contract"]
            if not demand_applies(items[ref], key, route):
                raise ValueError(f"{ref}: professional demand does not match current deliverable type or identity scope")
            allowed.update("domain_adapter:" + name for name in route["local_support_adapters"])
            allowed.update("production:" + name for name in route["local_support_operations"])
            records.append({"demand_id": key, "operation_contract": route,
                            "local_support": group["executor_routes"],
                            "resource_resolution": group["demand_resolution"],
                            "knowledge_resources": group["knowledge_resources"],
                            "methods": group["methods"],
                            "professional_roles": group["professional_roles"],
                            "skill_sections": group["skill_sections"]})
        if local_route and local_route not in allowed:
            raise ValueError(f"{ref}: actual local route {local_route} is outside selected professional demand support")
        if external_review and "independent_acceptance" not in demands:
            raise ValueError(f"{ref}: separate review executor requires independent_acceptance demand")
        resolved[ref] = records
    # Outputs remain candidates until actual artifact and owner-outcome evidence.
    # No inference from file names or task completion.
    output_bindings = requirements.get("deliverable_outputs", {})
    if not isinstance(output_bindings, dict) or set(output_bindings) - set(task.get("outputs", [])):
        raise ValueError("deliverable_outputs must reference exact declared task outputs")
    for name, binding in output_bindings.items():
        if (not isinstance(binding, dict) or set(binding) != {"deliverable_id", "variant_id"}
                or not isinstance(binding["deliverable_id"], str) or binding["deliverable_id"] not in refs):
            raise ValueError(f"{name}: invalid deliverable output identity")
        item = items[binding["deliverable_id"]]
        variants = {v["id"] for v in item["variants"]} or {item["id"]}
        if not isinstance(binding["variant_id"], str) or binding["variant_id"] not in variants:
            raise ValueError(f"{name}: output references unknown current deliverable variant")
    payload = {"professional_routes": resolved, "executor": executor,
               "local_dispatch": local_route, "separate_review_executor": external_review,
               "deliverable_outputs": output_bindings}
    return {"sha256": hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                                separators=(",", ":")).encode("utf-8")).hexdigest(),
            "local_dispatch": local_route, "deliverable_outputs": output_bindings,
            "assurance": "STRUCTURAL_SCOPE_ONLY_NOT_METHOD_OR_OUTCOME_VERIFIED"}


def read_project_brief(root: str | Path, project_id: str) -> dict[str, Any]:
    if not isinstance(project_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", project_id):
        raise ValueError("exact safe project_id required")
    workspace = Path(root).expanduser().resolve()
    db = workspace / "projects" / project_id / "studio.sqlite3"
    if not db.is_file() or not db.resolve().is_relative_to(workspace):
        raise ValueError("exact workspace project not found")
    try:
        with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            row = connection.execute("SELECT brief_json FROM projects WHERE project_id=?", (project_id,)).fetchone()
    except sqlite3.Error as exc:
        raise ValueError("workspace project cannot be read") from exc
    if row is None:
        raise ValueError("exact project identity not found")
    return json.loads(row[0])


def resolve_intake(root: str | Path, request: dict[str, Any], *, selection: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a read-only route; never create a task, infer a project, or assert CAOS ran."""
    if not isinstance(request, dict) or request.get("mode") not in {"NEW", "RESUME"}:
        raise ValueError("explicit NEW or RESUME mode required")
    manifest = contract()
    assert_scope_epoch(manifest)
    mode = request["mode"]
    if mode == "NEW":
        goal = request.get("goal")
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("NEW requires exact current owner goal")
        project_id = request.get("project_id")
        if project_id is not None:
            project_id = _id(project_id)
            if (Path(root).expanduser().resolve() / "projects" / project_id).exists():
                raise ValueError("NEW cannot reuse an existing project")
        brief = None
    else:
        extra = set(request) - {"mode", "project_id"}
        if extra:
            raise ValueError(
                "RESUME is read-only and cannot apply owner corrections; revise the "
                f"stored brief explicitly before resuming: {sorted(extra)}"
            )
        project_id = _id(request.get("project_id"))
        brief = read_project_brief(root, project_id)
        if brief.get("scope_epoch") != EPOCH:
            raise ValueError("pre-cutover task instance is retired; create a fresh owner demand")
        goal = brief["goal"]
    from .domain.demand import inspect_demand
    demand = inspect_demand(request if mode == "NEW" else brief, durable=mode == "RESUME")
    typed = demand["typed_deliverables"]
    from .domain.identity import identity_route
    identity_routing = identity_route(typed["deliverables"]) if typed else None
    from .subsystems import route_declared_content
    internal_subsystem_routing = route_declared_content(typed["deliverables"]) if typed else None
    from .application.demand_composition import compose_demand
    from .domain.assurance import build_quality_plan
    original = request if mode == "NEW" else brief
    quality = build_quality_plan(original["deliverable_specs"]) if typed else None
    composition = compose_demand(demand, mode=mode, selection=selection, quality=quality,
                                 ownership=internal_subsystem_routing, identity=identity_routing,
                                 manifest=manifest, lookup=capability_lookup)
    return {
        "mode": mode, "goal": goal, "project_id": project_id, "brief": brief,
        "demand_composition": composition,
        "typed_deliverables": typed,
        "demand": demand,
        "identity_routing": identity_routing,
        "internal_subsystem_routing": internal_subsystem_routing,
        "scope_epoch": EPOCH, "selected_task_graph": None,
        "default_project_id": None, "automatic_resume": False,
        "architecture": manifest["architecture"],
        "capabilities": manifest["capabilities"],
        "knowledge_catalog": manifest["knowledge_lifecycle"]["index"],
        "capability_catalog": "social_media_studio/legacy/data/capabilities.json",
        "professional_capability_lookup": "sms-studio capabilities",
        "parent_governance": "REQUIRED_IN_OWNER_SESSION",
        "native_activation": "NOT_VERIFIED_BY_RUNTIME",
        "effect_authorized": False,
    }


def knowledge_lookup(method_id: str | None = None, *, include_nonactive: bool = False,
                     repo_root: str | Path | None = None) -> dict[str, Any]:
    """Locate reusable sources by exact stable identity; never select a task or grant authority."""
    catalog = json.loads(files("social_media_studio").joinpath("data", "knowledge_catalog.json").read_text(encoding="utf-8"))
    entries = catalog["entries"]
    active = {"ACTIVE_REFERENCE", "VERIFIED_OPERATION"}
    known_statuses = active | {"CANDIDATE_REQUIRES_REVALIDATION", "LEGACY_REFERENCE_ONLY", "RETIRED_EVIDENCE_ONLY"}
    ids = set()
    for entry in entries:
        key = entry["id"]
        ref = Path(entry["ref"])
        if key in ids or entry["status"] not in known_statuses or ref.is_absolute() or ".." in ref.parts:
            raise ValueError("invalid or ambiguous knowledge catalog")
        if entry["status"] in active and ref.parts[0] in {"projects", "examples", "archive"}:
            raise ValueError("historic task evidence cannot be active knowledge authority")
        ids.add(key)
    selected = [entry for entry in entries if (method_id is None or entry["id"] == method_id)
                and (include_nonactive or entry["status"] in active)]
    if method_id is not None and not selected:
        raise ValueError("exact active method not found; nonactive evidence requires explicit inclusion")
    root = Path(repo_root).expanduser().resolve() if repo_root is not None else None
    result = []
    for entry in selected:
        item = dict(entry)
        item["authority"] = "METHOD_REFERENCE_ONLY"
        item["execution_verified"] = False
        if root is not None:
            source = (root / entry["ref"]).resolve()
            if not source.is_relative_to(root) or not source.is_file():
                raise ValueError(f"knowledge source unavailable: {entry['id']}")
            item["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        result.append(item)
    return {"entries": result, "source_verification": "HASHED_LOCAL_BYTES" if root else "LOCATOR_ONLY",
            "native_caos_activation": "NOT_VERIFIED_BY_RUNTIME", "automatic_task_selection": False}


def capability_lookup(
    group_id: str | None = None, *, demand_id: str | None = None,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve scoped professional resources; discovery never selects tasks or authorizes effects."""
    from .domain_adapters.registry import DOMAIN_ADAPTERS, SUPPORTED_DOMAIN_ADAPTERS, public_domain_adapter_registry
    from .production.registry import PRODUCTION_EXECUTORS

    data = profile if profile is not None else json.loads(
        files("social_media_studio.legacy").joinpath("data", "capabilities.json").read_text(encoding="utf-8"))
    groups = data["professional_capability_groups"]
    ids = [group["id"] for group in groups]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate professional capability group")
    demands = [demand for group in groups for demand in group["demands"]]
    if len(demands) != len(set(demands)):
        raise ValueError("ambiguous professional demand identity")

    adapters = {name for group in groups for name in group["adapters"]}
    operations = {name for group in groups for name in group["operations"]}
    if adapters != set(SUPPORTED_DOMAIN_ADAPTERS) or operations != set(PRODUCTION_EXECUTORS.operations()):
        raise ValueError("professional capability routes diverge from actual executor registries")
    if any(DOMAIN_ADAPTERS[name].capability_group != group["id"]
           for group in groups for name in group["adapters"]):
        raise ValueError("domain adapter operation is assigned to the wrong capability group")
    if any(group["activation"] != "DEMAND_SELECTED_ONLY" or not group["gaps"] for group in groups):
        raise ValueError("professional groups must be demand-selected and disclose limits")

    knowledge_data = json.loads(files("social_media_studio").joinpath("data", "knowledge_catalog.json").read_text(encoding="utf-8"))
    technique_data = json.loads(files("social_media_studio.legacy").joinpath("data", "techniques.json").read_text(encoding="utf-8"))
    role_data = json.loads(files("social_media_studio.legacy").joinpath("data", "roles.json").read_text(encoding="utf-8"))
    knowledge_by_id = {item["id"]: item for item in knowledge_data["entries"]}
    methods_by_id = {item["id"]: item for item in technique_data["techniques"]}
    roles_by_id = role_data["roles"]
    resource_fields = (
        ("knowledge_refs", knowledge_by_id),
        ("method_ids", methods_by_id),
        ("role_ids", roles_by_id),
    )
    profile_fields = {
        "knowledge_refs", "method_ids", "role_ids", "skill_sections",
        "applies_to", "avoid_when", "selection_notes",
    }

    from .domain.contracts import DELIVERABLE_TYPES
    route_fields = {"deliverable_types", "local_support_adapters", "local_support_operations",
                    "scope", "requires_current_method_and_executor_check"}
    for group in groups:
        routes = group.get("demand_routes")
        if not isinstance(routes, dict) or set(routes) != set(group["demands"]):
            raise ValueError(f"{group['id']}: operation route must cover every declared demand exactly")
        for key, route in routes.items():
            if not isinstance(route, dict) or set(route) != route_fields:
                raise ValueError(f"{key}: malformed demand operation route")
            for field, allowed in (("deliverable_types", DELIVERABLE_TYPES),
                                   ("local_support_adapters", set(group["adapters"])),
                                   ("local_support_operations", set(group["operations"]))):
                values = route[field]
                if (not isinstance(values, list) or any(not isinstance(v, str) for v in values)
                        or len(values) != len(set(values)) or not set(values) <= allowed):
                    raise ValueError(f"{key}: invalid {field}")
            if (not route["deliverable_types"] or not isinstance(route["scope"], str)
                    or not route["scope"].strip() or route["requires_current_method_and_executor_check"] is not True):
                raise ValueError(f"{key}: missing operation scope or verification boundary")
        for field, available in resource_fields:
            refs = group.get(field)
            if (not isinstance(refs, list)
                    or any(not isinstance(ref, str) or not ref.strip() for ref in refs)
                    or len(refs) != len(set(refs)) or not set(refs).issubset(available)):
                raise ValueError(f"{group['id']}: unresolved or duplicate {field}")
        sections = group.get("skill_sections")
        if (not isinstance(sections, list) or not sections
                or any(not isinstance(section, str) or not section.strip() for section in sections)
                or len(sections) != len(set(sections))):
            raise ValueError(f"{group['id']}: skill_sections must be a non-empty unique list")

        demand_profiles = group.get("demand_profiles", {})
        if not isinstance(demand_profiles, dict) or not set(demand_profiles).issubset(set(group["demands"])):
            raise ValueError(f"{group['id']}: demand_profiles must map only declared demands")
        for exact_demand, spec in demand_profiles.items():
            if not isinstance(spec, dict) or set(spec) - profile_fields:
                raise ValueError(f"{group['id']}.{exact_demand}: malformed demand profile")
            for field, available in resource_fields:
                refs = spec.get(field, [])
                if (not isinstance(refs, list)
                        or any(not isinstance(ref, str) or not ref.strip() for ref in refs)
                        or len(refs) != len(set(refs)) or not set(refs).issubset(available)):
                    raise ValueError(f"{group['id']}.{exact_demand}: unresolved or duplicate {field}")
            for field in ("skill_sections", "applies_to", "avoid_when"):
                values = spec.get(field, [])
                if (not isinstance(values, list)
                        or any(not isinstance(value, str) or not value.strip() for value in values)
                        or len(values) != len(set(values))):
                    raise ValueError(f"{group['id']}.{exact_demand}: {field} must be a unique text list")
            if not spec.get("applies_to") or not isinstance(spec.get("selection_notes"), str) or not spec["selection_notes"].strip():
                raise ValueError(f"{group['id']}.{exact_demand}: applies_to and selection_notes are required")

    if demand_id is not None:
        if not isinstance(demand_id, str) or not demand_id.strip():
            raise ValueError("exact nonempty demand_id required")
        matching = [group for group in groups if demand_id in group["demands"]]
        if group_id is not None:
            matching = [group for group in matching if group["id"] == group_id]
        if len(matching) != 1:
            raise ValueError("exact professional demand identity not found in the requested group")
        selected = matching
        effective_group_id = matching[0]["id"]
    else:
        selected = [group for group in groups if group_id is None or group["id"] == group_id]
        if not selected:
            raise ValueError("exact professional capability group not found")
        effective_group_id = group_id

    resolved_groups = []
    for group in selected:
        selected_profile = group.get("demand_profiles", {}).get(demand_id) if demand_id else None
        selected_route = group["demand_routes"][demand_id] if demand_id else None
        route_adapters = selected_route["local_support_adapters"] if selected_route else group["adapters"]
        route_operations = selected_route["local_support_operations"] if selected_route else group["operations"]

        def merged(field: str) -> list[str]:
            extra = selected_profile.get(field, []) if selected_profile else []
            return list(dict.fromkeys([*group[field], *extra]))

        knowledge_refs = merged("knowledge_refs")
        method_ids = merged("method_ids")
        role_ids = merged("role_ids")
        skill_sections = merged("skill_sections")
        resolution = (
            "EXACT_DEMAND_PROFILE" if selected_profile
            else "GROUP_LEVEL_FALLBACK" if demand_id
            else "GROUP_OVERVIEW"
        )
        resolved_groups.append({
            **group,
            "knowledge_resources": [knowledge_by_id[ref] for ref in knowledge_refs],
            "methods": [methods_by_id[ref] for ref in method_ids],
            "professional_roles": [{"id": role_id, **roles_by_id[role_id]} for role_id in role_ids],
            "skill_sections": skill_sections,
            "available_demand_profiles": sorted(group.get("demand_profiles", {}).keys()),
            "selected_demand_id": demand_id,
            "selected_operation_contract": selected_route,
            "demand_resolution": resolution,
            "selected_demand_profile": ({
                "applies_to": selected_profile["applies_to"],
                "avoid_when": selected_profile["avoid_when"],
                "selection_notes": selected_profile["selection_notes"],
            } if selected_profile else None),
            "executor_routes": {
                "domain_adapters": [item for item in public_domain_adapter_registry()
                                    if item["name"] in route_adapters],
                "production_operations": list(route_operations),
                "route_scope": ("EXACT_DEMAND_SUPPORT_CANDIDATES__NOT_EXECUTOR_ADMISSION" if selected_route
                                else "GROUP_LEVEL_CANDIDATE__VERIFY_EXACT_TASK_OPERATION_BEFORE_EXECUTION"),
                "actual_executor_verified": False,
                "nonlocal_execution": "CURRENT_SESSION_CAPABILITY_HANDSHAKE__AGENT_HUMAN_EXTERNAL_HANDOFF",
            },
        })
    return {
        "groups": resolved_groups,
        "domain_operations": [
            item for item in public_domain_adapter_registry()
            if (item["name"] in {a["name"] for g in resolved_groups for a in g["executor_routes"]["domain_adapters"]})
        ],
        "legacy_capabilities": data["capabilities"] if effective_group_id is None and demand_id is None else [],
        "registry_alignment": "VERIFIED_STRUCTURE_ONLY",
        "selected_demand_id": demand_id,
        "demand_resolution": (
            "EXACT_DEMAND_PROFILE" if demand_id and resolved_groups[0]["demand_resolution"] == "EXACT_DEMAND_PROFILE"
            else "GROUP_LEVEL_FALLBACK" if demand_id
            else "GROUP_OVERVIEW"
        ),
        "routing_warning": (
            "No exact demand profile is registered; returned resources are group-level only."
            if demand_id and resolved_groups[0]["demand_resolution"] == "GROUP_LEVEL_FALLBACK"
            else None
        ),
        "selected_task_graph": None,
        "effect_authorized": False,
        "native_activation": "NOT_VERIFIED_BY_RUNTIME",
        "business_outcome_verified": False,
    }
