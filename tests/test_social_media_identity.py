"""System-wide branding and package identity invariants."""
from pathlib import Path
import json
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_single_social_media_studio_identity():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["name"] == "social-media-studio"
    assert config["project"]["scripts"] == {"sms-studio": "social_media_studio.cli:main"}
    assert config["project"]["version"] == "2.0.0"
    from social_media_studio.cli import build_parser
    assert build_parser().prog == "sms-studio"
    manifest = json.loads((ROOT / "social_media_studio/data/studio_manifest.json").read_text(encoding="utf-8"))
    assert manifest["product_name_zh"] == "自媒体系统"
    assert manifest["owner"] == "SOCIAL_MEDIA_STUDIO"
    assert manifest["governance"]["system"] == "CAOS"
    assert manifest["domain_adapter_policy"]["specialist_domain_modules"].startswith("SOCIAL_MEDIA_")
    assert (ROOT / "social_media_studio/legacy/ip_identity.py").is_file()
    assert not (ROOT / ("video" + "_studio")).exists()
    assert not (ROOT / ("video" + "_growth_agent")).exists()


def test_no_retired_product_identifiers_in_active_files():
    banned = (
        "video" + "_studio", "video" + "_growth_agent",
        "vga" + "-studio", "VGA" + "_STUDIO",
        "VIDEO" + "_GROWTH_AGENT", "Video" + " Growth Agent",
        "Universal" + " Content Studio",
    )
    included = [ROOT / x for x in (
        "pyproject.toml", "README.md", "STUDIO_ENTRY.md", ".github/workflows/ci.yml",
        "docs/standalone_social_media_studio.md", "docs/SOCIAL_MEDIA_STUDIO_ARCHITECTURE_V2.md",
    )]
    for folder in ("social_media_studio", "skills/social-media-studio"):
        included += [p for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix in (".py", ".json", ".md", ".yml")]
    violations = [(str(p.relative_to(ROOT)), token)
                  for p in included for token in banned
                  if token in p.read_text(encoding="utf-8")]
    assert not violations, violations


def test_startup_contract_uses_self_media_as_product_scope():
    for rel in ("README.md", "STUDIO_ENTRY.md", "skills/social-media-studio/SKILL.md"):
        content = (ROOT / rel).read_text(encoding="utf-8")
        for stale in ("Video-owned", "Video-domain requirements", "Video runtime", "Video work", "Video conversations"):
            assert stale not in content, (rel, stale)


def test_repository_audit_detects_retired_runtime_prefix(tmp_path):
    from social_media_studio.system_audit import _brand_violations
    assert _brand_violations(ROOT) == []
    folder = tmp_path / "social_media_studio"
    folder.mkdir()
    (folder / "rogue.py").write_text("identifier = " + repr("vga" + "-old"), encoding="utf-8")
    assert any("rogue.py" in finding for finding in _brand_violations(tmp_path))
