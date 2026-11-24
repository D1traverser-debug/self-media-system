"""Ported visual-method provenance and task scope from superseded PR #6."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def test_visual_method_is_discoverable_but_not_universal_gate():
    cat = json.loads((ROOT / "social_media_studio/data/knowledge_catalog.json").read_text(encoding="utf-8"))
    entries = [x for x in cat["entries"] if x["id"] == "visual-development"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["status"] == "CANDIDATE_REQUIRES_REVALIDATION"
    ref = ROOT / entry["ref"]
    assert ref.is_file()
    source = ref.read_text(encoding="utf-8")
    assert "standalone caption" in source
    assert "4–8 second prototypes" in source
    assert "historical research notes" in source
    skill = (ROOT / "skills/social-media-studio/SKILL.md").read_text(encoding="utf-8")
    assert "references/visual-development.md" in skill
    assert "does not impose a shot probe on standalone images" in skill
