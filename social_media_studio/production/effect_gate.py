"""Effect admission at real local process launch, not the planner's declaration.

The operator allowlist is read exclusively from the hosting process
environment, never from a task, asset or rights-clearance JSON.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil

from ..domain.effects import authorize_effect, TRUSTED_CODE_UNSANDBOXED
from .contracts import FrameRenderSpec, ProductionContractError


GRANT_ENV = "SMS_TRUSTED_PYTHON_RENDERER_SHA256"


def require_exact_code_grant(renderer_path: str | Path) -> str:
    source = Path(renderer_path).resolve(strict=True)
    if not source.is_file():
        raise ProductionContractError("trusted renderer source must be a regular file")
    hasher = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    digest = hasher.hexdigest()
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


def snapshot_exact_operator_granted_source(
    renderer_path: str | Path, destination_dir: str | Path, expected_sha256: str,
) -> Path:
    """Copy a granted exact version into a private one-attempt execution snapshot.

    The worker is pointed at this snapshot, never the mutable registered path.
    A changed source during the copy fails the post-copy digest comparison.
    This does not restrict arbitrary imports, filesystem access or networking
    from the *approved* code once it runs.
    """
    source = Path(renderer_path).resolve(strict=True)
    if require_exact_code_grant(source) != expected_sha256:
        raise ProductionContractError("registered renderer digest differs from granted source")
    destination = Path(destination_dir).resolve(strict=True) / "authorized-renderer.py"
    if destination.exists():
        raise ProductionContractError("trusted source snapshot must not overwrite an existing file")
    shutil.copyfile(source, destination)
    if require_exact_code_grant(destination) != expected_sha256:
        destination.unlink(missing_ok=True)
        raise ProductionContractError("trusted source changed while making execution snapshot")
    return destination
