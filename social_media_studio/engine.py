from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import uuid
from typing import Any, Iterable

from .review_execution import (
    ReviewExecutionError, ReviewExecutionTrustRegistry, build_review_packet,
    digest_json, review_contract_digest, review_contract_requires_execution,
)

from .engine_support import (
    SCHEMA_VERSION, TASK_STATES, RIGHTS_ALLOWED, _ID,
    StudioError, ProjectNotFound, ContractError, ClaimError, GateError,
    _now, _iso, _parse_time, _json, _loads, _safe_id, _sha256, _inside,
    TaskClaim, validate_brief, completion_guidance,
)
from .application.project_tasks import ProjectTaskService


class StudioEngine:
    """Outcome-driven, standalone project and production runtime.

    The engine deliberately has no dependency on CAOS, an LLM vendor, or a fixed
    stage machine. A planner supplies a project-specific DAG; independent workers
    claim ready nodes through SQLite transactions and return immutable artifacts.
    """

    def __init__(self, root: str | Path | None = None):
        default = Path(os.environ.get("SMS_STUDIO_HOME", Path.home() / ".sms-studio"))
        self.root = Path(root or default).expanduser().resolve()
        self.review_trust_registry = ReviewExecutionTrustRegistry()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "projects").mkdir(exist_ok=True)
        self._project_task_service = ProjectTaskService(self)

    def _project_dir(self, project_id: str) -> Path:
        project_id = _safe_id(project_id, "project_id")
        return self.root / "projects" / project_id

    def _connect(self, project_id: str) -> sqlite3.Connection:
        db_path = self._project_dir(project_id) / "studio.sqlite3"
        if not db_path.is_file():
            raise ProjectNotFound(project_id)
        connection = sqlite3.connect(db_path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA synchronous = FULL")
        self._ensure_schema_extensions(connection)
        return connection

    @staticmethod
    def _ensure_schema_extensions(connection: sqlite3.Connection) -> None:
        """Idempotent migrations for projects created by earlier standalone releases."""
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS review_execution_nonces (
                project_id TEXT NOT NULL,
                nonce TEXT NOT NULL,
                review_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(project_id, nonce),
                UNIQUE(project_id, review_id),
                FOREIGN KEY(project_id, review_id)
                    REFERENCES reviews(project_id, review_id)
            );
            CREATE TRIGGER IF NOT EXISTS review_execution_nonces_no_update
                BEFORE UPDATE ON review_execution_nonces
                BEGIN SELECT RAISE(ABORT, 'review execution nonce records are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS review_execution_nonces_no_delete
                BEFORE DELETE ON review_execution_nonces
                BEGIN SELECT RAISE(ABORT, 'review execution nonce records are immutable'); END;
            CREATE TABLE IF NOT EXISTS artifact_inputs (
                project_id TEXT NOT NULL,
                output_artifact_id TEXT NOT NULL,
                input_artifact_id TEXT NOT NULL,
                input_sha256 TEXT NOT NULL,
                relationship TEXT NOT NULL DEFAULT 'DERIVED_FROM',
                created_at TEXT NOT NULL,
                PRIMARY KEY(project_id, output_artifact_id, input_artifact_id),
                FOREIGN KEY(project_id, output_artifact_id)
                    REFERENCES artifacts(project_id, artifact_id),
                FOREIGN KEY(project_id, input_artifact_id)
                    REFERENCES artifacts(project_id, artifact_id)
            );
            CREATE INDEX IF NOT EXISTS idx_artifact_inputs_input
                ON artifact_inputs(project_id, input_artifact_id);
            CREATE TRIGGER IF NOT EXISTS artifact_inputs_no_update
                BEFORE UPDATE ON artifact_inputs
                BEGIN SELECT RAISE(ABORT, 'artifact lineage is immutable'); END;
            CREATE TRIGGER IF NOT EXISTS artifact_inputs_no_delete
                BEFORE DELETE ON artifact_inputs
                BEGIN SELECT RAISE(ABORT, 'artifact lineage is immutable'); END;
            """
        )
        task_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
        }
        if "claim_inputs_json" not in task_columns:
            connection.execute(
                "ALTER TABLE tasks ADD COLUMN claim_inputs_json TEXT NOT NULL DEFAULT '[]'"
            )

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
                claim_inputs_json TEXT NOT NULL DEFAULT '[]',
                lease_until TEXT,
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
            INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', '1');
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

    def _project_row(self, connection: sqlite3.Connection, project_id: str) -> sqlite3.Row:
        return self._project_task_service._project_row(connection, project_id)

    @staticmethod
    def _validate_brief(brief: dict[str, Any]) -> None:
        return validate_brief(brief)


    def create_project(self, project_id: str, title: str, brief: dict[str, Any]) -> dict[str, Any]:
        return self._project_task_service.create_project(project_id, title, brief)
    def project(self, project_id: str) -> dict[str, Any]:
        return self._project_task_service.project(project_id)
    @staticmethod
    def _descendant_closure(tasks: dict[str, dict[str, Any]], roots: Iterable[str]) -> set[str]:
        return ProjectTaskService._descendant_closure(tasks, roots)

    def brief_history(self, project_id: str) -> list[dict[str, Any]]:
        return self._project_task_service.brief_history(project_id)
    def revise_brief(
        self, project_id: str, brief: dict[str, Any], *, reason: str,
        affected_task_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._project_task_service.revise_brief(project_id, brief, reason=reason, affected_task_ids=affected_task_ids)
    def _validate_graph(self, all_tasks: dict[str, dict[str, Any]]) -> None:
        return self._project_task_service._validate_graph(all_tasks)
    def add_tasks(self, project_id: str, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._project_task_service.add_tasks(project_id, tasks)
    def revise_task(self, project_id: str, task_id: str, patch: dict[str, Any], *, reason: str) -> dict[str, Any]:
        return self._project_task_service.revise_task(project_id, task_id, patch, reason=reason)
    def _task_map(self, connection: sqlite3.Connection, project_id: str) -> dict[str, dict[str, Any]]:
        return self._project_task_service._task_map(connection, project_id)
    def _refresh_in_tx(self, connection: sqlite3.Connection, project_id: str) -> None:
        return self._project_task_service._refresh_in_tx(connection, project_id)
    def _refresh_cross_project_transfers_in_tx(self, connection: sqlite3.Connection, project_id: str) -> None:
        return self._project_task_service._refresh_cross_project_transfers_in_tx(connection, project_id)
    def refresh(self, project_id: str) -> None:
        return self._project_task_service.refresh(project_id)
    def list_tasks(self, project_id: str) -> list[dict[str, Any]]:
        return self._project_task_service.list_tasks(project_id)
    def _artifact_by_name(self, connection: sqlite3.Connection, project_id: str, name: str) -> sqlite3.Row | None:
        return self._project_task_service._artifact_by_name(connection, project_id, name)

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

    def _review_stage_dir(self, project_id: str, task_id: str, attempt: int) -> Path:
        return (
            self.root / "review_sessions" / _safe_id(project_id, "project_id")
            / _safe_id(task_id, "task_id") / str(int(attempt))
        )

    def _stage_review_inputs(
        self, project_id: str, task: sqlite3.Row, packet: dict[str, Any], *,
        reuse_existing: bool = False,
    ) -> None:
        """Give a review executor only staged, digest-verified declared inputs."""
        stage_root = self._review_stage_dir(project_id, task["task_id"], task["attempts"])
        review_root = self.root / "review_sessions"
        project_stage_root = review_root / _safe_id(project_id, "project_id")
        task_stage_root = project_stage_root / _safe_id(task["task_id"], "task_id")
        if any(path.is_symlink() for path in (review_root, project_stage_root, task_stage_root, stage_root)):
            raise GateError("review staging path cannot contain symlinks")
        if stage_root.exists() and not reuse_existing:
            shutil.rmtree(stage_root)
        try:
            inputs_root = stage_root / "inputs"
            if inputs_root.is_symlink():
                raise GateError("review input staging path cannot be a symlink")
            inputs_root.mkdir(parents=True, exist_ok=True)
            staged_inputs: dict[str, dict[str, Any]] = {}
            expected_names: set[str] = set()
            for name, item in packet.get("input_artifacts", {}).items():
                source = Path(item["path"])
                expected_digest = item["sha256"]
                if not source.is_file() or _sha256(source) != expected_digest:
                    raise GateError(f"review input changed before isolation staging: {name}")
                destination = inputs_root / f"{_safe_id(name, 'review_input')}{source.suffix.lower()}"
                expected_names.add(destination.name)
                if destination.is_symlink():
                    destination.unlink()
                if not destination.is_file() or _sha256(destination) != expected_digest:
                    shutil.copyfile(source, destination)
                if _sha256(destination) != expected_digest:
                    raise GateError(f"review input staging digest mismatch: {name}")
                staged_item = dict(item)
                staged_item["path"] = str(destination)
                staged_item["staged_sha256"] = expected_digest
                staged_inputs[name] = staged_item
            for child in inputs_root.iterdir():
                if child.is_file() and child.name not in expected_names:
                    child.unlink()
                elif child.is_dir():
                    shutil.rmtree(child)
            packet["input_artifacts"] = staged_inputs
            project = packet.get("project")
            if isinstance(project, dict):
                packet["project"] = {
                    key: value for key, value in project.items() if key != "workspace"
                }
            packet["review_isolation"] = {
                "mode": "DECLARED_INPUTS_ONLY",
                "staged_input_root": str(inputs_root),
                "shared_workspace_path_exposed": False,
                "sibling_verdicts_included": False,
                "input_digests_verified": True,
            }
        except Exception:
            shutil.rmtree(stage_root, ignore_errors=True)
            raise

    def _verify_review_stage_inputs(
        self, connection: sqlite3.Connection, project_id: str, task: sqlite3.Row,
        input_bindings: list[dict[str, Any]],
    ) -> None:
        stage_root = self._review_stage_dir(project_id, task["task_id"], task["attempts"])
        review_root = self.root / "review_sessions"
        project_stage_root = review_root / _safe_id(project_id, "project_id")
        task_stage_root = project_stage_root / _safe_id(task["task_id"], "task_id")
        inputs_root = stage_root / "inputs"
        if any(path.is_symlink() for path in (review_root, project_stage_root, task_stage_root, stage_root, inputs_root)) or not inputs_root.is_dir():
            raise GateError("review isolated input staging directory is missing or unsafe")
        expected_files: set[str] = set()
        for binding in input_bindings:
            source = connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                (project_id, binding["artifact_id"]),
            ).fetchone()
            if source is None or source["name"] != binding["name"]:
                raise GateError("review staged input no longer maps to its registered artifact")
            suffix = Path(source["relative_path"]).suffix.lower()
            filename = f"{_safe_id(source['name'], 'review_input')}{suffix}"
            expected_files.add(filename)
            staged = inputs_root / filename
            if staged.is_symlink() or not staged.is_file() or _sha256(staged) != binding["sha256"]:
                raise GateError(f"review staged input bytes changed before completion: {source['name']}")
        actual_files = {item.name for item in inputs_root.iterdir() if item.is_file()}
        if actual_files != expected_files or any(item.is_dir() for item in inputs_root.iterdir()):
            raise GateError("review staging contains undeclared or missing input files")

    def _cleanup_review_stage(self, project_id: str, task_id: str, attempt: int) -> None:
        stage_root = self._review_stage_dir(project_id, task_id, attempt)
        if stage_root.exists():
            shutil.rmtree(stage_root)

    def _reclaim_expired_claims_in_tx(
        self, connection: sqlite3.Connection, project_id: str, now: datetime,
    ) -> list[dict[str, Any]]:
        expired = connection.execute(
            "SELECT * FROM tasks WHERE project_id=? AND status='RUNNING' AND lease_until < ?",
            (project_id, _iso(now)),
        ).fetchall()
        reclaimed: list[dict[str, Any]] = []
        for row in expired:
            next_status = "PENDING" if row["attempts"] < row["max_attempts"] else "FAILED"
            connection.execute(
                "UPDATE tasks SET status=?,worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,updated_at=? WHERE project_id=? AND task_id=?",
                (next_status, _iso(now), project_id, row["task_id"]),
            )
            self._event(connection, project_id, "TASK", row["task_id"], "TASK_LEASE_EXPIRED", {
                "worker_id": row["worker_id"], "attempt": row["attempts"], "next_status": next_status,
            })
            if row["kind"] == "review":
                self._cleanup_review_stage(project_id, row["task_id"], row["attempts"])
            reclaimed.append({
                "task_id": row["task_id"], "worker_id": row["worker_id"],
                "attempt": row["attempts"], "next_status": next_status,
            })
        return reclaimed

    def reclaim_expired_claims(self, project_id: str) -> list[dict[str, Any]]:
        """Recover expired task leases even when no task is currently READY."""
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._project_row(connection, project_id)
                self._refresh_cross_project_transfers_in_tx(connection, project_id)
                reclaimed = self._reclaim_expired_claims_in_tx(connection, project_id, _now())
                self._refresh_in_tx(connection, project_id)
                connection.commit()
                return reclaimed
            except Exception:
                connection.rollback()
                raise

    def _decision_action_snapshot(self, connection: sqlite3.Connection, project_id: str, task: sqlite3.Row) -> dict[str, Any]:
        """Bind a local action to actual current goal/task/input bytes, not a parent attestation."""
        brief = _loads(self._project_row(connection, project_id)["brief_json"], {})
        route_binding = self._task_scope_binding(brief, task)
        fields = ("task_id", "title", "kind", "executor", "depends_on_json", "inputs_json",
                  "outputs_json", "acceptance_json", "requirements_json", "priority", "max_attempts")
        inputs = []
        for name in _loads(task["inputs_json"], []):
            item = self._artifact_by_name(connection, project_id, name)
            if item is None:
                raise GateError(f"decision input unavailable: {name}")
            path = self._project_dir(project_id) / item["relative_path"]
            if not path.is_file() or _sha256(path) != item["sha256"]:
                raise GateError(f"decision input changed: {name}")
            inputs.append({"name": name, "artifact_id": item["artifact_id"], "sha256": item["sha256"]})
        # Revision identities prevent an old decision from reviving when the
        # owner changes a goal/contract and later restores identical text.
        brief_event = connection.execute(
            "SELECT MAX(event_no) FROM events WHERE project_id=? AND entity_type='PROJECT' AND event_type IN ('PROJECT_CREATED','PROJECT_BRIEF_REVISED')",
            (project_id,)).fetchone()[0]
        task_event = connection.execute(
            """SELECT MAX(event_no) FROM events WHERE project_id=? AND entity_type='TASK' AND entity_id=?
               AND (event_type IN ('TASK_ADDED','TASK_CONTRACT_REVISED','TASK_REOPENED','TASK_INVALIDATED')
                    OR event_type LIKE 'TASK_INVALIDATED_BY_%')""",
            (project_id, task["task_id"])).fetchone()[0]
        if brief_event is None or task_event is None:
            raise GateError("decision requires current goal and task event identity")
        return {"project_id": project_id, "task_id": task["task_id"],
                "brief_event_no": brief_event, "task_event_no": task_event,
                "brief_sha256": hashlib.sha256(_json(brief).encode("utf-8")).hexdigest(),
                "task_sha256": hashlib.sha256(_json({key: task[key] for key in fields}).encode("utf-8")).hexdigest(),
                "inputs": inputs, "assurance": "LOCAL_STRUCTURAL_BINDING_ONLY",
                **({"professional_route_binding": route_binding} if route_binding is not None else {})}

    @staticmethod
    def _task_scope_binding(brief, task):
        from .scope import validate_task_binding
        try:
            return validate_task_binding(brief, {
                "requirements": _loads(task["requirements_json"], {}),
                "kind": task["kind"], "executor": task["executor"],
                "outputs": _loads(task["outputs_json"], []),
            })
        except ValueError as exc:
            raise GateError(str(exc)) from exc

    def _require_task_decision(self, connection: sqlite3.Connection, project_id: str, task: sqlite3.Row) -> None:
        from .scope import EPOCH
        brief = _loads(self._project_row(connection, project_id)["brief_json"], {})
        if brief.get("scope_epoch") != EPOCH:
            return  # isolated historical regression compatibility
        requirements = _loads(task["requirements_json"], {})
        decision_id = requirements.get("decision_id")
        if not isinstance(decision_id, str) or not _ID.fullmatch(decision_id):
            raise GateError("current owner task requires an exact decision_id")
        row = connection.execute(
            "SELECT payload_json,status FROM decisions WHERE project_id=? AND decision_id=?",
            (project_id, decision_id)).fetchone()
        if row is None or row["status"] != "ACTIVE":
            raise GateError("current task-bound decision is missing or inactive")
        if connection.execute(
            "SELECT 1 FROM events WHERE project_id=? AND entity_type='DECISION'"
            " AND entity_id=? AND event_type='DECISION_SUPERSEDED_BY_SCOPE_UPGRADE' LIMIT 1",
            (project_id, decision_id),
        ).fetchone() is not None:
            raise GateError("decision was superseded by owner-scope upgrade; record a new current decision")
        payload = _loads(row["payload_json"], {})
        if payload.get("action_binding") != self._decision_action_snapshot(connection, project_id, task):
            raise GateError("decision no longer binds current goal, task and input bytes or professional route; re-decide")

    def claim_next(
        self, project_id: str, worker_id: str, lease_seconds: int = 900, *,
        executor: str | None = None, task_id: str | None = None,
    ) -> dict[str, Any] | None:
        worker_id = _safe_id(worker_id, "worker_id")
        if lease_seconds < 30 or lease_seconds > 86400:
            raise ContractError("lease_seconds must be 30..86400")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = None
            claimed = None
            try:
                self._project_row(connection, project_id)
                now = _now()
                self._refresh_cross_project_transfers_in_tx(connection, project_id)
                self._reclaim_expired_claims_in_tx(connection, project_id, now)
                self._refresh_in_tx(connection, project_id)
                query = "SELECT * FROM tasks WHERE project_id=? AND status='READY'"
                query_params: list[Any] = [project_id]
                if executor is not None:
                    if executor not in {"agent", "tool", "human", "external"}:
                        raise ContractError(f"unsupported executor filter: {executor}")
                    query += " AND executor=?"
                    query_params.append(executor)
                if task_id is not None:
                    task_id = _safe_id(task_id, "task_id")
                    query += " AND task_id=?"
                    query_params.append(task_id)
                query += " ORDER BY priority DESC,created_at,task_id"
                for candidate in connection.execute(query, query_params).fetchall():
                    try:
                        if candidate["attempts"] >= candidate["max_attempts"]:
                            raise GateError("task retry budget exhausted; revise task contract before re-admission")
                        self._require_task_decision(connection, project_id, candidate)
                    except GateError:
                        if task_id is not None:
                            raise
                        continue  # an unadmitted branch cannot starve unrelated ready work
                    row = candidate
                    break
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
                self._event(connection, project_id, "TASK", row["task_id"], "TASK_INPUTS_BOUND", {
                    "worker_id": worker_id, "input_bindings": input_bindings,
                })
                if claimed["kind"] == "review":
                    requirements = _loads(claimed["requirements_json"], {})
                    task_contract = requirements.get("review_contract") if isinstance(requirements, dict) else None
                    if not isinstance(task_contract, dict):
                        raise ContractError("review tasks require an immutable requirements.review_contract")
                    brief = _loads(self._project_row(connection, project_id)["brief_json"], {})
                    release_policy = brief.get("release_policy", {})
                    rubric_contracts = release_policy.get("review_contracts", {})
                    rubric_id = task_contract.get("rubric_id")
                    rubric_contract = rubric_contracts.get(rubric_id) if isinstance(rubric_contracts, dict) else None
                    if not isinstance(rubric_contract, dict):
                        raise ContractError("review task rubric is not declared in the current owner release contract")
                    for binding in input_bindings:
                        source_artifact = connection.execute(
                            "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                            (project_id, binding["artifact_id"]),
                        ).fetchone()
                        if source_artifact is not None and source_artifact["produced_by_task"]:
                            source_task = connection.execute(
                                "SELECT kind FROM tasks WHERE project_id=? AND task_id=?",
                                (project_id, source_artifact["produced_by_task"]),
                            ).fetchone()
                            if source_task is not None and source_task["kind"] == "review":
                                raise ContractError("blind review tasks cannot consume outputs from sibling review tasks")
                    review_packet = build_review_packet(
                        project_id=project_id, task_id=row["task_id"],
                        task_contract=task_contract, rubric_contract=rubric_contract,
                        input_bindings=input_bindings,
                    )
                    packet_digest = digest_json(review_packet)
                    contract_digest = review_contract_digest(task_contract, rubric_contract)
                    packet["review_packet"] = review_packet
                    packet["review_packet_digest"] = packet_digest
                    self._stage_review_inputs(project_id, claimed, packet)
                    self._event(connection, project_id, "TASK", row["task_id"], "REVIEW_PACKET_BOUND", {
                        "review_packet": review_packet,
                        "review_packet_digest": packet_digest,
                        "review_contract_digest": contract_digest,
                    })
                connection.commit()
                packet["claim"] = asdict(TaskClaim(project_id, row["task_id"], worker_id, token, lease_until, claimed["attempts"]))
                return packet
            except Exception:
                connection.rollback()
                if claimed is not None and claimed["kind"] == "review":
                    self._cleanup_review_stage(project_id, claimed["task_id"], claimed["attempts"])
                raise

    def _verify_claimed_inputs(
        self, connection: sqlite3.Connection, project_id: str, task: sqlite3.Row,
    ) -> tuple[list[dict[str, Any]], list[sqlite3.Row]]:
        bindings = _loads(task["claim_inputs_json"], [])
        declared_names = _loads(task["inputs_json"], [])
        if not isinstance(bindings, list) or not isinstance(declared_names, list):
            raise ContractError("claimed input lineage is malformed")
        names: list[str] = []
        rows: list[sqlite3.Row] = []
        for binding in bindings:
            if not isinstance(binding, dict):
                raise ContractError("claimed input lineage contains a non-object binding")
            name = binding.get("name")
            artifact_id = binding.get("artifact_id")
            digest = binding.get("sha256")
            version = binding.get("version")
            if not isinstance(name, str) or not isinstance(artifact_id, str) or not isinstance(digest, str):
                raise ContractError("claimed input lineage contains an invalid artifact binding")
            names.append(name)
            source = connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                (project_id, artifact_id),
            ).fetchone()
            if (
                source is None or source["name"] != name or source["sha256"] != digest
                or source["version"] != version or source["status"] not in {"CURRENT", "ACCEPTED"}
            ):
                raise GateError(f"claimed input artifact changed or became stale before completion: {name}")
            source_path = self._project_dir(project_id) / source["relative_path"]
            if not source_path.is_file() or _sha256(source_path) != digest:
                raise GateError(f"claimed input artifact bytes changed before completion: {name}")
            rows.append(source)
        if names != declared_names:
            raise GateError(
                f"claimed input lineage does not match declared inputs: expected {declared_names}, got {names}"
            )
        return bindings, rows

    def claimed_packet(self, project_id: str, task_id: str, worker_id: str, claim_token: str) -> dict[str, Any]:
        # A claim can outlive its upstream Program transfer; reconcile before exposing inputs.
        self.refresh(project_id)
        with closing(self._connect(project_id)) as connection:
            task = self._assert_claim(connection, project_id, task_id, worker_id, claim_token)
            packet = self._work_packet(connection, project_id, task)
            _, rows = self._verify_claimed_inputs(connection, project_id, task)
            packet["input_artifacts"] = {
                row["name"]: {
                    "artifact_id": row["artifact_id"], "version": row["version"],
                    "path": str(self._project_dir(project_id) / row["relative_path"]),
                    "sha256": row["sha256"], "kind": row["kind"], "media_type": row["media_type"],
                    "rights_status": row["rights_status"], "metadata": _loads(row["metadata_json"], {}),
                    "producer_id": row["producer_id"], "produced_by_task": row["produced_by_task"],
                }
                for row in rows
            }
            if task["kind"] == "review":
                event_row = connection.execute(
                    """SELECT payload_json FROM events
                       WHERE project_id=? AND entity_type='TASK' AND entity_id=?
                         AND event_type='REVIEW_PACKET_BOUND'
                       ORDER BY event_no DESC LIMIT 1""",
                    (project_id, task_id),
                ).fetchone()
                event_payload = _loads(event_row["payload_json"], {}) if event_row else {}
                review_packet = event_payload.get("review_packet") if isinstance(event_payload, dict) else None
                if not isinstance(review_packet, dict) or event_payload.get("review_packet_digest") != digest_json(review_packet):
                    raise GateError("claimed review task has no intact immutable review packet")
                packet["review_packet"] = review_packet
                packet["review_packet_digest"] = event_payload["review_packet_digest"]
                self._stage_review_inputs(project_id, task, packet, reuse_existing=True)
            else:
                packet["missing_inputs"] = []
            return packet

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
            try:
                self._require_task_decision(connection, project_id, row)
            except GateError as exc:
                raise ClaimError(str(exc)) from exc
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
        try:
            self._require_task_decision(connection, project_id, row)
        except GateError as exc:
            raise ClaimError(str(exc)) from exc
        return row

    def _snapshot_rights_evidence_bindings_in_tx(
        self, connection: sqlite3.Connection, project_id: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(metadata, dict):
            raise ContractError("artifact metadata must be an object")
        payload = dict(metadata)
        # Caller-supplied snapshots are never trusted. Bind the declared refs
        # to the exact registered artifacts and bytes visible in this transaction.
        payload.pop("rights_evidence_bindings", None)
        if "rights_evidence_refs" not in payload:
            return payload

        raw_refs = payload.get("rights_evidence_refs")
        bindings: list[dict[str, Any]] = []
        if isinstance(raw_refs, list):
            for reference in raw_refs:
                if (
                    not isinstance(reference, str) or not reference.strip()
                    or reference != reference.strip()
                ):
                    bindings.append({
                        "reference": reference,
                        "reference_type": "INVALID",
                        "resolved": False,
                        "reason": "INVALID_REFERENCE",
                    })
                    continue
                if reference.startswith(("https://", "http://")):
                    bindings.append({
                        "reference": reference,
                        "reference_type": "EXTERNAL_URI",
                        "resolved": True,
                        "verification": "EXTERNAL_REFERENCE_NOT_FETCHED",
                    })
                    continue
                evidence = connection.execute(
                    "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, reference),
                ).fetchone()
                if evidence is None:
                    evidence = self._artifact_by_name(connection, project_id, reference)
                if evidence is None:
                    bindings.append({
                        "reference": reference,
                        "reference_type": "ARTIFACT",
                        "resolved": False,
                        "reason": "ARTIFACT_NOT_FOUND",
                    })
                    continue
                if evidence["status"] not in {"CURRENT", "ACCEPTED"}:
                    bindings.append({
                        "reference": reference,
                        "reference_type": "ARTIFACT",
                        "resolved": False,
                        "reason": "ARTIFACT_NOT_CURRENT_OR_ACCEPTED",
                        "artifact_id": evidence["artifact_id"],
                    })
                    continue
                evidence_path = self._project_dir(project_id) / evidence["relative_path"]
                if (
                    not evidence_path.is_file()
                    or _sha256(evidence_path) != evidence["sha256"]
                ):
                    bindings.append({
                        "reference": reference,
                        "reference_type": "ARTIFACT",
                        "resolved": False,
                        "reason": "BYTES_MISSING_OR_DIGEST_CHANGED",
                        "artifact_id": evidence["artifact_id"],
                    })
                    continue
                bindings.append({
                    "reference": reference,
                    "reference_type": "ARTIFACT",
                    "resolved": True,
                    "artifact_id": evidence["artifact_id"],
                    "name": evidence["name"],
                    "version": int(evidence["version"]),
                    "sha256": evidence["sha256"],
                    "kind": evidence["kind"],
                    "media_type": evidence["media_type"],
                    "producer_id": evidence["producer_id"],
                })
        payload["rights_evidence_bindings"] = {
            "schema_version": 1,
            "binding_mode": "ARTIFACT_CREATION_EVENT_ID_VERSION_SHA256_SNAPSHOT",
            "items": bindings,
        }
        return payload

    def _register_artifact_in_tx(
        self, connection: sqlite3.Connection, project_id: str, name: str,
        path_value: str | Path, *, kind: str, media_type: str,
        rights_status: str, producer_id: str, produced_by_task: str | None,
        metadata: dict[str, Any], expected_sha256: str | None = None,
    ) -> dict[str, Any]:
        metadata = self._snapshot_rights_evidence_bindings_in_tx(
            connection, project_id, metadata,
        )
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
        source_digest = _sha256(source)
        metadata_payload = dict(metadata or {})
        destination: Path | None = None
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                metadata_payload = self._snapshot_rights_evidence_bindings_in_tx(
                    connection, project_id, metadata_payload,
                )
                metadata_json = _json(metadata_payload)
                output_rows = connection.execute(
                    "SELECT task_id,outputs_json FROM tasks WHERE project_id=?", (project_id,)
                ).fetchall()
                output_owner = next((row["task_id"] for row in output_rows if safe_name in _loads(row["outputs_json"], [])), None)
                if output_owner is not None:
                    raise ContractError(f"imported asset name is already reserved as a task output by {output_owner}: {safe_name}")
                previous_rows = connection.execute(
                    "SELECT * FROM artifacts WHERE project_id=? AND name=? AND status IN ('CURRENT','ACCEPTED')",
                    (project_id, safe_name),
                ).fetchall()
                for previous in previous_rows:
                    previous_path = self._project_dir(project_id) / previous["relative_path"]
                    if (
                        previous["sha256"] == source_digest
                        and previous["kind"] == kind
                        and previous["media_type"] == media_type
                        and previous["rights_status"] == rights_status
                        and previous["metadata_json"] == metadata_json
                        and previous_path.is_file()
                        and _sha256(previous_path) == source_digest
                    ):
                        connection.commit()
                        return {
                            "artifact_id": previous["artifact_id"], "name": previous["name"],
                            "version": previous["version"], "path": str(previous_path),
                            "sha256": previous["sha256"], "size_bytes": previous["size_bytes"],
                            "media_type": previous["media_type"], "kind": previous["kind"],
                            "rights_status": previous["rights_status"], "producer_id": previous["producer_id"],
                            "produced_by_task": previous["produced_by_task"],
                            "metadata": _loads(previous["metadata_json"], {}),
                        }
                if previous_rows:
                    # A new source version revokes every task that declared or actually
                    # consumed the old version, including RUNNING leases and descendants.
                    root_tasks: set[str] = set()
                    for task_row in connection.execute("SELECT task_id,inputs_json FROM tasks WHERE project_id=?", (project_id,)).fetchall():
                        if safe_name in _loads(task_row["inputs_json"], []):
                            root_tasks.add(task_row["task_id"])
                    previous_ids = {row["artifact_id"] for row in previous_rows}
                    frontier = set(previous_ids)
                    seen_artifacts = set(previous_ids)
                    while frontier:
                        placeholders = ",".join("?" for _ in frontier)
                        consumers = connection.execute(
                            f"""SELECT DISTINCT a.artifact_id,a.produced_by_task
                                FROM artifact_inputs ai
                                JOIN artifacts a ON a.project_id=ai.project_id
                                                AND a.artifact_id=ai.output_artifact_id
                                WHERE ai.project_id=? AND ai.input_artifact_id IN ({placeholders})""",
                            (project_id, *sorted(frontier)),
                        ).fetchall()
                        next_frontier: set[str] = set()
                        for consumer in consumers:
                            if consumer["produced_by_task"]:
                                root_tasks.add(consumer["produced_by_task"])
                            if consumer["artifact_id"] not in seen_artifacts:
                                seen_artifacts.add(consumer["artifact_id"])
                                next_frontier.add(consumer["artifact_id"])
                        frontier = next_frontier
                    task_map = self._task_map(connection, project_id)
                    affected = set(root_tasks)
                    changed = True
                    while changed:
                        changed = False
                        for candidate, row in task_map.items():
                            deps = _loads(row["depends_on_json"], [])
                            if candidate not in affected and any(dep in affected for dep in deps):
                                affected.add(candidate)
                                changed = True
                    for affected_task in sorted(affected):
                        if task_map[affected_task]["kind"] == "review":
                            self._cleanup_review_stage(project_id, affected_task, task_map[affected_task]["attempts"])
                        connection.execute(
                            """UPDATE tasks SET status='STALE',worker_id=NULL,claim_token=NULL,
                               lease_until=NULL,error_json=?,updated_at=?
                               WHERE project_id=? AND task_id=?""",
                            (_json({"reason": f"source artifact {safe_name} was replaced"}), _iso(), project_id, affected_task),
                        )
                        connection.execute(
                            "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                            (project_id, affected_task),
                        )
                        self._event(connection, project_id, "TASK", affected_task, "TASK_INVALIDATED_BY_SOURCE_REVISION", {
                            "source_name": safe_name, "superseded_artifact_ids": sorted(previous_ids),
                        })
                    connection.executemany(
                        "UPDATE artifacts SET status='STALE' WHERE project_id=? AND artifact_id=?",
                        [(project_id, row["artifact_id"]) for row in previous_rows],
                    )
                    for previous in previous_rows:
                        self._event(connection, project_id, "ARTIFACT", previous["artifact_id"], "ASSET_VERSION_SUPERSEDED", {
                            "replacement_name": safe_name,
                        })
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
                    metadata=metadata_payload,
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

    def _resolve_transfer_rights_evidence_refs(
        self,
        source_connection: sqlite3.Connection,
        source_project_id: str,
        target_project_id: str,
        source_metadata: dict[str, Any],
    ) -> list[str] | None:
        if "rights_evidence_refs" not in source_metadata:
            return None
        raw_refs = source_metadata["rights_evidence_refs"]
        if not isinstance(raw_refs, list):
            raise ContractError("source rights_evidence_refs must be an array")
        resolved: list[str] = []
        target_rows: list[sqlite3.Row] | None = None
        for raw_ref in raw_refs:
            if not isinstance(raw_ref, str) or not raw_ref.strip():
                raise ContractError("source rights_evidence_refs must contain non-empty strings")
            ref = raw_ref.strip()
            if ref.startswith(("https://", "http://")):
                resolved.append(ref)
                continue
            source_evidence = source_connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                (source_project_id, ref),
            ).fetchone()
            if source_evidence is not None and source_evidence["status"] not in {"CURRENT", "ACCEPTED"}:
                raise ContractError(
                    f"source rights evidence artifact is stale: {source_project_id}/{ref}"
                )
            if source_evidence is None:
                source_evidence = self._artifact_by_name(source_connection, source_project_id, ref)
            if source_evidence is None:
                raise ContractError(
                    f"source rights evidence reference does not resolve: {source_project_id}/{ref}"
                )
            if target_rows is None:
                with closing(self._connect(target_project_id)) as target_connection:
                    target_rows = target_connection.execute(
                        "SELECT artifact_id,metadata_json FROM artifacts WHERE project_id=? AND status IN ('CURRENT','ACCEPTED')",
                        (target_project_id,),
                    ).fetchall()
            target_evidence_id = None
            for target_row in target_rows:
                target_metadata = _loads(target_row["metadata_json"], {})
                transfer = target_metadata.get("cross_project_transfer") if isinstance(target_metadata, dict) else None
                if not isinstance(transfer, dict):
                    continue
                if (
                    transfer.get("source_project_id") == source_project_id
                    and transfer.get("source_artifact_id") == source_evidence["artifact_id"]
                    and transfer.get("source_artifact_name") == source_evidence["name"]
                    and transfer.get("source_artifact_version") == int(source_evidence["version"])
                    and transfer.get("source_sha256") == source_evidence["sha256"]
                    and transfer.get("target_project_id") == target_project_id
                ):
                    target_evidence_id = target_row["artifact_id"]
                    break
            if target_evidence_id is None:
                raise ContractError(
                    "transfer the referenced rights evidence artifact first: "
                    f"{source_project_id}/{source_evidence['name']} -> {target_project_id}"
                )
            resolved.append(target_evidence_id)
        return list(dict.fromkeys(resolved))

    def transfer_artifact(
        self,
        source_project_id: str,
        source_name: str,
        target_project_id: str,
        target_name: str | None = None,
        *,
        expected_artifact_id: str,
        expected_version: int,
        expected_sha256: str,
    ) -> dict[str, Any]:
        """Copy one exact current source artifact into another project with pinned provenance.

        The source DB is write-locked while its immutable bytes are snapshotted and
        imported. Repeating the same transfer is idempotent. A later source revision
        is a distinct transfer and therefore a new target artifact version.
        """
        source_project_id = _safe_id(source_project_id, "source_project_id")
        target_project_id = _safe_id(target_project_id, "target_project_id")
        source_name = _safe_id(source_name, "source artifact name")
        target_name = _safe_id(target_name or source_name, "target artifact name")
        if source_project_id == target_project_id:
            raise ContractError("cross-project transfer requires different source and target projects")
        if not isinstance(expected_artifact_id, str) or not expected_artifact_id.strip():
            raise ContractError("expected_artifact_id is required to pin a cross-project transfer")
        if isinstance(expected_version, bool) or not isinstance(expected_version, int) or expected_version < 1:
            raise ContractError("expected_version must be a positive integer")
        expected_digest = str(expected_sha256 or "").strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
            raise ContractError("expected_sha256 must be a 64-character hexadecimal digest")

        with closing(self._connect(source_project_id)) as source_connection:
            source_connection.execute("BEGIN IMMEDIATE")
            try:
                source_row = self._artifact_by_name(source_connection, source_project_id, source_name)
                if source_row is None:
                    raise ContractError(f"current source artifact does not exist: {source_project_id}/{source_name}")
                if source_row["artifact_id"] != expected_artifact_id:
                    raise ContractError("source artifact ID changed; inspect the latest source artifact before transferring")
                if int(source_row["version"]) != expected_version:
                    raise ContractError("source artifact version changed; inspect the latest source artifact before transferring")
                if source_row["sha256"].lower() != expected_digest:
                    raise ContractError("source artifact digest changed; inspect the latest source artifact before transferring")

                source_root = self._project_dir(source_project_id).resolve()
                source_path = (source_root / source_row["relative_path"]).resolve(strict=True)
                if not source_path.is_relative_to(source_root) or not source_path.is_file():
                    raise ContractError("source artifact path is missing or escapes its project workspace")
                if _sha256(source_path) != expected_digest:
                    raise ContractError("source artifact bytes no longer match the registered digest")

                transfer = {
                    "schema_version": "1.0",
                    "transfer_mode": "IMMUTABLE_COPY",
                    "source_project_id": source_project_id,
                    "source_artifact_id": source_row["artifact_id"],
                    "source_artifact_name": source_name,
                    "source_artifact_version": int(source_row["version"]),
                    "source_sha256": expected_digest,
                    "source_produced_by_task": source_row["produced_by_task"],
                    "target_project_id": target_project_id,
                    "target_artifact_name": target_name,
                }
                source_metadata = _loads(source_row["metadata_json"], {})
                metadata = {
                    "cross_project_transfer": transfer,
                    "source_metadata": source_metadata,
                }
                if isinstance(source_metadata, dict):
                    transferred_rights_refs = self._resolve_transfer_rights_evidence_refs(
                        source_connection, source_project_id, target_project_id, source_metadata,
                    )
                    if transferred_rights_refs is not None:
                        metadata["rights_evidence_refs"] = transferred_rights_refs
                with tempfile.TemporaryDirectory(prefix="sms-cross-project-transfer-") as temp_dir:
                    snapshot = Path(temp_dir) / source_path.name
                    shutil.copy2(source_path, snapshot)
                    if _sha256(snapshot) != expected_digest or _sha256(source_path) != expected_digest:
                        raise ContractError("source artifact changed while its immutable transfer snapshot was being prepared")
                    target_artifact = self.import_asset(
                        target_project_id, target_name, snapshot,
                        kind=source_row["kind"], media_type=source_row["media_type"],
                        rights_status=source_row["rights_status"], metadata=metadata,
                    )
                source_connection.commit()
                return {
                    "source": {
                        "project_id": source_project_id,
                        "artifact_id": source_row["artifact_id"],
                        "name": source_name,
                        "version": int(source_row["version"]),
                        "sha256": expected_digest,
                    },
                    "target": target_artifact,
                    "transfer": transfer,
                }
            except Exception:
                source_connection.rollback()
                raise

    def complete_task(
        self, project_id: str, task_id: str, worker_id: str, claim_token: str,
        outputs: dict[str, dict[str, Any]], result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._refresh_cross_project_transfers_in_tx(connection, project_id)
                self._refresh_in_tx(connection, project_id)
                task = self._assert_claim(connection, project_id, task_id, worker_id, claim_token)
                expected = set(_loads(task["outputs_json"], []))
                if set(outputs) != expected:
                    raise ContractError(f"expected outputs {sorted(expected)}, got {sorted(outputs)}")
                input_bindings, input_rows = self._verify_claimed_inputs(connection, project_id, task)
                if task["kind"] == "review":
                    self._verify_review_stage_inputs(connection, project_id, task, input_bindings)
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
                    for input_row in input_rows:
                        connection.execute(
                            """INSERT INTO artifact_inputs(
                                   project_id,output_artifact_id,input_artifact_id,input_sha256,relationship,created_at
                               ) VALUES(?,?,?,?,?,?)""",
                            (project_id, registered[name]["artifact_id"], input_row["artifact_id"],
                             input_row["sha256"], "DERIVED_FROM", _iso()),
                        )
                    self._event(connection, project_id, "ARTIFACT", registered[name]["artifact_id"], "ARTIFACT_CREATED", registered[name])
                result_payload = {
                    **(result or {}),
                    "outputs": {key: value["artifact_id"] for key, value in registered.items()},
                    "input_bindings": input_bindings,
                }
                connection.execute(
                    "UPDATE tasks SET status='COMPLETED',worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,result_json=?,error_json=NULL,updated_at=? WHERE project_id=? AND task_id=?",
                    (_json(result_payload), _iso(), project_id, task_id),
                )
                self._event(connection, project_id, "TASK", task_id, "TASK_COMPLETED", {
                    "worker_id": worker_id, "outputs": result_payload["outputs"],
                    "input_bindings": input_bindings, "result": result or {},
                })
                self._refresh_in_tx(connection, project_id)
                connection.commit()
                if task["kind"] == "review":
                    self._cleanup_review_stage(project_id, task_id, task["attempts"])
                return {"task_id": task_id, "status": "COMPLETED", "artifacts": registered, "result": result_payload}
            except ClaimError:
                # Persist any upstream-transfer invalidation before reporting the revoked claim.
                connection.commit()
                raise
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
                "UPDATE tasks SET status=?,worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                (status, _json(error), _iso(), project_id, task_id),
            )
            self._event(connection, project_id, "TASK", task_id, "TASK_FAILED", {"error": error, "retryable": retryable, "next_status": status})
            self._refresh_in_tx(connection, project_id)
            actual = connection.execute(
                "SELECT status FROM tasks WHERE project_id=? AND task_id=?", (project_id, task_id)
            ).fetchone()["status"]
            connection.commit()
            if task["kind"] == "review":
                self._cleanup_review_stage(project_id, task_id, task["attempts"])
            return {"task_id": task_id, "status": actual, "retry_scheduled": retry}

    def wait_for_input(self, project_id: str, task_id: str, worker_id: str, claim_token: str, reason: str) -> None:
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            task = self._assert_claim(connection, project_id, task_id, worker_id, claim_token)
            connection.execute(
                "UPDATE tasks SET status='WAITING_INPUT',worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                (_json({"reason": reason, "explicit_external_wait": True}), _iso(), project_id, task_id),
            )
            self._event(connection, project_id, "TASK", task_id, "TASK_WAITING_INPUT",
                        {"reason": reason, "explicit_external_wait": True})
            connection.commit()
            if task["kind"] == "review":
                self._cleanup_review_stage(project_id, task_id, task["attempts"])

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
            if "action_binding" in payload:
                raise ContractError("action_binding is engine-derived, not caller supplied")
            if payload.get("task_id") is not None:
                task_id = _safe_id(payload["task_id"], "task_id")
                task = self._task_map(connection, project_id).get(task_id)
                if task is None:
                    raise ProjectNotFound(task_id)
                if _loads(task["requirements_json"], {}).get("decision_id") != decision_id:
                    raise ContractError("task must reference this exact decision_id before binding")
                payload = {**payload, "action_binding": self._decision_action_snapshot(connection, project_id, task)}
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
            self._project_row(connection, project_id)
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

    def resolve_failure(
        self, project_id: str, failure_id: str, resolution: dict[str, Any],
    ) -> dict[str, Any]:
        """Close only after current, digest-bound, role-specific reviewed evidence is verified.

        This verifies artifact bytes and structural reviewer/producer separation. It does
        not authenticate reviewer identity or determine semantic correctness.
        """
        if not isinstance(resolution, dict):
            raise ContractError("failure resolution must be a JSON object")
        refs_by_role: dict[str, list[str]] = {}
        for role in ("verification_refs", "regression_refs"):
            refs = resolution.get(role)
            if (
                not isinstance(refs, list) or not refs
                or any(not isinstance(ref, str) or not ref.strip() or ref != ref.strip() for ref in refs)
            ):
                raise ContractError(
                    f"failure resolution requires a non-empty exact artifact ID list: {role}"
                )
            refs_by_role[role] = list(refs)
        all_refs = refs_by_role["verification_refs"] + refs_by_role["regression_refs"]
        if len(set(all_refs)) != len(all_refs):
            raise ContractError(
                "verification_refs and regression_refs must use distinct artifact IDs"
            )
        reserved = {"verified_evidence", "evidence_verification", "reviewer_independence"}
        if reserved.intersection(resolution):
            raise ContractError("failure resolution contains reserved engine verification fields")
        if resolution.get("result") != "PASS":
            raise ContractError(
                "failure can be resolved only when independent verification and regression result are PASS"
            )

        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._refresh_cross_project_transfers_in_tx(connection, project_id)
                self._refresh_in_tx(connection, project_id)
                row = connection.execute(
                    "SELECT * FROM failures WHERE project_id=? AND failure_id=?",
                    (project_id, failure_id),
                ).fetchone()
                if row is None:
                    raise ProjectNotFound(failure_id)
                if row["status"] != "OPEN":
                    raise ContractError("only OPEN failures can be resolved")
                original_task_producer_ids: set[str] = set()
                if row["task_id"]:
                    original_producers = connection.execute(
                        """SELECT DISTINCT producer_id FROM artifacts
                           WHERE project_id=? AND produced_by_task=?""",
                        (project_id, row["task_id"]),
                    ).fetchall()
                    original_task_producer_ids = {
                        producer["producer_id"] for producer in original_producers
                        if isinstance(producer["producer_id"], str) and producer["producer_id"].strip()
                    }

                def verify_artifact(artifact_id: str, role: str) -> sqlite3.Row:
                    artifact = connection.execute(
                        "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                        (project_id, artifact_id),
                    ).fetchone()
                    if artifact is None:
                        raise ContractError(
                            f"{role} must reference a registered artifact_id in this project: {artifact_id}"
                        )
                    if artifact["status"] not in {"CURRENT", "ACCEPTED"}:
                        raise ContractError(
                            f"{role} artifact is not current: {artifact_id}:{artifact['status']}"
                        )
                    artifact_path = self._project_dir(project_id) / artifact["relative_path"]
                    if not artifact_path.is_file() or _sha256(artifact_path) != artifact["sha256"]:
                        raise ContractError(
                            f"{role} artifact bytes are missing or changed: {artifact_id}"
                        )
                    return artifact

                def verify_review_evidence(
                    review: sqlite3.Row, reviewed_artifact_id: str, role: str,
                ) -> list[dict[str, Any]]:
                    evidence_refs = _loads(review["evidence_refs_json"], [])
                    if (
                        not isinstance(evidence_refs, list) or not evidence_refs
                        or any(not isinstance(ref, str) or not ref.strip() or ref != ref.strip()
                               for ref in evidence_refs)
                    ):
                        raise ContractError(
                            f"{role} review requires exact registered evidence artifact IDs: {review['review_id']}"
                        )
                    if len(set(evidence_refs)) != len(evidence_refs):
                        raise ContractError(
                            f"{role} review contains duplicate evidence artifact IDs: {review['review_id']}"
                        )
                    event_row = connection.execute(
                        """SELECT payload_json FROM events
                           WHERE project_id=? AND entity_type='REVIEW' AND entity_id=?
                             AND event_type='REVIEW_RECORDED'
                           ORDER BY event_no DESC LIMIT 1""",
                        (project_id, review["review_id"]),
                    ).fetchone()
                    event_payload = _loads(event_row["payload_json"], {}) if event_row else {}
                    snapshot = event_payload.get("evidence_bindings", {})
                    snapshots = snapshot.get("review_evidence", []) if isinstance(snapshot, dict) else []
                    if not isinstance(snapshots, list) or len(snapshots) != len(evidence_refs):
                        raise ContractError(
                            f"{role} review lacks review-time evidence digest bindings: {review['review_id']}"
                        )
                    bindings: list[dict[str, Any]] = []
                    for index, evidence_id in enumerate(evidence_refs):
                        binding = snapshots[index]
                        if not isinstance(binding, dict) or binding.get("reference") != evidence_id or binding.get("resolved") is not True:
                            raise ContractError(
                                f"{role} review evidence must reference a registered artifact_id and be digest-bound when reviewed: {review['review_id']}:{evidence_id}"
                            )
                        if evidence_id == reviewed_artifact_id:
                            raise ContractError(
                                f"{role} review cannot cite the reviewed report as its own evidence: {review['review_id']}"
                            )
                        evidence_artifact = verify_artifact(evidence_id, f"{role} review evidence")
                        if (
                            int(evidence_artifact["version"]) != binding.get("version")
                            or evidence_artifact["sha256"] != binding.get("sha256")
                            or evidence_artifact["producer_id"] != binding.get("producer_id")
                        ):
                            raise ContractError(
                                f"{role} review evidence no longer matches its review-time digest binding: {evidence_id}"
                            )
                        evidence_producer_id = evidence_artifact["producer_id"]
                        if not isinstance(evidence_producer_id, str) or not evidence_producer_id.strip():
                            raise ContractError(
                                f"{role} review evidence has no recorded producer identity: {evidence_id}"
                            )
                        if review["reviewer_id"] == evidence_producer_id:
                            raise ContractError(
                                f"{role} reviewer also produced cited evidence artifact: {review['review_id']}:{evidence_id}"
                            )
                        bindings.append({
                            "artifact_id": evidence_id,
                            "version": int(evidence_artifact["version"]),
                            "sha256": evidence_artifact["sha256"],
                            "kind": evidence_artifact["kind"],
                            "media_type": evidence_artifact["media_type"],
                            "producer_id": evidence_producer_id,
                        })
                    return bindings

                def verify_evidence_refs(role: str) -> list[dict[str, Any]]:
                    verified: list[dict[str, Any]] = []
                    rubric_id = (
                        "failure-verification"
                        if role == "verification_refs"
                        else "failure-regression"
                    )
                    for artifact_id in refs_by_role[role]:
                        artifact = verify_artifact(artifact_id, role)
                        producer_id = artifact["producer_id"]
                        if not isinstance(producer_id, str) or not producer_id.strip():
                            raise ContractError(
                                f"{role} artifact has no recorded producer identity: {artifact_id}"
                            )
                        reviews = connection.execute(
                            """SELECT * FROM reviews
                               WHERE project_id=? AND artifact_id=? AND artifact_digest=? AND rubric_id=?
                               ORDER BY created_at,review_id""",
                            (project_id, artifact_id, artifact["sha256"], rubric_id),
                        ).fetchall()
                        if not reviews:
                            raise ContractError(
                                f"{role} artifact requires an exact-digest PASS {rubric_id} review: {artifact_id}"
                            )
                        if any(review["outcome"] != "PASS" for review in reviews):
                            raise ContractError(
                                f"{role} artifact has a non-PASS or conflicting {rubric_id} review: {artifact_id}"
                            )
                        if any(
                            review["producer_id"] != producer_id
                            or not review["reviewer_id"]
                            or review["reviewer_id"] == producer_id
                            for review in reviews
                        ):
                            raise ContractError(
                                f"{role} artifact review lacks structural reviewer/producer separation: {artifact_id}"
                            )
                        review_receipts = []
                        for review in reviews:
                            reviewer_id = review["reviewer_id"]
                            if reviewer_id in original_task_producer_ids:
                                raise ContractError(
                                    f"{role} reviewer also produced the failed task output: {review['review_id']}"
                                )
                            evidence_bindings = verify_review_evidence(
                                review, artifact_id, role,
                            )
                            evidence_producer_ids = {
                                item["producer_id"] for item in evidence_bindings
                            }
                            if reviewer_id in evidence_producer_ids:
                                raise ContractError(
                                    f"{role} reviewer also produced cited evidence artifact: {review['review_id']}"
                                )
                            review_receipts.append({
                                "review_id": review["review_id"],
                                "rubric_id": rubric_id,
                                "reviewer_id": reviewer_id,
                                "separated_from_producer_ids": sorted({
                                    producer_id,
                                    *original_task_producer_ids,
                                    *evidence_producer_ids,
                                }),
                                "evidence_artifacts": evidence_bindings,
                            })
                        verified.append({
                            "artifact_id": artifact_id,
                            "version": int(artifact["version"]),
                            "sha256": artifact["sha256"],
                            "kind": artifact["kind"],
                            "media_type": artifact["media_type"],
                            "producer_id": producer_id,
                            "review_ids": sorted(review["review_id"] for review in reviews),
                            "reviewer_ids": sorted({review["reviewer_id"] for review in reviews}),
                            "review_receipts": review_receipts,
                        })
                    return verified

                verification = verify_evidence_refs("verification_refs")
                regression = verify_evidence_refs("regression_refs")
                verified_resolution = {
                    **resolution,
                    "verification_refs": [item["artifact_id"] for item in verification],
                    "regression_refs": [item["artifact_id"] for item in regression],
                    "verified_evidence": {
                        "verification": verification,
                        "regression": regression,
                    },
                    "evidence_verification": "CURRENT_ARTIFACT_BYTES_AND_EXACT_DIGEST_ROLE_SPECIFIC_PASS_REVIEWS",
                    "reviewer_independence": "STRUCTURAL_SEPARATION_FROM_REPORT_FAILED_TASK_AND_CITED_EVIDENCE_PRODUCERS_ONLY_NOT_CRYPTOGRAPHIC",
                }
                connection.execute(
                    "UPDATE failures SET status='RESOLVED',resolution_json=?,updated_at=? WHERE project_id=? AND failure_id=?",
                    (_json(verified_resolution), _iso(), project_id, failure_id),
                )
                self._event(
                    connection, project_id, "FAILURE", failure_id,
                    "FAILURE_RESOLVED", verified_resolution,
                )
                connection.commit()
                return {
                    "failure_id": failure_id,
                    "status": "RESOLVED",
                    "resolution": verified_resolution,
                }
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _review_contract_requires_execution(contract: dict[str, Any]) -> bool:
        return review_contract_requires_execution(contract)

    def record_review(
        self, project_id: str, artifact_id: str, *, reviewer_id: str, rubric_id: str,
        outcome: str, dimensions: dict[str, Any], evidence_refs: list[str], notes: str = "",
        attestation: dict[str, Any] | None = None, review_task_id: str | None = None,
        review_result_artifact_id: str | None = None,
        execution_receipt: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(dimensions, dict):
            raise ContractError("review dimensions must be a JSON object")
        if "_attestation" in dimensions or "_execution_receipt" in dimensions:
            raise ContractError("review execution proof is reserved and cannot be supplied inside dimensions")
        if attestation is not None:
            raise ContractError("caller-supplied attestation fields are not execution proof; use a signed DSSE execution receipt")
        if outcome not in {"PASS", "REVISE", "FAIL", "BLOCKED", "NOT_TESTED"}:
            raise ContractError("invalid review outcome")
        if not reviewer_id or not rubric_id:
            raise ContractError("review requires reviewer and rubric")
        if (
            not isinstance(evidence_refs, list) or not evidence_refs
            or not all(isinstance(reference, str) and reference.strip() for reference in evidence_refs)
        ):
            raise ContractError("review evidence_refs must be a non-empty array of artifact IDs or names")
        _safe_id(reviewer_id, "reviewer_id")
        _safe_id(rubric_id, "rubric_id")
        self.refresh(project_id)
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._refresh_cross_project_transfers_in_tx(connection, project_id)
            self._refresh_in_tx(connection, project_id)
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
            rubric_contracts = release_policy.get("review_contracts", {})
            rubric_contract = rubric_contracts.get(rubric_id, {}) if isinstance(rubric_contracts, dict) else {}
            if not isinstance(rubric_contract, dict):
                raise ContractError("review rubric contract must be an object")
            requires_execution = self._review_contract_requires_execution(rubric_contract)
            verified_execution: dict[str, Any] | None = None
            execution_expected: dict[str, Any] | None = None
            execution_nonce: str | None = None

            if requires_execution:
                if not review_task_id or not review_result_artifact_id or not isinstance(execution_receipt, dict):
                    raise ContractError(
                        "high-assurance review requires a completed review task, registered review-report artifact, and signed execution receipt"
                    )
                _safe_id(review_task_id, "review_task_id")
                _safe_id(review_result_artifact_id, "review_result_artifact_id")
                task = connection.execute(
                    "SELECT * FROM tasks WHERE project_id=? AND task_id=?",
                    (project_id, review_task_id),
                ).fetchone()
                if task is None or task["kind"] != "review" or task["status"] != "COMPLETED":
                    raise ContractError("high-assurance review must be produced by a completed kind='review' task")
                task_requirements = _loads(task["requirements_json"], {})
                task_contract = task_requirements.get("review_contract") if isinstance(task_requirements, dict) else None
                if not isinstance(task_contract, dict):
                    raise ContractError("completed review task has no immutable review contract")
                if task_contract.get("rubric_id") != rubric_id or task_contract.get("reviewer_id") != reviewer_id:
                    raise ContractError("review task identity does not match the submitted review")
                if task_contract.get("subject_artifact") != artifact["name"]:
                    raise ContractError("review task subject does not match the reviewed artifact")
                task_result = _loads(task["result_json"], {})
                output_ids = task_result.get("outputs", {}) if isinstance(task_result, dict) else {}
                if review_result_artifact_id not in set(output_ids.values()):
                    raise ContractError("review result artifact is not an output of the completed review task")
                result_artifact = connection.execute(
                    "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, review_result_artifact_id),
                ).fetchone()
                if (
                    result_artifact is None or result_artifact["status"] not in {"CURRENT", "ACCEPTED"}
                    or result_artifact["produced_by_task"] != review_task_id
                    or result_artifact["kind"] != "review_report"
                    or result_artifact["media_type"] != "application/json"
                    or result_artifact["producer_id"] == artifact["producer_id"]
                ):
                    raise ContractError("review result must be a current JSON review_report artifact from an executor independent of the original producer")
                result_path = self._project_dir(project_id) / result_artifact["relative_path"]
                if not result_path.is_file() or _sha256(result_path) != result_artifact["sha256"]:
                    raise ContractError("review report bytes are missing or have changed")
                try:
                    report_payload = json.loads(result_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise ContractError("review report artifact is not valid JSON") from exc
                if not isinstance(report_payload, dict):
                    raise ContractError("review report artifact must contain a JSON object")
                expected_report = {
                    "schema_version": 1, "outcome": outcome, "dimensions": dimensions,
                    "evidence_refs": evidence_refs, "notes": notes,
                }
                if rubric_contract.get("required_media_inspection"):
                    expected_report["media_inspection"] = report_payload.get("media_inspection")
                if report_payload != expected_report:
                    raise ContractError("review arguments do not exactly match the registered review report artifact")

                input_bindings = task_result.get("input_bindings", [])
                if not isinstance(input_bindings, list):
                    raise ContractError("completed review task has malformed input bindings")
                subject_binding = next(
                    (item for item in input_bindings if isinstance(item, dict) and item.get("name") == artifact["name"]),
                    None,
                )
                if (
                    not isinstance(subject_binding, dict)
                    or subject_binding.get("artifact_id") != artifact_id
                    or subject_binding.get("sha256") != artifact["sha256"]
                ):
                    raise ContractError("review task did not inspect the current exact subject artifact")
                packet_event_row = connection.execute(
                    """SELECT payload_json FROM events
                       WHERE project_id=? AND entity_type='TASK' AND entity_id=?
                         AND event_type='REVIEW_PACKET_BOUND'
                       ORDER BY event_no DESC LIMIT 1""",
                    (project_id, review_task_id),
                ).fetchone()
                packet_event = _loads(packet_event_row["payload_json"], {}) if packet_event_row else {}
                packet = packet_event.get("review_packet") if isinstance(packet_event, dict) else None
                if not isinstance(packet, dict) or packet_event.get("review_packet_digest") != digest_json(packet):
                    raise ContractError("review task has no intact immutable review packet")
                expected_packet = build_review_packet(
                    project_id=project_id, task_id=review_task_id,
                    task_contract=task_contract, rubric_contract=rubric_contract,
                    input_bindings=input_bindings,
                )
                if packet != expected_packet:
                    raise ContractError("review packet no longer matches the task contract and exact inputs")
                packet_digest = digest_json(packet)
                contract_digest = review_contract_digest(task_contract, rubric_contract)
                input_digests = {
                    item["name"]: item["sha256"] for item in input_bindings
                    if isinstance(item, dict) and isinstance(item.get("name"), str)
                    and isinstance(item.get("sha256"), str)
                }
                execution_expected = {
                    "review_task_id": review_task_id,
                    "review_contract_digest": contract_digest,
                    "reviewer_id": reviewer_id,
                    "reviewer_kind": rubric_contract.get("reviewer_kind"),
                    "execution_mode": rubric_contract.get("execution_mode"),
                    "packet_digest": packet_digest,
                    "result_digest": result_artifact["sha256"],
                    "input_digests": input_digests,
                    "blind_review": bool(rubric_contract.get("blind_review", False)),
                    "required_media_inspection": rubric_contract.get("required_media_inspection"),
                    "media_inspection": report_payload.get("media_inspection") if rubric_contract.get("required_media_inspection") else None,
                    "reviewed_artifact_sha256": artifact["sha256"],
                    "review_result_sha256": result_artifact["sha256"],
                    "executor_id": result_artifact["producer_id"],
                }
                try:
                    verified_execution = self.review_trust_registry.verify(
                        execution_receipt, expected=execution_expected,
                    )
                except ReviewExecutionError as exc:
                    raise ContractError(f"review execution proof rejected: {exc}") from exc
                execution_nonce = str(verified_execution["nonce"])
                if connection.execute(
                    "SELECT 1 FROM review_execution_nonces WHERE project_id=? AND nonce=?",
                    (project_id, execution_nonce),
                ).fetchone():
                    raise ContractError("review execution receipt nonce has already been used")
            elif any(value is not None for value in (review_task_id, review_result_artifact_id, execution_receipt)):
                raise ContractError("review execution task/receipt is accepted only when the owner rubric requires high assurance")

            def snapshot_evidence_reference(reference: Any) -> dict[str, Any]:
                if (
                    not isinstance(reference, str) or not reference.strip()
                    or reference != reference.strip()
                ):
                    return {"reference": reference, "resolved": False, "reason": "INVALID_REFERENCE"}
                evidence_artifact = connection.execute(
                    "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, reference),
                ).fetchone()
                if evidence_artifact is None:
                    evidence_artifact = self._artifact_by_name(connection, project_id, reference)
                if evidence_artifact is None or evidence_artifact["status"] not in {"CURRENT", "ACCEPTED"}:
                    return {"reference": reference, "resolved": False, "reason": "NOT_CURRENT_OR_REGISTERED"}
                evidence_path = self._project_dir(project_id) / evidence_artifact["relative_path"]
                if not evidence_path.is_file() or _sha256(evidence_path) != evidence_artifact["sha256"]:
                    return {
                        "reference": reference, "resolved": False,
                        "reason": "BYTES_MISSING_OR_DIGEST_CHANGED",
                        "artifact_id": evidence_artifact["artifact_id"],
                    }
                return {
                    "reference": reference, "resolved": True,
                    "artifact_id": evidence_artifact["artifact_id"],
                    "name": evidence_artifact["name"],
                    "version": int(evidence_artifact["version"]),
                    "sha256": evidence_artifact["sha256"],
                    "kind": evidence_artifact["kind"],
                    "media_type": evidence_artifact["media_type"],
                    "producer_id": evidence_artifact["producer_id"],
                }

            review_evidence_bindings = [
                snapshot_evidence_reference(reference) for reference in evidence_refs
            ]
            finding_evidence_bindings: list[dict[str, Any]] = []
            findings = dimensions.get("findings", [])
            if isinstance(findings, list):
                for finding_index, finding in enumerate(findings):
                    if isinstance(finding, dict) and "evidence_ref" in finding:
                        finding_evidence_bindings.append({
                            "finding_index": finding_index,
                            **snapshot_evidence_reference(finding.get("evidence_ref")),
                        })
            evidence_bindings = {
                "review_evidence": review_evidence_bindings,
                "finding_evidence": finding_evidence_bindings,
                "binding_mode": "REVIEW_TIME_CURRENT_ARTIFACT_ID_VERSION_SHA256_SNAPSHOT",
            }
            review_id = "r_" + uuid.uuid4().hex[:16]
            payload = {
                "artifact_id": artifact_id, "artifact_digest": artifact["sha256"],
                "rubric_id": rubric_id, "reviewer_id": reviewer_id,
                "producer_id": artifact["producer_id"], "outcome": outcome,
                "dimensions": dimensions, "evidence_refs": evidence_refs,
                "evidence_bindings": evidence_bindings, "notes": notes,
                "review_task_id": review_task_id,
                "review_result_artifact_id": review_result_artifact_id,
                "execution_receipt": execution_receipt,
                "execution_expected": execution_expected,
                "verified_execution": verified_execution,
            }
            connection.execute(
                """INSERT INTO reviews(project_id,review_id,artifact_id,artifact_digest,rubric_id,reviewer_id,
                   producer_id,outcome,dimensions_json,evidence_refs_json,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (project_id, review_id, artifact_id, artifact["sha256"],
                 rubric_id, reviewer_id, artifact["producer_id"], outcome,
                 _json(dimensions), _json(evidence_refs), notes, _iso()),
            )
            if execution_nonce is not None:
                connection.execute(
                    "INSERT INTO review_execution_nonces(project_id,nonce,review_id,created_at) VALUES(?,?,?,?)",
                    (project_id, execution_nonce, review_id, _iso()),
                )
            self._event(connection, project_id, "REVIEW", review_id, "REVIEW_RECORDED", payload)
            connection.commit()
        return {"review_id": review_id, **payload}

    def _artifact_lineage_rows(
        self, connection: sqlite3.Connection, project_id: str, artifact_id: str,
    ) -> tuple[list[sqlite3.Row], list[str]]:
        rows: dict[str, sqlite3.Row] = {}
        failures: list[str] = []
        pending = [artifact_id]
        while pending:
            current_id = pending.pop()
            if current_id in rows:
                continue
            current = connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                (project_id, current_id),
            ).fetchone()
            if current is None:
                failures.append(f"lineage_artifact_missing:{current_id}")
                continue
            rows[current_id] = current
            parents = connection.execute(
                "SELECT input_artifact_id,input_sha256 FROM artifact_inputs WHERE project_id=? AND output_artifact_id=?",
                (project_id, current_id),
            ).fetchall()
            for parent in parents:
                parent_row = connection.execute(
                    "SELECT sha256 FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, parent["input_artifact_id"]),
                ).fetchone()
                if parent_row is None:
                    failures.append(f"lineage_parent_missing:{current_id}:{parent['input_artifact_id']}")
                elif parent_row["sha256"] != parent["input_sha256"]:
                    failures.append(f"lineage_parent_digest_mismatch:{current_id}:{parent['input_artifact_id']}")
                pending.append(parent["input_artifact_id"])
        return list(rows.values()), failures

    @staticmethod
    def _is_media_artifact(artifact: sqlite3.Row) -> bool:
        media_type = str(artifact["media_type"] or "").lower()
        kind = str(artifact["kind"] or "").lower()
        return media_type.startswith(("video/", "image/", "audio/")) or kind in {
            "media", "video", "image", "audio", "visual_asset", "sound_asset", "font_asset",
        }

    def release_check(
        self, project_id: str, artifact_id: str, *, required_rubrics: list[str],
        evidence_refs: list[str] | None = None, require_rights: bool = True,
    ) -> dict[str, Any]:
        """Delegate artifact-only release to the shared assurance service."""
        from .application.release_service import ReleaseAssuranceService
        return ReleaseAssuranceService(self).release_check(
            project_id, artifact_id, required_rubrics=required_rubrics,
            evidence_refs=evidence_refs, require_rights=require_rights,
        )

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
                if tasks[affected]["kind"] == "review":
                    self._cleanup_review_stage(project_id, affected, tasks[affected]["attempts"])
                connection.execute(
                    "UPDATE tasks SET status='STALE',worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
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
                    "UPDATE tasks SET status='PENDING',worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,error_json=NULL,updated_at=? WHERE project_id=? AND task_id=? AND status IN ('STALE','BLOCKED','FAILED','WAITING_INPUT')",
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
        # Input text or caller-asserted replay metadata is NOT independent proof.
        # Promotion requires a separate, currently unavailable independent
        # method-result oracle, not a Boolean or unresolvable reference string.
        status = "CANDIDATE"
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._project_row(connection, project_id)
            connection.execute(
                "INSERT INTO learning(project_id,learning_id,status,payload_json,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (project_id, learning_id, status, _json(payload), _iso(), _iso()),
            )
            self._event(connection, project_id, "LEARNING", learning_id, "LEARNING_RECORDED", {"status": status, "payload": payload})
            connection.commit()
        return {"learning_id": learning_id, "status": status, "payload": payload}

    def list_learning(self, project_id: str, *, include_retired: bool = False) -> list[dict[str, Any]]:
        """Read exact project-local method candidates without granting global method authority."""
        with closing(self._connect(project_id)) as connection:
            self._project_row(connection, project_id)
            if include_retired:
                rows = connection.execute(
                    "SELECT * FROM learning WHERE project_id=? ORDER BY created_at,learning_id",
                    (project_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM learning WHERE project_id=? AND status NOT IN ('RETIRED','SUPERSEDED')"
                    " ORDER BY created_at,learning_id", (project_id,),
                ).fetchall()
        return [{"learning_id": row["learning_id"], "status": row["status"],
                 "payload": _loads(row["payload_json"], {}),
                 "created_at": row["created_at"], "updated_at": row["updated_at"]}
                for row in rows]

    def retire_learning(self, project_id: str, learning_id: str, *, reason: str,
                        expected_status: str = "CANDIDATE") -> dict[str, Any]:
        """CAS retirement of an unpromoted method, preserving immutable method and event evidence."""
        learning_id = _safe_id(learning_id, "learning_id")
        if not isinstance(reason, str) or not reason.strip():
            raise ContractError("learning retirement requires a nonempty reason")
        if expected_status not in {"CANDIDATE", "VALIDATED"}:
            raise ContractError("unsupported expected learning status")
        with closing(self._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._project_row(connection, project_id)
            row = connection.execute(
                "SELECT status FROM learning WHERE project_id=? AND learning_id=?",
                (project_id, learning_id),
            ).fetchone()
            if row is None:
                raise ProjectNotFound(learning_id)
            if row["status"] != expected_status:
                raise GateError("learning status has changed; refresh before retirement")
            connection.execute(
                "UPDATE learning SET status='RETIRED',updated_at=?"
                " WHERE project_id=? AND learning_id=? AND status=?",
                (_iso(), project_id, learning_id, expected_status),
            )
            self._event(connection, project_id, "LEARNING", learning_id, "LEARNING_RETIRED",
                        {"old_status": expected_status, "status": "RETIRED", "reason": reason})
            connection.commit()
        return {"learning_id": learning_id, "status": "RETIRED", "reason": reason,
                "source_history_retained": True, "other_methods_changed": False}

    def _deliverable_progress_in_tx(self, connection, project_id, rows=None):
        """Derived candidate coverage, never a second ledger or an outcome approval."""
        from .scope import EPOCH
        from .domain.demand import inspect_demand
        brief = _loads(self._project_row(connection, project_id)["brief_json"], {})
        if brief.get("scope_epoch") != EPOCH or "deliverable_specs" not in brief:
            return {"status": "UNTYPED_OR_HISTORICAL", "candidate_coverage_complete": None,
                    "owner_outcome_verified": False}
        items = inspect_demand(brief, durable=True)["typed_deliverables"]["deliverables"]
        by_key = {
            (d["id"], v["id"]): {
                "deliverable_id": d["id"], "type": d["type"], "variant_id": v["id"],
                "expected_shape": v.get("shape") or d.get("shape"),
                "constraints": dict(d.get("constraints") or {}), "candidates": [],
            }
            for d in items
            for v in (d["variants"] or [{"id": d["id"], "shape": d.get("shape")}])
        }
        rejected = []
        if rows is None:
            rows = connection.execute("SELECT * FROM tasks WHERE project_id=?", (project_id,)).fetchall()
        for task in rows:
            if task["status"] != "COMPLETED":
                continue
            requirements = _loads(task["requirements_json"], {})
            bindings = requirements.get("deliverable_outputs", {})
            if not bindings:
                continue
            try:
                self._require_task_decision(connection, project_id, task)
            except GateError as exc:
                rejected.append({"task_id": task["task_id"], "reason": str(exc)})
                continue
            result = _loads(task["result_json"], {})
            output_ids = result.get("outputs", {})
            for name, binding in bindings.items():
                key = (binding["deliverable_id"], binding["variant_id"])
                artifact = connection.execute(
                    "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, output_ids.get(name))).fetchone()
                if (key not in by_key or artifact is None or artifact["name"] != name
                        or artifact["produced_by_task"] != task["task_id"]
                        or artifact["status"] not in {"CURRENT", "ACCEPTED"}):
                    rejected.append({"task_id": task["task_id"], "output": name,
                                     "reason": "CURRENT_BOUND_ARTIFACT_MISSING"})
                    continue
                path = self._project_dir(project_id) / artifact["relative_path"]
                if not path.is_file() or _sha256(path) != artifact["sha256"]:
                    rejected.append({"task_id": task["task_id"], "output": name,
                                     "reason": "ARTIFACT_BYTES_MISSING_OR_CHANGED"})
                    continue
                by_key[key]["candidates"].append({
                    "task_id": task["task_id"], "name": name, "artifact_id": artifact["artifact_id"],
                    "version": artifact["version"], "sha256": artifact["sha256"],
                    "media_type": artifact["media_type"], "artifact_status": artifact["status"],
                    "format_and_quality_verified": False,
                })
        from .domain.outcome_assurance import variant_release_coverage
        variants = list(by_key.values())
        coverage = variant_release_coverage(variants)
        return {"status": "CANDIDATE_COVERAGE_ONLY",
                "variants": variants, "rejected_bindings": rejected,
                "candidate_coverage_complete": all(v["candidates"] for v in variants),
                "release_authorized": False, **coverage}

    def inspect_outcome(self, project_id: str) -> dict[str, Any]:
        """Explicit read-only observation of current typed deliverable file bytes."""
        from .application.outcome_inspection import OutcomeInspectionService
        return OutcomeInspectionService(self).inspect(project_id)

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
            decision_blocked = {}
            retry_exhausted = {}
            explicit_waits = {}
            rows = connection.execute("SELECT * FROM tasks WHERE project_id=?", (project_id,)).fetchall()
            deliverable_progress = self._deliverable_progress_in_tx(connection, project_id, rows)
            for task in rows:
                detail = _loads(task["error_json"], {})
                if (task["status"] == "WAITING_INPUT" and isinstance(detail, dict)
                        and detail.get("explicit_external_wait") is True):
                    explicit_waits[task["task_id"]] = detail.get("reason", "external dependency")
                if task["status"] != "READY":
                    continue
                if task["attempts"] >= task["max_attempts"]:
                    retry_exhausted[task["task_id"]] = {
                        "attempts": task["attempts"], "max_attempts": task["max_attempts"]}
                    continue
                try:
                    self._require_task_decision(connection, project_id, task)
                except GateError as exc:
                    decision_blocked[task["task_id"]] = str(exc)
        unavailable = set(decision_blocked) | set(retry_exhausted)
        return {"project": project, "task_counts": counts, "ready_tasks": ready,
                "admitted_ready_tasks": [task_id for task_id in ready if task_id not in unavailable],
                "decision_blocked_tasks": decision_blocked,
                "retry_exhausted_tasks": retry_exhausted,
                "explicit_external_wait_tasks": explicit_waits,
                "open_failures": open_failures, "event_count": events,
                "deliverable_progress": deliverable_progress}

    def resume(self, project_id: str, *, event_limit: int = 40) -> dict[str, Any]:
        """Reconstruct an actionable project handoff from durable Video state only."""
        self.refresh(project_id)
        status = self.status(project_id)
        tasks = self.list_tasks(project_id)
        with closing(self._connect(project_id)) as connection:
            artifact_rows = connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? AND status IN ('CURRENT','ACCEPTED') ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
            decision_rows = connection.execute(
                "SELECT * FROM decisions WHERE project_id=? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
            failure_rows = connection.execute(
                "SELECT * FROM failures WHERE project_id=? AND status='OPEN' ORDER BY created_at",
                (project_id,),
            ).fetchall()
            learning_rows = connection.execute(
                "SELECT * FROM learning WHERE project_id=? ORDER BY updated_at DESC",
                (project_id,),
            ).fetchall()
        ready_by_executor: dict[str, list[str]] = {}
        admitted = set(status["admitted_ready_tasks"])
        for task in tasks:
            if task["task_id"] in admitted:
                ready_by_executor.setdefault(task["executor"], []).append(task["task_id"])
        unfinished = [task for task in tasks if task["status"] not in {"COMPLETED", "CANCELLED"}]
        if failure_rows:
            next_action = "Resolve the open root-cause records with artifact-backed verification and regression evidence."
        elif ready_by_executor.get("tool"):
            next_action = "Run the registered local tool workers; independent READY tool tasks can execute concurrently."
        elif ready_by_executor.get("agent"):
            next_action = "Dispatch the READY agent work packets; do not treat the declared executor as proof of execution."
        elif ready_by_executor.get("human"):
            next_action = "Obtain the required owner/human decision or review; do not synthesize an approval."
        elif ready_by_executor.get("external"):
            next_action = "Verify the external capability, rights, availability and cost; obtain owner authorization before any paid operation."
        elif status["decision_blocked_tasks"]:
            next_action = "Re-investigate missing or stale scoped decisions and bind current evidence before claiming affected tasks."
        elif status["retry_exhausted_tasks"]:
            next_action = "Repair and revise exhausted task contracts; reopen alone does not grant more attempts."
        elif status["explicit_external_wait_tasks"]:
            next_action = "Verify the actual external dependency and explicitly reopen waiting tasks when satisfied."
        elif any(task["status"] == "WAITING_INPUT" for task in tasks):
            next_action = "Import or produce the missing declared inputs, then refresh the task graph."
        elif unfinished:
            next_action = "Inspect dependency blockers and task failures; revise only the affected descendants."
        else:
            next_action = completion_guidance(status["deliverable_progress"])["next_action"]
        return {
            "project": status["project"],
            "project_status": "TASK_GRAPH_COMPLETE" if not unfinished else "IN_PROGRESS",
            "task_counts": status["task_counts"],
            "deliverable_progress": status["deliverable_progress"],
            "ready_by_executor": ready_by_executor,
            "decision_blocked_tasks": status["decision_blocked_tasks"],
            "retry_exhausted_tasks": status["retry_exhausted_tasks"],
            "explicit_external_wait_tasks": status["explicit_external_wait_tasks"],
            "unfinished_tasks": [
                {"task_id": task["task_id"], "executor": task["executor"], "status": task["status"],
                 "depends_on": task["depends_on"], "inputs": task["inputs"], "outputs": task["outputs"]}
                for task in unfinished
            ],
            "current_artifacts": [
                {"artifact_id": row["artifact_id"], "name": row["name"], "version": row["version"],
                 "sha256": row["sha256"], "kind": row["kind"], "media_type": row["media_type"],
                 "rights_status": row["rights_status"], "status": row["status"]}
                for row in artifact_rows
            ],
            "decisions": [
                {"decision_id": row["decision_id"], "question": row["question"], "status": row["status"],
                 "payload": _loads(row["payload_json"], {})}
                for row in decision_rows
            ],
            "open_failures": [
                {"failure_id": row["failure_id"], "task_id": row["task_id"], "payload": _loads(row["payload_json"], {})}
                for row in failure_rows
            ],
            "learning": [
                {"learning_id": row["learning_id"], "status": row["status"], "payload": _loads(row["payload_json"], {})}
                for row in learning_rows
            ],
            "recent_events": self.events(project_id, event_limit),
            "open_failure_count": status["open_failures"],
            "next_action": next_action,
            "release_authorized": False,
        }

    def events(self, project_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with closing(self._connect(project_id)) as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE project_id=? ORDER BY event_no DESC LIMIT ?",
                (project_id, max(1, min(limit, 1000))),
            ).fetchall()
            return [{**dict(row), "payload": _loads(row["payload_json"], {})} for row in reversed(rows)]

    def audit(self, project_id: str) -> dict[str, Any]:
        self.refresh(project_id)
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
            lineage_rows = connection.execute("SELECT * FROM artifact_inputs WHERE project_id=?", (project_id,)).fetchall()
            for lineage_row in lineage_rows:
                input_row = connection.execute(
                    "SELECT sha256 FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, lineage_row["input_artifact_id"]),
                ).fetchone()
                output_row = connection.execute(
                    "SELECT 1 FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, lineage_row["output_artifact_id"]),
                ).fetchone()
                if input_row is None or output_row is None:
                    failures.append(f"artifact_lineage_reference_missing:{lineage_row['output_artifact_id']}:{lineage_row['input_artifact_id']}")
                elif input_row["sha256"] != lineage_row["input_sha256"]:
                    failures.append(f"artifact_lineage_digest_mismatch:{lineage_row['output_artifact_id']}:{lineage_row['input_artifact_id']}")
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
