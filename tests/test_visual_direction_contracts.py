import pytest
from social_media_studio.domain.creative import VisualContractError, inspect_visual_direction


def base(**kwargs):
    return {"schema_version":"1.0","deliverable_id":"single-image","mode":"SINGLE_IMAGE",
            "owner_intent":"A single image only, no collage or title graphics",
            "primary_story_or_subject":"The joke walks out of a broken arcade game", **kwargs}


def test_visual_prompt_only_is_a_real_contract_not_permission_to_generate():
    route=inspect_visual_direction(base(mode="PROMPT_ONLY",draft_prompt="One decisive cinematic arcade moment, readable at mobile scale."))
    assert route["generation_authorized"] is False
    assert route["generated_pixels_observed"] is False
    assert route["aesthetic_quality_verified"] is False
    assert route["selected_task_graph"] is None


def test_separate_image_reference_roles_do_not_silently_transfer_style_to_anatomy():
    direction=inspect_visual_direction(base(
        references=[{"source_ref":"owner-avatar-v2","role":"small emblem only",
                     "allowed_influence":["badge silhouette"],"excluded_influence":["main protagonist","photographic face identity"],
                     "source_sha256":"a"*64}]))
    item=direction["references"][0]
    assert item["source_ref"]=="owner-avatar-v2"
    assert item["source_bytes_verified"] is False
    assert item["allowed_influence"]==["badge silhouette"]
    assert "main protagonist" in item["excluded_influence"]
    assert direction["reference_fidelity_verified"] is False


def test_unrelated_or_malformed_references_are_never_implicitly_added():
    route=inspect_visual_direction(base())
    assert route["references"]==[]
    for change in [
        {"references":[{"source_ref":"img-1","role":"style","allowed_influence":[]}]},
        {"references":[{"source_ref":"img-1","role":"style","allowed_influence":["face"],"excluded_influence":["face"]}]},
        {"references":[{"source_ref":"img-1","role":"style","allowed_influence":["lighting"],"source_sha256":"fake"}]},
        {"references":[{"source_ref":"img-1","role":"style","allowed_influence":["lighting"]},
                       {"source_ref":"img-1","role":"anatomy","allowed_influence":["face"]}]},
        {"candidates":["candidate-a","candidate-a"]},
    ]:
        with pytest.raises(VisualContractError):
            inspect_visual_direction(base(**change))


def test_editing_needs_a_reference_and_prompt_not_mandatory_for_other_visual_tasks():
    with pytest.raises(VisualContractError):
        inspect_visual_direction(base(mode="EDIT_EXISTING"))
    report=inspect_visual_direction(base(mode="EDIT_EXISTING",
        references=[{"source_ref":"owner-selected-image-001","role":"edit target",
                     "allowed_influence":["scene composition","subject placement"],
                     "excluded_influence":["unrelated earlier conversation images"]}]))
    assert report["generated_pixels_observed"] is False
    assert report["independent_review_verified"] is False
    with pytest.raises(VisualContractError):
        inspect_visual_direction(base(mode="PROMPT_ONLY"))
