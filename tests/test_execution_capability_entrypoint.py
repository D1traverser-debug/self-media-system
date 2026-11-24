import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_caos_entry_and_capability_profile_require_current_session_handshake():
    skill = (ROOT / "STUDIO_ENTRY.md").read_text(encoding="utf-8")
    profile = json.loads((ROOT / "social_media_studio/legacy/data/capabilities.json").read_text(encoding="utf-8"))

    assert "social_media_studio/legacy/data/capabilities.json" in skill
    assert "decision loop" in skill.lower()
    assert "execution loop" in skill.lower()
    assert "do not modify the caos repository" in skill.lower()
    assert "decision quality" in skill.lower()
    assert "independent acceptance" in skill.lower()
    assert profile["governance_binding"]["entrypoint"] == "STUDIO_ENTRY.md"
    assert profile["execution_readiness_contract"] == "2.0"
    assert profile["owner"] == "SOCIAL_MEDIA_STUDIO"
    assert profile["domain_id"] == "social_media"
    assert profile["governance_binding"]["system"] == "CAOS"
    assert profile["governance_binding"]["mode"] == "CHAT_GOVERNED_EXTERNAL"
    assert profile["governance_binding"]["runtime_dependency"] is False
    assert profile["governance_binding"]["source_mutation"] == "FORBIDDEN"
    assert all(item["side_channel_allowed"] is False for item in profile["capabilities"])


def test_studio_domain_import_does_not_load_old_controller_modules():
    import subprocess
    import sys

    code = (
        "import sys; import social_media_studio.adapters; "
        "blocked = {'social_media_studio.legacy.runtime', 'social_media_studio.legacy.orchestrator', "
        "'social_media_studio.legacy.studio_agents', 'social_media_studio.legacy.program_orchestration', "
        "'social_media_studio.legacy.storage'}; "
        "loaded = sorted(blocked.intersection(sys.modules)); "
        "assert not loaded, loaded"
    )
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True)


def test_legacy_direct_cli_cannot_create_new_owner_project_by_default(tmp_path):
    import os
    import subprocess
    import sys
    env = dict(os.environ)
    env.pop("SMS_LEGACY_FIXTURE_ROOT", None)
    env.pop("SMS_PROJECTS_DIR", None)
    result = subprocess.run([sys.executable, "-m", "social_media_studio.legacy.cli", "init", "unauthorized"],
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
    env.pop("SMS_PROJECTS_DIR", None)
    env["SMS_LEGACY_FIXTURE_ROOT"] = str(fixture)
    result = subprocess.run([sys.executable, "-m", "social_media_studio.legacy.cli", "init", "fixture-example"],
                            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert (fixture / "fixture-example" / "state.json").is_file()
    assert not (tmp_path / "projects").exists()
    env["SMS_LEGACY_FIXTURE_ROOT"] = str(Path(__file__).resolve().parents[1])
    denied = subprocess.run([sys.executable, "-m", "social_media_studio.legacy.cli", "init", "bad"],
                            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30)
    assert denied.returncode == 2


def test_legacy_readonly_techniques_preserved_without_project_store(tmp_path):
    import os
    import subprocess
    import sys
    env = dict(os.environ)
    env.pop("SMS_LEGACY_FIXTURE_ROOT", None)
    env.pop("SMS_PROJECTS_DIR", None)
    result = subprocess.run([sys.executable, "-m", "social_media_studio.legacy.cli", "techniques"],
                            cwd=tmp_path, env=env, capture_output=True,text=True,timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("[")
    assert not (tmp_path/"projects").exists()


def test_legacy_qa_frame_export_and_graphics_side_effects_require_isolated_paths(tmp_path):
    import os
    import subprocess
    import sys
    fixture=tmp_path/"fixture"
    fixture.mkdir()
    env=dict(os.environ)
    env["SMS_LEGACY_FIXTURE_ROOT"]=str(fixture)
    env.pop("SMS_PROJECTS_DIR",None)
    commands=[
        ["qa-media","nonexistent.mp4","--frames-dir",str(tmp_path/"outside")],
        ["render-graphic","nonexistent.json","--output",str(tmp_path/"outside.mp4")],
        ["render-graphic","nonexistent.json","--output",str(fixture/"inside.mp4"),
         "--graph",str(tmp_path/"external-graph.json")],
    ]
    for command in commands:
        result=subprocess.run([sys.executable,"-m","social_media_studio.legacy.cli",*command],
                              cwd=tmp_path,env=env,capture_output=True,text=True,timeout=30)
        assert result.returncode==2, (command,result.stdout,result.stderr)
        assert "writes must remain inside" in result.stderr
    assert not (tmp_path/"outside").exists()
    assert not (tmp_path/"outside.mp4").exists()
    assert not (tmp_path/"external-graph.json").exists()
