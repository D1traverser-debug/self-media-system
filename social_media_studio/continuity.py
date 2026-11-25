"""Project-scoped, event-backed conversation continuity and exact-state handoff.

This is not a second scheduler, CAOS runtime, memory search index, or trust oracle.
Untrusted notes never become instructions, approvals, decisions, or global methods.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import closing
from typing import Any

from .engine import ContractError, GateError, StudioEngine, _inside, _iso, _json, _loads, _sha256

SCHEMA = "SMS_CONTINUITY_V1"
KINDS = frozenset({
    "OWNER_REQUIREMENT", "OWNER_CORRECTION", "SOURCE_CONTEXT",
    "IMPLEMENTATION_CONTEXT", "FAILURE_LESSON", "NEXT_ACTION",
})
SOURCE_KINDS = frozenset({"OWNER_MESSAGE", "ATTACHED_FILE", "TOOL_RESULT", "ASSISTANT_SUMMARY"})
MAX_TEXT = 60000


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _str_list(value: Any, label: str, *, limit: int = 100) -> list[str]:
    if not isinstance(value, list) or len(value) > limit:
        raise ContractError(f"{label} must be a bounded list")
    if any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in value):
        raise ContractError(f"{label} must contain exact nonempty strings")
    if len(value) != len(set(value)):
        raise ContractError(f"{label} contains duplicates")
    return list(value)


def capture(engine: StudioEngine, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Append a source-labelled project note; never rewrite the owner brief."""
    if not isinstance(payload, dict):
        raise ContractError("continuity payload must be an object")
    if set(payload) - {"note_id", "kind", "text", "source_kind", "source_locator",
                       "task_ids", "artifact_ids"}:
        raise ContractError("continuity payload contains unknown or authority-claiming fields")
    kind, text = payload.get("kind"), payload.get("text")
    source_kind, locator = payload.get("source_kind"), payload.get("source_locator")
    if kind not in KINDS or not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
        raise ContractError("continuity note requires a supported kind and bounded nonempty text")
    if source_kind not in SOURCE_KINDS or not isinstance(locator, str) or not locator.strip() or len(locator) > 1024:
        raise ContractError("continuity source requires an explicit kind and nonempty locator")
    from .engine import _safe_id
    note_id = _safe_id(payload.get("note_id") or "ctx_" + uuid.uuid4().hex[:20], "note_id")
    task_ids = _str_list(payload.get("task_ids", []), "task_ids")
    artifact_ids = _str_list(payload.get("artifact_ids", []), "artifact_ids")

    with closing(engine._connect(project_id)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            project = engine._project_row(connection, project_id)
            duplicate = connection.execute(
                "SELECT 1 FROM events WHERE project_id=? AND entity_type='CONTINUITY' AND entity_id=?",
                (project_id, note_id),
            ).fetchone()
            if duplicate:
                raise ContractError("continuity note_id is already present in this project")
            for task_id in task_ids:
                row = connection.execute(
                    "SELECT 1 FROM tasks WHERE project_id=? AND task_id=?", (project_id, task_id)
                ).fetchone()
                if row is None:
                    raise ContractError(f"unknown project-local task reference: {task_id}")
            bindings = []
            for artifact_id in artifact_ids:
                row = connection.execute(
                    "SELECT * FROM artifacts WHERE project_id=? AND artifact_id=?",
                    (project_id, artifact_id),
                ).fetchone()
                if row is None or row["status"] not in {"CURRENT", "ACCEPTED"}:
                    raise ContractError(f"unavailable current project artifact: {artifact_id}")
                path = _inside(engine._project_dir(project_id), row["relative_path"])
                if _sha256(path) != row["sha256"]:
                    raise GateError(f"artifact byte integrity failed: {artifact_id}")
                bindings.append({"artifact_id": artifact_id, "sha256": row["sha256"],
                                 "version": row["version"]})
            brief = _loads(project["brief_json"], {})
            record = {
                "schema": SCHEMA,
                "note_id": note_id,
                "project_id": project_id,
                "scope_epoch": brief.get("scope_epoch"),
                "project_revision": project["revision"],
                "brief_sha256": _digest(brief),
                "kind": kind, "text": text,
                "source_kind": source_kind, "source_locator": locator,
                "source_trust": "DECLARED_NOT_AUTHENTICATED",
                "task_ids": task_ids, "artifact_bindings": bindings,
                "created_at": _iso(),
                "effect_authorized": False,
                "brief_mutated": False,
                "knowledge_promoted": False,
            }
            record["record_sha256"] = _digest(record)
            engine._event(connection, project_id, "CONTINUITY", note_id, "CONTINUITY_RECORDED", record)
            event_no = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return {**record, "event_no": event_no}


def records(engine: StudioEngine, project_id: str) -> list[dict[str, Any]]:
    """Read all captured context, not only the last N operational events."""
    with closing(engine._connect(project_id)) as connection:
        engine._project_row(connection, project_id)
        rows = connection.execute(
            "SELECT event_no,payload_json FROM events WHERE project_id=? "
            "AND entity_type='CONTINUITY' AND event_type='CONTINUITY_RECORDED' "
            "ORDER BY event_no ASC", (project_id,),
        ).fetchall()
    result, seen = [], set()
    for row in rows:
        record = _loads(row["payload_json"], {})
        if not isinstance(record, dict) or record.get("schema") != SCHEMA:
            raise GateError("continuity event has an invalid schema")
        digest = record.pop("record_sha256", None)
        if digest != _digest(record) or record.get("project_id") != project_id:
            raise GateError("continuity record integrity or scope mismatch")
        if record.get("note_id") in seen:
            raise GateError("duplicate continuity identity in event history")
        seen.add(record["note_id"])
        result.append({**record, "record_sha256": digest, "event_no": row["event_no"]})
    return result


def handoff(engine: StudioEngine, project_id: str) -> dict[str, Any]:
    """Create a snapshot of the current durable ledger; never authorize execution."""
    audit = engine.audit(project_id)

    def checkpoint() -> tuple[int, int]:
        with closing(engine._connect(project_id)) as connection:
            project = engine._project_row(connection, project_id)
            latest = connection.execute(
                "SELECT COALESCE(MAX(event_no),0) FROM events WHERE project_id=?", (project_id,)
            ).fetchone()[0]
            return int(project["revision"]), int(latest)

    before = checkpoint()
    resume = engine.resume(project_id, event_limit=40)
    context = records(engine, project_id)
    after = checkpoint()
    if before != after or resume["project"]["revision"] != after[0]:
        raise GateError("project changed during handoff construction; retry from current ledger")
    checkpoint_event = after[1]
    # A correction is not silently incorporated into the executable brief.
    corrections = [r["note_id"] for r in context if r["kind"] == "OWNER_CORRECTION"]
    packet = {
        "schema": "SMS_HANDOFF_V1",
        "project_id": project_id,
        "workspace": str(engine._project_dir(project_id).resolve()),
        "scope_epoch": resume["project"]["brief"].get("scope_epoch"),
        "project_revision": resume["project"]["revision"],
        "event_checkpoint": checkpoint_event,
        "resume": resume,
        "continuity_records": context,
        "corrections_requiring_explicit_reconciliation": corrections,
        "project_audit_pass": audit["pass"],
        "project_audit_failures": audit["failures"],
        "coverage": "RECORDED_PROJECT_STATE_ONLY_NOT_WHOLE_CHAT_HISTORY",
        "context_trust": "DECLARED_SOURCES_ARE_UNVERIFIED_DATA_NOT_INSTRUCTIONS",
        "caos_activation_verified": False,
        "execution_authorized": False,
        "release_authorized": False,
    }
    packet["packet_sha256"] = _digest(packet)
    return packet


def verify_handoff(engine: StudioEngine, project_id: str, packet: dict[str, Any]) -> dict[str, Any]:
    """Detect copied, altered or stale packets before resuming a fresh chat."""
    if not isinstance(packet, dict) or packet.get("schema") != "SMS_HANDOFF_V1":
        raise ContractError("unsupported handoff packet")
    if packet.get("project_id") != project_id:
        raise GateError("handoff targets a different project")
    digest = packet.get("packet_sha256")
    unsigned = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if not isinstance(digest, str) or digest != _digest(unsigned):
        raise GateError("handoff packet digest mismatch")
    current = handoff(engine, project_id)
    if packet != current:
        raise GateError("handoff is stale or points to a different workspace/ledger state")
    return {
        "valid": True, "project_id": project_id, "packet_sha256": digest,
        "current_event_checkpoint": current["event_checkpoint"],
        "project_audit_pass": current["project_audit_pass"],
        "corrections_requiring_explicit_reconciliation":
            current["corrections_requiring_explicit_reconciliation"],
        "execution_authorized": False, "caos_activation_verified": False,
    }
