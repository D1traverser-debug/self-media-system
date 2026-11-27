"""Adversarial effect admissions: task truthiness cannot authorize unsandboxed code."""
from __future__ import annotations

import hashlib

import pytest

from social_media_studio.domain.effects import (
    LOCAL_DETERMINISTIC, TRUSTED_CODE_UNSANDBOXED, authorize_effect,
)
from social_media_studio.production.effect_gate import require_exact_code_grant
from social_media_studio.production.contracts import ProductionContractError
from social_media_studio.production.registry import PRODUCTION_EXECUTORS, ProductionExecutorRegistry


def test_registered_operations_declare_one_effect_risk():
    operations = PRODUCTION_EXECUTORS.operations()
    assert len(operations) == 6
    assert PRODUCTION_EXECUTORS.effect_risk("python_frame_render") == TRUSTED_CODE_UNSANDBOXED
    assert all(PRODUCTION_EXECUTORS.effect_risk(name) == LOCAL_DETERMINISTIC
               for name in operations if name != "python_frame_render")


def test_unknown_risk_and_implicit_registration_fail_closed():
    r = ProductionExecutorRegistry()
    with pytest.raises(TypeError):
        r.register("unverified", lambda context: None)
    with pytest.raises(ValueError, match="known effect risk"):
        r.register("unverified", lambda context: None, effect_risk="TRUST_ME")
    assert not r.supports("unverified")
    assert not authorize_effect("UNKNOWN_RISK").admitted


def test_task_boolean_or_fake_self_declared_trust_cannot_grant_code():
    value = "0" * 64
    assert not authorize_effect(TRUSTED_CODE_UNSANDBOXED, source_sha256=value).admitted
    assert not authorize_effect(
        TRUSTED_CODE_UNSANDBOXED, source_sha256=value,
        operator_trusted_sha256="false",
    ).admitted


def test_missing_or_wrong_operator_digest_blocks_before_python_execution(tmp_path, monkeypatch):
    code = tmp_path / "renderer.py"
    code.write_text("raise AssertionError('must never execute')", encoding="utf-8")
    monkeypatch.delenv("SMS_TRUSTED_PYTHON_RENDERER_SHA256", raising=False)
    with pytest.raises(ProductionContractError, match="OPERATOR_EXACT_CODE_GRANT_MISSING"):
        require_exact_code_grant(code)
    monkeypatch.setenv("SMS_TRUSTED_PYTHON_RENDERER_SHA256", "a" * 64)
    with pytest.raises(ProductionContractError, match="OPERATOR_CODE_GRANT_DIGEST_MISMATCH"):
        require_exact_code_grant(code)


def test_exact_operator_digest_admits_only_original_bytes(tmp_path, monkeypatch):
    code = tmp_path / "renderer.py"
    code.write_text("def render_frame(): pass", encoding="utf-8")
    digest = hashlib.sha256(code.read_bytes()).hexdigest()
    monkeypatch.setenv("SMS_TRUSTED_PYTHON_RENDERER_SHA256", digest)
    assert require_exact_code_grant(code) == digest
    code.write_text("def render_frame(): return 42", encoding="utf-8")
    with pytest.raises(ProductionContractError, match="DIGEST_MISMATCH"):
        require_exact_code_grant(code)


def test_local_registered_operations_do_not_need_arbitrary_code_grant():
    assert authorize_effect(LOCAL_DETERMINISTIC).admitted is True


def test_discovery_discloses_unsafe_effect_without_claiming_operator_approval():
    from social_media_studio.scope import capability_lookup
    route = capability_lookup(demand_id="programmatic_motion_graphics")["groups"][0]["executor_routes"]
    risks = route["production_effect_risks"]
    assert risks == [{
        "operation": "python_frame_render", "risk_class": TRUSTED_CODE_UNSANDBOXED,
        "independent_operator_grant_required": True, "current_operator_grant_verified": False,
    }]
    safe = capability_lookup(demand_id="original_audio_preservation")["groups"][0]["executor_routes"]
    assert safe["production_effect_risks"] == [{
        "operation": "ffmpeg_video_audio_copy", "risk_class": LOCAL_DETERMINISTIC,
        "independent_operator_grant_required": False, "current_operator_grant_verified": False,
    }]
