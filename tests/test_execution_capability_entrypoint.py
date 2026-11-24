import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_caos_entry_and_capability_profile_require_current_session_handshake():
    skill = (ROOT / "STUDIO_ENTRY.md").read_text(encoding="utf-8")
    profile = json.loads((ROOT / "video_growth_agent/data/capabilities.json").read_text(encoding="utf-8"))

    assert "video_growth_agent/data/capabilities.json" in skill
    assert "decision loop" in skill.lower()
    assert "execution loop" in skill.lower()
    assert "do not modify the caos repository" in skill.lower()
    assert "decision quality" in skill.lower()
    assert "independent acceptance" in skill.lower()
    assert profile["governance_binding"]["entrypoint"] == "STUDIO_ENTRY.md"
    assert profile["execution_readiness_contract"] == "2.0"
    assert profile["owner"] == "VIDEO_GROWTH_AGENT"
    assert profile["domain_id"] == "video"
    assert profile["governance_binding"]["system"] == "CAOS"
    assert profile["governance_binding"]["mode"] == "CHAT_GOVERNED_EXTERNAL"
    assert profile["governance_binding"]["runtime_dependency"] is False
    assert profile["governance_binding"]["source_mutation"] == "FORBIDDEN"
    assert all(item["side_channel_allowed"] is False for item in profile["capabilities"])


def test_studio_domain_import_does_not_load_old_controller_modules():
    import subprocess
    import sys

    code = (
        "import sys; import video_studio.adapters; "
        "blocked = {'video_growth_agent.runtime', 'video_growth_agent.orchestrator', "
        "'video_growth_agent.studio_agents', 'video_growth_agent.program_orchestration', "
        "'video_growth_agent.storage'}; "
        "loaded = sorted(blocked.intersection(sys.modules)); "
        "assert not loaded, loaded"
    )
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True)


def test_legacy_direct_cli_cannot_create_new_owner_project_by_default(tmp_path):
    import os
    import subprocess
    import sys
    env = dict(os.environ)
    env.pop("VGA_LEGACY_FIXTURE_ROOT", None)
    env.pop("VGA_PROJECTS_DIR", None)
    result = subprocess.run([sys.executable, "-m", "video_growth_agent.cli", "init", "unauthorized"],
                            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 2
    assert "Legacy Video 0.8 control is retired" in result.stderr
    assert not (tmp_path / "projects").exists()


def test_legacy_cli_only_writes_under_explicit_separate_fixture_root(tmp_path):
    import os
    import subprocess
    import sys
    fixture = tmp_path / "legacy-fixture"
    fixture.mkdir()
    env = dict(os.environ)
    env.pop("VGA_PROJECTS_DIR", None)
    env["VGA_LEGACY_FIXTURE_ROOT"] = str(fixture)
    result = subprocess.run([sys.executable, "-m", "video_growth_agent.cli", "init", "fixture-example"],
                            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert (fixture / "fixture-example" / "state.json").is_file()
    assert not (tmp_path / "projects").exists()
    env["VGA_LEGACY_FIXTURE_ROOT"] = str(Path(__file__).resolve().parents[1])
    denied = subprocess.run([sys.executable, "-m", "video_growth_agent.cli", "init", "bad"],
                            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30)
    assert denied.returncode == 2
