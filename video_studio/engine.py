from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import uuid
from typing import Any, Iterable


SCHEMA_VERSION = 1
TASK_STATES = {
    "PENDING", "READY", "RUNNING", "WAITING_INPUT", "BLOCKED",
    "FAILED", "COMPLETED", "STALE", "CANCELLED",
}
RIGHTS_ALLOWED = {"OWNED", "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN"}
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class StudioError(RuntimeError):
    """Base error for the standalone Video Studio runtime."""


class ProjectNotFound(StudioError):
    pass


class ContractError(StudioError):
    pass


class ClaimError(StudioError):
    pass


class GateError(StudioError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _now()).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, default: Any = None) -> Any:
    return json.loads(value) if value is not None else default


def _safe_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ContractError(f"{label} must match {_ID.pattern}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(root: Path, candidate: str | Path) -> Path:
    path = Path(candidate)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve(strict=True)
    base = root.resolve(strict=True)
    if resolved != base and base not in resolved.parents:
        raise ContractError(f"artifact path escapes project workspace: {candidate}")
    if not resolved.is_file():
        raise ContractError(f"artifact must be a regular file: {candidate}")
    return resolved


@dataclass(frozen=True)
class TaskClaim:
    project_id: str
    task_id: str
    worker_id: str
    claim_token: str
    lease_until: str
    attempt: int


class StudioEngine:
    """Outcome-driven, standalone project and production runtime.

    The engine deliberately has no dependency on CAOS, an LLM vendor, or a fixed
    stage machine. A planner supplies a project-specific DAG; independent workers
    claim ready nodes through SQLite transactions and return immutable artifacts.
    """

    def __init__(self, root: str | Path | None = None):
        default = Path(os.environ.get("VGA_STUDIO_HOME", Path.home() / ".vga-studio"))
        self.root = Path(root or default).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "projects").mkdir(exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        project_id = _safe_id(project_id, "project_id")
        return self.root / "projects" / project_id

    @staticmethod
    def _migrate(connection: sqlite3.Connection) -> None:
        task_columns = {row[1] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()}
        if "claim_inputs_json" not in task_columns:
            connection.execute("ALTER TABLE tasks ADD COLUMN claim_inputs_json TEXT NOT NULL DEFAULT '[]'")
        review_columns = {row[1] for row in connection.execute("PRAGMA table_info(reviews)").fetchall()}
        if "evidence_bindings_json" not in review_columns:
            connection.execute("ALTER TABLE reviews ADD COLUMN evidence_bindings_json TEXT NOT NULL DEFAULT '[]'")
        version_row = connection.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        if version_row is None or version_row["value"] != "2":
            connection.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', '2')")

    def _connect(self, project_id: str) -> sqlite3.Connection:
        db_path = self._project_dir(project_id) / "studio.sqlite3"
        if not db_path.is_file():
            raise ProjectNotFound(project_id)
        connection = sqlite3.connect(db_path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA synchronous = FULL")
        self._migrate(connection)
        return connection

    @staticmethod
    def _schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous = FULL;
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                brief_json TEXT NOT NULL,
                revision INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                project_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                executor TEXT NOT NULL,
                depends_on_json TEXT NOT NULL,
                inputs_json TEXT NOT NULL,
                outputs_json TEXT NOT NULL,
                acceptance_json TEXT NOT NULL,
                requirements_json TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                attempts INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                worker_id TEXT,
                claim_token TEXT,
                lease_until TEXT,
                claim_inputs_json TEXT NOT NULL DEFAULT '[]',
                result_json TEXT,
                error_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(project_id, task_id),
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_claim
                ON tasks(project_id, status, priority DESC, created_at);
            CREATE TABLE IF NOT EXISTS artifacts (
                project_id TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                name TEXT NOT NULL,
                version INTEGER NOT NULL,
                relative_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                rights_status TEXT NOT NULL,
                produced_by_task TEXT,
                producer_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(project_id, artifact_id),
                UNIQUE(project_id, name, version),
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE INDEX IF NOT EXISTS idx_artifacts_name
                ON artifacts(project_id, name, version DESC);
            CREATE TABLE IF NOT EXISTS reviews (
                project_id TEXT NOT NULL,
                review_id TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                artifact_digest TEXT NOT NULL,
                rubric_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                producer_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                dimensions_json TEXT NOT NULL,
                evidence_refs_json TEXT NOT NULL,
                evidence_bindings_json TEXT NOT NULL DEFAULT '[]',
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(project_id, review_id),
                FOREIGN KEY(project_id, artifact_id)
                    REFERENCES artifacts(project_id, artifact_id)
            );
            CREATE TABLE IF NOT EXISTS decisions (
                project_id TEXT NOT NULL,
                decision_id TEXT NOT NULL,
                question TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(project_id, decision_id),
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TABLE IF NOT EXISTS failures (
                project_id TEXT NOT NULL,
                failure_id TEXT NOT NULL,
                task_id TEXT,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                resolution_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(project_id, failure_id),
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TABLE IF NOT EXISTS learning (
                project_id TEXT NOT NULL,
                learning_id TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(project_id, learning_id),
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TABLE IF NOT EXISTS events (
                event_no INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TRIGGER IF NOT EXISTS events_no_update
                BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'event history is append-only'); END;
            CREATE TRIGGER IF NOT EXISTS events_no_delete
                BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'event history is append-only'); END;
            CREATE TRIGGER IF NOT EXISTS artifact_identity_immutable
                BEFORE UPDATE OF name,version,relative_path,sha256,size_bytes,media_type,kind,rights_status,
                                 produced_by_task,producer_id,metadata_json ON artifacts
                BEGIN SELECT RAISE(ABORT, 'artifact identity and provenance are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS reviews_no_update
                BEFORE UPDATE ON reviews BEGIN SELECT RAISE(ABORT, 'review receipts are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS reviews_no_delete
                BEFORE DELETE ON reviews BEGIN SELECT RAISE(ABORT, 'review receipts are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS decisions_no_update
                BEFORE UPDATE ON decisions BEGIN SELECT RAISE(ABORT, 'decision receipts are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS decisions_no_delete
                BEFORE DELETE ON decisions BEGIN SELECT RAISE(ABORT, 'decision receipts are immutable'); END;
            INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', '2');
            """
        )

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        project_id: str,
        entity_type: str,
        entity_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        connection.execute(
            "INSERT INTO events(project_id,entity_type,entity_id,event_type,payload_json,created_at) VALUES(?,?,?,?,?,?)",
            (project_id, entity_type, entity_id, event_type, _json(payload), _iso()),
        )

    @staticmethod
    def _project_row(connection: sqlite3.Connection, project_id: str) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
        if row is None:
            raise ProjectNotFound(project_id)
        return row

    @staticmethod
    def _validate_brief(brief: dict[str, Any]) -> None:
        if not isinstance(brief, dict):
            raise ContractError("brief must be a JSON object")
        required = ["goal", "audience", "deliverables"]
        missing = [key for key in required if not brief.get(key)]
        if missing:
            raise ContractError(f"brief is missing required outcome fields: {missing}")
        if not isinstance(brief["goal"], str) or not isinstance(brief["audience"], str):
            raise ContractError("brief.goal and brief.audience must be strings")
        if not isinstance(brief["deliverables"], list) or not all(isinstance(item, str) and item.strip() for item in brief["deliverables"]):
            raise ContractError("brief.deliverables must be a non-empty array of strings")

    def create_project(self, project_id: str, title: str, brief: dict[str, Any]) -> dict[str, Any]:
        project_id = _safe_id(project_id, "project_id")
        self._validate_brief(brief)
        directory = self._project_dir(project_id)
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "assets").mkdir()
        (directory / "artifacts").mkdir()
        db_path = directory / "studio.sqlite3"
        connection = sqlite3.connect(db_path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            self._schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            now = _iso()
            connection.execute(
                "INSERT INTO projects(project_id,title,brief_json,created_at,updated_at) VALUES(?,?,?,?,?)",
                (project_id, title or project_id, _json(brief), now, now),
            )
            self._event(connection, project_id, "PROJECT", project_id, "PROJECT_CREATED", {"title": title, "brief": brief})
            connection.commit()
        except Exception:
            connection.rollback()
            shutil.rmtree(directory, ignore_errors=True)
            raise
        finally:
            connection.close()
        return self.project(project_id)

    def project(self, project_id: str) -> dict[str, Any]:
        with closing(self._connect(project_id)) as connection:
            row = self._project_row(connection, project_id)
            return {
                "project_id": row["project_id"], "title": row["title"],
                "brief": _loads(row["brief_json"], {}), "revision": row["revision"],
                "created_at": row["created_at"], "updated_at": row["updated_at"],
                "workspace": str(self._project_dir(project_id)),
            }

    @staticmethod
    def _descendant_closure(tasks: dict[str, dict[str, Any]], roots: Iterable[str]) -> set[str]:
        closure = set(roots)
        changed = True
        while changed:
            changed = False
            for candidate, row in tasks.items():
                deps = _loads(row["depends_on_json"], []) if "depends_on_json" in row else row.get("depends_on", [])
                if candidate not in closure and any(dep in closure for dep in deps):
                    closure.add(candidate)
                    changed = True
        return closure

    def brief_history(self, project_id: str) -> list[dict[str, Any]]:
        with closing(self._connect(project_id)) as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE project_id=? AND entity_type='PROJECT' AND event_type IN ('PROJECT_CREATED','PROJECT_BRIEF_REVISED') ORDER BY event_no",
                (project_id,),
            ).fetchall()
            return [{**dict(row), "payload": _loads(row["payload_json"], {})} for row in rows]

    def revise_brief(
        self, project_id: str, brief: dict[str, Any], *, reason: str,
        affected_task_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        self._validate_brief(brief)
        if not isinstance(reason, str) or not reason.strip():
            raise ContractError("brief revision requires a reason")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                project = self._project_row(connection, project_id)
                tasks = self._task_map(connection, project_id)
                roots = list(tasks) if affected_task_ids is None else list(affected_task_ids)
                unknown = sorted(set(roots) - set(tasks))
                if unknown:
                    raise ContractError(f"unknown affected_task_ids: {unknown}")
                invalidated = self._descendant_closure(tasks, roots) if roots else set()
                old_brief = _loads(project["brief_json"], {})
                old_digest = hashlib.sha256(_json(old_brief).encode("utf-8")).hexdigest()
                new_digest = hashlib.sha256(_json(brief).encode("utf-8")).hexdigest()
                now = _iso()
                connection.execute(
                    "UPDATE projects SET brief_json=?,revision=revision+1,updated_at=? WHERE project_id=?",
                    (_json(brief), now, project_id),
                )
                for task_id in invalidated:
                    connection.execute(
                        "UPDATE tasks SET status='STALE',worker_id=NULL,claim_token=NULL,lease_until=NULL,claim_inputs_json='[]',error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                        (_json({"reason": reason, "brief_revision": int(project["revision"]) + 1}), now, project_id, task_id),
                    )
                    connection.execute(
                        "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                        (project_id, task_id),
                    )
                    self._event(connection, project_id, "TASK", task_id, "TASK_INVALIDATED_BY_BRIEF_REVISION", {
                        "reason": reason, "project_revision": int(project["revision"]) + 1,
                    })
                self._event(connection, project_id, "PROJECT", project_id, "PROJECT_BRIEF_REVISED", {
                    "previous_brief": old_brief, "brief": brief,
                    "previous_sha256": old_digest, "sha256": new_digest,
                    "reason": reason, "invalidated_tasks": sorted(invalidated),
                })
                self._refresh_in_tx(connection, project_id)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {"project": self.project(project_id), "invalidated_tasks": sorted(invalidated), "brief_history": self.brief_history(project_id)}

    def _validate_graph(self, all_tasks: dict[str, dict[str, Any]]) -> None:
        for task_id, task in all_tasks.items():
            deps = task.get("depends_on", [])
            if len(deps) != len(set(deps)):
                raise ContractError(f"{task_id}: duplicate dependencies")
            missing = [dep for dep in deps if dep not in all_tasks]
            if missing:
                raise ContractError(f"{task_id}: unknown dependencies {missing}")
            if task_id in deps:
                raise ContractError(f"{task_id}: task cannot depend on itself")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ContractError(f"dependency cycle detected at {task_id}")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in all_tasks[task_id].get("depends_on", []):
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in all_tasks:
            visit(task_id)
        output_owners: dict[str, str] = {}
        for task_id, task in all_tasks.items():
            for output in task.get("outputs", []):
                previous = output_owners.get(output)
                if previous is not None and previous != task_id:
                    raise ContractError(f"artifact output {output!r} has multiple producers: {previous}, {task_id}")
                output_owners[output] = task_id

    def add_tasks(self, project_id: str, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(tasks, list) or not tasks:
            raise ContractError("tasks must be a non-empty array")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._project_row(connection, project_id)
                existing_rows = connection.execute(
                    "SELECT task_id,title,kind,executor,depends_on_json,inputs_json,outputs_json,acceptance_json,requirements_json,priority,max_attempts FROM tasks WHERE project_id=?",
                    (project_id,),
                ).fetchall()
                existing_artifact_names = {
                    row["name"] for row in connection.execute(
                        "SELECT name FROM artifacts WHERE project_id=? AND status IN ('CURRENT','ACCEPTED')",
                        (project_id,),
                    ).fetchall()
                }
                graph: dict[str, dict[str, Any]] = {
                    row["task_id"]: {
                        "depends_on": _loads(row["depends_on_json"], []),
                        "outputs": _loads(row["outputs_json"], []),
                    } for row in existing_rows
                }
                prepared: list[dict[str, Any]] = []
                new_ids: set[str] = set()
                declared_outputs = {
                    output for task in graph.values() for output in task.get("outputs", [])
                }
                for raw in tasks:
                    if not isinstance(raw, dict):
                        raise ContractError("each task must be an object")
                    task_id = _safe_id(raw.get("task_id", ""), "task_id")
                    if task_id in graph or task_id in new_ids:
                        raise ContractError(f"duplicate task_id: {task_id}")
                    title = str(raw.get("title") or task_id).strip()
                    kind = str(raw.get("kind") or "production").strip()
                    executor = str(raw.get("executor") or "agent").strip()
                    if executor not in {"agent", "tool", "human", "external"}:
                        raise ContractError(f"{task_id}: unsupported executor {executor}")
                    deps_raw = raw.get("depends_on", [])
                    inputs_raw = raw.get("inputs", [])
                    outputs_raw = raw.get("outputs", [])
                    if not all(isinstance(value, list) for value in (deps_raw, inputs_raw, outputs_raw)):
                        raise ContractError(f"{task_id}: depends_on, inputs and outputs must be arrays")
                    deps = list(deps_raw)
                    inputs = list(inputs_raw)
                    outputs = list(outputs_raw)
                    if not all(isinstance(value, str) for value in deps + inputs + outputs):
                        raise ContractError(f"{task_id}: dependency, input and output names must be strings")
                    if len(inputs) != len(set(inputs)):
                        raise ContractError(f"{task_id}: duplicate inputs")
                    if len(outputs) != len(set(outputs)) or not outputs:
                        raise ContractError(f"{task_id}: outputs must be a non-empty unique list")
                    for output in outputs:
                        _safe_id(output, "artifact output name")
                    duplicate_outputs = declared_outputs.intersection(outputs)
                    if duplicate_outputs:
                        raise ContractError(f"output names must have one producer: {sorted(duplicate_outputs)}")
                    imported_name_conflicts = existing_artifact_names.intersection(outputs)
                    if imported_name_conflicts:
                        raise ContractError(f"task outputs cannot reuse existing artifact names: {sorted(imported_name_conflicts)}")
                    declared_outputs.update(outputs)
                    acceptance = raw.get("acceptance", {})
                    requirements = raw.get("requirements", {})
                    if not isinstance(acceptance, dict) or not acceptance:
                        raise ContractError(f"{task_id}: acceptance must be a non-empty object")
                    if not isinstance(requirements, dict):
                        raise ContractError(f"{task_id}: requirements must be an object")
                    max_attempts = int(raw.get("max_attempts", 3))
                    if max_attempts < 1 or max_attempts > 20:
                        raise ContractError(f"{task_id}: max_attempts must be 1..20")
                    task = {
                        "task_id": task_id, "title": title, "kind": kind,
                        "executor": executor, "depends_on": deps, "inputs": inputs,
                        "outputs": outputs, "acceptance": acceptance, "requirements": requirements,
                        "priority": int(raw.get("priority", 0)),
                        "max_attempts": max_attempts,
                    }
                    prepared.append(task)
                    graph[task_id] = task
                    new_ids.add(task_id)
                self._validate_graph(graph)
                now = _iso()
                for task in prepared:
                    connection.execute(
                        """INSERT INTO tasks(project_id,task_id,title,kind,executor,depends_on_json,inputs_json,
                           outputs_json,acceptance_json,requirements_json,priority,max_attempts,status,created_at,updated_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'PENDING',?,?)""",
                        (project_id, task["task_id"], task["title"], task["kind"], task["executor"],
                         _json(task["depends_on"]), _json(task["inputs"]), _json(task["outputs"]),
                         _json(task["acceptance"]), _json(task["requirements"]), task["priority"], task["max_attempts"], now, now),
                    )
                    self._event(connection, project_id, "TASK", task["task_id"], "TASK_ADDED", task)
                connection.execute(
                    "UPDATE projects SET revision=revision+1,updated_at=? WHERE project_id=?",
                    (now, project_id),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        self.refresh(project_id)
        return self.list_tasks(project_id)

    def revise_task(self, project_id: str, task_id: str, patch: dict[str, Any], *, reason: str) -> dict[str, Any]:
        """Revise one task contract, stale only its descendants, and revoke any old lease."""
        if not isinstance(patch, dict) or not patch:
            raise ContractError("task revision patch must be a non-empty object")
        if not isinstance(reason, str) or not reason.strip():
            raise ContractError("task revision requires a reason")
        allowed = {"title", "kind", "executor", "depends_on", "inputs", "outputs", "acceptance", "requirements", "priority", "max_attempts"}
        unknown_fields = sorted(set(patch) - allowed)
        if unknown_fields:
            raise ContractError(f"unsupported task revision fields: {unknown_fields}")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                rows = self._task_map(connection, project_id)
                if task_id not in rows:
                    raise ProjectNotFound(task_id)
                old = rows[task_id]
                current = {
                    "task_id": task_id, "title": old["title"], "kind": old["kind"],
                    "executor": old["executor"], "depends_on": _loads(old["depends_on_json"], []),
                    "inputs": _loads(old["inputs_json"], []), "outputs": _loads(old["outputs_json"], []),
                    "acceptance": _loads(old["acceptance_json"], {}), "requirements": _loads(old["requirements_json"], {}),
                    "priority": old["priority"], "max_attempts": old["max_attempts"],
                }
                revised = {**current, **patch}
                if revised["executor"] not in {"agent", "tool", "human", "external"}:
                    raise ContractError(f"unsupported executor: {revised['executor']}")
                for field in ("depends_on", "inputs", "outputs"):
                    if not isinstance(revised[field], list) or not all(isinstance(item, str) for item in revised[field]):
                        raise ContractError(f"{field} must be an array of strings")
                if len(revised["depends_on"]) != len(set(revised["depends_on"])) or len(revised["inputs"]) != len(set(revised["inputs"])):
                    raise ContractError("task dependencies and inputs must be unique")
                if not revised["outputs"] or len(revised["outputs"]) != len(set(revised["outputs"])):
                    raise ContractError("task outputs must be a non-empty unique list")
                for output in revised["outputs"]:
                    _safe_id(output, "artifact output name")
                if not isinstance(revised["acceptance"], dict) or not revised["acceptance"]:
                    raise ContractError("acceptance must be a non-empty object")
                if not isinstance(revised["requirements"], dict):
                    raise ContractError("requirements must be an object")
                revised["max_attempts"] = int(revised["max_attempts"])
                revised["priority"] = int(revised["priority"])
                if revised["max_attempts"] < 1 or revised["max_attempts"] > 20:
                    raise ContractError("max_attempts must be 1..20")
                graph = {
                    key: {"depends_on": _loads(value["depends_on_json"], []), "outputs": _loads(value["outputs_json"], [])}
                    for key, value in rows.items()
                }
                graph[task_id] = {"depends_on": revised["depends_on"], "outputs": revised["outputs"]}
                existing_artifact_names = {
                    row["name"] for row in connection.execute(
                        "SELECT name FROM artifacts WHERE project_id=? AND status IN ('CURRENT','ACCEPTED') AND produced_by_task IS NULL",
                        (project_id,),
                    ).fetchall()
                }
                if existing_artifact_names.intersection(revised["outputs"]):
                    raise ContractError(f"task outputs cannot reuse imported asset names: {sorted(existing_artifact_names.intersection(revised['outputs']))}")
                self._validate_graph(graph)
                descendants = self._descendant_closure(rows, [task_id]) - {task_id}
                now = _iso()
                connection.execute(
                    """UPDATE tasks SET title=?,kind=?,executor=?,depends_on_json=?,inputs_json=?,outputs_json=?,
                       acceptance_json=?,requirements_json=?,priority=?,max_attempts=?,status='PENDING',
                       attempts=0,worker_id=NULL,claim_token=NULL,lease_until=NULL,result_json=NULL,error_json=?,updated_at=?
                       WHERE project_id=? AND task_id=?""",
                    (revised["title"], revised["kind"], revised["executor"], _json(revised["depends_on"]),
                     _json(revised["inputs"]), _json(revised["outputs"]), _json(revised["acceptance"]),
                     _json(revised["requirements"]), revised["priority"], revised["max_attempts"],
                     _json({"reason": reason}), now, project_id, task_id),
                )
                for descendant in descendants:
                    connection.execute(
                        "UPDATE tasks SET status='STALE',worker_id=NULL,claim_token=NULL,lease_until=NULL,error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                        (_json({"reason": f"upstream task {task_id} contract changed"}), now, project_id, descendant),
                    )
                    connection.execute(
                        "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                        (project_id, descendant),
                    )
                    self._event(connection, project_id, "TASK", descendant, "TASK_INVALIDATED_BY_UPSTREAM_CONTRACT", {"upstream_task": task_id, "reason": reason})
                connection.execute(
                    "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                    (project_id, task_id),
                )
                connection.execute("UPDATE projects SET revision=revision+1,updated_at=? WHERE project_id=?", (now, project_id))
                self._event(connection, project_id, "TASK", task_id, "TASK_CONTRACT_REVISED", {"previous": current, "revised": revised, "reason": reason, "invalidated_descendants": sorted(descendants)})
                self._refresh_in_tx(connection, project_id)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {"task": next(item for item in self.list_tasks(project_id) if item["task_id"] == task_id), "invalidated_descendants": sorted(descendants)}

    def _task_map(self, connection: sqlite3.Connection, project_id: str) -> dict[str, dict[str, Any]]:
        rows = connection.execute("SELECT * FROM tasks WHERE project_id=?", (project_id,)).fetchall()
        return {row["task_id"]: dict(row) for row in rows}

    def _refresh_in_tx(self, connection: sqlite3.Connection, project_id: str) -> None:
        tasks = self._task_map(connection, project_id)
        now = _iso()
        for task_id, row in tasks.items():
            status = row["status"]
            if status not in {"PENDING", "READY", "BLOCKED", "WAITING_INPUT"}:
                continue
            deps = _loads(row["depends_on_json"], [])
            dep_states = [tasks[dep]["status"] for dep in deps]
            if any(state in {"FAILED", "BLOCKED", "STALE", "CANCELLED"} for state in dep_states):
                new_status = "BLOCKED"
            elif not all(self._artifact_by_name(connection, project_id, name) is not None for name in _loads(row["inputs_json"], [])):
                new_status = "WAITING_INPUT"
            elif all(state == "COMPLETED" for state in dep_states):
                new_status = "READY"
            else:
                new_status = "PENDING"
            if new_status != status:
                connection.execute(
                    "UPDATE tasks SET status=?,updated_at=? WHERE project_id=? AND task_id=?",
                    (new_status, now, project_id, task_id),
                )
                self._event(connection, project_id, "TASK", task_id, "TASK_READINESS_CHANGED", {"from": status, "to": new_status})

    def refresh(self, project_id: str) -> None:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._refresh_in_tx(connection, project_id)
            connection.commit()

    def list_tasks(self, project_id: str) -> list[dict[str, Any]]:
        with closing(self._connect(project_id)) as connection:
            rows = connection.execute(
                "SELECT * FROM tasks WHERE project_id=? ORDER BY priority DESC,created_at,task_id",
                (project_id,),
            ).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                for key in ("depends_on_json", "inputs_json", "outputs_json", "acceptance_json", "requirements_json", "result_json", "error_json"):
                    item[key.removesuffix("_json")] = _loads(item.pop(key), {} if key in {"acceptance_json", "requirements_json", "result_json", "error_json"} else [])
                result.append(item)
            return result

    def _artifact_by_name(self, connection: sqlite3.Connection, project_id: str, name: str) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM artifacts WHERE project_id=? AND name=? AND status IN ('CURRENT','ACCEPTED') ORDER BY version DESC LIMIT 1",
            (project_id, name),
        ).fetchone()

    def _work_packet(self, connection: sqlite3.Connection, project_id: str, task: sqlite3.Row) -> dict[str, Any]:
        input_names = _loads(task["inputs_json"], [])
        inputs: dict[str, Any] = {}
        missing: list[str] = []
        for name in input_names:
            artifact = self._artifact_by_name(connection, project_id, name)
            if artifact is None:
                missing.append(name)
            else:
                artifact_path = self._project_dir(project_id) / artifact["relative_path"]
                if not artifact_path.is_file() or _sha256(artifact_path) != artifact["sha256"]:
                    raise GateError(f"input artifact is missing or changed: {name}; audit and invalidate affected work")
                inputs[name] = {
                    "artifact_id": artifact["artifact_id"], "version": artifact["version"],
                    "path": str(artifact_path), "sha256": artifact["sha256"], "kind": artifact["kind"],
                    "media_type": artifact["media_type"], "rights_status": artifact["rights_status"],
                    "metadata": _loads(artifact["metadata_json"], {}),
                }
        return {
            "project": self.project(project_id),
            "task": {
                "task_id": task["task_id"], "title": task["title"], "kind": task["kind"],
                "executor": task["executor"], "depends_on": _loads(task["depends_on_json"], []),
                "inputs": input_names, "outputs": _loads(task["outputs_json"], []),
                "acceptance": _loads(task["acceptance_json"], {}),
                "requirements": _loads(task["requirements_json"], {}), "attempt": task["attempts"],
            },
            "input_artifacts": inputs,
            "missing_inputs": missing,
            "instructions": "Produce only the declared outputs. Preserve source truth, provenance and rights. If the task cannot meet its acceptance contract, return a structured failure instead of claiming completion.",
        }

    def claim_next(
        self, project_id: str, worker_id: str, lease_seconds: int = 900, *,
        executor: str | None = None, task_id: str | None = None,
    ) -> dict[str, Any] | None:
        worker_id = _safe_id(worker_id, "worker_id")
        if lease_seconds < 30 or lease_seconds > 86400:
            raise ContractError("lease_seconds must be 30..86400")
        if executor is not None:
            executor = _safe_id(executor, "executor")
        if task_id is not None:
            task_id = _safe_id(task_id, "task_id")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._project_row(connection, project_id)
                now = _now()
                expired = connection.execute(
                    "SELECT * FROM tasks WHERE project_id=? AND status='RUNNING' AND lease_until < ?",
                    (project_id, _iso(now)),
                ).fetchall()
                for row in expired:
                    next_status = "PENDING" if row["attempts"] < row["max_attempts"] else "FAILED"
                    connection.execute(
                        "UPDATE tasks SET status=?,worker_id=NULL,claim_token=NULL,lease_until=NULL,claim_inputs_json='[]',updated_at=? WHERE project_id=? AND task_id=?",
                        (next_status, _iso(now), project_id, row["task_id"]),
                    )
                    self._event(connection, project_id, "TASK", row["task_id"], "TASK_LEASE_EXPIRED", {"worker_id": row["worker_id"], "attempt": row["attempts"], "next_status": next_status})
                self._refresh_in_tx(connection, project_id)
                query = "SELECT * FROM tasks WHERE project_id=? AND status='READY'"
                parameters: list[Any] = [project_id]
                if executor is not None:
                    query += " AND executor=?"
                    parameters.append(executor)
                if task_id is not None:
                    query += " AND task_id=?"
                    parameters.append(task_id)
                query += " ORDER BY priority DESC,created_at,task_id LIMIT 1"
                row = connection.execute(query, parameters).fetchone()
                if row is None:
                    connection.commit()
                    return None
                token = secrets_token = uuid.uuid4().hex + uuid.uuid4().hex
                lease_until = _iso(now + timedelta(seconds=lease_seconds))
                connection.execute(
                    "UPDATE tasks SET status='RUNNING',attempts=attempts+1,worker_id=?,claim_token=?,lease_until=?,updated_at=? WHERE project_id=? AND task_id=? AND status='READY'",
                    (worker_id, token, lease_until, _iso(now), project_id, row["task_id"]),
                )
                claimed = connection.execute(
                    "SELECT * FROM tasks WHERE project_id=? AND task_id=?",
                    (project_id, row["task_id"]),
                ).fetchone()
                self._event(connection, project_id, "TASK", row["task_id"], "TASK_CLAIMED", {"worker_id": worker_id, "lease_until": lease_until, "attempt": claimed["attempts"]})
                packet = self._work_packet(connection, project_id, claimed)
                input_bindings = [
                    {
                        "artifact_id": artifact["artifact_id"], "name": name,
                        "version": artifact["version"], "sha256": artifact["sha256"],
                        "kind": artifact["kind"], "media_type": artifact["media_type"],
                        "rights_status": artifact["rights_status"],
                    }
                    for name, artifact in packet["input_artifacts"].items()
                ]
                connection.execute(
                    "UPDATE tasks SET claim_inputs_json=? WHERE project_id=? AND task_id=?",
                    (_json(input_bindings), project_id, row["task_id"]),
                )
                self._event(connection, project_id, "TASK", row["task_id"], "TASK_INPUTS_BOUND", {"worker_id": worker_id, "input_bindings": input_bindings})
                connection.commit()
                packet["claim"] = asdict(TaskClaim(project_id, row["task_id"], worker_id, token, lease_until, claimed["attempts"]))
                return packet
            except Exception:
                connection.rollback()
                raise

    def claimed_packet(self, project_id: str, task_id: str, worker_id: str, claim_token: str) -> dict[str, Any]:
        with closing(self._connect(project_id)) as connection:
            task = self._assert_claim(connection, project_id, task_id, worker_id, claim_token)
            return self._work_packet(connection, project_id, task)

    def heartbeat(self, project_id: str, task_id: str, worker_id: str, claim_token: str, lease_seconds: int = 900) -> str:
        if lease_seconds < 30 or lease_seconds > 86400:
            raise ContractError("lease_seconds must be 30..86400")
        now = _now()
        until = _iso(now + timedelta(seconds=lease_seconds))
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM tasks WHERE project_id=? AND task_id=?", (project_id, task_id)
            ).fetchone()
            if row is None or row["status"] != "RUNNING" or row["worker_id"] != worker_id or row["claim_token"] != claim_token:
                raise ClaimError("claim ownership does not match")
            if _parse_time(row["lease_until"]) < now:
                raise ClaimError("claim lease has expired")
            connection.execute(
                "UPDATE tasks SET lease_until=?,updated_at=? WHERE project_id=? AND task_id=?",
                (until, _iso(now), project_id, task_id),
            )
            self._event(connection, project_id, "TASK", task_id, "TASK_HEARTBEAT", {"worker_id": worker_id, "lease_until": until})
            connection.commit()
        return until

    def _assert_claim(self, connection: sqlite3.Connection, project_id: str, task_id: str, worker_id: str, claim_token: str) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM tasks WHERE project_id=? AND task_id=?", (project_id, task_id)).fetchone()
        if row is None:
            raise ProjectNotFound(f"task {task_id}")
        if row["status"] != "RUNNING" or row["worker_id"] != worker_id or row["claim_token"] != claim_token:
            raise ClaimError("worker does not hold the current task claim")
        if _parse_time(row["lease_until"]) < _now():
            raise ClaimError("task claim expired; reclaim before completing")
        return row

    def _register_artifact_in_tx(
        self, connection: sqlite3.Connection, project_id: str, name: str,
        path_value: str | Path, *, kind: str, media_type: str,
        rights_status: str, producer_id: str, produced_by_task: str | None,
        metadata: dict[str, Any], expected_sha256: str | None = None,
    ) -> dict[str, Any]:
        _safe_id(name, "artifact name")
        if rights_status not in RIGHTS_ALLOWED | {"UNKNOWN", "NOT_APPLICABLE"}:
            raise ContractError(f"unsupported rights_status: {rights_status}")
        project_dir = self._project_dir(project_id)
        file_path = _inside(project_dir, path_value)
        digest = _sha256(file_path)
        if expected_sha256 and digest.lower() != expected_sha256.lower():
            raise ContractError(f"digest mismatch for {name}: expected {expected_sha256}, got {digest}")
        version_row = connection.execute(
            "SELECT MAX(version) AS version FROM artifacts WHERE project_id=? AND name=?",
            (project_id, name),
        ).fetchone()
        version = int(version_row["version"] or 0) + 1
        artifact_id = "a_" + uuid.uuid4().hex
        relative = file_path.relative_to(project_dir.resolve()).as_posix()
        previous_path = connection.execute(
            "SELECT artifact_id FROM artifacts WHERE project_id=? AND relative_path=? LIMIT 1",
            (project_id, relative),
        ).fetchone()
        if previous_path is not None:
            raise ContractError(f"artifact path is immutable and already registered: {relative}")
        size = file_path.stat().st_size
        connection.execute(
            """INSERT INTO artifacts(project_id,artifact_id,name,version,relative_path,sha256,size_bytes,
               media_type,kind,status,rights_status,produced_by_task,producer_id,metadata_json,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,'CURRENT',?,?,?,?,?)""",
            (project_id, artifact_id, name, version, relative, digest, size, media_type,
             kind, rights_status, produced_by_task, producer_id, _json(metadata), _iso()),
        )
        return {
            "artifact_id": artifact_id, "name": name, "version": version,
            "path": str(file_path), "sha256": digest, "size_bytes": size,
            "media_type": media_type, "kind": kind, "rights_status": rights_status,
            "producer_id": producer_id, "produced_by_task": produced_by_task,
            "metadata": metadata,
        }

    def import_asset(
        self, project_id: str, name: str, source_path: str | Path, *,
        kind: str, media_type: str, rights_status: str = "UNKNOWN",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        source = Path(source_path).expanduser().resolve(strict=True)
        if not source.is_file():
            raise ContractError("source asset must be a regular file")
        directory = self._project_dir(project_id) / "assets"
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = _safe_id(name, "artifact name")
        destination: Path | None = None
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                output_rows = connection.execute(
                    "SELECT task_id,outputs_json FROM tasks WHERE project_id=?", (project_id,)
                ).fetchall()
                output_owner = next((row["task_id"] for row in output_rows if safe_name in _loads(row["outputs_json"], [])), None)
                if output_owner is not None:
                    raise ContractError(f"imported asset name is already reserved as a task output by {output_owner}: {safe_name}")
                version_row = connection.execute(
                    "SELECT MAX(version) AS version FROM artifacts WHERE project_id=? AND name=?",
                    (project_id, safe_name),
                ).fetchone()
                version = int(version_row["version"] or 0) + 1
                destination = directory / f"{safe_name}.v{version}{source.suffix.lower()}"
                shutil.copy2(source, destination)
                artifact = self._register_artifact_in_tx(
                    connection, project_id, safe_name, destination, kind=kind,
                    media_type=media_type, rights_status=rights_status,
                    producer_id="owner-import", produced_by_task=None,
                    metadata=metadata or {},
                )
                self._event(connection, project_id, "ARTIFACT", artifact["artifact_id"], "ASSET_IMPORTED", artifact)
                self._refresh_in_tx(connection, project_id)
                connection.commit()
                return artifact
            except Exception:
                connection.rollback()
                if destination is not None:
                    destination.unlink(missing_ok=True)
                raise

    def complete_task(
        self, project_id: str, task_id: str, worker_id: str, claim_token: str,
        outputs: dict[str, dict[str, Any]], result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                task = self._assert_claim(connection, project_id, task_id, worker_id, claim_token)
                expected = set(_loads(task["outputs_json"], []))
                if set(outputs) != expected:
                    raise ContractError(f"expected outputs {sorted(expected)}, got {sorted(outputs)}")
                registered: dict[str, Any] = {}
                for name, payload in outputs.items():
                    if not isinstance(payload, dict) or not payload.get("path"):
                        raise ContractError(f"output {name} must include a project-relative path")
                    registered[name] = self._register_artifact_in_tx(
                        connection, project_id, name, payload["path"],
                        kind=str(payload.get("kind", "media")),
                        media_type=str(payload.get("media_type", "application/octet-stream")),
                        rights_status=str(payload.get("rights_status", "UNKNOWN")),
                        producer_id=worker_id, produced_by_task=task_id,
                        metadata=dict(payload.get("metadata", {})),
                        expected_sha256=payload.get("sha256"),
                    )
                    self._event(connection, project_id, "ARTIFACT", registered[name]["artifact_id"], "ARTIFACT_CREATED", registered[name])
                input_bindings = _loads(task["claim_inputs_json"], [])
                if not isinstance(input_bindings, list):
                    raise ContractError("claimed input lineage is malformed")
                for binding in input_bindings:
                    if not isinstance(binding, dict) or not binding.get("artifact_id") or not binding.get("sha256"):
                        raise ContractError("claimed input lineage contains an invalid artifact binding")
                    source = connection.execute(
                        "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                        (project_id, binding["artifact_id"]),
                    ).fetchone()
                    if source is None or source["sha256"] != binding["sha256"] or source["status"] not in {"CURRENT", "ACCEPTED"}:
                        raise GateError(f"claimed input artifact changed or became stale before completion: {binding.get('name')}")
                    source_path = self._project_dir(project_id) / source["relative_path"]
                    if not source_path.is_file() or _sha256(source_path) != source["sha256"]:
                        raise GateError(f"claimed input artifact bytes changed before completion: {binding.get('name')}")
                result_payload = {**(result or {}), "outputs": {key: value["artifact_id"] for key, value in registered.items()}, "input_bindings": input_bindings}
                connection.execute(
                    "UPDATE tasks SET status='COMPLETED',worker_id=NULL,claim_token=NULL,lease_until=NULL,claim_inputs_json='[]',result_json=?,error_json=NULL,updated_at=? WHERE project_id=? AND task_id=?",
                    (_json(result_payload), _iso(), project_id, task_id),
                )
                self._event(connection, project_id, "TASK", task_id, "TASK_COMPLETED", {"worker_id": worker_id, "outputs": result_payload["outputs"], "input_bindings": input_bindings, "result": result or {}})
                self._refresh_in_tx(connection, project_id)
                connection.commit()
                return {"task_id": task_id, "status": "COMPLETED", "artifacts": registered, "result": result_payload}
            except Exception:
                connection.rollback()
                raise

    def fail_task(
        self, project_id: str, task_id: str, worker_id: str, claim_token: str,
        error: dict[str, Any], *, retryable: bool = True,
    ) -> dict[str, Any]:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            task = self._assert_claim(connection, project_id, task_id, worker_id, claim_token)
            retry = bool(retryable and task["attempts"] < task["max_attempts"])
            status = "PENDING" if retry else "FAILED"
            connection.execute(
                "UPDATE tasks SET status=?,worker_id=NULL,claim_token=NULL,lease_until=NULL,claim_inputs_json='[]',error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                (status, _json(error), _iso(), project_id, task_id),
            )
            self._event(connection, project_id, "TASK", task_id, "TASK_FAILED", {"error": error, "retryable": retryable, "next_status": status})
            self._refresh_in_tx(connection, project_id)
            actual = connection.execute(
                "SELECT status FROM tasks WHERE project_id=? AND task_id=?", (project_id, task_id)
            ).fetchone()["status"]
            connection.commit()
            return {"task_id": task_id, "status": actual, "retry_scheduled": retry}

    def wait_for_input(self, project_id: str, task_id: str, worker_id: str, claim_token: str, reason: str) -> None:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_claim(connection, project_id, task_id, worker_id, claim_token)
            connection.execute(
                "UPDATE tasks SET status='WAITING_INPUT',worker_id=NULL,claim_token=NULL,lease_until=NULL,claim_inputs_json='[]',error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                (_json({"reason": reason}), _iso(), project_id, task_id),
            )
            self._event(connection, project_id, "TASK", task_id, "TASK_WAITING_INPUT", {"reason": reason})
            connection.commit()

    def record_decision(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        required = ["question", "scope", "source_refs", "hypotheses", "alternatives", "selected_option", "falsifier", "rollback"]
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise ContractError(f"decision receipt missing fields: {missing}")
        if len(payload["hypotheses"]) < 2 or len(payload["alternatives"]) < 2:
            raise ContractError("material decisions require competing hypotheses and at least two alternatives")
        if not any(item.get("id") == payload["selected_option"] for item in payload["alternatives"]):
            raise ContractError("selected_option must identify one declared alternative")
        if not all(item.get("discriminator") for item in payload["hypotheses"]):
            raise ContractError("each root-cause hypothesis needs a discriminating observation or test")
        decision_id = _safe_id(payload.get("decision_id") or "d_" + uuid.uuid4().hex[:16], "decision_id")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._project_row(connection, project_id)
            connection.execute(
                "INSERT INTO decisions(project_id,decision_id,question,payload_json,status,created_at) VALUES(?,?,?,?,?,?)",
                (project_id, decision_id, payload["question"], _json(payload), "ACTIVE", _iso()),
            )
            self._event(connection, project_id, "DECISION", decision_id, "DECISION_RECORDED", payload)
            connection.commit()
        return {"decision_id": decision_id, "status": "ACTIVE", "payload": payload}
    def record_failure(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        required = ["symptom", "hypotheses", "selected_root_cause", "method_challenge", "repair_plan", "falsifier", "rollback", "evidence_refs"]
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise ContractError(f"failure diagnosis missing fields: {missing}")
        if len(payload["hypotheses"]) < 2:
            raise ContractError("failure diagnosis must compare at least two root-cause hypotheses")
        if not all(item.get("discriminator") for item in payload["hypotheses"]):
            raise ContractError("each failure hypothesis needs a discriminator")
        hypothesis_ids = {item.get("id") for item in payload["hypotheses"]}
        if payload["selected_root_cause"] not in hypothesis_ids:
            raise ContractError("selected_root_cause must identify one declared hypothesis")
        failure_id = _safe_id(payload.get("failure_id") or "f_" + uuid.uuid4().hex[:16], "failure_id")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            project_row = self._project_row(connection, project_id)
            brief = _loads(project_row["brief_json"], {})
            if brief.get("release_policy", {}).get("require_resolvable_evidence_refs", False):
                payload["evidence_bindings"] = self._resolve_artifact_refs(
                    connection, project_id, payload["evidence_refs"], label="failure:evidence",
                )
            if payload.get("task_id"):
                task = connection.execute("SELECT 1 FROM tasks WHERE project_id=? AND task_id=?", (project_id, payload["task_id"])).fetchone()
                if task is None:
                    raise ContractError(f"unknown task_id: {payload['task_id']}")
            now = _iso()
            connection.execute(
                "INSERT INTO failures(project_id,failure_id,task_id,status,payload_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                (project_id, failure_id, payload.get("task_id"), "OPEN", _json(payload), now, now),
            )
            self._event(connection, project_id, "FAILURE", failure_id, "FAILURE_DIAGNOSED", payload)
            connection.commit()
        return {"failure_id": failure_id, "status": "OPEN", "payload": payload}

    def resolve_failure(self, project_id: str, failure_id: str, resolution: dict[str, Any]) -> None:
        if not resolution.get("verification_refs") or not resolution.get("regression_refs"):
            raise ContractError("failure resolution requires independent verification_refs and regression_refs")
        if resolution.get("result") != "PASS":
            raise ContractError("failure can be resolved only when independent verification and regression result are PASS")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM failures WHERE project_id=? AND failure_id=?", (project_id, failure_id)).fetchone()
            if row is None:
                raise ProjectNotFound(failure_id)
            if row["status"] != "OPEN":
                raise ContractError("only OPEN failures can be resolved")
            brief = _loads(self._project_row(connection, project_id)["brief_json"], {})
            if brief.get("release_policy", {}).get("require_resolvable_evidence_refs", False):
                resolution["verification_bindings"] = self._resolve_artifact_refs(
                    connection, project_id, resolution["verification_refs"], label="failure:verification",
                )
                resolution["regression_bindings"] = self._resolve_artifact_refs(
                    connection, project_id, resolution["regression_refs"], label="failure:regression",
                )
            connection.execute(
                "UPDATE failures SET status='RESOLVED',resolution_json=?,updated_at=? WHERE project_id=? AND failure_id=?",
                (_json(resolution), _iso(), project_id, failure_id),
            )
            self._event(connection, project_id, "FAILURE", failure_id, "FAILURE_RESOLVED", resolution)
            connection.commit()

    def _resolve_artifact_refs(
        self, connection: sqlite3.Connection, project_id: str, references: list[str],
        *, label: str, allowed_kinds: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        if not isinstance(references, list) or not references:
            raise ContractError(f"{label} must be a non-empty array of registered artifact references")
        resolved: list[dict[str, Any]] = []
        seen: set[str] = set()
        for reference in references:
            if isinstance(reference, dict):
                reference = reference.get("artifact_id") or reference.get("name")
            if not isinstance(reference, str) or not reference.strip():
                raise ContractError(f"{label} contains an invalid artifact reference")
            row = connection.execute(
                """SELECT * FROM artifacts WHERE project_id=? AND (artifact_id=? OR name=?)
                   ORDER BY CASE WHEN artifact_id=? THEN 0 ELSE 1 END, version DESC LIMIT 1""",
                (project_id, reference, reference, reference),
            ).fetchone()
            if row is None:
                raise ContractError(f"{label} does not resolve to a registered artifact: {reference}")
            if row["status"] not in {"CURRENT", "ACCEPTED"}:
                raise ContractError(f"{label} resolves to a non-current artifact: {reference}:{row['status']}")
            if allowed_kinds and row["kind"] not in allowed_kinds:
                raise ContractError(f"{label} resolves to an unsupported evidence kind: {reference}:{row['kind']}")
            path = self._project_dir(project_id) / row["relative_path"]
            if not path.is_file() or _sha256(path) != row["sha256"]:
                raise GateError(f"{label} artifact bytes are missing or changed: {reference}")
            if row["artifact_id"] not in seen:
                seen.add(row["artifact_id"])
                resolved.append({
                    "artifact_id": row["artifact_id"], "name": row["name"],
                    "version": row["version"], "sha256": row["sha256"],
                    "kind": row["kind"], "media_type": row["media_type"],
                    "rights_status": row["rights_status"],
                })
        return resolved

    def record_review(
        self, project_id: str, artifact_id: str, *, reviewer_id: str, rubric_id: str,
        outcome: str, dimensions: dict[str, Any], evidence_refs: list[str], notes: str = "",
    ) -> dict[str, Any]:
        if outcome not in {"PASS", "REVISE", "FAIL", "BLOCKED", "NOT_TESTED"}:
            raise ContractError("invalid review outcome")
        if not reviewer_id or not rubric_id or not evidence_refs:
            raise ContractError("review requires reviewer, rubric and evidence_refs")
        _safe_id(reviewer_id, "reviewer_id")
        _safe_id(rubric_id, "rubric_id")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            artifact = connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?", (project_id, artifact_id)
            ).fetchone()
            if artifact is None:
                raise ProjectNotFound(artifact_id)
            if artifact["status"] not in {"CURRENT", "ACCEPTED"}:
                raise ContractError("stale artifacts cannot receive a current review")
            artifact_path = self._project_dir(project_id) / artifact["relative_path"]
            if not artifact_path.is_file() or _sha256(artifact_path) != artifact["sha256"]:
                raise ContractError("artifact bytes changed; review must target a verified current digest")
            if reviewer_id == artifact["producer_id"]:
                raise ContractError("producer cannot independently review its own artifact")
            brief = _loads(self._project_row(connection, project_id)["brief_json"], {})
            release_policy = brief.get("release_policy", {})
            evidence_bindings = []
            if release_policy.get("require_resolvable_evidence_refs", False):
                evidence_bindings = self._resolve_artifact_refs(
                    connection, project_id, evidence_refs, label=f"review:{rubric_id}:evidence",
                    allowed_kinds={"evidence", "document", "rights_record", "qa_report", "review_report", "decision", "timeline", "domain_state", "image", "video", "audio", "source_code"},
                )
            review_id = "r_" + uuid.uuid4().hex[:16]
            payload = {
                "artifact_id": artifact_id, "artifact_digest": artifact["sha256"],
                "rubric_id": rubric_id, "reviewer_id": reviewer_id,
                "producer_id": artifact["producer_id"], "outcome": outcome,
                "dimensions": dimensions, "evidence_refs": evidence_refs,
                "evidence_bindings": evidence_bindings, "notes": notes,
            }
            connection.execute(
                """INSERT INTO reviews(project_id,review_id,artifact_id,artifact_digest,rubric_id,reviewer_id,
                   producer_id,outcome,dimensions_json,evidence_refs_json,evidence_bindings_json,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (project_id, review_id, artifact_id, artifact["sha256"], rubric_id, reviewer_id,
                 artifact["producer_id"], outcome, _json(dimensions), _json(evidence_refs),
                 _json(evidence_bindings), notes, _iso()),
            )
            self._event(connection, project_id, "REVIEW", review_id, "REVIEW_RECORDED", payload)
            connection.commit()
        return {"review_id": review_id, **payload}

    def release_check(
        self, project_id: str, artifact_id: str, *, required_rubrics: list[str],
        evidence_refs: list[str] | None = None, require_rights: bool = True,
    ) -> dict[str, Any]:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            artifact = connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?", (project_id, artifact_id)
            ).fetchone()
            if artifact is None:
                raise ProjectNotFound(artifact_id)
            failures: list[str] = []
            artifact_path = self._project_dir(project_id) / artifact["relative_path"]
            if not artifact_path.is_file() or _sha256(artifact_path) != artifact["sha256"]:
                failures.append("artifact_bytes_missing_or_digest_changed")
            if artifact["status"] not in {"CURRENT", "ACCEPTED"}:
                failures.append(f"artifact_not_current:{artifact['status']}")
            if require_rights and artifact["rights_status"] not in RIGHTS_ALLOWED:
                failures.append(f"rights_not_cleared:{artifact['rights_status']}")
            review_rows = connection.execute(
                "SELECT * FROM reviews WHERE project_id=? AND artifact_id=? AND artifact_digest=?",
                (project_id, artifact_id, artifact["sha256"]),
            ).fetchall()
            by_rubric: dict[str, list[str]] = {}
            for review in review_rows:
                by_rubric.setdefault(review["rubric_id"], []).append(review["outcome"])
            brief = _loads(self._project_row(connection, project_id)["brief_json"], {})
            release_policy = brief.get("release_policy", {})
            effective_rubrics = sorted(set(required_rubrics or []) | set(release_policy.get("required_review_rubrics", [])))
            if not effective_rubrics:
                raise ContractError("release_check requires at least one review rubric in the brief or command")
            for rubric in effective_rubrics:
                outcomes = by_rubric.get(rubric, [])
                if not outcomes or any(outcome != "PASS" for outcome in outcomes):
                    failures.append(f"required_review_missing_or_conflicting:{rubric}:{outcomes}")
            supplied_evidence = set(evidence_refs or [])
            required_evidence = set(release_policy.get("required_evidence_refs", []))
            missing_evidence = sorted(required_evidence - supplied_evidence)
            if missing_evidence:
                failures.append(f"release_evidence_missing:{missing_evidence}")
            required_artifacts = list(release_policy.get("required_artifact_names", []))
            for required_name in required_artifacts:
                required_artifact = self._artifact_by_name(connection, project_id, required_name)
                if required_artifact is None:
                    failures.append(f"required_deliverable_missing:{required_name}")
                else:
                    required_path = self._project_dir(project_id) / required_artifact["relative_path"]
                    if not required_path.is_file() or _sha256(required_path) != required_artifact["sha256"]:
                        failures.append(f"required_deliverable_bytes_changed:{required_name}")
            required_assets = list(release_policy.get("required_asset_names", []))
            for asset_name in required_assets:
                source_asset = self._artifact_by_name(connection, project_id, asset_name)
                if source_asset is None:
                    failures.append(f"required_source_asset_missing:{asset_name}")
                elif source_asset["rights_status"] not in RIGHTS_ALLOWED:
                    failures.append(f"required_source_asset_rights_not_cleared:{asset_name}:{source_asset['rights_status']}")
                else:
                    source_path = self._project_dir(project_id) / source_asset["relative_path"]
                    if not source_path.is_file() or _sha256(source_path) != source_asset["sha256"]:
                        failures.append(f"required_source_asset_bytes_changed:{asset_name}")
            receipt = {
                "artifact_id": artifact_id, "artifact_digest": artifact["sha256"],
                "required_rubrics": effective_rubrics, "required_artifacts": required_artifacts,
                "required_assets": required_assets, "evidence_refs": sorted(supplied_evidence),
                "rights_status": artifact["rights_status"], "failures": failures,
                "pass": not failures,
            }
            if not failures:
                connection.execute("UPDATE artifacts SET status='ACCEPTED' WHERE project_id=? AND artifact_id=?", (project_id, artifact_id))
                self._event(connection, project_id, "ARTIFACT", artifact_id, "ARTIFACT_RELEASE_ACCEPTED", receipt)
            else:
                self._event(connection, project_id, "ARTIFACT", artifact_id, "ARTIFACT_RELEASE_BLOCKED", receipt)
            connection.commit()
            return receipt

    def invalidate(self, project_id: str, task_id: str, reason: str) -> dict[str, Any]:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            tasks = self._task_map(connection, project_id)
            if task_id not in tasks:
                raise ProjectNotFound(task_id)
            descendants: set[str] = set()
            changed = True
            while changed:
                changed = False
                for candidate, row in tasks.items():
                    deps = _loads(row["depends_on_json"], [])
                    if candidate == task_id or any(dep in descendants or dep == task_id for dep in deps):
                        if candidate not in descendants:
                            descendants.add(candidate)
                            changed = True
            now = _iso()
            for affected in descendants:
                connection.execute(
                    "UPDATE tasks SET status='STALE',worker_id=NULL,claim_token=NULL,lease_until=NULL,error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                    (_json({"reason": reason}), now, project_id, affected),
                )
                connection.execute(
                    "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                    (project_id, affected),
                )
                self._event(connection, project_id, "TASK", affected, "TASK_INVALIDATED", {"root_task": task_id, "reason": reason})
            connection.commit()
        return {"root_task": task_id, "invalidated_tasks": sorted(descendants), "reason": reason}

    def reopen(self, project_id: str, task_id: str, reason: str) -> list[str]:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            tasks = self._task_map(connection, project_id)
            if task_id not in tasks:
                raise ProjectNotFound(task_id)
            descendants: set[str] = set()
            changed = True
            while changed:
                changed = False
                for candidate, row in tasks.items():
                    deps = _loads(row["depends_on_json"], [])
                    if candidate == task_id or any(dep in descendants or dep == task_id for dep in deps):
                        if candidate not in descendants:
                            descendants.add(candidate)
                            changed = True
            for affected in descendants:
                connection.execute(
                    "UPDATE tasks SET status='PENDING',worker_id=NULL,claim_token=NULL,lease_until=NULL,claim_inputs_json='[]',error_json=NULL,updated_at=? WHERE project_id=? AND task_id=? AND status IN ('STALE','BLOCKED','FAILED','WAITING_INPUT')",
                    (_iso(), project_id, affected),
                )
                self._event(connection, project_id, "TASK", affected, "TASK_REOPENED", {"reason": reason})
            self._refresh_in_tx(connection, project_id)
            connection.commit()
        return sorted(descendants)

    def record_learning(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        required = ["method", "applicability", "counterexamples", "failure_conditions", "evidence_refs", "replay_refs"]
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise ContractError(f"learning candidate missing fields: {missing}")
        learning_id = _safe_id(payload.get("learning_id") or "l_" + uuid.uuid4().hex[:16], "learning_id")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            brief = _loads(self._project_row(connection, project_id)["brief_json"], {})
            strict_evidence = brief.get("release_policy", {}).get("require_resolvable_evidence_refs", False)
            independently_validated = (
                payload.get("independent_replay_pass") is True
                and bool(payload.get("validation_evidence_refs"))
                and bool(payload.get("counterexample_trials"))
            )
            if independently_validated and strict_evidence:
                try:
                    payload["validation_bindings"] = self._resolve_artifact_refs(
                        connection, project_id, payload["validation_evidence_refs"], label="learning:validation",
                    )
                    trial_bindings = []
                    for index, trial in enumerate(payload["counterexample_trials"]):
                        refs = trial.get("evidence_refs") if isinstance(trial, dict) else None
                        trial_bindings.append(self._resolve_artifact_refs(
                            connection, project_id, refs, label=f"learning:counterexample:{index}",
                        ))
                    payload["counterexample_bindings"] = trial_bindings
                except (ContractError, GateError) as exc:
                    independently_validated = False
                    payload["validation_blockers"] = [str(exc)]
            status = "VALIDATED" if independently_validated else "CANDIDATE"
            connection.execute(
                "INSERT INTO learning(project_id,learning_id,status,payload_json,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (project_id, learning_id, status, _json(payload), _iso(), _iso()),
            )
            self._event(connection, project_id, "LEARNING", learning_id, "LEARNING_RECORDED", {"status": status, "payload": payload})
            connection.commit()
        return {"learning_id": learning_id, "status": status, "payload": payload}

    def status(self, project_id: str) -> dict[str, Any]:
        project = self.project(project_id)
        tasks = self.list_tasks(project_id)
        counts: dict[str, int] = {}
        for task in tasks:
            counts[task["status"]] = counts.get(task["status"], 0) + 1
        ready = [task["task_id"] for task in tasks if task["status"] == "READY"]
        with closing(self._connect(project_id)) as connection:
            events = connection.execute("SELECT COUNT(*) AS count FROM events WHERE project_id=?", (project_id,)).fetchone()["count"]
            open_failures = connection.execute("SELECT COUNT(*) AS count FROM failures WHERE project_id=? AND status='OPEN'", (project_id,)).fetchone()["count"]
        return {"project": project, "task_counts": counts, "ready_tasks": ready, "open_failures": open_failures, "event_count": events}

    def events(self, project_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with closing(self._connect(project_id)) as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE project_id=? ORDER BY event_no DESC LIMIT ?",
                (project_id, max(1, min(limit, 1000))),
            ).fetchall()
            return [{**dict(row), "payload": _loads(row["payload_json"], {})} for row in reversed(rows)]

    def audit(self, project_id: str) -> dict[str, Any]:
        failures: list[str] = []
        tasks = self.list_tasks(project_id)
        task_map = {task["task_id"]: task for task in tasks}
        try:
            self._validate_graph(task_map)
        except ContractError as exc:
            failures.append(str(exc))
        for task in tasks:
            if task["status"] == "RUNNING":
                if not task.get("worker_id") or not task.get("claim_token") or not task.get("lease_until"):
                    failures.append(f"running_task_missing_lease:{task['task_id']}")
            if task["status"] == "COMPLETED":
                outputs = task.get("result", {}).get("outputs", {})
                if set(outputs) != set(task["outputs"]):
                    failures.append(f"completed_task_output_contract_mismatch:{task['task_id']}")
        with closing(self._connect(project_id)) as connection:
            artifacts = connection.execute("SELECT * FROM artifacts WHERE project_id=?", (project_id,)).fetchall()
            for artifact in artifacts:
                path = self._project_dir(project_id) / artifact["relative_path"]
                # Stale versions are immutable evidence too; stale status removes
                # release authority, not the obligation to preserve historical bytes.
                if not path.is_file():
                    failures.append(f"artifact_file_missing:{artifact['artifact_id']}:{artifact['status']}")
                elif _sha256(path) != artifact["sha256"]:
                    failures.append(f"artifact_digest_mismatch:{artifact['artifact_id']}:{artifact['status']}")
            reviews = connection.execute("SELECT * FROM reviews WHERE project_id=?", (project_id,)).fetchall()
            for review in reviews:
                artifact = connection.execute(
                    "SELECT sha256,producer_id FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, review["artifact_id"]),
                ).fetchone()
                if artifact is None or review["artifact_digest"] != artifact["sha256"]:
                    failures.append(f"review_artifact_binding_mismatch:{review['review_id']}")
                if review["reviewer_id"] == review["producer_id"]:
                    failures.append(f"self_review_detected:{review['review_id']}")
            decisions = connection.execute("SELECT * FROM decisions WHERE project_id=?", (project_id,)).fetchall()
            for row in decisions:
                payload = _loads(row["payload_json"], {})
                if not payload.get("falsifier") or not payload.get("rollback"):
                    failures.append(f"decision_missing_falsifier_or_rollback:{row['decision_id']}")
        return {"project_id": project_id, "task_count": len(tasks), "artifact_count": len(artifacts), "failures": failures, "pass": not failures}