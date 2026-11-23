import importlib.util
import json
import re
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "x-article-when-everyone-has-a-bag"
SCRIPT = REPO_ROOT / "projects" / PROJECT_ID / "bootstrap.py"
spec = importlib.util.spec_from_file_location("meme_x_article_bootstrap", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_meme_x_article_v36_bootstraps_in_standalone_video_studio(tmp_path):
    branch = os.environ.get("GITHUB_REF_NAME")
    commit_sha = os.environ.get("GITHUB_SHA")
    result = module.bootstrap(tmp_path / "studio", branch, commit_sha)

    assert result["audit"]["pass"] is True, result["audit"]
    assert result["audit"]["task_count"] == 13
    status = result["status"]
    assert status["project"]["project_id"] == PROJECT_ID
    assert status["open_failures"] == 0

    tasks = module.StudioEngine(tmp_path / "studio").list_tasks(PROJECT_ID)
    task_status = {task["task_id"]: task["status"] for task in tasks}

    completed = {
        "recover_project_state",
        "verify_sources_and_claims",
        "diagnose_editorial_voice",
        "revise_manuscripts",
        "refresh_distribution_and_visual_assets",
        "build_delivery_package",
        "sync_candidate_branch",
    }
    assert all(task_status[task_id] == "COMPLETED" for task_id in completed), task_status

    if branch and commit_sha and len(commit_sha) == 40:
        ready = set(status["ready_tasks"])
        assert {
            "independent_editor_review",
            "target_reader_cold_read",
            "x_native_preview",
            "rights_review",
        } <= ready
        assert "owner_release_authorization" not in ready
        assert "release_acceptance" not in ready


def test_meme_x_article_v36_editorial_contract_is_coherent():
    project_dir = REPO_ROOT / "projects" / PROJECT_ID
    brief = json.loads((project_dir / "OUTCOME_BRIEF.json").read_text(encoding="utf-8"))
    manifest = json.loads((project_dir / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    task_graph = json.loads((project_dir / "TASK_GRAPH.json").read_text(encoding="utf-8"))
    assert manifest["current_candidate"] == "v3.6"
    assert brief["format"]["article_sections"] == 3
    assert len(task_graph) == 13
    assert module.V36_DIR.name == "v3.6"

    texts = {}
    urls = {}
    for lng in ("EN", "ZH"):
        name = f"Meme_X_Article_{lng}_v3_6.md"
        content = (module.V36_DIR / name).read_text(encoding="utf-8")
        texts[lng] = content
        urls[lng] = re.findall(r"https?://[^\s)]+", content)
        assert content.count("Bigfoot") == 1
        headings = re.findall(r"(?m)^## (.+)$", content)
        assert len(headings) == 3
        assert all(not re.match(r"^\d", h) for h in headings)
    assert urls["EN"] == urls["ZH"]
    assert len(urls["EN"]) == 5

    asset_manifest = json.loads((module.V36_DIR / "Meme_X_v3_6_Asset_Manifest.json").read_text(encoding="utf-8"))
    import hashlib
    for name, record in asset_manifest["files"].items():
        path = module.V36_DIR / name
        if path.suffix not in {".md", ".json"}:
            continue
        assert path.is_file(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], name
