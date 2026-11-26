from __future__ import annotations

from social_media_studio.application.project_tasks import ProjectTaskService
from social_media_studio.engine import StudioEngine


class NarrowInfrastructure:
    """Expose only workspace, persistence, event and review-file primitives."""

    def __init__(self, engine: StudioEngine):
        self._project_dir = engine._project_dir
        self._connect = engine._connect
        self._schema = engine._schema
        self._event = engine._event
        self._cleanup_review_stage = engine._cleanup_review_stage


def test_project_task_service_runs_without_calling_back_into_engine_application_api(tmp_path):
    engine = StudioEngine(tmp_path / "workspace")
    infrastructure = NarrowInfrastructure(engine)
    service = ProjectTaskService(infrastructure)

    service.create_project("narrow", "Narrow boundary", {
        "goal": "Write one short caption",
        "audience": "A test audience",
        "deliverables": ["caption"],
    })
    tasks = service.add_tasks("narrow", [{
        "task_id": "write", "title": "Write caption", "kind": "writing",
        "executor": "agent", "depends_on": [], "inputs": [],
        "outputs": ["caption"], "requirements": {},
        "acceptance": {"observable": "A real caption artifact is returned."},
    }])

    assert service.project("narrow")["project_id"] == "narrow"
    assert [task["task_id"] for task in tasks] == ["write"]
    assert service.list_tasks("narrow")[0]["status"] == "READY"
    assert not hasattr(infrastructure, "project")
    assert not hasattr(infrastructure, "list_tasks")
    assert not hasattr(infrastructure, "_validate_graph")
