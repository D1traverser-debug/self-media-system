from importlib.metadata import version
import json
from pathlib import Path
import shutil

from video_growth_agent.system_audit import package_audit, repository_audit, run_system_audit

ROOT = Path(__file__).resolve().parents[1]


def test_package_harness_passes_current_runtime_contract():
    report = package_audit()
    assert report["pass"] is True, report
    expected = version("video-growth-agent")
    assert expected == "0.8.0"
    assert report["legacy_adapter_bundle_version"] == "0.7.0"
    assert report["agent_registry_version"] == report["execution_plan_version"]
    assert report["execution_plan_version"] == report["coordination_policy_version"]


def test_repository_harness_requires_canonical_video_entry_and_external_caos_boundary():
    report = repository_audit(ROOT)
    assert report["pass"] is True, report
    assert report["runtime_version"] == "1.0.0"
    assert report["legacy_domain_runtime_version"] == "0.8.0"
    assert report["legacy_adapter_bundle_version"] == "0.7.0"
    assert not (ROOT / "config").exists()
    assert not (ROOT / "continuity").exists()
    assert not (ROOT / ".uaos").exists()
    assert not (ROOT / "UAOS_SKILL.md").exists()
    assert not (ROOT / "tests/test_uaos_current.py").exists()
    assert (ROOT / "STUDIO_ENTRY.md").is_file()
    assert (ROOT / "CAOS_VIDEO_ENTRY.md").is_file()
    project_index = json.loads((ROOT / "projects/PROJECT_INDEX.json").read_text(encoding="utf-8"))
    assert project_index["default_project_id"] is None
    assert project_index["governance"]["entrypoint"] == "STUDIO_ENTRY.md"
    assert project_index["governance"]["source_mutation"] == "FORBIDDEN"
    assert project_index["projects"][0]["default_for_generic_domain_intent"] is False
    studio_manifest = json.loads((ROOT / "video_studio/data/studio_manifest.json").read_text(encoding="utf-8"))
    assert studio_manifest["studio_version"] == "1.0.0"
    assert studio_manifest["release_status"] == "REBUILD_IN_PROGRESS"
    assert studio_manifest["governance"]["caos_runtime_dependency"] is False
    assert studio_manifest["governance"]["caos_source_mutation"] == "FORBIDDEN"
    for field in (
        "stable_artifact_name_mapping",
        "task_completion_checks_declared_deliverable_outputs",
        "release_checks_all_required_deliverables",
        "checks_real_bytes_and_media_type",
        "rights_status_checked_for_each_required_deliverable",
        "qualitative_review_remains_separate",
    ):
        assert studio_manifest["capabilities"]["media_job_contract"][field] is True
    assert (ROOT / "video_studio/job_contract.py").is_file()
    domain_manifest = json.loads((ROOT / "video_growth_agent/data/domain_manifest.json").read_text(encoding="utf-8"))
    assert domain_manifest["runtime"]["entrypoint"] == "video_studio.engine.StudioEngine"
    assert domain_manifest["legacy_runtime"]["version"] == "0.8.0"
    assert domain_manifest["legacy_runtime"]["status"] == "COMPATIBILITY_ONLY__NOT_NEW_STUDIO_CONTROLLER"
    assert (ROOT / "video_growth_agent/data/domain_manifest.json").is_file()
    assert (ROOT / "video_growth_agent/data/capabilities.json").is_file()
    assert (ROOT / "projects/pilot-002/PROGRAM_STATE.json").is_file()
    for rel in (
        "video_growth_agent/media_graph.py",
        "video_growth_agent/editorial_planning.py",
        "video_growth_agent/plan_graph_bridge.py",
        "video_growth_agent/production_os.py",
        "video_growth_agent/continuity.py",
        "video_growth_agent/model_registry.py",
        "video_growth_agent/timeline.py",
        "video_growth_agent/editorial_interchange.py",
        "video_growth_agent/experiments.py",
        "video_growth_agent/business_objects.py",
        "video_growth_agent/business_metrics.py",
        "video_growth_agent/operator_view.py",
        "video_growth_agent/owner_behavior_admission.py",
        "video_growth_agent/ip_identity.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_repository_harness_fails_closed_when_canonical_media_runtime_is_missing(tmp_path):
    shadow = tmp_path / "repo"
    shutil.copytree(
        ROOT,
        shadow,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    missing = shadow / "video_growth_agent/editorial_planning.py"
    missing.unlink()
    report = repository_audit(shadow)
    assert report["pass"] is False
    assert "media_business_runtime_missing:video_growth_agent/editorial_planning.py" in report["failures"]



def test_repository_harness_rejects_restoring_the_business_program_as_generic_default(tmp_path):
    shadow = tmp_path / "repo"
    shutil.copytree(
        ROOT,
        shadow,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    index_path = shadow / "projects/PROJECT_INDEX.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["default_project_id"] = "ai-self-media-commercialization"
    index["projects"][0]["default_for_generic_domain_intent"] = True
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = repository_audit(shadow)
    assert "project_index_generic_default_forbidden" in report["failures"]
    assert "project_index_business_program_generic_default_forbidden" in report["failures"]


def test_repository_harness_fails_when_caos_source_mutation_is_allowed(tmp_path):
    shadow = tmp_path / "repo"
    shutil.copytree(
        ROOT,
        shadow,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    manifest_path = shadow / "video_studio/data/studio_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["governance"]["caos_source_mutation"] = "ALLOWED"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = repository_audit(shadow)
    assert "video_studio_caos_source_mutation_not_forbidden" in report["failures"]

def test_combined_system_audit_passes_repository_and_package():
    report = run_system_audit(ROOT)
    assert report["pass"] is True, report
    assert report["failures"] == []
