from __future__ import annotations

import copy

import pytest

from video_studio.image_set import (
    ImageSetError,
    compile_image_prompt_pack,
    validate_image_set,
)


def _concepts():
    return [
        {
            "image_id": "IMG-01", "creative_angle": "customs absurdity",
            "satire_target": "opaque corporate controls",
            "subject": "a peacock in a tiny customs inspection booth",
            "visual_metaphor": "a peacock hiding a golden key inside a feather fan",
            "composition": "top-down diagonal airport conveyor composition",
            "style_family": "editorial cut-paper collage",
            "style_description": "layered cut-paper editorial collage with rough torn edges",
            "palette": "acid yellow, cobalt and vermilion",
            "creative_prompt": "A peacock hides a golden key inside its feather fan while passing through a top-down diagonal airport conveyor composition. Render as layered cut-paper editorial collage with rough torn edges, sharp paper shadows and one absurd focal event.",
            "text_budget_words": 0, "source_claim_refs": ["claim://source-01"],
            "fictional_elements": ["talking peacock customs officer"], "disclosure_required": True,
        },
        {
            "image_id": "IMG-02", "creative_angle": "bureaucratic theatre",
            "satire_target": "procedural opacity",
            "subject": "a giraffe wearing an oversized customs badge",
            "visual_metaphor": "a giraffe stamping a passport taller than a skyscraper",
            "composition": "worm's-eye monumental portrait with the stamp dominating foreground",
            "style_family": "surrealist oil painting",
            "style_description": "surrealist oil painting with impossible scale and visible brush texture",
            "palette": "burnt umber, turquoise and dusty rose",
            "creative_prompt": "A giraffe wearing an oversized customs badge stamps a passport taller than a skyscraper. Use a worm's-eye monumental portrait with the stamp dominating foreground, surrealist oil painting with impossible scale and visible brush texture.",
            "text_budget_words": 1, "source_claim_refs": ["claim://source-01"],
            "fictional_elements": ["impossibly large passport"], "disclosure_required": True,
        },
        {
            "image_id": "IMG-03", "creative_angle": "microscopic loophole",
            "satire_target": "the absurdity of hidden logistics",
            "subject": "a single USB stick dwarfed by a cargo container",
            "visual_metaphor": "a tiny USB stick smuggled inside a monumental shipping container",
            "composition": "extreme macro with shallow depth and a tiny object at the frame edge",
            "style_family": "macro product photography",
            "style_description": "hyper-detailed macro product photography with tactile metal and dust",
            "palette": "cold steel, orange safety paint and graphite",
            "creative_prompt": "A tiny USB stick is smuggled inside a monumental shipping container. Extreme macro with shallow depth and a tiny object at the frame edge, hyper-detailed macro product photography with tactile metal and dust, hard industrial side light.",
            "text_budget_words": 0, "source_claim_refs": ["claim://source-01"],
            "fictional_elements": ["oversized fictional shipping container"], "disclosure_required": True,
        },
        {
            "image_id": "IMG-04", "creative_angle": "corporate circus",
            "satire_target": "performative oversight",
            "subject": "a ringmaster balancing a circus tent on one finger",
            "visual_metaphor": "a ringmaster balancing an entire circus tent on a fingertip",
            "composition": "wide theatrical proscenium with a tiny central performer",
            "style_family": "stop-motion clay animation",
            "style_description": "handmade stop-motion clay animation with fingerprints and miniature props",
            "palette": "tomato red, cream and midnight blue",
            "creative_prompt": "A ringmaster balances an entire circus tent on a fingertip. Frame it as a wide theatrical proscenium with a tiny central performer, handmade stop-motion clay animation with fingerprints, miniature props and playful physical shadows.",
            "text_budget_words": 2, "source_claim_refs": ["claim://source-01"],
            "fictional_elements": ["impossible circus performance"], "disclosure_required": True,
        },
        {
            "image_id": "IMG-05", "creative_angle": "surveillance from orbit",
            "satire_target": "the gap between oversight and control",
            "subject": "a satellite observing a miniature customs queue",
            "visual_metaphor": "a satellite using a magnifying glass to inspect one tiny suitcase",
            "composition": "vast orbital wide shot with one bright pinpoint on a dark planet",
            "style_family": "retro science-fiction screen print",
            "style_description": "retro science-fiction screen print with coarse halftone and offset ink",
            "palette": "ultramarine, fluorescent coral and black",
            "creative_prompt": "A satellite uses a magnifying glass to inspect one tiny suitcase. Vast orbital wide shot with one bright pinpoint on a dark planet, retro science-fiction screen print with coarse halftone, offset ink and oversized negative space.",
            "text_budget_words": 0, "source_claim_refs": ["claim://source-01"],
            "fictional_elements": ["satellite magnifying glass"], "disclosure_required": True,
        },
        {
            "image_id": "IMG-06", "creative_angle": "noir investigation",
            "satire_target": "the mystery around corporate process",
            "subject": "a detective examining a briefcase-shaped shadow",
            "visual_metaphor": "a briefcase shadow shaped like a question mark",
            "composition": "low-key noir frame with hard venetian-blind shadows",
            "style_family": "black-and-white film noir still",
            "style_description": "black-and-white film noir still with hard chiaroscuro and grain",
            "palette": "silver gelatin monochrome",
            "creative_prompt": "A detective examines a briefcase shadow shaped like a question mark. Low-key noir frame with hard venetian-blind shadows, black-and-white film noir still with hard chiaroscuro, wet pavement reflections and visible film grain.",
            "text_budget_words": 0, "source_claim_refs": ["claim://source-01"],
            "fictional_elements": ["symbolic question-mark shadow"], "disclosure_required": True,
        },
        {
            "image_id": "IMG-07", "creative_angle": "museum exhibit",
            "satire_target": "the absurdity of institutional secrecy",
            "subject": "a museum curator unveiling a glass case of invisible cargo",
            "visual_metaphor": "an empty glass case with a velvet rope guarding nothing",
            "composition": "symmetrical museum gallery shot with a long receding perspective",
            "style_family": "miniature diorama photography",
            "style_description": "miniature diorama photography with handcrafted architectural details",
            "palette": "sage green, burgundy and warm ivory",
            "creative_prompt": "A museum curator unveils an empty glass case with a velvet rope guarding nothing. Symmetrical museum gallery shot with a long receding perspective, miniature diorama photography with handcrafted architectural details and realistic tiny spotlights.",
            "text_budget_words": 1, "source_claim_refs": ["claim://source-01"],
            "fictional_elements": ["fictional empty exhibit"], "disclosure_required": True,
        },
        {
            "image_id": "IMG-08", "creative_angle": "visual wordplay",
            "satire_target": "the language of corporate assurances",
            "subject": "a rubber stamp melting into a puddle",
            "visual_metaphor": "a rubber approval stamp melting before it touches paper",
            "composition": "dynamic diagonal close-up frozen at the instant of collapse",
            "style_family": "Japanese woodblock print",
            "style_description": "Japanese woodblock print with expressive carved lines and flat color fields",
            "palette": "indigo, persimmon and rice-paper white",
            "creative_prompt": "A rubber approval stamp melts before it touches paper. Dynamic diagonal close-up frozen at the instant of collapse, Japanese woodblock print with expressive carved lines, flat color fields and visible washi texture.",
            "text_budget_words": 0, "source_claim_refs": ["claim://source-01"],
            "fictional_elements": ["impossible melting stamp"], "disclosure_required": True,
        },
    ]


