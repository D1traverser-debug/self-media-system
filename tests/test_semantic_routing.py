"""Declarative, task-neutral editorial method applicability.

A user's declared genre/intent can make a method eligible, but does not
independently prove footage authenticity, a news fact or artistic quality.
"""
import copy
import json
from pathlib import Path

import pytest

from social_media_studio.engine import StudioEngine
from social_media_studio.scope import bind_owner_brief, capability_lookup, resolve_intake

ROOT = Path(__file__).resolve().parents[1]


def spec(*, content_class=None, treatment=None, sources=None):
    constraints = {}
    if content_class is not None:
        constraints["source_content_class"] = content_class
    if treatment is not None:
        constraints["editorial_treatment"] = treatment
    return {"id": "caption", "type": "SHORT_COPY",
            "constraints": constraints, "source_refs": list(sources or [])}


def preview(tmp_path, item, selected=None):
    return resolve_intake(tmp_path, {
        "mode": "NEW", "goal": "Write the current owner-requested caption",
        "deliverable_specs": [item],
    }, selection={"deliverables": {"caption": [selected]}} if selected else None)["demand_composition"]["deliverables"][0]


@pytest.mark.parametrize("item", [
    spec(),
    spec(content_class="GAMEPLAY", treatment="SATIRE", sources=["actual-video"]),
    spec(content_class="PET_ENTERTAINMENT", treatment="SATIRE", sources=["actual-video"]),
    spec(content_class="FICTIONAL_ENTERTAINMENT", treatment="SATIRE", sources=["actual-video"]),
    spec(content_class="NEWS_CURRENT_AFFAIRS", sources=["news-video"]),
    spec(content_class="NEWS_CURRENT_AFFAIRS", treatment="SATIRE"),
])
def test_non_news_or_unproven_news_satire_is_not_eligible(tmp_path, item):
    plan = preview(tmp_path, item)
    assert "news_satire_packaging" not in plan["candidate_demands_not_selected"]
    assert "short_form_copy" in plan["candidate_demands_not_selected"]
    with pytest.raises(ValueError, match="operation does not match"):
        preview(tmp_path, item, selected="news_satire_packaging")


def test_declared_sourced_news_satire_is_only_a_proposal_not_truth(tmp_path):
    item = spec(content_class="NEWS_CURRENT_AFFAIRS", treatment="SATIRE",
                sources=["owner-source-video"])
    plan = preview(tmp_path, item, selected="news_satire_packaging")
    route = plan["proposed_professional_routes"][0]
    assert route["demand_id"] == "news_satire_packaging"
    assert route["applicability_declaration_only"] is True
    assert route["source_and_content_authenticity_verified"] is False
    assert route["actual_executor_verified"] is False


def _task():
    return {
        "task_id": "write", "outputs": ["caption-output"], "executor": "agent",
        "acceptance": {"observable": "independently inspect the resulting caption"},
        "requirements": {
            "deliverable_refs": ["caption"], "decision_id": "d-write",
            "professional_demands": {"caption": ["news_satire_packaging"]},
            "deliverable_outputs": {
                "caption-output": {"deliverable_id": "caption", "variant_id": "caption"},
            },
        },
    }


def test_durable_admission_rejects_pet_news_satire_bypass(tmp_path):
    item = spec(content_class="PET_ENTERTAINMENT", treatment="SATIRE", sources=["video"])
    engine = StudioEngine(tmp_path / "studio")
    brief = bind_owner_brief("fresh", {
        "goal": "Make a pet caption, not current affairs commentary",
        "audience": "owner", "deliverables": ["caption"], "deliverable_specs": [item],
    })
    engine.create_project("fresh", "fresh", brief)
    with pytest.raises(ValueError, match="semantic preconditions"):
        engine.add_tasks("fresh", [_task()])


def test_durable_admission_accepts_only_declaration_not_actual_execution(tmp_path):
    item = spec(content_class="NEWS_CURRENT_AFFAIRS", treatment="SATIRE",
                sources=["owner-source"])
    engine = StudioEngine(tmp_path / "studio")
    brief = bind_owner_brief("fresh", {
        "goal": "An owner-selected factual news satire",
        "audience": "owner", "deliverables": ["caption"], "deliverable_specs": [item],
    })
    engine.create_project("fresh", "fresh", brief)
    tasks = engine.add_tasks("fresh", [_task()])
    assert tasks[0]["task_id"] == "write"
    assert engine.status("fresh")["deliverable_progress"]["owner_outcome_verified"] is False


@pytest.mark.parametrize("bad", [
    {},
    {"required_constraints": {}, "min_source_refs": 1},
    {"required_constraints": {"source_content_class": "NEWS_CURRENT_AFFAIRS"},
     "min_source_refs": 0},
    {"required_constraints": {"source_content_class": "NEWS_CURRENT_AFFAIRS"},
     "min_source_refs": True},
    {"required_constraints": {"source_content_class": 123}, "min_source_refs": 1},
])
def test_malformed_semantic_registry_configuration_rejected(bad):
    raw = json.loads((ROOT / "social_media_studio/legacy/data/capabilities.json").read_text())
    test_profile = copy.deepcopy(raw)
    group = next(x for x in test_profile["professional_capability_groups"]
                 if x["id"] == "editorial_writing")
    group["demand_routes"]["news_satire_packaging"]["semantic_preconditions"] = bad
    with pytest.raises(ValueError, match="malformed semantic preconditions"):
        capability_lookup(profile=test_profile)
