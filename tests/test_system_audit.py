from pathlib import Path

from social_media_studio.system_audit import run_system_audit

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_video_system_audit_passes_structural_contract():
    report = run_system_audit(ROOT)
    assert report["pass"] is True, report
    assert report["structural_status"] == "PASS"
    assert report["production_readiness"] == "PARTIAL"
    assert report["capability_gaps"]
    assert report["owner_inputs_required"] == []


def test_audit_distinguishes_caos_session_governance_from_runtime_independence():
    report = run_system_audit(ROOT)
    assert report["pass"] is True, report
    boundary = report["boundary"]
    assert boundary["caos_session_governance_required"] is True
    assert boundary["caos_runtime_dependency"] is False
    assert boundary["caos_source_mutation_allowed"] is False
    assert boundary["paid_provider_calls_made"] is False
    assert boundary["automatic_publication"] is False


def test_audit_checks_only_one_installed_video_cli():
    import tomllib

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["scripts"] == {"sms-studio": "social_media_studio.cli:main"}


def test_content_architecture_cases_are_audited_as_structure_not_craft():
    report = run_system_audit(ROOT)
    checks = {item["id"]: item for item in report["checks"]}
    arch = checks["typed_deliverables_and_architecture_negative_oracles"]
    assert arch["pass"], arch
    assert arch["detail"]["scenario_count"] >= 28
    assert arch["detail"]["verification"] == "STRUCTURE_ONLY_NOT_BUSINESS_OUTCOME"
    assert report["boundary"]["caos_source_mutation_allowed"] is False


def test_old_video_red_team_gate_is_not_universal_content_policy():
    report = run_system_audit(ROOT)
    checks = {c["id"]: c for c in report["checks"]}
    assert "hard_release_gates" not in checks
    fixture = checks["isolated_historical_video_fixture_release_policy"]
    assert fixture["pass"], fixture
    assert fixture["detail"]["scope"] == "HISTORICAL_VIDEO_FIXTURES_ONLY"
    assert fixture["detail"]["universal_content_gate"] is False
    from social_media_studio.domain.assurance import build_quality_plan
    tweet = build_quality_plan([{"id":"post","type":"SHORT_COPY"}])["plans"][0]
    assert "red-team" not in tweet["criteria"]
    assert "lookdev" not in tweet["criteria"]
    assert "full_playback" not in tweet["criteria"]
