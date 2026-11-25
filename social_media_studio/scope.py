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
    if "deliverable_specs" in brief:
        from .domain.contracts import inspect_declared_deliverables
        inspect_declared_deliverables(brief["deliverable_specs"], expected_ids=brief.get("deliverables"))
    return {**brief, "scope_epoch": EPOCH}


def validate_task_binding(brief: dict[str, Any], task: dict[str, Any]) -> None:
    assert_scope_epoch()
    requirements = task.get("requirements", {})
    if not isinstance(requirements, dict):
        raise ValueError("task requirements must be an object")
    boundary = requirements.get("context_boundary")
    if boundary is not None:
        inputs = task.get("inputs", [])
        if not isinstance(inputs, list) or any(not isinstance(item, str) or not item.strip() for item in inputs):
            raise ValueError("task inputs must be declared before validating context_boundary")
        validate_context_boundary(boundary, task_inputs=inputs)
    if brief.get("scope_epoch") != EPOCH:
        return  # mechanical compatibility and isolated fixture path
    refs = requirements.get("deliverable_refs")
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


def validate_context_boundary(
    boundary: dict[str, Any], *, task_inputs: list[str] | None = None,
) -> dict[str, Any]:
    """Validate a task's declared context boundary; this is a handoff contract, not a native chat sandbox."""
    if not isinstance(boundary, dict):
        raise ValueError("requirements.context_boundary must be an object")
    mode = boundary.get("mode", "DECLARED_INPUTS_PLUS_PROJECT_BRIEF")
    if not isinstance(mode, str) or mode not in {"DECLARED_INPUTS_ONLY", "DECLARED_INPUTS_PLUS_PROJECT_BRIEF"}:
        raise ValueError("context_boundary.mode is unsupported")
    allowed = boundary.get("allowed_input_names", task_inputs if task_inputs is not None else [])
    excluded = boundary.get("excluded_context_refs", [])
    for field, value in (("allowed_input_names", allowed), ("excluded_context_refs", excluded)):
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError(f"context_boundary.{field} must be an array of non-empty strings")
        if len(value) != len(set(value)):
            raise ValueError(f"context_boundary.{field} contains duplicates")
    if task_inputs is not None and set(allowed) != set(task_inputs):
        raise ValueError("context_boundary.allowed_input_names must exactly match the task's declared inputs")
    if set(allowed) & set(excluded):
        raise ValueError("context_boundary cannot both allow and exclude the same reference")
    allow_prior = boundary.get("allow_prior_conversation", False)
    allow_siblings = boundary.get("allow_sibling_task_context", False)
    isolated_chat = boundary.get("isolated_chat_required", False)
    if not all(isinstance(value, bool) for value in (allow_prior, allow_siblings, isolated_chat)):
        raise ValueError("context_boundary flags must be booleans")
    if allow_prior or allow_siblings:
        raise ValueError("prior conversation and sibling-task context must be imported as explicitly declared artifacts")
    if isolated_chat and mode != "DECLARED_INPUTS_ONLY":
        raise ValueError("isolated_chat_required requires DECLARED_INPUTS_ONLY")
    if "native_session_isolation_verified" in boundary:
        raise ValueError("native chat isolation cannot be asserted by a task contract")
    return {
        "mode": mode,
        "allowed_input_names": list(allowed),
        "excluded_context_refs": list(excluded),
        "allow_prior_conversation": allow_prior,
        "allow_sibling_task_context": allow_siblings,
        "isolated_chat_required": isolated_chat,
    }


