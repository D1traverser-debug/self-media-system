"""Structural security checks must follow the implementation, not a stale file path."""
from pathlib import Path
from social_media_studio.system_audit import run_system_audit

ROOT = Path(__file__).resolve().parents[1]


def test_high_assurance_source_audit_follows_extracted_release_service():
    report = run_system_audit(ROOT)
    check = next(x for x in report["checks"] if
                 x["id"] == "high_assurance_review_execution_default_fail_closed")
    assert check["pass"], check
    assert check["detail"]["execution_verifier_integrated"] is True
    assert check["detail"]["release_receipt_semantics_correct"] is True
