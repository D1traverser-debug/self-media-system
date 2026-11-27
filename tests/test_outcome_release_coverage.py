"""Project-wide release coverage is not the same as accepted owner outcome."""
from __future__ import annotations

import pytest

from social_media_studio.domain.outcome_assurance import variant_release_coverage
from social_media_studio.engine_support import completion_guidance


def item(deliverable, variant, *statuses):
    return {"deliverable_id": deliverable, "variant_id": variant,
            "candidates": [{"artifact_status": s} for s in statuses]}


def test_single_accepted_ratio_cannot_complete_multivariant_owner_request():
    progress = variant_release_coverage([
        item("cover", "portrait", "ACCEPTED"),
        item("cover", "landscape", "CURRENT"),
        item("caption", "zh-CN"),
    ])
    assert progress["declared_variant_count"] == 3
    assert progress["individually_released_variant_count"] == 1
    assert not progress["artifact_release_coverage_complete"]
    assert progress["unreleased_variants"] == [
        {"deliverable_id": "cover", "variant_id": "landscape"},
        {"deliverable_id": "caption", "variant_id": "zh-CN"},
    ]
    assert progress["missing_candidate_variants"] == [
        {"deliverable_id": "caption", "variant_id": "zh-CN"},
    ]
    assert progress["whole_demand_accepted"] is False


def test_all_variants_accepted_still_requires_independent_owner_outcome_review():
    progress = variant_release_coverage([
        item("cover", "3x4", "CURRENT", "ACCEPTED"),
        item("cover", "16x9", "ACCEPTED"),
        item("title", "en", "ACCEPTED"),
    ])
    assert progress["artifact_release_coverage_complete"] is True
    assert progress["individually_released_variant_count"] == 3
    assert progress["owner_outcome_verified"] is False
    assert progress["external_publication_authorized"] is False
    assert progress["next_required_boundary"] == "INDEPENDENT_OWNER_OUTCOME_AND_QUALITY_REVIEW"


def test_zero_variants_does_not_pass_vacuously():
    progress = variant_release_coverage([])
    assert progress["artifact_release_coverage_complete"] is False
    assert progress["whole_demand_accepted"] is False


def test_duplicate_variant_identity_fails_closed():
    with pytest.raises(ValueError, match="duplicate deliverable variant"):
        variant_release_coverage([item("cover", "portrait"), item("cover", "portrait", "ACCEPTED")])


def test_unreleased_current_candidates_generate_actionable_shared_guidance():
    current = variant_release_coverage([item("caption", "zh-CN", "CURRENT")])
    current["candidate_coverage_complete"] = True
    advice = completion_guidance(current)
    assert advice["state"] == "ARTIFACT_RELEASE_COVERAGE_INCOMPLETE"
    assert "each actual output" in advice["next_action"]


def test_accepted_artifact_coverage_never_proves_semantic_owner_approval():
    current = variant_release_coverage([item("caption", "en", "ACCEPTED")])
    current["candidate_coverage_complete"] = True
    advice = completion_guidance(current)
    assert advice["state"] == "QUALITY_AND_OWNER_OUTCOME_UNVERIFIED"
    assert "not owner approval" in advice["next_action"]


def test_multiple_individually_accepted_artifacts_for_same_variant_need_reconciliation():
    progress = variant_release_coverage([
        item("cover", "portrait", "ACCEPTED", "ACCEPTED"),
        item("caption", "zh-CN", "ACCEPTED"),
    ])
    assert progress["individually_released_variant_count"] == 1
    assert progress["ambiguous_release_variants"] == [
        {"deliverable_id": "cover", "variant_id": "portrait"},
    ]
    assert {"deliverable_id": "cover", "variant_id": "portrait"} in progress["unreleased_variants"]
    assert progress["artifact_release_coverage_complete"] is False
    assert progress["whole_demand_accepted"] is False