def validate_adoption_packet(packet: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
    """Validate a portable conversation-to-project context package without promoting its claims to proof."""
    if not isinstance(packet, dict) or packet.get("schema_version") != "1.0":
        raise ValueError("adoption packet must be an object with schema_version 1.0")
    if packet.get("kind") != "SOCIAL_MEDIA_STUDIO_ADOPTION_PACKET":
        raise ValueError("adoption packet kind must be SOCIAL_MEDIA_STUDIO_ADOPTION_PACKET")
    coverage = packet.get("source_coverage")
    if not isinstance(coverage, str) or coverage not in {"FULL_SOURCE_EXPORT", "PARTIAL_CONTEXT", "CURRENT_CHAT_ONLY", "UNKNOWN"}:
        raise ValueError("adoption packet source_coverage is invalid")
    coverage_notes = packet.get("coverage_notes")
    if not isinstance(coverage_notes, str) or not coverage_notes.strip():
        raise ValueError("adoption packet requires explicit coverage_notes")
    sources = packet.get("source_refs")
    if not isinstance(sources, list) or not sources:
        raise ValueError("adoption packet requires at least one source_refs entry")
    source_types = {"CHAT_EXPORT", "CHAT_CONTEXT", "LIBRARY_FILE", "LOCAL_FILE", "OTHER"}
    source_roles = {"OWNER_GOAL", "USER_CORRECTION", "REQUIREMENT", "DECISION", "FAILURE", "REFERENCE", "ARTIFACT", "OUTPUT"}
    source_verification = {"EXACT_BYTES_HASHED", "CONVERSATION_CONTEXT_ONLY", "UNVERIFIED"}
    seen_sources: set[tuple[str, str]] = set()
    seen_artifact_names: set[str] = {"adoption-context"}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"adoption source_refs[{index}] must be an object")
        source_ref = source.get("source_ref")
        source_type = source.get("source_type")
        role = source.get("role")
        verification = source.get("verification")
        if not isinstance(source_ref, str) or not source_ref.strip():
            raise ValueError(f"adoption source_refs[{index}] requires source_ref")
        if (
            not isinstance(source_type, str) or source_type not in source_types
            or not isinstance(role, str) or role not in source_roles
            or not isinstance(verification, str) or verification not in source_verification
        ):
            raise ValueError(f"adoption source_refs[{index}] has an unsupported source_type, role or verification")
        key = (source_ref, role)
        if key in seen_sources:
            raise ValueError(f"adoption packet contains duplicate source/role binding: {source_ref}/{role}")
        seen_sources.add(key)
        digest = source.get("sha256")
        if verification == "EXACT_BYTES_HASHED":
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                raise ValueError(f"adoption source_refs[{index}] requires a valid SHA-256 for EXACT_BYTES_HASHED")
            artifact_name = source.get("artifact_name")
            if not isinstance(artifact_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", artifact_name):
                raise ValueError(f"adoption source_refs[{index}] requires a safe artifact_name for exact-byte import")
            if artifact_name in seen_artifact_names:
                raise ValueError(f"adoption packet contains duplicate/reserved source artifact_name: {artifact_name}")
            seen_artifact_names.add(artifact_name)
            if source_type == "CHAT_CONTEXT":
                raise ValueError(f"adoption source_refs[{index}] CHAT_CONTEXT cannot claim exact file bytes")
            media_type = source.get("media_type", "text/plain")
            if not isinstance(media_type, str) or not media_type.strip():
                raise ValueError(f"adoption source_refs[{index}].media_type must be non-empty text")
        elif digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest)):
            raise ValueError(f"adoption source_refs[{index}] has an invalid optional SHA-256")
    if coverage == "FULL_SOURCE_EXPORT" and not any(
        source["source_type"] == "CHAT_EXPORT" and source["verification"] == "EXACT_BYTES_HASHED"
        for source in sources
    ):
        raise ValueError("FULL_SOURCE_EXPORT requires an exact-byte-hashed CHAT_EXPORT source")
    if coverage == "CURRENT_CHAT_ONLY" and not any(
        source["source_type"] == "CHAT_CONTEXT" and source["verification"] == "CONVERSATION_CONTEXT_ONLY"
        for source in sources
    ):
        raise ValueError("CURRENT_CHAT_ONLY requires an explicit CHAT_CONTEXT source")

    goal = packet.get("goal")
    if not isinstance(goal, dict):
        raise ValueError("adoption packet requires a goal object")
    original_goal = goal.get("original_user_goal")
    current_goal = goal.get("current_goal")
    deliverables = goal.get("deliverables")
    if not isinstance(original_goal, str) or not original_goal.strip():
        raise ValueError("adoption goal requires original_user_goal")
    if not isinstance(current_goal, str) or current_goal.strip() != brief.get("goal"):
        raise ValueError("adoption current_goal must exactly match the project brief goal")
    if not isinstance(deliverables, list) or deliverables != brief.get("deliverables"):
        raise ValueError("adoption deliverables must exactly match the project brief deliverables")
    for field in ("hard_constraints", "preferences", "prohibitions"):
        values = goal.get(field, [])
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError(f"adoption goal.{field} must be an array of non-empty strings")
    corrections = goal.get("corrections", [])
    if not isinstance(corrections, list):
        raise ValueError("adoption goal.corrections must be an array")
    correction_orders: set[int] = set()
    for index, correction in enumerate(corrections):
        if not isinstance(correction, dict) or not isinstance(correction.get("text"), str) or not correction["text"].strip():
            raise ValueError(f"adoption goal.corrections[{index}] requires text")
        order = correction.get("order")
        if not isinstance(order, int) or isinstance(order, bool) or order < 1 or order in correction_orders:
            raise ValueError(f"adoption goal.corrections[{index}] requires a unique positive order")
        correction_orders.add(order)
        if "source_ref" in correction and not isinstance(correction["source_ref"], str):
            raise ValueError(f"adoption goal.corrections[{index}].source_ref must be a string")

    completed = packet.get("completed_work", [])
    if not isinstance(completed, list):
        raise ValueError("adoption completed_work must be an array")
    for index, item in enumerate(completed):
        if not isinstance(item, dict) or not isinstance(item.get("description"), str) or not item["description"].strip():
            raise ValueError(f"adoption completed_work[{index}] requires description")
        item_status = item.get("status")
        if not isinstance(item_status, str) or item_status not in {"VERIFIED", "CLAIMED_UNVERIFIED"}:
            raise ValueError(f"adoption completed_work[{index}] status must be VERIFIED or CLAIMED_UNVERIFIED")
        evidence = item.get("evidence_refs", [])
        if not isinstance(evidence, list) or any(not isinstance(ref, str) or not ref.strip() for ref in evidence):
            raise ValueError(f"adoption completed_work[{index}].evidence_refs must be an array of non-empty strings")
        if item["status"] == "VERIFIED" and not evidence:
            raise ValueError(f"adoption completed_work[{index}] cannot be VERIFIED without evidence_refs")

    decisions = packet.get("prior_decisions", [])
    if not isinstance(decisions, list):
        raise ValueError("adoption prior_decisions must be an array")
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict) or not isinstance(decision.get("question"), str) or not decision["question"].strip():
            raise ValueError(f"adoption prior_decisions[{index}] requires question")
        if not isinstance(decision.get("choice"), str) or not decision["choice"].strip():
            raise ValueError(f"adoption prior_decisions[{index}] requires choice")
        if decision.get("status") != "REQUIRES_REVALIDATION":
            raise ValueError(f"adoption prior_decisions[{index}] must remain REQUIRES_REVALIDATION")

    open_items = packet.get("open_items", [])
    if not isinstance(open_items, list) or any(not isinstance(item, str) or not item.strip() for item in open_items):
        raise ValueError("adoption open_items must be an array of non-empty strings")
    failures = packet.get("failure_history", [])
    if not isinstance(failures, list):
        raise ValueError("adoption failure_history must be an array")
    for index, failure in enumerate(failures):
        if not isinstance(failure, dict) or not isinstance(failure.get("symptom"), str) or not failure["symptom"].strip():
            raise ValueError(f"adoption failure_history[{index}] requires symptom")
        failure_status = failure.get("status")
        if not isinstance(failure_status, str) or failure_status not in {"OPEN", "RESOLVED_UNVERIFIED", "RESOLVED_WITH_EVIDENCE"}:
            raise ValueError(f"adoption failure_history[{index}] has an unsupported status")
        refs = failure.get("evidence_refs", [])
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ValueError(f"adoption failure_history[{index}].evidence_refs must be an array of non-empty strings")
        if failure["status"] == "RESOLVED_WITH_EVIDENCE" and not refs:
            raise ValueError(f"adoption failure_history[{index}] cannot claim evidence-backed resolution without evidence_refs")

    next_action = packet.get("next_action")
    if not isinstance(next_action, str) or not next_action.strip():
        raise ValueError("adoption packet requires a concrete next_action")
    boundary = packet.get("context_boundary", {
        "mode": "DECLARED_INPUTS_PLUS_PROJECT_BRIEF",
        "allowed_input_names": [],
        "excluded_context_refs": [],
        "allow_prior_conversation": False,
        "allow_sibling_task_context": False,
        "isolated_chat_required": False,
    })
    validate_context_boundary(boundary)
    return packet


