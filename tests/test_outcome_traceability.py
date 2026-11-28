"""Exact user clauses remain scoped to the actual output and never self-approve."""
from __future__ import annotations

from copy import deepcopy

import pytest

from social_media_studio.domain.outcome_traceability import trace_owner_requirements


def brief():
    return {
        "goal": "Deliver a source-faithful bilingual package",
        "deliverables": ["caption", "cover"],
        "deliverable_specs": [
            {
                "id": "caption", "type": "SHORT_COPY", "locale": "zh-CN",
                "source_refs": ["user-media-source"],
                "acceptance": {"tone": "natural Chinese and playful, not a news narrator"},
            },
            {
                "id": "cover", "type": "MULTI_ASPECT_IMAGE_SET",
                "source_refs": ["user-media-source"],
                "prohibitions": ["do not duplicate the chosen title"],
                "variants": [
                    {"id": "3x4", "shape": {"width": 900, "height": 1200, "orientation": "PORTRAIT"}},
                    {"id": "16x9", "shape": {"width": 1600, "height": 900, "orientation": "LANDSCAPE"}},
                ],
            },
        ],
        "demand_contract": {
            "schema_version": 1, "owner_source_refs": ["current-owner-turn"],
            "clauses": [
                {"id": "global", "kind": "PROHIBITION", "text": "No automatic publishing",
                 "source_ref": "current-owner-turn", "deliverable_refs": []},
                {"id": "caption-only", "kind": "HARD_CONSTRAINT", "text": "Not a news report",
                 "source_ref": "current-owner-turn", "deliverable_refs": ["caption"]},
                {"id": "cover-only", "kind": "ACCEPTANCE", "text": "Visual hierarchy works at thumbnail size",
                 "source_ref": "current-owner-turn", "deliverable_refs": ["cover"]},
                {"id": "question", "kind": "UNRESOLVED_QUESTION", "text": "Final distribution channel?",
                 "source_ref": "current-owner-turn", "deliverable_refs": []},
            ],
        },
    }


def variants():
    return [
        {"deliverable_id": "caption", "variant_id": "caption", "type": "SHORT_COPY",
         "candidates": [{"artifact_id": "a", "sha256": "0" * 64, "conformance": {"status": "MATCH"}}]},
        {"deliverable_id": "cover", "variant_id": "3x4", "type": "MULTI_ASPECT_IMAGE_SET",
         "candidates": [{"artifact_id": "b", "sha256": "1" * 64, "conformance": {"status": "MATCH"}}]},
        {"deliverable_id": "cover", "variant_id": "16x9", "type": "MULTI_ASPECT_IMAGE_SET",
         "candidates": []},
    ]


def test_all_variants_trace_original_owner_clauses_without_cross_scope_leak():
    trace = trace_owner_requirements(brief(), variants())
    by_id = {(x["deliverable_id"], x["variant_id"]): x for x in trace["obligations"]}
    caption = by_id[("caption", "caption")]
    cover = by_id[("cover", "3x4")]
    assert {x["clause_id"] for x in caption["owner_clauses"]} == {"global", "caption-only", "question"}
    assert {x["clause_id"] for x in cover["owner_clauses"]} == {"global", "cover-only", "question"}
    assert by_id[("cover", "16x9")]["owner_clauses"] == cover["owner_clauses"]
    assert cover["declared_prohibitions"] == ["do not duplicate the chosen title"]
    assert caption["declared_acceptance"]["tone"].startswith("natural Chinese")
    assert caption["actual_artifact_bindings"][0]["sha256"] == "0" * 64
    assert trace["outstanding_unresolved_clause_ids"] == ["question"]


def test_declared_source_and_technical_match_cannot_prove_creative_owner_acceptance():
    trace = trace_owner_requirements(brief(), variants())
    assert trace["status"] == "DECLARED_OBLIGATIONS_MAPPED_NOT_VERIFIED"
    assert trace["owner_original_source_authenticated"] is False
    assert trace["semantic_completeness_verified"] is False
    assert trace["independent_quality_review_verified"] is False
    assert trace["owner_outcome_verified"] is False
    assert trace["external_publication_authorized"] is False
    assert all(not row["owner_acceptance_verified"] for row in trace["obligations"])
    assert all(row["professional_criteria"] for row in trace["obligations"])


def test_revised_owner_clause_changes_exact_trace_digest_without_reusing_old_proof():
    before = trace_owner_requirements(brief(), variants())
    changed = deepcopy(brief())
    changed["demand_contract"]["clauses"][1]["text"] = "No factual news narration and no artificial conflict"
    after = trace_owner_requirements(changed, variants())
    assert after["brief_sha256"] != before["brief_sha256"]
    assert after["obligations"][0]["owner_clauses"][1]["required_text"] != before["obligations"][0]["owner_clauses"][1]["required_text"]


def test_missing_or_fabricated_variant_fails_owner_requirement_mapping():
    with pytest.raises(ValueError, match="cannot drop or invent"):
        trace_owner_requirements(brief(), variants()[:-1])
    forged = variants() + [{"deliverable_id": "cover", "variant_id": "invented", "candidates": []}]
    with pytest.raises(ValueError, match="cannot drop or invent"):
        trace_owner_requirements(brief(), forged)
