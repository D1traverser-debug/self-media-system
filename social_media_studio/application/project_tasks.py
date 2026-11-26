from __future__ import annotations

from contextlib import closing
import hashlib
import shutil
import sqlite3
from typing import Any, Iterable, Protocol

from ..engine_support import ContractError, ProjectNotFound, _iso, _json, _loads, _safe_id, _sha256


class ProjectTaskEnginePort(Protocol):
    def _project_dir(self, project_id: str): ...
    def _connect(self, project_id: str) -> sqlite3.Connection: ...
    def _project_row(self, connection: sqlite3.Connection, project_id: str) -> sqlite3.Row: ...
    @staticmethod
    def _schema(connection: sqlite3.Connection) -> None: ...
    def _event(self, connection: sqlite3.Connection, project_id: str, entity_type: str,
               entity_id: str, event_type: str, payload: dict[str, Any]) -> None: ...
    @staticmethod
    def _validate_brief(brief: dict[str, Any]) -> None: ...
    def _artifact_by_name(self, connection: sqlite3.Connection, project_id: str, name: str): ...
    def _task_map(self, connection: sqlite3.Connection, project_id: str) -> dict[str, dict[str, Any]]: ...
    @staticmethod
    def _descendant_closure(tasks: dict[str, dict[str, Any]], roots: Iterable[str]) -> set[str]: ...
    def _validate_graph(self, all_tasks: dict[str, dict[str, Any]]) -> None: ...
    def _refresh_in_tx(self, connection: sqlite3.Connection, project_id: str) -> None: ...
    def _refresh_cross_project_transfers_in_tx(self, connection: sqlite3.Connection, project_id: str) -> None: ...
    def project(self, project_id: str) -> dict[str, Any]: ...
    def brief_history(self, project_id: str) -> list[dict[str, Any]]: ...
    def list_tasks(self, project_id: str) -> list[dict[str, Any]]: ...


