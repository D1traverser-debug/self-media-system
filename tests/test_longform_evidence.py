"""Synthetic regressions for trace mechanics; not tests of writing quality."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from social_media_studio.domain.editorial import EditorialContractError, inspect_long_article, inspect_short_copy
from social_media_studio.domain.longform_evidence import article_digest


def article():
    return {
        "schema_version": "1.0", "title": "A synthetic article",
        "locale": "en-US", "intent_kind": "ARGUMENT",
        "sections": [{"section_id": "s1", "body": "A bounded claim."}],
        "factual_claims": [{"claim_id": "c1", "statement": "An observed fact.",
                            "source_refs": ["source-v1"]}],
    }


def packet():
    a = article()
    a["editorial_trace"] = {
        "schema_version": "1.0", "article_sha256": article_digest(a),
        "nodes": [
            {"id": "source", "purpose": "source observation", "state": "SUPPORTED",
             "evidence_refs": ["source-v1"], "claim_ids": ["c1"]},
            {"id": "argument", "purpose": "inference", "state": "SUPPORTED",
             "depends_on": ["source"], "evidence_refs": ["argument-review-v1"]},
            {"id": "prose", "purpose": "reader-facing explanation", "state": "SUPPORTED",
             "depends_on": ["argument"], "section_ids": ["s1"], "evidence_refs": ["draft-v1"]},
            {"id": "unrelated", "purpose": "independent packaging research",
             "state": "SUPPORTED", "evidence_refs": ["package-note"]},
        ],
        "findings": [],
    }
    return a


def inspect(a):
    return inspect_long_article(a)["editorial_trace"]


def test_consistent_declarations_never_certify_quality():
    result = inspect(packet())
    assert result["status"] == "DECLARED_TRACE_CONSISTENT_REVIEW_PENDING"
    for flag in ("semantic_quality_verified", "source_authenticity_verified",
                 "independent_review_verified", "owner_outcome_verified",
                 "publication_authorized", "method_promoted"):
        assert result[flag] is False


def test_blocking_finding_reopens_ancestor_and_only_its_descendants():
    a = packet()
    a["editorial_trace"]["findings"] = [{
        "id": "unsupported-bridge", "target_id": "argument",
        "problem": "The observation does not entail the conclusion.",
        "severity": "BLOCKING", "state": "OPEN", "evidence_refs": ["review-v2"],
    }]
    r = inspect(a)
    assert r["status"] == "REOPEN_REQUIRED"
    assert r["reopen_roots"] == ["argument"]
    assert r["affected_nodes"] == ["argument", "prose"]
    assert r["unaffected_nodes"] == ["source", "unrelated"]


def test_changed_source_reopens_dependents_but_not_independent_node():
    a = packet()
    a["editorial_trace"]["changed_node_ids"] = ["source"]
    assert inspect(a)["affected_nodes"] == ["argument", "prose", "source"]


@pytest.mark.parametrize("field,new_value", [
    ("title", "Revised title"), ("locale", "en-GB"),
    ("sections", [{"section_id": "s1", "body": "A revised claim."}]),
])
def test_review_cannot_survive_article_revision(field, new_value):
    a = packet()
    a[field] = new_value
    assert inspect(a)["status"] == "STALE_ARTICLE_TRACE"


def test_unknown_deps_and_cycles_rejected():
    for deps in (["missing"], ["prose"], ["source"]):
        a = packet()
        a["editorial_trace"]["nodes"][0]["depends_on"] = deps
        with pytest.raises(EditorialContractError):
            inspect(a)


def test_unmapped_claim_and_section_reopen():
    a = packet()
    a["editorial_trace"]["nodes"][0].pop("claim_ids")
    a["editorial_trace"]["nodes"][2].pop("section_ids")
    r = inspect(a)
    assert r["status"] == "REOPEN_REQUIRED"
    assert r["unmapped_declared_claim_ids"] == ["c1"]
    assert r["unmapped_declared_section_ids"] == ["s1"]


def test_invalid_references_and_evidence_free_support_rejected():
    for key, value in (("claim_ids", ["unknown"]), ("evidence_refs", []),
                       ("section_ids", ["unknown"])):
        a = packet()
        a["editorial_trace"]["nodes"][0][key] = value
        with pytest.raises(EditorialContractError):
            inspect(a)


def test_resolved_finding_requires_resolution_reference():
    a = packet()
    a["editorial_trace"]["findings"] = [{
        "id": "x", "target_id": "argument", "severity": "BLOCKING",
        "state": "RESOLVED", "problem": "An unsupported inference.",
        "evidence_refs": ["review"],
    }]
    with pytest.raises(EditorialContractError):
        inspect(a)
    a["editorial_trace"]["findings"][0]["resolution_ref"] = "correction"
    assert inspect(a)["independent_review_verified"] is False


def test_open_advisory_is_visible_without_invalidating_other_nodes():
    a = packet()
    a["editorial_trace"]["findings"] = [{
        "id": "wording", "target_id": "prose", "severity": "ADVISORY",
        "state": "OPEN", "problem": "Awkward wording.", "evidence_refs": ["readback"],
    }]
    r = inspect(a)
    assert r["open_advisory_finding_ids"] == ["wording"]
    assert r["affected_nodes"] == []
    assert r["semantic_quality_verified"] is False


def test_nonargument_does_not_need_argument_graph_and_short_copy_unaffected():
    a = {"schema_version": "1.0", "title": "A memory", "locale": "en-US",
         "intent_kind": "PERSONAL_ESSAY", "body": "A synthetic memory."}
    assert inspect(a)["status"] == "TRACE_NOT_SUPPLIED"
    a["editorial_trace"] = {
        "schema_version": "1.0", "article_sha256": article_digest(a),
        "nodes": [{"id": "voice", "purpose": "voice and provenance",
                   "state": "SUPPORTED", "evidence_refs": ["draft-review"]}],
    }
    assert inspect(a)["status"] == "DECLARED_TRACE_CONSISTENT_REVIEW_PENDING"
    short = inspect_short_copy({"schema_version": "1.0", "text": "A line.",
                                "platform": "X", "locale": "en-US",
                                "content_intent": "short observation"})
    assert "editorial_trace" not in short


def test_longform_craft_atlas_is_registered_and_routed():
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "social_media_studio/data/knowledge_catalog.json").read_text(encoding="utf-8"))
    entry = next(item for item in catalog["entries"] if item["id"] == "long-form-craft-atlas")
    assert entry["status"] == "CANDIDATE_REQUIRES_REVALIDATION"
    assert (root / entry["ref"]).is_file()
    editorial = (root / "skills/social-media-studio/references/long-form-editorial.md").read_text(encoding="utf-8")
    skill = (root / "skills/social-media-studio/SKILL.md").read_text(encoding="utf-8")
    assert "long-form-craft-atlas.md" in editorial
    assert "long-form-craft-atlas" in skill


def test_longform_microcraft_playbook_is_registered_and_conditionally_routed():
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "social_media_studio/data/knowledge_catalog.json").read_text(encoding="utf-8"))
    entry = next(item for item in catalog["entries"] if item["id"] == "long-form-microcraft-playbook")
    assert entry["status"] == "CANDIDATE_REQUIRES_REVALIDATION"
    assert (root / entry["ref"]).is_file()
    playbook = (root / entry["ref"]).read_text(encoding="utf-8")
    assert "Given → new information flow" in playbook
    assert "answer-debt ledger" in playbook
    assert "Engagement is multidimensional" in playbook
    assert "Coherence versus cohesion" in playbook
    assert "No metric, style detector" in playbook
    editorial = (root / "skills/social-media-studio/references/long-form-editorial.md").read_text(encoding="utf-8")
    skill = (root / "skills/social-media-studio/SKILL.md").read_text(encoding="utf-8")
    assert "long-form-microcraft-playbook.md" in editorial
    assert "long-form-microcraft-playbook" in skill


def test_longform_argument_engineering_is_registered_and_conditionally_routed():
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "social_media_studio/data/knowledge_catalog.json").read_text(encoding="utf-8"))
    entry = next(item for item in catalog["entries"] if item["id"] == "long-form-argument-engineering")
    assert entry["status"] == "CANDIDATE_REQUIRES_REVALIDATION"
    assert (root / entry["ref"]).is_file()
    module = (root / entry["ref"]).read_text(encoding="utf-8")
    assert "Claim–grounds–warrant model" in module
    assert "Counterargument" in module
    assert "counterfactual" in module
    assert "Do not force the full Toulmin model everywhere" in module
    editorial = (root / "skills/social-media-studio/references/long-form-editorial.md").read_text(encoding="utf-8")
    skill = (root / "skills/social-media-studio/SKILL.md").read_text(encoding="utf-8")
    assert "long-form-argument-engineering.md" in editorial
    assert "long-form-argument-engineering" in skill
