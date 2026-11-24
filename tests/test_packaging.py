from social_media_studio.legacy.storage import ProjectStore


def test_default_project_store_never_targets_installed_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SMS_PROJECTS_DIR", raising=False)
    store = ProjectStore()
    assert store.root == tmp_path / "projects"
