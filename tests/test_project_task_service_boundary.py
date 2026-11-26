from __future__ import annotations

from pathlib import Path

from social_media_studio.application.project_tasks import ProjectTaskService
from social_media_studio.engine import StudioEngine


def test_project_task_service_preserves_engine_api_and_single_ledger(tmp_path):
    engine = StudioEngine(tmp_path)
    assert isinstance(engine._project_task_service, ProjectTaskService)
    assert engine._project_task_service.engine is engine

    brief = {
        "goal": "Create a fact-checked X Article.",
        "audience": "Technology readers",
        "deliverables": ["article"],
    }
    created = engine.create_project("article-project", "Article project", brief)
    assert created["brief"] == brief
    assert engine.project("article-project")["project_id"] == "article-project"

    tasks = engine.add_tasks("article-project", [
        {
            "task_id": "research",
            "title": "Research sources",
            "kind": "research",
            "executor": "agent",
            "depends_on": [],
            "inputs": [],
            "outputs": ["source-pack"],
            "acceptance": {"observable": "A source pack is registered."},
            "requirements": {},
        },
        {
            "task_id": "write",
            "title": "Write article",
            "kind": "production",
            "executor": "agent",
            "depends_on": ["research"],
            "inputs": ["source-pack"],
            "outputs": ["article"],
            "acceptance": {"observable": "A complete article is registered."},
            "requirements": {},
        },
    ])
    assert {task["task_id"] for task in tasks} == {"research", "write"}
    assert engine.list_tasks("article-project")[0]["task_id"] == "research"

    revised_task = engine.revise_task(
        "article-project", "research", {"title": "Research and verify sources"},
        reason="Clarify the research task contract",
    )
    assert revised_task["task"]["title"] == "Research and verify sources"
    assert "write" in revised_task["invalidated_descendants"]

    revised_brief = {**brief, "goal": "Create a fact-checked, platform-native X Article."}
    result = engine.revise_brief(
        "article-project", revised_brief, reason="Owner clarified the outcome",
    )
    assert result["project"]["brief"] == revised_brief
    assert set(result["invalidated_tasks"]) == {"research", "write"}
    assert len(engine.brief_history("article-project")) == 2
    assert engine.audit("article-project")["pass"] is True

    databases = list(Path(tmp_path).rglob("studio.sqlite3"))
    assert databases == [Path(tmp_path) / "projects" / "article-project" / "studio.sqlite3"]


def test_project_task_service_does_not_own_a_second_scheduler_or_workspace(tmp_path):
    engine = StudioEngine(tmp_path)
    service = engine._project_task_service
    assert service.engine is engine
    assert not hasattr(service, "root")
    assert not hasattr(service, "database")
    assert not hasattr(service, "scheduler")
    assert not hasattr(service, "worker_pool")
