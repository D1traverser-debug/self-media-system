"""Owner-scoped content contracts. Pure domain types; no model, provider or task ledger."""
from __future__ import annotations

from dataclasses import dataclass
from math import gcd
import re
from typing import Any, Mapping


class ContentContractError(ValueError):
    """A declared deliverable loses identity, scope or output semantics."""


DELIVERABLE_TYPES = frozenset({
    "SHORT_COPY", "LONG_ARTICLE", "PLATFORM_PACKAGE", "PROMPT_SPEC", "STATIC_IMAGE",
    "MULTI_ASPECT_IMAGE_SET", "MEDIA_TRANSFORM", "ORIGINAL_VIDEO",
    "IDENTITY_ASSET", "ANALYSIS_REPORT",
})
AUDIO_PROMISES = frozenset({"BITSTREAM_IDENTITY", "PCM_IDENTITY", "PERCEPTUAL_SIMILARITY"})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_ALLOWED_FIELDS = frozenset({
    "id", "type", "locale", "platform", "shape", "source_refs", "constraints",
    "acceptance", "prohibitions", "variants",
})


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContentContractError(f"{label} must be a non-empty string")
    return value.strip()


def _text_list(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ContentContractError(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ContentContractError(f"{label} may not contain duplicates")
    return tuple(value)


@dataclass(frozen=True)
class MediaShape:
    width: int
    height: int
    orientation: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "MediaShape":
        if not isinstance(value, Mapping) or set(value) != {"width", "height", "orientation"}:
            raise ContentContractError("shape must specify exactly width, height and orientation")
        width, height, orientation = value["width"], value["height"], value["orientation"]
        if (isinstance(width, bool) or isinstance(height, bool)
                or not isinstance(width, int) or not isinstance(height, int)
                or width < 1 or height < 1 or width > 16384 or height > 16384):
            raise ContentContractError("shape dimensions must be integer pixels in 1..16384")
        expected = "LANDSCAPE" if width > height else "PORTRAIT" if height > width else "SQUARE"
        if orientation != expected:
            raise ContentContractError(f"{width}:{height} requires {expected} orientation")
        return cls(width=width, height=height, orientation=orientation)

    @property
    def ratio(self) -> str:
        divisor = gcd(self.width, self.height)
        return f"{self.width // divisor}:{self.height // divisor}"

    def as_dict(self) -> dict[str, Any]:
        return {"width": self.width, "height": self.height,
                "orientation": self.orientation, "aspect_ratio": self.ratio,
                "ratio_order": "WIDTH:HEIGHT"}


@dataclass(frozen=True)
class DeliverableVariant:
    id: str
    locale: str | None
    platform: str | None
    shape: MediaShape | None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DeliverableVariant":
        if not isinstance(value, Mapping) or set(value) - {"id", "locale", "platform", "shape"}:
            raise ContentContractError("variant must declare only id/locale/platform/shape")
        identifier = _nonempty(value.get("id"), "variant id")
        if not _ID.fullmatch(identifier):
            raise ContentContractError("variant id must be a safe stable identifier")
        locale = _nonempty(value["locale"], "variant locale") if value.get("locale") is not None else None
        platform = _nonempty(value["platform"], "variant platform") if value.get("platform") is not None else None
        shape = MediaShape.from_mapping(value["shape"]) if value.get("shape") is not None else None
        return cls(identifier, locale, platform, shape)

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "locale": self.locale, "platform": self.platform,
                "shape": self.shape.as_dict() if self.shape is not None else None}


@dataclass(frozen=True)
class DeliverableContract:
    id: str
    type: str
    locale: str | None
    platform: str | None
    shape: MediaShape | None
    variants: tuple[DeliverableVariant, ...]
    source_refs: tuple[str, ...]
    prohibitions: tuple[str, ...]
    constraints: dict[str, Any]
    acceptance: dict[str, Any]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DeliverableContract":
        if not isinstance(value, Mapping):
            raise ContentContractError("each deliverable spec must be an object")
        unknown = set(value) - _ALLOWED_FIELDS
        if unknown:
            raise ContentContractError(f"unknown deliverable fields: {sorted(unknown)}")
        identifier = _nonempty(value.get("id"), "deliverable id")
        if not _ID.fullmatch(identifier):
            raise ContentContractError("deliverable id must be a safe stable identifier")
        kind = _nonempty(value.get("type"), "deliverable type")
        if kind not in DELIVERABLE_TYPES:
            raise ContentContractError(f"unsupported deliverable type: {kind}")
        for field in ("locale", "platform"):
            if value.get(field) is not None:
                _nonempty(value[field], field)
        shape = None
        if value.get("shape") is not None:
            shape = MediaShape.from_mapping(value["shape"])
            if kind not in {"STATIC_IMAGE", "MULTI_ASPECT_IMAGE_SET", "MEDIA_TRANSFORM",
                            "ORIGINAL_VIDEO", "IDENTITY_ASSET"}:
                raise ContentContractError("pixel shape requires a visual or media deliverable")
        raw_variants = value.get("variants", [])
        if not isinstance(raw_variants, list):
            raise ContentContractError("variants must be a list")
        variants = tuple(DeliverableVariant.from_mapping(item) for item in raw_variants)
        variant_ids = [item.id for item in variants]
        if len(variant_ids) != len(set(variant_ids)):
            raise ContentContractError("variant IDs must be unique within each deliverable")
        if kind == "MULTI_ASPECT_IMAGE_SET":
            if shape is not None or len(variants) < 2:
                raise ContentContractError("multi-aspect image set requires 2+ named variants and no single top-level shape")
            if any(item.shape is None for item in variants):
                raise ContentContractError("each multi-aspect image variant needs its own explicit shape")
            ratios = [item.shape.ratio for item in variants if item.shape is not None]
            if len(ratios) != len(set(ratios)):
                raise ContentContractError("multi-aspect variants must have distinct aspect ratios")
        elif kind == "STATIC_IMAGE" and len(variants) > 1:
            raise ContentContractError("multiple named image variants require a set deliverable")
        constraints = value.get("constraints", {})
        acceptance = value.get("acceptance", {})
        if not isinstance(constraints, dict) or not isinstance(acceptance, dict):
            raise ContentContractError("constraints and acceptance must be objects")
        from .identity import validate_identity_constraints
        validate_identity_constraints(kind, constraints)
        promise = constraints.get("original_audio_promise")
        if promise is not None and (kind != "MEDIA_TRANSFORM" or promise not in AUDIO_PROMISES):
            raise ContentContractError("original_audio_promise must be a supported MEDIA_TRANSFORM mode")
        return cls(
            id=identifier, type=kind, locale=value.get("locale"), platform=value.get("platform"),
            shape=shape, variants=variants, source_refs=_text_list(value.get("source_refs", []), "source_refs"),
            prohibitions=_text_list(value.get("prohibitions", []), "prohibitions"),
            constraints=dict(constraints), acceptance=dict(acceptance),
        )

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type, "locale": self.locale,
                "platform": self.platform, "shape": self.shape.as_dict() if self.shape else None,
                "variants": [item.as_dict() for item in self.variants],
            "source_refs": list(self.source_refs), "prohibitions": list(self.prohibitions),
                "constraints": dict(self.constraints), "acceptance": dict(self.acceptance),
                "acceptance_assurance": "UNVERIFIED"}


def inspect_declared_deliverables(specs: Any, *, expected_ids: Any = None) -> dict[str, Any]:
    """Validate explicit declarations; do not create tasks, infer skills, or authorize effects."""
    if not isinstance(specs, list) or not specs:
        raise ContentContractError("deliverable_specs must be a non-empty array")
    values = [DeliverableContract.from_mapping(item) for item in specs]
    names = [item.id for item in values]
    if len(names) != len(set(names)):
        raise ContentContractError("deliverable IDs must be unique")
    if expected_ids is not None and expected_ids != names:
        raise ContentContractError("durable project deliverables must equal typed deliverable IDs in order")
    return {"deliverables": [item.as_dict() for item in values],
            "deliverable_ids": names, "selected_task_graph": None,
            "effect_authorized": False, "quality_verified": False,
            "native_caos_activation": "NOT_VERIFIED"}
