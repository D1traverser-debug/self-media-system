"""Actual registered source evidence execution and explicit semantic assurance limits."""
import json
from pathlib import Path

from social_media_studio.engine import StudioEngine
from social_media_studio.production.worker_pool import run_ready_tool_tasks
from social_media_studio.domain.research import inspect_research_evidence


def test_source_quote_grounding_checks_bytes_and_keeps_truth_unverified(tmp_path):
    import hashlib
    source = tmp_path / "source.txt"
    source.write_text("The published result is 12 units.", encoding="utf-8")
    desc = {"source": {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                       "artifact_id": "a_source"}}
    bundle = {"schema_version": "1.0", "claims": [{
        "id": "c1", "statement": "12 units", "kind": "FACT",
        "evidence": [{"source_input": "source", "stance": "SUPPORTS",
                      "excerpt": "published result is 12"}],
    }]}
    report = inspect_research_evidence(bundle, desc, manifest_input="manifest")
    assert report["evidence_coverage_pass"]
    assert report["claims"][0]["evidence"][0]["byte_excerpt_match"]
    assert report["claims"][0]["factual_truth_verified"] is False
    assert report["semantic_fact_check_performed"] is False
    bundle["claims"][0]["evidence"][0]["excerpt"] = "fabricated 33"
    broken = inspect_research_evidence(bundle, desc, manifest_input="manifest")
    assert "QUOTED_EXCERPT_NOT_IN_SOURCE" in broken["claims"][0]["issues"]
    assert not broken["evidence_coverage_pass"]


def test_research_executor_creates_real_digest_bound_report(tmp_path):
    engine = StudioEngine(tmp_path / "workspace")
    engine.create_project("research", "Ground an actual owner source",
                          {"goal": "Inspect a specific source", "audience": "Editorial",
                           "deliverables": ["research-report"]})
    source = tmp_path / "primary.txt"
    source.write_text("Observed value: 12", encoding="utf-8")
    bundle = tmp_path / "manifest.json"
    bundle.write_text(json.dumps({
        "schema_version": "1.0", "claims": [{
            "id": "claim-1", "statement": "Value 12", "kind": "FACT",
            "evidence": [{"source_input": "primary", "stance": "SUPPORTS",
                          "excerpt": "Observed value: 12"}],
        }],
    }), encoding="utf-8")
    for name, src in (("primary", source), ("manifest", bundle)):
        engine.import_asset("research", name, src, kind="document",
                            media_type="application/json" if name == "manifest" else "text/plain",
                            rights_status="OWNED")
    engine.add_tasks("research", [{
        "task_id": "inspect-source", "title": "Verify exact source bytes and quotes",
        "kind": "research_evidence", "executor": "tool",
        "depends_on": [], "inputs": ["primary", "manifest"],
        "outputs": ["research-report"], "acceptance": {"observable": "Digest-bound source quote report"},
        "requirements": {"production": {"operation": "source_evidence_audit",
                                         "manifest_input": "manifest",
                                         "report_output": "research-report"}},
    }])
    cycle = run_ready_tool_tasks(engine, "research")
    assert not cycle["failed"], cycle
    assert cycle["scheduler_status"] == "TASK_GRAPH_COMPLETE_NOT_RELEASED"
    receipt = cycle["completed"][0]["result"]["completion"]["artifacts"]["research-report"]
    report = json.loads(Path(receipt["path"]).read_text(encoding="utf-8"))
    assert report["evidence_coverage_pass"] is True
    assert report["semantic_fact_check_performed"] is False
    assert engine.audit("research")["pass"] is True
