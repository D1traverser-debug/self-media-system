"""Contracts and deterministic diversity gates for multi-image social assets.

This module validates creative concepts before generation. It does not pretend
that prompt diversity proves visual diversity; generated images still require
an independent collection-level visual review.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import re
import unicodedata
from typing import Any, Mapping


class ImageSetError(ValueError):
    """Raised when an image-set contract is malformed or fails a hard gate."""


_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "into", "is", "it", "its", "of", "on", "or", "that", "the", "their",
    "this", "to", "with", "without", "image", "picture", "visual", "scene",
    "style", "composition", "create", "show", "showing", "single", "standalone",
}


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ImageSetError(f"{label} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ImageSetError(f"{label} must be an array of non-empty strings")
    return tuple(item.strip() for item in value)


def _normalise(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s-]", " ", text)).strip()


def _tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[\w-]+", _normalise(value))
        if len(token) > 2 and token not in _STOP_WORDS
    }


def _jaccard(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class ImageConcept:
    image_id: str
    creative_angle: str
    satire_target: str
    subject: str
    visual_metaphor: str
    composition: str
    style_family: str
    style_description: str
    palette: str
    creative_prompt: str
    text_budget_words: int
    source_claim_refs: tuple[str, ...] = ()
    fictional_elements: tuple[str, ...] = ()
    disclosure_required: bool = False

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ImageConcept":
        if not isinstance(payload, Mapping):
            raise ImageSetError("each image concept must be an object")
        data = dict(payload)
        for field in (
            "image_id", "creative_angle", "satire_target", "subject",
            "visual_metaphor", "composition", "style_family",
            "style_description", "palette", "creative_prompt",
        ):
            data[field] = _required_text(data.get(field), f"concept.{field}")
        data["source_claim_refs"] = _string_list(
            data.get("source_claim_refs", []), "concept.source_claim_refs"
        )
        data["fictional_elements"] = _string_list(
            data.get("fictional_elements", []), "concept.fictional_elements"
        )
        budget = data.get("text_budget_words")
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            raise ImageSetError("concept.text_budget_words must be a non-negative integer")
        data["disclosure_required"] = data.get("disclosure_required", False)
        if not isinstance(data["disclosure_required"], bool):
            raise ImageSetError("concept.disclosure_required must be boolean")
        if data["fictional_elements"] and not data["disclosure_required"]:
            raise ImageSetError(
                f"{data['image_id']}: fictional elements require an explicit disclosure gate"
            )
        allowed = {
            "image_id", "creative_angle", "satire_target", "subject",
            "visual_metaphor", "composition", "style_family",
            "style_description", "palette", "creative_prompt",
            "text_budget_words", "source_claim_refs", "fictional_elements",
            "disclosure_required",
        }
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise ImageSetError(f"concept has unsupported fields: {unknown}")
        try:
            return cls(**data)
        except TypeError as exc:
            raise ImageSetError(f"invalid image concept: {exc}") from exc


@dataclass(frozen=True)
class ImageSetSpec:
    set_id: str
    platform: str
    aspect_ratio: str
    expected_count: int
    min_style_families: int
    max_per_style_family: int
    max_text_words: int
    max_prompt_similarity: float
    source_refs: tuple[str, ...]
    concepts: tuple[ImageConcept, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ImageSetSpec":
        if not isinstance(payload, Mapping):
            raise ImageSetError("image-set root must be an object")
        data = dict(payload)
        for field in ("set_id", "platform", "aspect_ratio"):
            data[field] = _required_text(data.get(field), f"image_set.{field}")
        data["source_refs"] = _string_list(data.get("source_refs", []), "image_set.source_refs")
        raw_concepts = data.get("concepts")
        if not isinstance(raw_concepts, list):
            raise ImageSetError("image_set.concepts must be an array")
        data["concepts"] = tuple(ImageConcept.from_dict(item) for item in raw_concepts)
        defaults = {
            "expected_count": 8,
            "min_style_families": 6,
            "max_per_style_family": 2,
            "max_text_words": 5,
            "max_prompt_similarity": 0.68,
        }
        for field, default in defaults.items():
            data.setdefault(field, default)
        for field in ("expected_count", "min_style_families", "max_per_style_family", "max_text_words"):
            value = data[field]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ImageSetError(f"image_set.{field} must be a non-negative integer")
        threshold = data["max_prompt_similarity"]
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 < float(threshold) < 1:
            raise ImageSetError("image_set.max_prompt_similarity must be between 0 and 1")
        allowed = {
            "set_id", "platform", "aspect_ratio", "expected_count",
            "min_style_families", "max_per_style_family", "max_text_words",
            "max_prompt_similarity", "source_refs", "concepts",
        }
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise ImageSetError(f"image-set has unsupported fields: {unknown}")
        try:
            return cls(**data)
        except TypeError as exc:
            raise ImageSetError(f"invalid image-set contract: {exc}") from exc


def validate_image_set(payload: Mapping[str, Any] | ImageSetSpec) -> dict[str, Any]:
    """Return a deterministic contract/diversity report; does not inspect pixels."""
    spec = payload if isinstance(payload, ImageSetSpec) else ImageSetSpec.from_dict(payload)
    failures: list[str] = []
    concepts = spec.concepts

    if spec.expected_count < 1:
        failures.append("expected_count_must_be_positive")
    if len(concepts) != spec.expected_count:
        failures.append(f"concept_count_mismatch:{len(concepts)}!={spec.expected_count}")
    if spec.min_style_families > spec.expected_count:
        failures.append("min_style_families_exceeds_expected_count")
    if spec.max_per_style_family < 1:
        failures.append("max_per_style_family_must_be_positive")
    if not spec.source_refs:
        failures.append("source_refs_missing")

    for field in ("image_id", "creative_angle", "visual_metaphor", "composition"):
        values = [_normalise(getattr(item, field)) for item in concepts]
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            failures.append(f"duplicate_{field}:{duplicates}")

    style_counts = Counter(_normalise(item.style_family) for item in concepts)
    if len(style_counts) < spec.min_style_families:
        failures.append(f"style_family_diversity_below_minimum:{len(style_counts)}<{spec.min_style_families}")
    for style, count in sorted(style_counts.items()):
        if count > spec.max_per_style_family:
            failures.append(f"style_family_overused:{style}:{count}>{spec.max_per_style_family}")

    for concept in concepts:
        if concept.text_budget_words > spec.max_text_words:
            failures.append(
                f"text_budget_exceeded:{concept.image_id}:{concept.text_budget_words}>{spec.max_text_words}"
            )
        prompt_tokens = _tokens(concept.creative_prompt)
        for field in ("visual_metaphor", "composition", "style_description"):
            required_tokens = _tokens(getattr(concept, field))
            if required_tokens and len(required_tokens & prompt_tokens) / len(required_tokens) < 0.5:
                failures.append(f"prompt_does_not_encode_{field}:{concept.image_id}")
        lowered = concept.creative_prompt.casefold()
        if any(term in lowered for term in ("same style as above", "same composition as", "repeat the previous image")):
            failures.append(f"cross_image_reference_not_standalone:{concept.image_id}")

    similarity_pairs: list[dict[str, Any]] = []
    for index, left in enumerate(concepts):
        for right in concepts[index + 1:]:
            similarity = _jaccard(left.creative_prompt, right.creative_prompt)
            similarity_pairs.append({
                "left": left.image_id,
                "right": right.image_id,
                "jaccard": round(similarity, 4),
            })
            if similarity > float(spec.max_prompt_similarity):
                failures.append(
                    f"prompt_similarity_too_high:{left.image_id}:{right.image_id}:{similarity:.4f}"
                )

    return {
        "schema_version": "1.0",
        "set_id": spec.set_id,
        "hard_pass": not failures,
        "failures": failures,
        "metrics": {
            "expected_count": spec.expected_count,
            "actual_count": len(concepts),
            "unique_visual_metaphors": len({_normalise(item.visual_metaphor) for item in concepts}),
            "unique_compositions": len({_normalise(item.composition) for item in concepts}),
            "style_family_count": len(style_counts),
            "style_family_counts": dict(sorted(style_counts.items())),
            "max_prompt_similarity": max((item["jaccard"] for item in similarity_pairs), default=0.0),
            "max_text_words": max((item.text_budget_words for item in concepts), default=0),
        },
        "pairwise_prompt_similarity": similarity_pairs,
    }


def compile_image_prompt_pack(payload: Mapping[str, Any] | ImageSetSpec) -> dict[str, Any]:
    """Compile one complete, standalone prompt per concept; generation count is always one."""
    spec = payload if isinstance(payload, ImageSetSpec) else ImageSetSpec.from_dict(payload)
    report = validate_image_set(spec)
    if not report["hard_pass"]:
        raise ImageSetError("image-set hard gate failed: " + "; ".join(report["failures"]))

    images = []
    for concept in spec.concepts:
        prompt = (
            f"Create exactly ONE standalone {spec.aspect_ratio} image for {concept.image_id}. "
            f"Main subject: {concept.subject}. "
            f"Creative angle: {concept.creative_angle}. "
            f"Visual metaphor: {concept.visual_metaphor}. "
            f"Composition: {concept.composition}. "
            f"Art direction: {concept.style_description} "
            f"(style family: {concept.style_family}). "
            f"Palette: {concept.palette}. "
            f"Satire target: {concept.satire_target}. "
            f"{concept.creative_prompt.strip()} "
            f"Keep in-image text to at most {concept.text_budget_words} words. "
            "Do not create a collage, grid, contact sheet or multi-panel sheet. "
            "Do not reuse a generic template; this is one complete, independent concept."
        )
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        images.append({
            "image_id": concept.image_id,
            "style_family": concept.style_family,
            "visual_metaphor": concept.visual_metaphor,
            "composition": concept.composition,
            "text_budget_words": concept.text_budget_words,
            "source_claim_refs": list(concept.source_claim_refs),
            "fictional_elements": list(concept.fictional_elements),
            "disclosure_required": concept.disclosure_required,
            "generation_count": 1,
            "prompt_sha256": digest,
            "prompt": prompt,
        })

    return {
        "schema_version": "1.0",
        "set_id": spec.set_id,
        "platform": spec.platform,
        "aspect_ratio": spec.aspect_ratio,
        "generation_policy": {
            "generate_each_concept_separately": True,
            "generation_count_per_prompt": 1,
            "shared_prompt_batch_generation": False,
        },
        "diversity_report": report,
        "images": images,
    }


def image_set_report_json(payload: Mapping[str, Any] | ImageSetSpec) -> str:
    return json.dumps(validate_image_set(payload), ensure_ascii=False, indent=2) + "\n"


def image_prompt_pack_json(payload: Mapping[str, Any] | ImageSetSpec) -> str:
    return json.dumps(compile_image_prompt_pack(payload), ensure_ascii=False, indent=2) + "\n"
