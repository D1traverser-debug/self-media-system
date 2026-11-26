from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..engine import StudioEngine, StudioError
from .common import DomainAdapterError, _mapping, _safe_filename
from .registry import DOMAIN_ADAPTERS, DomainAdapterSpec


def validate_domain_adapter_contract(
    spec: DomainAdapterSpec, config: dict[str, Any], outputs: list[str],
) -> None:
    """Enforce the registry's declared local-effect and input/output boundary."""
    if not isinstance(config, dict):
        raise DomainAdapterError("domain adapter config must be an object")
    missing = sorted(set(spec.required_config) - set(config))
    if missing:
        raise DomainAdapterError(f"adapter {spec.name} missing required config: {missing}")
    if not spec.output_contract or not isinstance(spec.output_contract, str):
        raise DomainAdapterError(f"adapter {spec.name} has no declared output contract")
    if spec.effect_scope not in {"PROJECT_LOCAL_ARTIFACT_WRITE", "PROJECT_LOCAL_CANDIDATE_RENDER"}:
        raise DomainAdapterError(f"adapter {spec.name} has an unsupported effect scope")
    if spec.external_effects or spec.promotes_candidate or spec.publishes:
        raise DomainAdapterError(f"adapter {spec.name} exceeds the local non-promoting effect boundary")
    if not outputs or any(not isinstance(item, str) or not item.strip() for item in outputs):
        raise DomainAdapterError(f"adapter {spec.name} requires explicit nonempty output identities")
    if len(outputs) != len(set(outputs)):
        raise DomainAdapterError(f"adapter {spec.name} output identities must be unique")


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
        validate_domain_adapter_contract(spec, config, outputs)
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
