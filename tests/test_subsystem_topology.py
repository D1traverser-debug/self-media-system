"""Every original internal subsystem is source-owned and no old controller is active."""
import json
from pathlib import Path

from social_media_studio.subsystems import audit_subsystems, _imports, _module

ROOT = Path(__file__).resolve().parents[1]


def test_every_python_module_and_registered_executor_has_one_real_internal_owner():
    report = audit_subsystems(ROOT)
    assert report["pass"], report["violations"]
    assert report["code_modules"] == report["owned_modules"]
    catalog = json.loads((ROOT/"social_media_studio/data/subsystem_catalog.json").read_text())
    floors = catalog["topology_contract"]
    assert report["code_modules"] >= floors["minimum_code_modules"]
    assert report["subsystems"] >= floors["minimum_subsystems"]
    assert report["domain_adapters"] >= floors["minimum_domain_adapters"]
    assert report["production_operations"] >= floors["minimum_production_operations"]
    assert report["unclassified_paths"] == []
    assert report["all_tracked_bytes_inspected"] is True
    assert len(report["all_tracked_file_sha256"]) == report["tracked_files"]
    assert report["json_documents_parsed"] >= 20
    assert report["semantic_line_by_line_complete"] is False


def test_ipos_and_other_professional_systems_are_not_external_peer_apps():
    data = json.loads((ROOT/"social_media_studio/data/subsystem_catalog.json").read_text())
    by_id = {s["id"]: s for s in data["subsystems"]}
    assert data["boundaries"]["ipos"]["product_membership"] == "INTERNAL_SOCIAL_MEDIA_STUDIO"
    assert "social_media_studio/legacy/ip_identity.py" in by_id["original_identity_ipos"]["code_paths"]
    assert len(by_id["original_identity_ipos"]["domain_adapters"]) == 5
    assert "business_growth_commercial" in by_id
    assert "motion_and_production" in by_id
    assert "source_and_asset_lineage" in by_id
    assert all(s["active_by_default"] is False for s in by_id.values())


def test_legacy_control_plane_is_not_reactivated_by_current_import_graph():
    report = audit_subsystems(ROOT)
    assert report["pass"], report["violations"]
    cat = json.loads((ROOT/"social_media_studio/data/subsystem_catalog.json").read_text())
    old = next(s for s in cat["subsystems"] if s["id"] == "legacy_agent_control_plane")
    assert old["activation"] == "ISOLATED_HISTORICAL_FIXTURE_ONLY"
    assert "social_media_studio/legacy/runtime.py" in old["code_paths"]
    assert "social_media_studio/legacy/orchestrator.py" in old["code_paths"]


def test_relative_import_graph_follows_actual_package_levels(tmp_path):
    sample=tmp_path/"example.py"
    sample.write_text("from ..engine import StudioEngine\nfrom .contracts import X\n")
    assert _imports(sample,"social_media_studio.production.example") == {
        "social_media_studio.engine", "social_media_studio.production.contracts"}
    assert _module("social_media_studio/legacy/ip_identity.py")=="social_media_studio.legacy.ip_identity"
    assert _module("social_media_studio/domain/__init__.py")=="social_media_studio.domain"


def test_x_article_and_social_posts_are_internal_not_stolen_by_peer_writing_systems():
    from social_media_studio.subsystems import route_declared_content
    plan = route_declared_content([
        {"id": "post", "type": "SHORT_COPY", "constraints": {}},
        {"id": "article", "type": "LONG_ARTICLE", "constraints": {}},
        {"id": "avatar", "type": "STATIC_IMAGE",
         "constraints": {"identity_mode": "TEMPORARY_CHARACTER"}},
    ])
    assert [x["primary_internal_subsystem"] for x in plan["routes"]] == [
        "editorial_and_language", "editorial_and_language",
        "visual_and_static_design"]
    assert plan["routes"][2]["identity_scope"] == "TEMPORARY_NO_PERSONAL_IPOS"
    assert plan["peer_system_task_authority_inherited"] is False
    assert plan["selected_task_graph"] is None
    assert all(x["effect_authorized"] is False for x in plan["routes"])
    catalog = json.loads((ROOT / "social_media_studio/data/subsystem_catalog.json").read_text())
    assert {x["id"] for x in catalog["caos_sibling_business_systems"]} == {
        "novel-writing-agent", "financial-writing-agent", "a-share-event-driven-agent"}
    assert {x["id"] for x in catalog["nested_product_capabilities"]} >= {
        "x_short_post_and_thread", "x_articles_longform", "original_identity_ipos_design"}


def test_owner_route_discloses_unimplemented_research_instead_of_claiming_tool():
    from social_media_studio.subsystems import route_declared_content
    r = route_declared_content([{"id":"analysis","type":"ANALYSIS_REPORT","constraints":{}}])
    assert r["routes"][0]["primary_internal_subsystem"] == "research_and_understanding"
    assert r["routes"][0]["actual_executor_verified"] is False
    assert r["routes"][0]["independent_outcome_verified"] is False