def _spec():
    return {
        "set_id": "news-meme-8",
        "platform": "X",
        "aspect_ratio": "1:1",
        "expected_count": 8,
        "min_style_families": 6,
        "max_per_style_family": 2,
        "max_text_words": 5,
        "max_prompt_similarity": 0.68,
        "source_refs": ["source://news-article"],
        "concepts": _concepts(),
    }


def test_eight_concepts_pass_with_distinct_metaphors_compositions_and_styles():
    report = validate_image_set(_spec())
    assert report["hard_pass"] is True, report["failures"]
    assert report["metrics"]["actual_count"] == 8
    assert report["metrics"]["unique_visual_metaphors"] == 8
    assert report["metrics"]["unique_compositions"] == 8
    assert report["metrics"]["style_family_count"] == 8


def test_prompt_pack_emits_eight_independent_single_generation_prompts():
    pack = compile_image_prompt_pack(_spec())
    assert len(pack["images"]) == 8
    assert pack["generation_policy"] == {
        "generate_each_concept_separately": True,
        "generation_count_per_prompt": 1,
        "shared_prompt_batch_generation": False,
    }
    assert len({item["prompt_sha256"] for item in pack["images"]}) == 8
    assert all(item["generation_count"] == 1 for item in pack["images"])
    assert all(item["visual_metaphor"] in item["prompt"] for item in pack["images"])


def test_duplicate_visual_metaphor_is_rejected():
    payload = _spec()
    payload["concepts"][1]["visual_metaphor"] = payload["concepts"][0]["visual_metaphor"]
    report = validate_image_set(payload)
    assert report["hard_pass"] is False
    assert any(item.startswith("duplicate_visual_metaphor") for item in report["failures"])


def test_repeated_style_family_is_rejected_when_it_breaks_diversity_floor():
    payload = _spec()
    for concept in payload["concepts"][1:]:
        concept["style_family"] = payload["concepts"][0]["style_family"]
    report = validate_image_set(payload)
    assert report["hard_pass"] is False
    assert any(item.startswith("style_family_diversity_below_minimum") for item in report["failures"])
    assert any(item.startswith("style_family_overused") for item in report["failures"])


def test_excessive_in_image_text_is_rejected():
    payload = _spec()
    payload["concepts"][0]["text_budget_words"] = 9
    report = validate_image_set(payload)
    assert report["hard_pass"] is False
    assert "text_budget_exceeded:IMG-01:9>5" in report["failures"]


def test_near_duplicate_prompt_bodies_are_rejected():
    payload = _spec()
    payload["concepts"][1]["creative_prompt"] = payload["concepts"][0]["creative_prompt"]
    report = validate_image_set(payload)
    assert report["hard_pass"] is False
    assert any(item.startswith("prompt_similarity_too_high:IMG-01:IMG-02") for item in report["failures"])


def test_fictional_elements_require_disclosure():
    payload = _spec()
    payload["concepts"][0]["disclosure_required"] = False
    with pytest.raises(ImageSetError, match="fictional elements require"):
        validate_image_set(payload)


def test_expected_image_count_is_exact():
    payload = _spec()
    payload["concepts"].pop()
    report = validate_image_set(payload)
    assert report["hard_pass"] is False
    assert "concept_count_mismatch:7!=8" in report["failures"]


def test_source_refs_are_required():
    payload = _spec()
    payload["source_refs"] = []
    report = validate_image_set(payload)
    assert report["hard_pass"] is False
    assert "source_refs_missing" in report["failures"]


def test_style_family_default_scales_down_for_small_sets():
    payload = _spec()
    payload["expected_count"] = 4
    payload["min_style_families"] = 4
    payload["concepts"] = payload["concepts"][:4]
    report = validate_image_set(payload)
    assert report["hard_pass"] is True, report["failures"]


