"""Explicit effect-risk semantics; independent of task JSON and provider code.

This is an operator-controlled exact-source allowlist, not an OS sandbox,
cryptographic signer, or authority to publish or release an artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
import hmac
import re

LOCAL_DETERMINISTIC = "LOCAL_DETERMINISTIC"
TRUSTED_CODE_UNSANDBOXED = "TRUSTED_CODE_UNSANDBOXED"
RISK_CLASSES = frozenset({LOCAL_DETERMINISTIC, TRUSTED_CODE_UNSANDBOXED})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class EffectDecision:
    admitted: bool
    risk_class: str
    reason: str


def authorize_effect(
    risk_class: str, *, source_sha256: str | None = None,
    operator_trusted_sha256: str | None = None,
) -> EffectDecision:
    if risk_class not in RISK_CLASSES:
        return EffectDecision(False, str(risk_class), "UNKNOWN_EFFECT_RISK_DENIED")
    if risk_class == LOCAL_DETERMINISTIC:
        return EffectDecision(True, risk_class, "REGISTERED_LOCAL_OPERATION")
    if (not isinstance(source_sha256, str) or not _SHA256.fullmatch(source_sha256)
            or not isinstance(operator_trusted_sha256, str)
            or not _SHA256.fullmatch(operator_trusted_sha256)):
        return EffectDecision(False, risk_class, "OPERATOR_EXACT_CODE_GRANT_MISSING")
    if not hmac.compare_digest(source_sha256, operator_trusted_sha256):
        return EffectDecision(False, risk_class, "OPERATOR_CODE_GRANT_DIGEST_MISMATCH")
    return EffectDecision(True, risk_class, "OPERATOR_EXACT_SOURCE_GRANT_PRESENT_NOT_SANDBOXED")
