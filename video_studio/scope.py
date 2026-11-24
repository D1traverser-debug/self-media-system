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

EPOCH = "VIDEO_TASK_NEUTRAL_20261124"


def contract() -> dict[str, Any]:
    return json.loads(files("video_studio").joinpath("data", "studio_manifest.json").read_text(encoding="utf-8"))


def _id(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value):
        raise ValueError("exact safe project_id required")
    if value.casefold() in {item.casefold() for item in contract()["task_admission"]["retired_project_ids"]}:
        raise ValueError("retired project instance cannot be resumed or reused")
    return value


def bind_owner_brief(project_id: str, brief: dict[str, Any]) -> dict[str, Any]:
    _id(project_id)
    if not isinstance(brief, dict) or not isinstance(brief.get("goal"), str) or not brief["goal"].strip():
        raise ValueError("exact current owner goal is required")
    if brief.get("scope_epoch", EPOCH) != EPOCH:
        raise ValueError("cannot reuse a retired scope epoch")
    return {**brief, "scope_epoch": EPOCH}


def validate_task_binding(brief: dict[str, Any], task: dict[str, Any]) -> None:
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
    return {
        "mode": mode, "goal": goal, "project_id": project_id, "brief": brief,
        "scope_epoch": EPOCH, "selected_task_graph": None,
        "default_project_id": None, "automatic_resume": False,
        "architecture": manifest["architecture"],
        "capabilities": manifest["capabilities"],
        "knowledge_catalog": manifest["knowledge_lifecycle"]["index"],
        "capability_catalog": "video_growth_agent/data/capabilities.json",
        "parent_governance": "REQUIRED_IN_OWNER_SESSION",
        "native_activation": "NOT_VERIFIED_BY_RUNTIME",
        "effect_authorized": False,
    }


def knowledge_lookup(method_id: str | None = None, *, include_nonactive: bool = False,
                     repo_root: str | Path | None = None) -> dict[str, Any]:
    """Locate reusable sources by exact stable identity; never select a task or grant authority."""
    catalog = json.loads(files("video_studio").joinpath("data", "knowledge_catalog.json").read_text(encoding="utf-8"))
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