def _isolated_source_checkout(tmp_path):
    """Only source bytes and catalog, no user workspace or legacy task instances."""
    from shutil import copy2
    cat = json.loads((ROOT/"social_media_studio/data/subsystem_catalog.json").read_text())
    for group in cat["subsystems"]:
        for relative in group["code_paths"]:
            target = tmp_path/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            copy2(ROOT/relative,target)
    target=tmp_path/"social_media_studio/data/subsystem_catalog.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    copy2(ROOT/"social_media_studio/data/subsystem_catalog.json",target)
    return cat


def test_new_unowned_module_is_rejected_by_full_code_scan(tmp_path):
    _isolated_source_checkout(tmp_path)
    orphan=tmp_path/"social_media_studio/orphan_renderer.py"
    orphan.write_text("def pretend_to_render(): return True\n")
    audit=audit_subsystems(tmp_path)
    assert audit["pass"] is False
    assert any("UNOWNED Python module" in x and "orphan_renderer.py" in x
               for x in audit["violations"])


def test_active_import_of_old_controller_is_rejected_not_whitelisted(tmp_path):
    _isolated_source_checkout(tmp_path)
    source=tmp_path/"social_media_studio/domain/editorial.py"
    source.write_text(source.read_text()+"\nfrom social_media_studio.legacy.runtime import StudioRuntime\n")
    audit=audit_subsystems(tmp_path)
    assert audit["pass"] is False
    assert any("reaches old controller" in x and "social_media_studio.legacy.runtime" in x
               for x in audit["violations"])


def test_topology_regression_floor_is_enforced_when_catalog_and_code_shrink_together(tmp_path):
    cat = _isolated_source_checkout(tmp_path)
    cat["topology_contract"]["minimum_subsystems"] = len(cat["subsystems"]) + 1
    cat["topology_contract"]["minimum_code_modules"] = sum(
        len(item["code_paths"]) for item in cat["subsystems"]
    ) + 1
    catalog_path = tmp_path/"social_media_studio/data/subsystem_catalog.json"
    catalog_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2))
    report = audit_subsystems(tmp_path)
    assert report["pass"] is False
    assert any("topology regression floor violated: minimum_subsystems" in item
               for item in report["violations"])
    assert any("topology regression floor violated: minimum_code_modules" in item
               for item in report["violations"])


def test_false_external_ipos_and_duplicate_executor_ownership_are_rejected(tmp_path):
    cat=_isolated_source_checkout(tmp_path)
    catalog_path=tmp_path/"social_media_studio/data/subsystem_catalog.json"
    ipos=next(x for x in cat["subsystems"] if x["id"]=="original_identity_ipos")
    ipos["product_membership"]="EXTERNAL_STUDIO"
    cat["subsystems"][0]["production_operations"].append("ffmpeg_video_audio_copy")
    catalog_path.write_text(json.dumps(cat,ensure_ascii=False,indent=2))
    audit=audit_subsystems(tmp_path)
    assert audit["pass"] is False
    assert any("subsystem wrongly external: original_identity_ipos" in x for x in audit["violations"])
    assert any("duplicate operation ownership" in x for x in audit["violations"])


def test_private_cross_system_peer_cannot_inherit_video_execution_rights(tmp_path):
    cat=_isolated_source_checkout(tmp_path)
    cat["caos_sibling_business_systems"][0]["task_authority_transfer"]=True
    (tmp_path/"social_media_studio/data/subsystem_catalog.json").write_text(
        json.dumps(cat,ensure_ascii=False,indent=2))
    report=audit_subsystems(tmp_path)
    assert report["pass"] is False
    assert any("cross-system authority mistakenly merged" in x for x in report["violations"])


def test_current_domain_authority_is_internal_ipos_and_old_external_wording_is_historical():
    dom=json.loads((ROOT/"social_media_studio/legacy/data/domain_manifest.json").read_text())
    auth=dom["domain_authority"]
    assert "external_identity_authority" not in auth
    identity=auth["internal_original_identity_subsystem"]
    assert identity["product_membership"]=="INTERNAL_SOCIAL_MEDIA_STUDIO"
    assert identity["implementation_source"]=="social_media_studio/legacy/ip_identity.py"
    assert identity["studio_mutation_of_canon"] is False
    assert identity["owner_approval_required"] is True
    assert audit_subsystems(ROOT)["pass"]


def test_verified_retired_operator_view_cannot_be_reintroduced(tmp_path):
    """A Git deletion is a reviewed lifecycle change, not a reversible alias."""
    cat = _isolated_source_checkout(tmp_path)
    retired = next(item for item in cat["source_retirements"]
                   if item["path"] == "social_media_studio/legacy/operator_view.py")
    assert retired["status"] == "DELETED_FROM_HEAD"
    assert retired["source_history_preserved_by_git"] is True
    assert retired["user_workspaces_touched"] is False
    assert not (ROOT / retired["path"]).exists()
    assert not (ROOT / retired["deleted_test"]).exists()
    assert not (tmp_path / retired["path"]).exists()
    obsolete = tmp_path / retired["path"]
    obsolete.parent.mkdir(parents=True, exist_ok=True)
    obsolete.write_text("class OperatorSnapshot: pass\n", encoding="utf-8")
    report = audit_subsystems(tmp_path)
    assert report["pass"] is False
    assert any("retired source path was reintroduced" in issue
               for issue in report["violations"])
