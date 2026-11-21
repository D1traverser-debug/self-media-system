import importlib.util
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "x-article-when-everyone-has-a-bag"
SCRIPT = REPO_ROOT / "projects" / PROJECT_ID / "bootstrap.py"
spec = importlib.util.spec_from_file_location("meme_x_article_bootstrap", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

def test_meme_x_article_bootstraps_in_standalone_video_studio(tmp_path):
    branch = os.environ.get("GITHUB_REF_NAME")
    commit_sha = os.environ.get("GITHUB_SHA")
    result = module.bootstrap(tmp_path / "studio", branch, commit_sha)

    assert result["audit"]["pass"] is True, result["audit"]
    assert result["audit"]["task_count"] == 7
    status = result["status"]
    assert status["project"]["project_id"] == PROJECT_ID
    assert status["open_failures"] == 0

    task_status = {task["task_id"]: task["status"] for task in module.StudioEngine(tmp_path / "studio").list_tasks(PROJECT_ID)}
    assert task_status["recover_source_state"] == "COMPLETED"
    assert task_status["integrate_keyword"] == "COMPLETED"
    if branch and commit_sha and len(commit_sha) == 40:
        assert task_status["sync_assets_to_branch"] == "COMPLETED"
        assert {"independent_editor_review", "trench_reader_review", "x_native_preview"} <= set(status["ready_tasks"])
    else:
        assert task_status["sync_assets_to_branch"] == "READY"
