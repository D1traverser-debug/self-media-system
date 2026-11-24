from social_media_studio.legacy.models import Approval, ArtifactRecord, AssetRecord, ProjectState


def test_state_serialization_roundtrip():
    s = ProjectState("x")
    s.approvals["INTAKE"] = {"showrunner": Approval("showrunner", "PASS", findings=("a",))}
    s.artifacts["brief"] = ArtifactRecord("brief", "file://brief", "INTAKE", digest="abc")
    s.assets["asset"] = AssetRecord("asset", "file://a", "image", "OWNED")
    clone = ProjectState.from_dict(s.to_dict())
    assert clone.to_dict() == s.to_dict()


def test_packaged_runtime_resources_are_single_repository_authority():
    import json
    from pathlib import Path
    from social_media_studio.legacy.resources import data_path

    root = Path(__file__).resolve().parents[1]
    assert not (root / "config").exists()
    for name in ("roles.json", "workflow.json", "techniques.json", "quality-rubric.json"):
        payload = json.loads(data_path(name).read_text(encoding="utf-8"))
        assert isinstance(payload, dict) and payload
    assert data_path("team.md").read_text(encoding="utf-8") == (
        root / "skills/social-media-studio/references/team.md"
    ).read_text(encoding="utf-8")
    roles = json.loads(data_path("roles.json").read_text(encoding="utf-8"))
    assert roles["canonical_prompt_source"] == "social_media_studio/legacy/data/team.md"
    assert roles["documentation_projection"] == "skills/social-media-studio/references/team.md"
    from social_media_studio.legacy.roles import RoleRegistry
    registry = RoleRegistry()
    # Role sections are a subset: generic review protocols are continuous
    # methods, not permanent roles or mandatory workflow nodes.
    expected_roles = {entry["prompt_section"] for entry in roles["roles"].values()}
    assert expected_roles <= set(registry.sections)
    assert "Blind review protocol" in registry.sections
    for role_id in roles["roles"]:
        prompt = registry.get(role_id).prompt
        assert prompt and "Blind review protocol" not in prompt
    assert "not permanently instantiated agents" in data_path("team.md").read_text(encoding="utf-8")
