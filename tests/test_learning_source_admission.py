from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "skills/social-media-studio/references/self-learning.md"


def test_ad_hoc_session_material_is_not_implicitly_a_learning_source():
    text = POLICY.read_text(encoding="utf-8")
    assert "Seeing content during a session does **not** make it a learning source." in text
    assert "outside the durable learning boundary by default" in text
    assert "The declared work packet is the learning context boundary." in text
    assert "Ambient conversation" in text


def test_external_learning_requires_explicit_import_and_authorization():
    text = POLICY.read_text(encoding="utf-8")
    assert "explicitly imported as an external learning source" in text
    assert "affirmative learning authorization" in text
    assert "If provenance or authorization cannot be proved, reject the candidate" in text


def test_no_learn_exclusion_must_not_be_implemented_as_a_content_denylist():
    text = POLICY.read_text(encoding="utf-8")
    assert "exclude it before durable serialization" in text
    assert "Do not create a topic/title/URL/fingerprint denylist" in text
    assert "that would itself persist a trace" in text



def test_explicit_owner_authorized_cross_chat_import_is_a_scoped_exception():
    text = POLICY.read_text(encoding="utf-8")
    assert "scoped retrospective cross-chat source explicitly authorized by the owner" in text
    assert "relevant self-media history only" in text
    assert "Ambient conversation, unrelated chats" in text
    assert "summary-level retrieval" in text
    assert "Never commit raw private conversation" in text


def test_direct_session_learning_uses_private_episode_source_without_dummy_project():
    text = POLICY.read_text(encoding="utf-8")
    assert "Direct-session work may not have a Studio project." in text
    assert "private Library experience casebook" in text
    assert "rather than creating a dummy project" in text


def test_owner_preference_is_not_subject_to_method_promotion_threshold():
    text = POLICY.read_text(encoding="utf-8")
    assert "An explicit owner preference is authoritative within its scope" in text
    assert "does not need two replays" in text
    assert "A direct owner correction is not the same thing as a method validation." in text


def test_private_owner_profile_and_casebook_are_discovered_from_skill_entry():
    skill_text = (ROOT / "skills/social-media-studio/SKILL.md").read_text(encoding="utf-8")
    entry_text = (ROOT / "STUDIO_ENTRY.md").read_text(encoding="utf-8")
    for token in ("OWNER_PREFERENCE_PROFILE.md", "CROSS_CHAT_EXPERIENCE_CASEBOOK.md",
                  "PROCESS_QUALITY_BASELINE.md"):
        assert token in skill_text
        assert token in entry_text
    assert "current owner instructions" in skill_text.lower()
    assert "do not import unrelated conversations" in skill_text.lower()


def test_process_quality_separates_owner_scope_changes_from_preventable_assistant_failures():
    skill_text = (ROOT / "skills/social-media-studio/SKILL.md").read_text(encoding="utf-8")
    assert "PROCESS_QUALITY_BASELINE.md" in skill_text
    assert "Do not turn every rejected draft into a global rule." in skill_text


def test_candidate_methods_are_loaded_for_scoped_use_not_silently_skipped():
    skill_text = (ROOT / "skills/social-media-studio/SKILL.md").read_text(encoding="utf-8")
    assert "Candidate status is not a reason to skip a relevant professional reference." in skill_text
    assert "sms-studio knowledge --id ID --include-nonactive" in skill_text
    assert "bounded method hypothesis" in skill_text
    assert "Preserve its candidate status" in skill_text
    for demand in ("short_form_copy", "platform_title", "cover_copy", "cover_design", "long_form_editorial"):
        assert "`" + demand + "`" in skill_text


def test_exact_demand_profiles_point_to_the_expected_editorial_and_packaging_sources():
    import json
    profile = json.loads((ROOT / "social_media_studio/legacy/data/capabilities.json").read_text(encoding="utf-8"))
    groups = {g["id"]: g for g in profile["professional_capability_groups"]}
    assert "short-form-social-copy" in groups["editorial_writing"]["demand_profiles"]["short_form_copy"]["knowledge_refs"]
    assert "platform-packaging" in groups["platform_packaging"]["demand_profiles"]["platform_title"]["knowledge_refs"]
    assert "platform-packaging" in groups["platform_packaging"]["demand_profiles"]["cover_copy"]["knowledge_refs"]
    assert "visual-development" in groups["visual_design"]["knowledge_refs"]
    assert "platform-packaging" in groups["visual_design"]["demand_profiles"]["cover_design"]["knowledge_refs"]


def test_self_learning_protocol_has_unique_ordered_sections():
    import re
    text = POLICY.read_text(encoding="utf-8")
    numbers = [int(x) for x in re.findall(r"^## (\\d+)\\.", text, flags=re.MULTILINE)]
    assert numbers == list(range(1, len(numbers) + 1))
