"""Source-based internal subsystem ownership and static import graph audit.

Checks real files and imports in the single package and nested legacy domain, not subsystem
names guessed from a diagram. Static evidence cannot certify business quality.
"""
from __future__ import annotations

import ast
from collections import deque
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


def _source_files(root: Path) -> list[str]:
    try:
        run = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                             capture_output=True, check=False, timeout=20)
        if run.returncode == 0 and run.stdout:
            return sorted(p for p in run.stdout.decode("utf-8").split("\0")
                          if p and (root / p).is_file())
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        pass
    ignored = {".git", ".pytest_cache", ".mypy_cache", ".ruff_cache",
               "__pycache__", "dist", "build", ".venv", "venv"}
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and not set(p.relative_to(root).parts).intersection(ignored)
                  and p.suffix not in {".pyc", ".pyo"})


def _module(path: str) -> str:
    parts = Path(path).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _imports(path: Path, module: str) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    deps: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            deps.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if not node.level:
                if node.module:
                    deps.add(node.module)
            else:
                package = module.split(".") if path.name == "__init__.py" else module.split(".")[:-1]
                if node.level > len(package):
                    raise ValueError(f"relative import escapes package at {path}:{node.lineno}")
                prefix = ".".join(package[:len(package) - node.level + 1])
                if node.module:
                    deps.add(prefix + "." + node.module)
                else:
                    deps.update(prefix + "." + alias.name for alias in node.names)
    return deps


def _classification(path: str, owners: dict[str, str]) -> str | None:
    if path in owners:
        return owners[path]
    prefixes = {
        "tests/": "TEST_COVERAGE", "examples/": "RETIRED_TASK_FIXTURE",
        "projects/": "RETIRED_PROJECT_EVIDENCE", "audits/": "AUDIT_EVIDENCE",
        "docs/": "DOCUMENTATION", "skills/social-media-studio/": "CURRENT_SKILL_REFERENCES",
        "social_media_studio/data/": "CURRENT_DOMAIN_CONFIGURATION",
        "social_media_studio/legacy/data/": "SCOPED_DOMAIN_OR_HISTORICAL_CONFIGURATION",
        ".github/": "REPOSITORY_CI",
    }
    for prefix, category in prefixes.items():
        if path.startswith(prefix):
            return category
    if path in {".gitignore", "README.md", "STUDIO_ENTRY.md", "pyproject.toml"}:
        return "REPOSITORY_ENTRY"
    return None


