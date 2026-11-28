"""One transactional release implementation behind the current StudioEngine facade."""
import inspect

from social_media_studio.engine import StudioEngine
from social_media_studio.application.release_service import ReleaseAssuranceService


def test_single_release_implementation_is_in_assurance_service():
    public = inspect.getsource(StudioEngine.release_check)
    internal = inspect.getsource(ReleaseAssuranceService.release_check)
    assert "ReleaseAssuranceService(self).release_check" in public
    assert "BEGIN IMMEDIATE" not in public
    assert 'connection.execute("BEGIN IMMEDIATE")' in internal
    assert "ARTIFACT_RELEASE_ACCEPTED" in internal
    assert "ARTIFACT_RELEASE_BLOCKED" in internal
    assert "whole_demand_accepted" in internal
    assert "external_publication_authorized" in internal


def test_release_service_does_not_create_another_control_plane():
    source = inspect.getsource(ReleaseAssuranceService)
    assert "sqlite3.connect(" not in source
    assert "CREATE TABLE" not in source
    assert "create_project(" not in source
    assert "claim_next(" not in source
