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
    if candidate.is_symlink():
        raise ValueError("workspace root cannot be a symlink")
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
    if "deliverable_specs" in brief:
        from .domain.contracts import inspect_declared_deliverables
        inspect_declared_deliverables(brief["deliverable_specs"], expected_ids=brief.get("deliverables"))
    return {**brief, "scope_epoch": EPOCH}


def validate_task_binding(brief: dict[str, Any], task: dict[str, Any]) -> None:
    assert_scope_epoch()
    if brief.get("scope_epoch") != EPOCH:
        return  # mechanical compatibility and isolated fixture path
    refs = task.get("requirements", {}).get("deliverable_refs")
    deliverables = brief.get("deliverables", [])
    if not isinstance(refs, list) or not refs or any(
        not isinstance(ref, str) or ref not in deliverables for ref in refs
    ):
        raise ValueError("every governed task must reference exact current deliverables")


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


def resolve_intake(root: str | Path, request: dict[str, Any]) -> dict[str, Any]:
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
        project_id = _id(request.get("project_id"))
        brief = read_project_brief(root, project_id)
        if brief.get("scope_epoch") != EPOCH:
            raise ValueError("pre-cutover task instance is retired; create a fresh owner demand")
        goal = brief["goal"]
    declarations = request.get("deliverable_specs") if mode == "NEW" else brief.get("deliverable_specs")
    typed = None
    if declarations is not None:
        from .domain.contracts import inspect_declared_deliverables
        typed = inspect_declared_deliverables(
            declarations, expected_ids=(brief.get("deliverables") if mode == "RESUME" else request.get("deliverables")))
    from .domain.identity import identity_route
    identity_routing = identity_route(typed["deliverables"]) if typed else None
    from .subsystems import route_declared_content
    internal_subsystem_routing = route_declared_content(typed["deliverables"]) if typed else None
    return {
        "mode": mode, "goal": goal, "project_id": project_id, "brief": brief,
        "typed_deliverables": typed,
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


def capability_lookup(group_id: str | None = None, *, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Read-only discovery, with no inference of provider access, decision, or task."""
    from .adapters import SUPPORTED_DOMAIN_ADAPTERS
    from .production.registry import PRODUCTION_EXECUTORS
    data = profile if profile is not None else json.loads(
        files("social_media_studio.legacy").joinpath("data", "capabilities.json").read_text(encoding="utf-8"))
    groups = data["professional_capability_groups"]
    ids = [g["id"] for g in groups]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate professional capability group")
    demands = [d for g in groups for d in g["demands"]]
    if len(demands) != len(set(demands)):
        raise ValueError("ambiguous professional demand identity")
    adapters = {x for g in groups for x in g["adapters"]}
    operations = {x for g in groups for x in g["operations"]}
    if adapters != set(SUPPORTED_DOMAIN_ADAPTERS) or operations != set(PRODUCTION_EXECUTORS.operations()):
        raise ValueError("professional capability routes diverge from actual executor registries")
    if any(g["activation"] != "DEMAND_SELECTED_ONLY" or not g["gaps"] for g in groups):
        raise ValueError("professional groups must be demand-selected and disclose limits")
    if any(not item.get("current_route", {}).get("status") for item in data["capabilities"]):
        raise ValueError("legacy capability must have explicit current disposition")
    selected = [g for g in groups if group_id is None or g["id"] == group_id]
    if not selected:
        raise ValueError("exact professional capability group not found")
    return {
        "groups": selected, "legacy_capabilities": data["capabilities"] if group_id is None else [],
        "registry_alignment": "VERIFIED_STRUCTURE_ONLY",
        "selected_task_graph": None, "effect_authorized": False,
        "native_activation": "NOT_VERIFIED_BY_RUNTIME", "business_outcome_verified": False,
    }
