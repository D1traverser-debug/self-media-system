from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..engine import StudioEngine, StudioError
from .common import DomainAdapterError, _mapping, _safe_filename
from .registry import DOMAIN_ADAPTERS


def run_claimed_domain_adapter(
    engine: StudioEngine,
    project_id: str,
    task_id: str,
    worker_id: str,
    claim_token: str,
) -> dict[str, Any]:
    """Dispatch one declared local adapter under the existing Studio task lease.

    The registry selects a domain handler. The existing engine still owns claim,
    workspace, transaction, artifact lineage, task completion and failure state.
    No adapter may publish, promote a candidate, or invoke an external provider.
    """
    packet = engine.claimed_packet(project_id, task_id, worker_id, claim_token)
    task = packet["task"]
    requirements = _mapping(task.get("requirements", {}), "task.requirements")
    config = _mapping(requirements.get("domain_adapter"), "task.requirements.domain_adapter")
    name = str(config.get("name", "")).strip()
    if not name:
        raise DomainAdapterError("domain_adapter.name is required")
    outputs = list(task.get("outputs", []))
    if not outputs:
        raise DomainAdapterError("domain adapter task must declare at least one output")
    attempt = int(task.get("attempt", 1))
    claim_fingerprint = hashlib.sha256(claim_token.encode("utf-8")).hexdigest()[:24]
    output_dir = (
        engine._project_dir(project_id) / "artifacts" / "domain-adapters"
        / _safe_filename(task_id) / f"attempt-{attempt}-claim-{claim_fingerprint}"
    )
    result: dict[str, Any]

    try:
        spec = DOMAIN_ADAPTERS.get(name)
        if spec is None:
            raise DomainAdapterError(f"unsupported domain adapter: {name}")
        artifact_outputs, result = spec.handler(
            engine, project_id, packet, config, outputs, output_dir, attempt, name,
        )
        if set(artifact_outputs) != set(outputs):
            raise DomainAdapterError(
                f"adapter {name} produced {sorted(artifact_outputs)} but task declares {sorted(outputs)}"
            )
        completed = engine.complete_task(
            project_id, task_id, worker_id, claim_token, artifact_outputs, result=result,
        )
        return {"status": "COMPLETED", "adapter": name, "result": result, "completion": completed}

    except Exception as exc:
        try:
            engine.fail_task(
                project_id, task_id, worker_id, claim_token,
                {
                    "category": "domain_adapter_failed", "adapter": name,
                    "exception": type(exc).__name__, "message": str(exc),
                },
                retryable=False,
            )
        except Exception:
            pass
        if isinstance(exc, StudioError):
            raise
        raise DomainAdapterError(f"domain adapter {name} failed: {exc}") from exc
