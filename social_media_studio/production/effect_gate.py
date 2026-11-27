"""Effect admission at real local process launch, not the planner's declaration.

The operator allowlist is read exclusively from the hosting process
environment, never from a task, asset or rights-clearance JSON.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from ..domain.effects import authorize_effect, TRUSTED_CODE_UNSANDBOXED
from .contracts import FrameRenderSpec, ProductionContractError


GRANT_ENV = "SMS_TRUSTED_PYTHON_RENDERER_SHA256"


def require_exact_code_grant(renderer_path: str | Path) -> str:
    source = Path(renderer_path).resolve(strict=True)
    if not source.is_file():
        raise ProductionContractError("trusted renderer source must be a regular file")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    decision = authorize_effect(
        TRUSTED_CODE_UNSANDBOXED, source_sha256=digest,
        operator_trusted_sha256=os.environ.get(GRANT_ENV),
    )
    if not decision.admitted:
        raise ProductionContractError(
            f"{decision.reason}: unsandboxed Python execution requires an independent "
            f"operator-owned {GRANT_ENV} matching the exact renderer file SHA256"
        )
    return digest


def admit_registered_effect(risk_class: str, context) -> None:
    if risk_class != TRUSTED_CODE_UNSANDBOXED:
        decision = authorize_effect(risk_class)
        if not decision.admitted:
            raise ProductionContractError(decision.reason)
        return
    spec_input = str(context.config.get("render_spec_input", "")).strip()
    spec_artifact = context.inputs.get(spec_input)
    if spec_artifact is None:
        raise ProductionContractError("code execution gate requires declared render_spec_input")
    try:
        spec = FrameRenderSpec.from_dict(
            json.loads(Path(str(spec_artifact["path"])).read_text(encoding="utf-8"))
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ProductionContractError("cannot resolve frame render spec for effect admission") from exc
    renderer = context.inputs.get(spec.renderer_input)
    if renderer is None:
        raise ProductionContractError("code execution gate requires declared renderer source")
    if renderer.get("kind") != "source_code":
        raise ProductionContractError("code execution gate requires a source_code artifact")
    digest = require_exact_code_grant(str(renderer["path"]))
    if renderer.get("sha256") != digest:
        raise ProductionContractError("code execution gate source bytes differ from registered SHA256")
