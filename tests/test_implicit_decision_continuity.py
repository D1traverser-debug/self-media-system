from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "STUDIO_ENTRY.md"
SKILL = ROOT / "skills/social-media-studio/SKILL.md"
ENGINE = ROOT / "social_media_studio/engine.py"


def test_dependent_stage_can_lock_only_the_required_upstream_decision_atoms():
    for path in (ENTRY, SKILL):
        text = path.read_text(encoding="utf-8")
        assert "IMPLICITLY_LOCKED_FOR_DEPENDENT_STAGE" in text
        assert "only the decision atoms" in text
        assert "exact source message, artifact/version, dependency" in text
        assert "multiple live candidates remain" in text


def test_implicit_continuity_is_not_blanket_acceptance_or_publication_authority():
    for path in (ENTRY, SKILL):
        text = path.read_text(encoding="utf-8")
        assert "not blanket approval" in text
        assert "not final artifact acceptance" in text
        assert "not publication authorization" in text
        assert "Keep decision state separate from production, verification and business-outcome state." in text


def test_durable_engine_decisions_remain_project_scoped_not_global_chat_approvals():
    text = ENGINE.read_text(encoding="utf-8")
    assert "def record_decision(self, project_id: str" in text
    assert "INSERT INTO decisions(project_id,decision_id" in text
