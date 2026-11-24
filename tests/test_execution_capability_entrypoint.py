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