class ProjectTaskService:
    """Project and task-graph application service over the single StudioEngine ledger.

    This service owns project/brief/task graph operations. It does not own a database,
    scheduler, workspace, event stream or second authority; those remain on the engine.
    """

    def __init__(self, engine: ProjectTaskEnginePort):
        self.engine = engine

    def create_project(self, project_id: str, title: str, brief: dict[str, Any]) -> dict[str, Any]:
        project_id = _safe_id(project_id, "project_id")
        self.engine._validate_brief(brief)
        if "scope_epoch" in brief:
            from .scope import bind_owner_brief
            bind_owner_brief(project_id, brief)
        directory = self.engine._project_dir(project_id)
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "assets").mkdir()
        (directory / "artifacts").mkdir()
        db_path = directory / "studio.sqlite3"
        connection = sqlite3.connect(db_path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            self.engine._schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            now = _iso()
            connection.execute(
                "INSERT INTO projects(project_id,title,brief_json,created_at,updated_at) VALUES(?,?,?,?,?)",
                (project_id, title or project_id, _json(brief), now, now),
            )
            self.engine._event(connection, project_id, "PROJECT", project_id, "PROJECT_CREATED", {"title": title, "brief": brief})
            connection.commit()
        except Exception:
            connection.rollback()
            shutil.rmtree(directory, ignore_errors=True)
            raise
        finally:
            connection.close()
        return self.engine.project(project_id)


    def project(self, project_id: str) -> dict[str, Any]:
        with closing(self.engine._connect(project_id)) as connection:
            row = self.engine._project_row(connection, project_id)
            return {
                "project_id": row["project_id"], "title": row["title"],
                "brief": _loads(row["brief_json"], {}), "revision": row["revision"],
                "created_at": row["created_at"], "updated_at": row["updated_at"],
                "workspace": str(self.engine._project_dir(project_id)),
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
        with closing(self.engine._connect(project_id)) as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE project_id=? AND entity_type='PROJECT' AND event_type IN ('PROJECT_CREATED','PROJECT_BRIEF_REVISED') ORDER BY event_no",
                (project_id,),
            ).fetchall()
            return [{**dict(row), "payload": _loads(row["payload_json"], {})} for row in rows]


    def revise_brief(
        self, project_id: str, brief: dict[str, Any], *, reason: str,
        affected_task_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        self.engine._validate_brief(brief)
        if not isinstance(reason, str) or not reason.strip():
            raise ContractError("brief revision requires a reason")
        with closing(self.engine._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                project = self.engine._project_row(connection, project_id)
                tasks = self.engine._task_map(connection, project_id)
                roots = list(tasks) if affected_task_ids is None else list(affected_task_ids)
                unknown = sorted(set(roots) - set(tasks))
                if unknown:
                    raise ContractError(f"unknown affected_task_ids: {unknown}")
                invalidated = self.engine._descendant_closure(tasks, roots) if roots else set()
                old_brief = _loads(project["brief_json"], {})
                if "scope_epoch" in old_brief:
                    if brief.get("scope_epoch") != old_brief["scope_epoch"]:
                        raise ContractError("owner task scope epoch cannot change")
                    if brief != old_brief:
                        # Until a task-level semantic dependency oracle proves a narrower
                        # change set, the whole owner brief is the governing upstream input.
                        invalidated = set(tasks)
                elif "scope_epoch" in brief:
                    raise ContractError("retired instance cannot be converted into a current owner task")
                old_digest = hashlib.sha256(_json(old_brief).encode("utf-8")).hexdigest()
                new_digest = hashlib.sha256(_json(brief).encode("utf-8")).hexdigest()
                now = _iso()
                connection.execute(
                    "UPDATE projects SET brief_json=?,revision=revision+1,updated_at=? WHERE project_id=?",
                    (_json(brief), now, project_id),
                )
                for task_id in invalidated:
                    connection.execute(
                        "UPDATE tasks SET status='STALE',worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                        (_json({"reason": reason, "brief_revision": int(project["revision"]) + 1}), now, project_id, task_id),
                    )
                    connection.execute(
                        "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                        (project_id, task_id),
                    )
                    self.engine._event(connection, project_id, "TASK", task_id, "TASK_INVALIDATED_BY_BRIEF_REVISION", {
                        "reason": reason, "project_revision": int(project["revision"]) + 1,
                    })
                self.engine._event(connection, project_id, "PROJECT", project_id, "PROJECT_BRIEF_REVISED", {
                    "previous_brief": old_brief, "brief": brief,
                    "previous_sha256": old_digest, "sha256": new_digest,
                    "reason": reason, "invalidated_tasks": sorted(invalidated),
                })
                self.engine._refresh_in_tx(connection, project_id)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {"project": self.engine.project(project_id), "invalidated_tasks": sorted(invalidated), "brief_history": self.engine.brief_history(project_id)}


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
        candidate_groups: dict[str, set[str]] = {}
        adjudications: list[tuple[str, dict[str, Any]]] = []
        for task_id, task in all_tasks.items():
            for output in task.get("outputs", []):
                previous = output_owners.get(output)
                if previous is not None and previous != task_id:
                    raise ContractError(f"artifact output {output!r} has multiple producers: {previous}, {task_id}")
                output_owners[output] = task_id
            requirements = task.get("requirements", {})
            coordination = requirements.get("coordination", {}) if isinstance(requirements, dict) else {}
            if not coordination:
                continue
            if not isinstance(coordination, dict):
                raise ContractError(f"{task_id}: requirements.coordination must be an object")
            pattern = coordination.get("pattern")
            if pattern == "COMPETITIVE_CANDIDATES":
                group = coordination.get("decision_group")
                criteria = coordination.get("candidate_criteria")
                if not isinstance(group, str) or not group.strip():
                    raise ContractError(f"{task_id}: competitive candidate task requires decision_group")
                if not isinstance(criteria, list) or not criteria:
                    raise ContractError(f"{task_id}: competitive candidate task requires declared candidate_criteria")
                candidate_groups.setdefault(group, set()).add(task_id)
            elif pattern == "OWNER_ADJUDICATION":
                group = coordination.get("consumes_group")
                adjudicator = coordination.get("adjudicator")
                if not isinstance(group, str) or not group.strip() or not isinstance(adjudicator, str) or not adjudicator.strip():
                    raise ContractError(f"{task_id}: owner adjudication requires consumes_group and adjudicator")
                if task.get("executor") != "human":
                    raise ContractError(f"{task_id}: owner adjudication must use the human executor")
                if coordination.get("decision_receipt_required") is not True:
                    raise ContractError(f"{task_id}: owner adjudication requires a durable decision receipt")
                adjudications.append((task_id, coordination))
            elif pattern == "CONSULTATIVE_ADVICE":
                if coordination.get("advisory_only") is not True or not coordination.get("decision_owner"):
                    raise ContractError(f"{task_id}: consultative advice must be advisory_only and name decision_owner")
            elif pattern == "STRUCTURED_CRITIQUE_AND_REVISION":
                rounds = int(coordination.get("max_rounds", 0))
                if rounds < 1 or rounds > 3:
                    raise ContractError(f"{task_id}: critique/revision must declare bounded max_rounds in 1..3")
            elif pattern in {"INDEPENDENT_PARALLEL", "SERIAL_DEPENDENCY", "FAN_OUT_FAN_IN", "QUORUM_OR_PANEL_REVIEW"}:
                pass
            else:
                raise ContractError(f"{task_id}: unknown coordination pattern {pattern!r}")
        ancestor_cache: dict[str, set[str]] = {}

        def ancestors(task_id: str) -> set[str]:
            cached = ancestor_cache.get(task_id)
            if cached is not None:
                return cached
            result: set[str] = set()
            for dependency in all_tasks[task_id].get("depends_on", []):
                result.add(dependency)
                result.update(ancestors(dependency))
            ancestor_cache[task_id] = result
            return result

        for task_id, task in all_tasks.items():
            for input_name in task.get("inputs", []):
                producer = output_owners.get(input_name)
                if producer is not None and producer not in ancestors(task_id):
                    raise ContractError(f"{task_id}: input artifact {input_name!r} is produced by {producer!r} but its producer is not a declared dependency")

        for group, candidates in candidate_groups.items():
            if len(candidates) < 2:
                raise ContractError(f"decision group {group!r} requires at least two independent candidates")
        for task_id, coordination in adjudications:
            group = coordination["consumes_group"]
            candidates = candidate_groups.get(group)
            if not candidates:
                raise ContractError(f"{task_id}: unknown decision group {group!r}")
            missing_candidates = sorted(candidates - set(all_tasks[task_id].get("depends_on", [])))
            if missing_candidates:
                raise ContractError(f"{task_id}: owner adjudication must depend on every candidate in {group!r}: {missing_candidates}")


    def add_tasks(self, project_id: str, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(tasks, list) or not tasks:
            raise ContractError("tasks must be a non-empty array")
        with closing(self.engine._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                project = self.engine._project_row(connection, project_id)
                from .scope import validate_task_binding
                brief = _loads(project["brief_json"], {})
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
                        "inputs": _loads(row["inputs_json"], []),
                        "outputs": _loads(row["outputs_json"], []),
                        "requirements": _loads(row["requirements_json"], {}),
                        "executor": row["executor"],
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
                    validate_task_binding(brief, task)
                    prepared.append(task)
                    graph[task_id] = task
                    new_ids.add(task_id)
                self.engine._validate_graph(graph)
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
                    self.engine._event(connection, project_id, "TASK", task["task_id"], "TASK_ADDED", task)
                connection.execute(
                    "UPDATE projects SET revision=revision+1,updated_at=? WHERE project_id=?",
                    (now, project_id),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        self.engine.refresh(project_id)
        return self.engine.list_tasks(project_id)


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
        with closing(self.engine._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                rows = self.engine._task_map(connection, project_id)
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
                from .scope import validate_task_binding
                validate_task_binding(_loads(self.engine._project_row(connection, project_id)["brief_json"], {}), revised)
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
                    key: {
                        "depends_on": _loads(value["depends_on_json"], []),
                        "inputs": _loads(value["inputs_json"], []),
                        "outputs": _loads(value["outputs_json"], []),
                        "requirements": _loads(value["requirements_json"], {}),
                        "executor": value["executor"],
                    }
                    for key, value in rows.items()
                }
                graph[task_id] = {
                    "depends_on": revised["depends_on"], "inputs": revised["inputs"], "outputs": revised["outputs"],
                    "requirements": revised["requirements"], "executor": revised["executor"],
                }
                existing_artifact_names = {
                    row["name"] for row in connection.execute(
                        "SELECT name FROM artifacts WHERE project_id=? AND status IN ('CURRENT','ACCEPTED') AND produced_by_task IS NULL",
                        (project_id,),
                    ).fetchall()
                }
                if existing_artifact_names.intersection(revised["outputs"]):
                    raise ContractError(f"task outputs cannot reuse imported asset names: {sorted(existing_artifact_names.intersection(revised['outputs']))}")
                self.engine._validate_graph(graph)
                descendants = self.engine._descendant_closure(rows, [task_id]) - {task_id}
                now = _iso()
                connection.execute(
                    """UPDATE tasks SET title=?,kind=?,executor=?,depends_on_json=?,inputs_json=?,outputs_json=?,
                       acceptance_json=?,requirements_json=?,priority=?,max_attempts=?,status='PENDING',
                       attempts=0,worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,result_json=NULL,error_json=?,updated_at=?
                       WHERE project_id=? AND task_id=?""",
                    (revised["title"], revised["kind"], revised["executor"], _json(revised["depends_on"]),
                     _json(revised["inputs"]), _json(revised["outputs"]), _json(revised["acceptance"]),
                     _json(revised["requirements"]), revised["priority"], revised["max_attempts"],
                     _json({"reason": reason}), now, project_id, task_id),
                )
                for descendant in descendants:
                    connection.execute(
                        "UPDATE tasks SET status='STALE',worker_id=NULL,claim_token=NULL,claim_inputs_json='[]',lease_until=NULL,error_json=?,updated_at=? WHERE project_id=? AND task_id=?",
                        (_json({"reason": f"upstream task {task_id} contract changed"}), now, project_id, descendant),
                    )
                    connection.execute(
                        "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                        (project_id, descendant),
                    )
                    self.engine._event(connection, project_id, "TASK", descendant, "TASK_INVALIDATED_BY_UPSTREAM_CONTRACT", {"upstream_task": task_id, "reason": reason})
                connection.execute(
                    "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                    (project_id, task_id),
                )
                connection.execute("UPDATE projects SET revision=revision+1,updated_at=? WHERE project_id=?", (now, project_id))
                self.engine._event(connection, project_id, "TASK", task_id, "TASK_CONTRACT_REVISED", {"previous": current, "revised": revised, "reason": reason, "invalidated_descendants": sorted(descendants)})
                self.engine._refresh_in_tx(connection, project_id)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {"task": next(item for item in self.engine.list_tasks(project_id) if item["task_id"] == task_id), "invalidated_descendants": sorted(descendants)}


    def _task_map(self, connection: sqlite3.Connection, project_id: str) -> dict[str, dict[str, Any]]:
        rows = connection.execute("SELECT * FROM tasks WHERE project_id=?", (project_id,)).fetchall()
        return {row["task_id"]: dict(row) for row in rows}


    def _refresh_in_tx(self, connection: sqlite3.Connection, project_id: str) -> None:
        tasks = self.engine._task_map(connection, project_id)
        now = _iso()
        for task_id, row in tasks.items():
            status = row["status"]
            if status not in {"PENDING", "READY", "BLOCKED", "WAITING_INPUT"}:
                continue
            deps = _loads(row["depends_on_json"], [])
            dep_states = [tasks[dep]["status"] for dep in deps]
            if any(state in {"FAILED", "BLOCKED", "STALE", "CANCELLED"} for state in dep_states):
                new_status = "BLOCKED"
            elif not all(state == "COMPLETED" for state in dep_states):
                # Do not label an expected upstream output as an external missing input.
                new_status = "PENDING"
            elif not all(self.engine._artifact_by_name(connection, project_id, name) is not None for name in _loads(row["inputs_json"], [])):
                new_status = "WAITING_INPUT"
            else:
                new_status = "READY"
            # External waiting is an intentional owner/worker dependency, not
            # the same as waiting for a declared file. Only an explicit reopen
            # releases it, even if all declared artifact inputs already exist.
            wait_reason = _loads(row["error_json"], {})
            if new_status == "READY" and isinstance(wait_reason, dict) and wait_reason.get("explicit_external_wait") is True:
                new_status = "WAITING_INPUT"
            if new_status != status:
                connection.execute(
                    "UPDATE tasks SET status=?,updated_at=? WHERE project_id=? AND task_id=?",
                    (new_status, now, project_id, task_id),
                )
                self.engine._event(connection, project_id, "TASK", task_id, "TASK_READINESS_CHANGED", {"from": status, "to": new_status})


    def _refresh_cross_project_transfers_in_tx(self, connection: sqlite3.Connection, project_id: str) -> None:
        """Invalidate imported snapshots when their exact source artifact is no longer current."""
        rows = connection.execute(
            "SELECT * FROM artifacts WHERE project_id=? AND status IN ('CURRENT','ACCEPTED')",
            (project_id,),
        ).fetchall()
        for row in rows:
            metadata = _loads(row["metadata_json"], {})
            transfer = metadata.get("cross_project_transfer") if isinstance(metadata, dict) else None
            if not isinstance(transfer, dict):
                continue
            source_project_id = str(transfer.get("source_project_id") or "").strip()
            source_artifact_id = str(transfer.get("source_artifact_id") or "").strip()
            source_name = str(transfer.get("source_artifact_name") or "").strip()
            source_version = transfer.get("source_artifact_version")
            source_digest = str(transfer.get("source_sha256") or "").strip().lower()
            valid = (
                transfer.get("schema_version") == "1.0"
                and transfer.get("transfer_mode") == "IMMUTABLE_COPY"
                and transfer.get("target_project_id") == project_id
                and transfer.get("target_artifact_name") == row["name"]
                and bool(source_project_id) and bool(source_artifact_id) and bool(source_name)
                and isinstance(source_version, int) and source_version >= 1
                and bool(re.fullmatch(r"[0-9a-f]{64}", source_digest))
                and row["sha256"].lower() == source_digest
            )
            if valid:
                try:
                    with closing(self.engine._connect(source_project_id)) as source_connection:
                        source = source_connection.execute(
                            "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                            (source_project_id, source_artifact_id),
                        ).fetchone()
                        valid = bool(
                            source is not None
                            and source["name"] == source_name
                            and int(source["version"]) == source_version
                            and source["sha256"].lower() == source_digest
                            and source["status"] in {"CURRENT", "ACCEPTED"}
                        )
                        if valid:
                            source_root = self.engine._project_dir(source_project_id).resolve()
                            source_path = (source_root / source["relative_path"]).resolve(strict=True)
                            valid = source_path.is_relative_to(source_root) and source_path.is_file() and _sha256(source_path) == source_digest
                except (ProjectNotFound, OSError, sqlite3.Error):
                    valid = False
            if valid:
                continue

            connection.execute(
                "UPDATE artifacts SET status='STALE' WHERE project_id=? AND artifact_id=?",
                (project_id, row["artifact_id"]),
            )
            task_rows = connection.execute(
                "SELECT task_id,depends_on_json,inputs_json FROM tasks WHERE project_id=?",
                (project_id,),
            ).fetchall()
            task_map = {item["task_id"]: item for item in task_rows}
            affected = {
                item["task_id"] for item in task_rows
                if row["name"] in _loads(item["inputs_json"], [])
            }
            changed = True
            while changed:
                changed = False
                for candidate, task in task_map.items():
                    if candidate not in affected and any(
                        dependency in affected for dependency in _loads(task["depends_on_json"], [])
                    ):
                        affected.add(candidate)
                        changed = True
            now = _iso()
            for task_id in sorted(affected):
                connection.execute(
                    """UPDATE tasks SET status='STALE',worker_id=NULL,claim_token=NULL,
                       claim_inputs_json='[]',lease_until=NULL,error_json=?,updated_at=?
                       WHERE project_id=? AND task_id=?""",
                    (_json({
                        "reason": "cross-project source artifact is missing, superseded, or digest-invalid",
                        "source_project_id": source_project_id,
                        "source_artifact_id": source_artifact_id,
                        "source_sha256": source_digest,
                    }), now, project_id, task_id),
                )
                connection.execute(
                    "UPDATE artifacts SET status='STALE' WHERE project_id=? AND produced_by_task=? AND status IN ('CURRENT','ACCEPTED')",
                    (project_id, task_id),
                )
                self.engine._event(connection, project_id, "TASK", task_id, "TASK_INVALIDATED_BY_CROSS_PROJECT_SOURCE", {
                    "source_project_id": source_project_id,
                    "source_artifact_id": source_artifact_id,
                    "transferred_artifact_id": row["artifact_id"],
                })
            self.engine._event(connection, project_id, "ARTIFACT", row["artifact_id"], "CROSS_PROJECT_SOURCE_STALE", {
                "source_project_id": source_project_id,
                "source_artifact_id": source_artifact_id,
                "source_artifact_version": source_version,
                "source_sha256": source_digest,
                "invalidated_tasks": sorted(affected),
            })


    def refresh(self, project_id: str) -> None:
        with closing(self.engine._connect(project_id)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self.engine._refresh_cross_project_transfers_in_tx(connection, project_id)
            self.engine._refresh_in_tx(connection, project_id)
            connection.commit()


    def list_tasks(self, project_id: str) -> list[dict[str, Any]]:
        with closing(self.engine._connect(project_id)) as connection:
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

