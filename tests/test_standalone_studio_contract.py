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
