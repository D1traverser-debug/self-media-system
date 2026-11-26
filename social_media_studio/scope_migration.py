"""Explicit one-time current-owner scope upgrade; never resurrect old execution grants."""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from .scope import EPOCH, _id, bind_owner_brief

# Historical database discriminator retained solely for a safe, auditable
# transition of already-created owner workspaces. Never used for new intake.
PRIOR_EPOCH = "VIDEO_TASK_NEUTRAL_20261124"


def migrate_owner_scope(engine: Any, project_id: str, *, reason: str) -> dict[str, Any]:
    _id(project_id)  # refuse migration of intentionally retired project identities
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("scope upgrade requires an explicit nonempty owner reason")
    with closing(engine._connect(project_id)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute(
                "SELECT brief_json FROM projects WHERE project_id=?", (project_id,)
            ).fetchone()
            if row is None:
                raise ValueError("exact project does not exist")
            old_brief = json.loads(row["brief_json"])
            old_epoch = old_brief.get("scope_epoch")
            if old_epoch == EPOCH:
                conn.commit()
                return {"project_id": project_id, "scope_epoch": EPOCH,
                        "already_current": True, "decisions_superseded": 0,
                        "leases_revoked": [], "historical_records_deleted": False}
            if old_epoch != PRIOR_EPOCH:
                raise ValueError("scope upgrade is limited to the previous owner scope; unmarked history remains retired")
            new_brief = bind_owner_brief(project_id, {**old_brief, "scope_epoch": EPOCH})
            now = datetime.now(timezone.utc).isoformat()
            running = conn.execute(
                "SELECT task_id FROM tasks WHERE project_id=? AND status='RUNNING'",
                (project_id,),
            ).fetchall()
            revoked = sorted(row["task_id"] for row in running)
            for task_id in revoked:
                conn.execute(
                    """UPDATE tasks
                       SET status='STALE',worker_id=NULL,claim_token=NULL,
                           claim_inputs_json='[]',lease_until=NULL,
                           error_json=?,updated_at=?
                       WHERE project_id=? AND task_id=? AND status='RUNNING'""",
                    (json.dumps({"reason": "scope epoch upgraded; re-admit and reclaim"},
                                ensure_ascii=False), now, project_id, task_id),
                )
                engine._event(conn, project_id, "TASK", task_id,
                              "TASK_INVALIDATED_BY_SCOPE_UPGRADE",
                              {"reason": reason, "scope_epoch": EPOCH})
            # Decision receipts are immutable. Supersession is append-only,
            # and the claim gate checks these events before honoring authority.
            active_ids = [
                x["decision_id"] for x in conn.execute(
                    "SELECT decision_id FROM decisions WHERE project_id=? AND status='ACTIVE'",
                    (project_id,),
                ).fetchall()
            ]
            for decision_id in active_ids:
                engine._event(conn, project_id, "DECISION", decision_id,
                              "DECISION_SUPERSEDED_BY_SCOPE_UPGRADE",
                              {"reason": reason, "scope_epoch": EPOCH})
            n = len(active_ids)
            conn.execute(
                "UPDATE projects SET brief_json=?,updated_at=? WHERE project_id=?",
                (json.dumps(new_brief, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":")), now, project_id),
            )
            engine._event(conn, project_id, "PROJECT", project_id,
                          "PROJECT_BRIEF_REVISED", {
                              "reason": reason, "migration": True,
                              "previous_scope_epoch": old_epoch, "scope_epoch": EPOCH,
                              "previous_brief_sha256": hashlib.sha256(
                                  row["brief_json"].encode("utf-8")).hexdigest(),
                              "decisions_superseded": n, "leases_revoked": revoked,
                          })
            engine._refresh_in_tx(conn, project_id)
            conn.commit()
            return {"project_id": project_id, "scope_epoch": EPOCH,
                    "already_current": False, "decisions_superseded": n,
                    "leases_revoked": revoked, "historical_records_deleted": False,
                    "independent_reacceptance_required": True}
        except Exception:
            conn.rollback()
            raise
