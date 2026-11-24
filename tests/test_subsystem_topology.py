"""Every original internal subsystem is source-owned and no old controller is active."""
import json
from pathlib import Path

from video_studio.subsystems import audit_subsystems, _imports, _module

ROOT = Path(__file__).resolve().parents[1]


def test_every_python_module_and_registered_executor_has_one_real_internal_owner():
    report = audit_subsystems(ROOT)
    assert report["pass"], report["violations"]
    assert report["code_modules"] == report["owned_modules"]
    assert report["code_modules"] >= 59
    assert report["subsystems"] == 15
    assert report["domain_adapters"] == 17
    assert report["production_operations"] == 5
    assert report["unclassified_paths"] == []
    assert report["semantic_line_by_line_complete"] is False


def test_ipos_and_other_professional_systems_are_not_external_peer_apps():
    data = json.loads((ROOT/"video_studio/data/subsystem_catalog.json").read_text())
    by_id = {s["id"]: s for s in data["subsystems"]}
    assert data["boundaries"]["ipos"]["product_membership"] == "INTERNAL_CONTENT_STUDIO"
    assert "video_growth_agent/ip_identity.py" in by_id["original_identity_ipos"]["code_paths"]
    assert len(by_id["original_identity_ipos"]["domain_adapters"]) == 5
    assert "business_growth_commercial" in by_id
    assert "motion_and_production" in by_id
    assert "source_and_asset_lineage" in by_id
    assert all(s["active_by_default"] is False for s in by_id.values())


def test_legacy_control_plane_is_not_reactivated_by_current_import_graph():
    report = audit_subsystems(ROOT)
    assert report["pass"], report["violations"]
    cat = json.loads((ROOT/"video_studio/data/subsystem_catalog.json").read_text())
    old = next(s for s in cat["subsystems"] if s["id"] == "legacy_agent_control_plane")
    assert old["activation"] == "ISOLATED_HISTORICAL_FIXTURE_ONLY"
    assert "video_growth_agent/runtime.py" in old["code_paths"]
    assert "video_growth_agent/orchestrator.py" in old["code_paths"]


def test_relative_import_graph_follows_actual_package_levels(tmp_path):
    sample=tmp_path/"example.py"
    sample.write_text("from ..engine import StudioEngine\nfrom .contracts import X\n")
    assert _imports(sample,"video_studio.production.example") == {
        "video_studio.engine", "video_studio.production.contracts"}
    assert _module("video_growth_agent/ip_identity.py")=="video_growth_agent.ip_identity"
    assert _module("video_studio/domain/__init__.py")=="video_studio.domain"
