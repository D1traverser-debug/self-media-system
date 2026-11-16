from __future__ import annotations

import json
from pathlib import Path
import tomllib

from video_studio.engine import StudioEngine

ROOT = Path(__file__).resolve().parents[1]


def test_standalone_studio_is_the_new_entry_and_has_no_parent_runtime_dependency():
    manifest = json.loads((ROOT / "video_studio/data/studio_manifest.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    skill = (ROOT / "skills/video-growth-agent/SKILL.md").read_text(encoding="utf-8")
    entry = (ROOT / "STUDIO_ENTRY.md").read_text(encoding="utf-8")
    source = (ROOT / "video_studio/engine.py").read_text(encoding="utf-8")

    assert manifest["governance"]["system"] == "VIDEO_STUDIO_NATIVE"
    assert manifest["governance"]["mode"] == "STANDALONE"
    assert manifest["governance"]["caos_runtime_dependency"] is False
    assert manifest["governance"]["caos_api_dependency"] is False
    assert manifest["governance"]["caos_skill_dependency"] is False
    assert manifest["execution"]["fixed_stage_machine"] is False
    assert set(manifest["business_workstreams"]) == {"MEDIA_GROWTH", "ORIGINAL_DIGITAL_IP", "COMMERCIALIZATION", "PRODUCTION_SYSTEM"}
    assert manifest["domain_adapter_policy"]["legacy_fixed_stage_orchestrator"] == "NOT_A_CONTROLLER"
    assert pyproject["project"]["scripts"]["vga-studio"] == "video_studio.cli:main"
    assert "STUDIO_ENTRY.md" in skill and "STUDIO_ENTRY.md" in entry
    assert "CAOS_VIDEO_ENTRY.md" not in skill
    assert "import caos" not in source.lower()
    assert "from caos" not in source.lower()


def test_example_graphs_are_valid_dynamic_dags(tmp_path):
    engine = StudioEngine(tmp_path)
    for project_id, brief_name, tasks_name in (
        ("explainer", "technology-explainer.brief.json", "technology-explainer.tasks.json"),
        ("satire", "news-fictional-media.brief.json", "news-fictional-media.tasks.json"),
        ("media-program", "ai-self-media-commercialization.brief.json", "ai-self-media-commercialization.tasks.json"),
    ):
        brief = json.loads((ROOT / "examples" / brief_name).read_text(encoding="utf-8"))
        tasks = json.loads((ROOT / "examples" / tasks_name).read_text(encoding="utf-8"))
        engine.create_project(project_id, project_id, brief)
        engine.add_tasks(project_id, tasks)
        assert engine.audit(project_id)["pass"] is True
        assert engine.status(project_id)["task_counts"]["READY"] >= 1


def test_engine_uses_no_external_runtime_dependency():
    source = (ROOT / "video_studio/engine.py").read_text(encoding="utf-8")
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source.lower()
    assert "sqlite3" in source
    assert "video_growth_agent" not in source

def test_legacy_engine_import_is_only_a_compatibility_shim():
    from video_growth_agent.studio_engine import StudioEngine as LegacyImport
    from video_studio.engine import StudioEngine as CanonicalEngine

    assert LegacyImport is CanonicalEngine


def test_all_canonical_runtime_modules_are_independent_of_legacy_namespace():
    for module in ("__init__.py", "__main__.py", "cli.py", "media.py"):
        source = (ROOT / "video_studio" / module).read_text(encoding="utf-8")
        assert "video_growth_agent" not in source
        assert "from caos" not in source.lower()
        assert "import caos" not in source.lower()


def test_example_briefs_preserve_nonnegotiable_video_release_gates():
    root = ROOT / "examples"
    explainer = json.loads((root / "technology-explainer.brief.json").read_text(encoding="utf-8"))
    satire = json.loads((root / "news-fictional-media.brief.json").read_text(encoding="utf-8"))
    program = json.loads((root / "ai-self-media-commercialization.brief.json").read_text(encoding="utf-8"))

    policy = explainer["release_policy"]
    assert policy["require_rights"] is True
    assert policy["require_rights_evidence"] is True
    assert policy["require_technical_qa"] is True
    assert "red-team" in policy["required_review_rubrics"]
    assert policy["review_contracts"]["red-team"]["min_findings"] >= 3
    assert policy["review_contracts"]["human-cold-read"]["execution_mode"] == "INDEPENDENT_COLD_READ"
    assert satire["release_policy"]["required_asset_names"] == ["source-video"]
    assert satire["release_policy"]["no_auto_publish"] is True
    assert program["program_context"]["ip_identity_authority"] == "IPOS"
    assert program["program_context"]["caos_runtime_dependency"] is False


def test_program_example_keeps_independent_workstreams_parallel_and_ipos_fail_closed(tmp_path):
    engine = StudioEngine(tmp_path)
    brief_path = ROOT / "examples" / "ai-self-media-commercialization.brief.json"
    tasks_path = ROOT / "examples" / "ai-self-media-commercialization.tasks.json"
    project_brief = json.loads(brief_path.read_text(encoding="utf-8"))
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    engine.create_project("program", "Integrated media program", project_brief)
    engine.add_tasks("program", tasks)
    status = engine.status("program")
    task_map = {item["task_id"]: item for item in engine.list_tasks("program")}
    assert task_map["growth-baseline-and-topic-hypotheses"]["status"] == "READY"
    assert task_map["commercial-advertiser-map"]["status"] == "READY"
    assert task_map["ipos-video-identity-bundle-import"]["status"] == "WAITING_INPUT"
    assert task_map["jensen-source-media-inspection"]["status"] == "WAITING_INPUT"
    assert task_map["commercial-offer-native-integration"]["status"] == "PENDING"
    assert status["task_counts"]["READY"] >= 4
    assert engine.audit("program")["pass"] is True