def resolve_intake(root: str | Path, request: dict[str, Any]) -> dict[str, Any]:
    """Return a read-only route; never create a task, infer a project, or assert CAOS ran."""
    if not isinstance(request, dict) or request.get("mode") not in {"NEW", "RESUME", "ADOPT"}:
        raise ValueError("explicit NEW, RESUME or ADOPT mode required")
    manifest = contract()
    assert_scope_epoch(manifest)
    mode = request["mode"]
    adoption_packet = None
    if mode == "NEW":
        goal = request.get("goal")
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("NEW requires exact current owner goal")
        project_id = request.get("project_id")
        if project_id is not None:
            project_id = _id(project_id)
            project_path = Path(root).expanduser().resolve() / "projects" / project_id
            if project_path.exists() or project_path.is_symlink():
                raise ValueError("NEW cannot reuse an existing project")
        brief = None
    elif mode == "ADOPT":
        project_id = _id(request.get("project_id"))
        project_path = Path(root).expanduser().resolve() / "projects" / project_id
        if project_path.exists() or project_path.is_symlink():
            raise ValueError("ADOPT requires a new project_id; use RESUME for an existing project")
        brief = bind_owner_brief(project_id, request.get("brief"))
        adoption_packet = validate_adoption_packet(request.get("adoption_packet"), brief)
        goal = brief["goal"]
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
            declarations, expected_ids=(brief.get("deliverables") if mode in {"RESUME", "ADOPT"} else request.get("deliverables")))
    from .domain.identity import identity_route
    identity_routing = identity_route(typed["deliverables"]) if typed else None
    from .subsystems import route_declared_content
    internal_subsystem_routing = route_declared_content(typed["deliverables"]) if typed else None
    return {
        "mode": mode, "goal": goal, "project_id": project_id, "brief": brief,
        "adoption_packet": adoption_packet if mode == "ADOPT" else None,
        "task_graph_created": False,
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
