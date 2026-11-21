import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_video_entry_and_capability_profile_require_current_session_handshake():
    entry = (ROOT / "STUDIO_ENTRY.md").read_text(encoding="utf-8").lower()
    profile = json.loads((ROOT / "video_growth_agent/data/capabilities.json").read_text(encoding="utf-8"))

    assert "canonical entry" in entry
    assert "caos-governed" in entry
    assert "decision loop" in entry
    assert "execution loop" in entry
    assert "independent acceptance" in entry
    assert "do not modify the caos repository" in entry
    assert "runtime/api dependency" in entry
    assert profile["execution_readiness_contract"] == "2.0"
    assert profile["owner"] == "VIDEO_GROWTH_AGENT"
    assert profile["domain_id"] == "video"
    assert profile["governance_binding"]["system"] == "CAOS"
    assert profile["governance_binding"]["mode"] == "CHAT_GOVERNED_EXTERNAL"
    assert profile["governance_binding"]["runtime_dependency"] is False
    assert profile["governance_binding"]["source_mutation"] == "FORBIDDEN"
    assert all(item["side_channel_allowed"] is False for item in profile["capabilities"])
