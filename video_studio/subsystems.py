"""Source-based internal subsystem ownership and static import graph audit.

Checks the real files and Python imports in BOTH packages, not subsystem
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
        "docs/": "DOCUMENTATION", "skills/video-growth-agent/": "CURRENT_SKILL_REFERENCES",
        "video_studio/data/": "CURRENT_DOMAIN_CONFIGURATION",
        "video_growth_agent/data/": "SCOPED_DOMAIN_OR_HISTORICAL_CONFIGURATION",
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
    cat = json.loads((root / "video_studio/data/subsystem_catalog.json").read_text(encoding="utf-8"))
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
        if sub["product_membership"] != "INTERNAL_CONTENT_STUDIO":
            errors.append(f"subsystem wrongly external: {sid}")
        if sub["active_by_default"] is not False:
            errors.append(f"unauthorized default activation: {sid}")
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
    python_files = [x for x in files if x.endswith(".py") and
                    x.startswith(("video_studio/", "video_growth_agent/"))]
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
    for start in sorted(n for n in module_files if n.startswith("video_studio")):
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

    if cat.get("current_runtime") != "video_studio.engine.StudioEngine":
        errors.append("multiple or wrong durable control authority")
    if cat.get("boundaries", {}).get("ipos", {}).get("product_membership") != "INTERNAL_CONTENT_STUDIO":
        errors.append("IPOS product ownership misidentified")
    if owners.get("video_growth_agent/ip_identity.py") != "original_identity_ipos":
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
        "dependency_edges": [{"from": a, "to": b, "source": s, "target": t}
                             for a,b,s,t in sorted(cross)],
        "module_sha256": digests,
        "semantic_line_by_line_complete": False,
        "real_creative_quality_verified": False,
        "native_caos_selection_verified": False,
    }