def audit_subsystems(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[1]
    cat = json.loads((root / "social_media_studio/data/subsystem_catalog.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    owners: dict[str, str] = {}
    adapter_map: dict[str, str] = {}
    operation_map: dict[str, str] = {}
    subs = cat.get("subsystems", [])
    ids: set[str] = set()
    for sub in subs:
        sid = sub["id"]
        if sid in ids:
            errors.append(f"duplicate subsystem: {sid}")
        ids.add(sid)
        if sub["product_membership"] != "INTERNAL_SOCIAL_MEDIA_STUDIO":
            errors.append(f"subsystem wrongly external: {sid}")
        if sub["active_by_default"] is not False:
            errors.append(f"unauthorized default activation: {sid}")
        if not sub["code_paths"] and not (
            sid == "research_and_understanding"
            and sub.get("status") == "IMPLEMENTATION_GAP_NOT_A_REMOTE_SERVICE"
            and not sub["domain_adapters"] and not sub["production_operations"]
        ):
            errors.append(f"unjustified code-free internal subsystem: {sid}")
        for path in sub["code_paths"]:
            if path in owners:
                errors.append(f"duplicate module owner: {path}")
            owners[path] = sid
        for field, mapping in (("domain_adapters", adapter_map),
                               ("production_operations", operation_map)):
            for op in sub[field]:
                if op in mapping:
                    errors.append(f"duplicate operation ownership: {op}")
                mapping[op] = sid
    files = _source_files(root)
    all_file_sha256: dict[str, str] = {}
    parsed_json_count = 0
    for tracked in files:
        try:
            raw = (root / tracked).read_bytes()
            all_file_sha256[tracked] = hashlib.sha256(raw).hexdigest()
            if tracked.endswith(".json"):
                json.loads(raw.decode("utf-8"))
                parsed_json_count += 1
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"unreadable or malformed tracked source: {tracked}: {exc}")
    python_files = [x for x in files if x.endswith(".py") and
                    x.startswith(("social_media_studio/", "social_media_studio/legacy/"))]
    for path in python_files:
        if path not in owners:
            errors.append(f"UNOWNED Python module: {path}")
    for path in owners:
        if path not in python_files:
            errors.append(f"missing declared Python module: {path}")
    unclassified = [path for path in files if _classification(path, owners) is None]
    errors.extend(f"unclassified repository path: {path}" for path in unclassified)

    module_files = {_module(path): path for path in python_files}
    imports: dict[str, set[str]] = {}
    cross: set[tuple[str, str, str, str]] = set()
    digests: dict[str, str] = {}
    for path in python_files:
        name = _module(path)
        try:
            digests[path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
            found = set()
            for candidate in _imports(root / path, name):
                while candidate not in module_files and "." in candidate:
                    candidate = candidate.rsplit(".", 1)[0]
                if candidate in module_files:
                    found.add(candidate)
                    other = module_files[candidate]
                    if owners.get(path) != owners.get(other):
                        cross.add((owners.get(path, "?"), owners.get(other, "?"), path, other))
            imports[name] = found
        except (OSError, SyntaxError, UnicodeError, ValueError) as exc:
            errors.append(f"source could not be inspected: {path}: {exc}")

    old = next((s for s in subs if s["id"] == "legacy_agent_control_plane"), None)
    if old is None or old.get("activation") != "ISOLATED_HISTORICAL_FIXTURE_ONLY":
        errors.append("legacy controller not explicitly retired")
    retired = {_module(path) for path in old["code_paths"]} if old else set()
    for start in sorted(n for n in module_files if (n == "social_media_studio" or n.startswith("social_media_studio.")) and not (n == "social_media_studio.legacy" or n.startswith("social_media_studio.legacy."))):
        seen: set[str] = set()
        to_visit = deque([start])
        while to_visit:
            current = to_visit.popleft()
            if current in seen:
                continue
            seen.add(current)
            if current in retired:
                errors.append(f"current module {start} reaches old controller {current}")
                break
            to_visit.extend(imports.get(current, set()) - seen)

    from .domain.contracts import DELIVERABLE_TYPES
    routes = cat.get("deliverable_ownership", {})
    if set(routes) != DELIVERABLE_TYPES:
        errors.append("typed deliverable ownership is incomplete or contains phantom types")
    for typ, route in routes.items():
        selected = [route.get("primary"), *route.get("optional", [])]
        if len(selected) != len(set(selected)) or any(x not in ids for x in selected):
            errors.append(f"invalid internal subsystem route for {typ}")
        if "legacy_agent_control_plane" in selected:
            errors.append(f"retired controller cannot own current deliverable: {typ}")
    nested = cat.get("nested_product_capabilities", [])
    for item in nested:
        sid = item.get("owner_subsystem")
        module = item.get("source_module")
        if sid not in ids or owners.get(module) != sid:
            errors.append(f"nested content capability has no actual internal code owner: {item.get('id')}")
        if item.get("membership") != "INTERNAL_SOCIAL_MEDIA_STUDIO":
            errors.append(f"nested capability misidentified as external: {item.get('id')}")
    siblings = cat.get("caos_sibling_business_systems", [])
    for item in siblings:
        if item.get("relationship") != "CAOS_PEER_BUSINESS_SYSTEM" or item.get("task_authority_transfer") is not False or item.get("canon_or_file_write_transfer") is not False:
            errors.append(f"cross-system authority mistakenly merged: {item.get('id')}")
    previous_cli = (root / "social_media_studio/legacy/cli.py").read_text(encoding="utf-8")
    if ('SMS_LEGACY_FIXTURE_ROOT' not in previous_cli or
            'Legacy Video 0.8 control is retired' not in previous_cli or
            'Legacy output/graph writes must remain inside explicit fixture root' not in previous_cli or
            'StudioRuntime(store=ProjectStore(Path(fixture_root)))' not in previous_cli):
        errors.append("old standalone CLI owner-write entrypoint is not fenced")
    if cat.get("current_runtime") != "social_media_studio.engine.StudioEngine":
        errors.append("multiple or wrong durable control authority")
    try:
        active_domain = json.loads((root / "social_media_studio/legacy/data/domain_manifest.json")
                                   .read_text(encoding="utf-8"))["domain_authority"]
        identity_source = active_domain.get("internal_original_identity_subsystem", {})
        if "external_identity_authority" in active_domain:
            errors.append("misleading old external identity key remains current authority")
        if (identity_source.get("product_membership") != "INTERNAL_SOCIAL_MEDIA_STUDIO"
                or identity_source.get("subsystem_id") != "original_identity_ipos"
                or identity_source.get("studio_mutation_of_canon") is not False):
            errors.append("internal IPOS product authority contradicts source custody")
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"current IPOS domain authority cannot be verified: {exc}")
    if cat.get("boundaries", {}).get("ipos", {}).get("product_membership") != "INTERNAL_SOCIAL_MEDIA_STUDIO":
        errors.append("IPOS product ownership misidentified")
    if owners.get("social_media_studio/legacy/ip_identity.py") != "original_identity_ipos":
        errors.append("IPOS implementation source is not owned by identity subsystem")
    if cat.get("boundaries", {}).get("caos", {}).get("code_mutation_forbidden") is not True:
        errors.append("CAOS parent source is not protected read-only")
    if cat.get("boundaries", {}).get("publication", {}).get("auto_post") is not False:
        errors.append("implicit publication authority")
    from .adapters import SUPPORTED_DOMAIN_ADAPTERS
    from .production.registry import PRODUCTION_EXECUTORS
    if set(adapter_map) != set(SUPPORTED_DOMAIN_ADAPTERS):
        errors.append("catalog adapter ownership differs from real registered adapters")
    if set(operation_map) != set(PRODUCTION_EXECUTORS.operations()):
        errors.append("catalog executor ownership differs from actual registered tool operations")
    return {
        "pass": not errors, "assurance": "REPOSITORY_STRUCTURE_AND_STATIC_AST_ONLY",
        "tracked_files": len(files), "code_modules": len(python_files),
        "owned_modules": len(owners), "subsystems": len(ids),
        "domain_adapters": len(adapter_map), "production_operations": len(operation_map),
        "unclassified_paths": unclassified, "violations": sorted(set(errors)),
        "all_tracked_file_sha256": all_file_sha256,
        "all_tracked_bytes_inspected": len(all_file_sha256) == len(files),
        "json_documents_parsed": parsed_json_count,
        "dependency_edges": [{"from": a, "to": b, "source": s, "target": t}
                             for a,b,s,t in sorted(cross)],
        "module_sha256": digests,
        "semantic_line_by_line_complete": False,
        "real_creative_quality_verified": False,
        "native_caos_selection_verified": False,
    }


def route_declared_content(deliverables: list[dict[str, Any]]) -> dict[str, Any]:
    """Read-only owner routing by REAL internal product responsibility.

    Secondary specialists are advisory, not automatically enlisted. CAOS parent
    is a cross-cutting authority, not a new Studio task-graph controller.
    """
    from importlib.resources import files
    from .domain.contracts import DELIVERABLE_TYPES
    cat = json.loads(files("social_media_studio").joinpath("data", "subsystem_catalog.json")
                     .read_text(encoding="utf-8"))
    known = {s["id"]: s for s in cat["subsystems"]}
    routes = cat["deliverable_ownership"]
    if set(routes) != DELIVERABLE_TYPES:
        raise ValueError("unmapped or phantom content deliverable type")
    result = []
    for item in deliverables:
        kind = item["type"]
        entry = routes.get(kind)
        if not entry or entry["primary"] not in known:
            raise ValueError(f"unowned content deliverable: {kind}")
        primary = entry["primary"]
        if primary == "legacy_agent_control_plane":
            raise ValueError("retired controller cannot own a current owner outcome")
        if any(x not in known for x in entry["optional"]):
            raise ValueError("optional specialist is not internally declared")
        constraints = item.get("constraints", {})
        mode = constraints.get("identity_mode")
        # This boundary applies to a one-time visual avatar, not all images.
        identity = ("CURRENT_IPOS_APPROVAL_REQUIRED"
                    if mode in {"APPROVED_CANON_USE", "IDENTITY_DERIVATIVE"}
                    else "CURRENT_IPOS_SPECIALIST_DESIGN"
                    if mode == "PERSISTENT_IDENTITY_DESIGN"
                    else "TEMPORARY_NO_PERSONAL_IPOS"
                    if mode == "TEMPORARY_CHARACTER"
                    else "NOT_AUTOMATIC")
        result.append({
            "deliverable_id": item["id"], "type": kind,
            "primary_internal_subsystem": primary,
            "potential_specialists_not_selected": entry["optional"],
            "internal_product_membership": "SOCIAL_MEDIA_STUDIO",
            "identity_scope": identity,
            "source_custody_is_not_business_boundary": True,
            "actual_executor_verified": False,
            "independent_outcome_verified": False,
            "effect_authorized": False,
        })
    return {
        "routes": result, "no_default_project": True,
        "selected_task_graph": None, "caos_native_activation": "NOT_VERIFIED",
        "peer_system_task_authority_inherited": False,
        "status": "CONTENT_DOMAIN_OWNERSHIP_ONLY_NO_ACTION",
    }
