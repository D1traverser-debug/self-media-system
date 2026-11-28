"""Non-video business observations use exact source inputs, never fake Episode economics."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from social_media_studio.domain_adapters.business import business_observation_metrics
from social_media_studio.domain_adapters.common import DomainAdapterError
from social_media_studio.engine import StudioEngine
from social_media_studio.scope import bind_owner_brief
from social_media_studio.production.worker_pool import run_ready_tool_tasks


def observation(kind="ACCOUNT"):
    return {
        "schema_version": "SMS_BUSINESS_OBSERVATION_V1",
        "subject": {"kind": kind, "id": "current-subject"},
        "window": {"start": "2026-11-01T00:00:00+00:00", "end": "2026-11-08T00:00:00+00:00"},
        "metrics": [
            {"id": "impressions", "unit": "count", "semantics": "reported impressions",
             "source": {"input": "source", "path": ["data", 0, "impressions"]}},
            {"id": "clicks", "unit": "count", "semantics": "reported clicks",
             "source": {"input": "source", "path": ["data", 0, "clicks"]}},
            {"id": "zero", "unit": "count", "semantics": "reported zero",
             "source": {"input": "source", "path": ["data", 0, "zero"]}},
            {"id": "revenue", "unit": "USD", "semantics": "recorded revenue",
             "unavailable_reason": "No transaction evidence supplied"},
        ],
        "ratios": [
            {"id": "click_ratio", "numerator": "clicks", "denominator": "impressions",
             "semantics": "clicks per reported impression"},
            {"id": "undefined", "numerator": "clicks", "denominator": "zero",
             "semantics": "example undefined ratio"},
            {"id": "unknown", "numerator": "revenue", "denominator": "impressions",
             "semantics": "revenue per impression"},
        ],
    }


def source_data():
    return {"data": [{"impressions": 100, "clicks": 7, "zero": 0}]}


@pytest.mark.parametrize("kind", ["ACCOUNT", "CONTENT", "CAMPAIGN", "OFFER", "PORTFOLIO"])
def test_business_observation_does_not_require_video_minutes(tmp_path, kind):
    file = tmp_path / "source.json"
    file.write_text(json.dumps(source_data()), encoding="utf-8")
    packet = {"input_artifacts": {"source": {"path": str(file), "artifact_id": "fixture",
              "version": 1, "sha256": "fixture-sha"}}}
    result = business_observation_metrics(observation(kind), packet, "spec")
    assert result["subject"]["kind"] == kind
    assert result["raw_metrics"]["clicks"]["value"] == 7
    assert result["raw_metrics"]["clicks"]["source_binding"]["artifact_id"] == "fixture"
    assert result["raw_metrics"]["revenue"]["value"] is None
    assert result["derived_metrics"]["click_ratio"]["value"] == pytest.approx(0.07)
    assert result["derived_metrics"]["undefined"]["status"] == "NONPOSITIVE_DENOMINATOR"
    assert result["derived_metrics"]["undefined"]["value"] is None
    assert result["derived_metrics"]["unknown"]["status"] == "UNAVAILABLE_OPERAND"
    assert not result["platform_authenticity_verified"]
    assert not result["metric_semantics_verified"]
    assert not result["causal_effect_verified"]
    assert not result["owner_outcome_verified"]


@pytest.mark.parametrize("defect", ["missing_input", "missing_path", "self_source",
                                      "naive_window", "wrong_window", "boolean", "duplicate", "nan"])
def test_observation_rejects_fabricated_or_invalid_source(tmp_path, defect):
    data = source_data()
    payload = observation()
    if defect == "missing_input":
        payload["metrics"][0]["source"]["input"] = "not-an-input"
    elif defect == "missing_path":
        payload["metrics"][0]["source"]["path"] = ["bad"]
    elif defect == "self_source":
        payload["metrics"][0]["source"]["input"] = "spec"
    elif defect == "naive_window":
        payload["window"]["start"] = "2026-11-01T00:00:00"
    elif defect == "wrong_window":
        payload["window"]["end"] = payload["window"]["start"]
    elif defect == "boolean":
        data["data"][0]["impressions"] = True
    elif defect == "nan":
        data["data"][0]["impressions"] = float("nan")
    else:
        payload["metrics"].append(copy.deepcopy(payload["metrics"][0]))
    file = tmp_path / "source.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    packet = {"input_artifacts": {"source": {"path": str(file), "artifact_id": "fixture",
              "version": 1, "sha256": "fixture-sha"}}}
    with pytest.raises(DomainAdapterError):
        business_observation_metrics(payload, packet, "spec")


def test_real_typed_account_report_uses_existing_worker_and_artifact_ledger(tmp_path):
    project = "account-measurement"
    engine = StudioEngine(tmp_path / "studio")
    brief = bind_owner_brief(project, {
        "goal": "Report observed account metrics from supplied export; no publishing",
        "audience": "owner", "deliverables": ["report"],
        "deliverable_specs": [{"id": "report", "type": "ANALYSIS_REPORT"}],
    })
    engine.create_project(project, "Account report", brief)
    for name, payload in (("spec", observation()), ("source", source_data())):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        engine.import_asset(project, name, path, kind="document",
                            media_type="application/json", rights_status="NOT_APPLICABLE")
    engine.add_tasks(project, [{
        "task_id": "measure", "executor": "tool", "kind": "domain_adapter",
        "inputs": ["spec", "source"], "outputs": ["report"],
        "requirements": {"deliverable_refs": ["report"], "decision_id": "d-measure",
            "professional_demands": {"report": ["business_measurement"]},
            "deliverable_outputs": {"report": {"deliverable_id": "report", "variant_id": "report"}},
            "domain_adapter": {"name": "business_outcome_metrics", "outcome_receipt_input": "spec"}},
        "acceptance": {"evidence": "exact imported numeric values; missing metrics remain unknown"},
    }])
    engine.record_decision(project, {
        "task_id": "measure", "decision_id": "d-measure", "question": "Which measurement route?",
        "scope": "source-bound account report", "source_refs": ["source", "spec"],
        "hypotheses": [{"id": "a", "discriminator": "source JSON supports extraction"},
                       {"id": "b", "discriminator": "video-specific receipt is unrelated"}],
        "alternatives": [{"id": "a"}, {"id": "b"}], "selected_option": "a",
        "falsifier": "source value or identity mismatch", "rollback": "reopen",
    })
    result = run_ready_tool_tasks(engine, project, max_workers=1)
    assert result["failed"] == [], result
    progress = engine.status(project)["deliverable_progress"]
    assert progress["candidate_coverage_complete"]
    assert not progress["owner_outcome_verified"]
    candidate = progress["variants"][0]["candidates"][0]
    resumed = engine.resume(project)
    actual = next(a for a in resumed["current_artifacts"] if a["artifact_id"] == candidate["artifact_id"])
    registered = result["completed"][0]["result"]["completion"]["artifacts"]["report"]
    assert registered["artifact_id"] == actual["artifact_id"]
    output = json.loads(Path(registered["path"]).read_text(encoding="utf-8"))
    source = next(a for a in resumed["current_artifacts"] if a["name"] == "source")
    assert output["raw_metrics"]["impressions"]["source_binding"]["sha256"] == source["sha256"]
    assert output["raw_metrics"]["revenue"]["value"] is None
    assert output["derived_metrics"]["click_ratio"]["value"] == pytest.approx(0.07)
    assert output["effect_authorized"] is False
    assert output["owner_outcome_verified"] is False
