"""Reusable editorial and platform packaging contracts.

Structural checking only. The text is authored by a human or a current, actual
session tool. This module does not publish, fact-check, infer CTR or judge art.
"""
from __future__ import annotations
import re
from typing import Any, Mapping

class EditorialContractError(ValueError):
    pass

PLATFORMS = frozenset({
    "X", "TIKTOK", "YOUTUBE", "DOUYIN", "WECHAT_CHANNELS",
    "TOUTIAO", "XIAOHONGSHU", "BILIBILI", "OTHER",
})
_LOCALE = re.compile(r"^[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$")
_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")
_TAG = re.compile(r"^#[^\s#]+$")

def _text(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise EditorialContractError(f"{field} must be nonempty text")
    return value.strip()

def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise EditorialContractError(f"{field} needs a safe stable ID")
    return value

def _locale(value: Any) -> str:
    if not isinstance(value, str) or not _LOCALE.fullmatch(value):
        raise EditorialContractError("locale must be an explicit BCP47-like language tag")
    return value

def _norm(text: str) -> str:
    return "".join(ch.casefold() for ch in text if ch.isalnum())

def _tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise EditorialContractError("hashtags must be an explicit list")
    if any(not isinstance(x, str) or not _TAG.fullmatch(x) for x in value):
        raise EditorialContractError("hashtags need leading # and no whitespace")
    if len({x.casefold() for x in value}) != len(value):
        raise EditorialContractError("duplicate hashtags")
    return list(value)

def inspect_platform_package(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping) or data.get("schema_version") != "1.0":
        raise EditorialContractError("platform package needs schema_version 1.0")
    intent = _text(data.get("content_intent"), "content_intent")
    variants = data.get("variants")
    if not isinstance(variants, list) or not variants:
        raise EditorialContractError("platform package must contain platform variants")
    results = []
    seen = set()
    for v in variants:
        if not isinstance(v, Mapping):
            raise EditorialContractError("each variant must be an object")
        identifier = _identifier(v.get("variant_id"), "variant_id")
        if identifier in seen:
            raise EditorialContractError("duplicate platform variant identity")
        seen.add(identifier)
        platform = v.get("platform")
        if platform not in PLATFORMS:
            raise EditorialContractError("unknown platform; use OTHER with an explicit platform name")
        if platform == "OTHER" and not isinstance(v.get("platform_name"), str):
            raise EditorialContractError("OTHER requires platform_name")
        locale = _locale(v.get("locale"))
        fields = {name: _text(v.get(name), name, optional=True)
                  for name in ("title", "description", "cover_copy")}
        if not any(fields.values()):
            raise EditorialContractError("platform variant has no public text or cover copy")
        strings = [(name, _norm(text)) for name, text in fields.items() if text]
        if len({x[1] for x in strings}) != len(strings):
            raise EditorialContractError("title, description and cover_copy cannot repeat exactly")
        tags = _tags(v.get("hashtags", []))
        source_refs = v.get("source_refs", [])
        if (not isinstance(source_refs, list)
                or any(not isinstance(x, str) or not x.strip() for x in source_refs)):
            raise EditorialContractError("source_refs must be a list of source identities")
        results.append({
            "variant_id": identifier, "platform": platform,
            "platform_name": v.get("platform_name") if platform == "OTHER" else None,
            "locale": locale, **fields, "hashtags": tags, "source_refs": list(source_refs),
            "semantic_distinctness_verified": False,
            "platform_spec_current_verified": False,
            "native_language_verified": False,
            "click_through_rate_observed": False,
        })
    return {
        "schema_version": "1.0", "content_intent": intent, "variants": results,
        "structural_status": "PASS", "creative_quality_verified": False,
        "semantic_accuracy_verified": False, "publication_authorized": False,
        "no_automatic_posting": True,
    }

def inspect_long_article(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping) or data.get("schema_version") != "1.0":
        raise EditorialContractError("long article needs schema_version 1.0")
    title = _text(data.get("title"), "article title")
    locale = _locale(data.get("locale"))
    kind = data.get("intent_kind")
    if kind not in {"ARGUMENT", "EXPLAINER", "NARRATIVE", "SATIRE", "REPORTAGE", "PERSONAL_ESSAY"}:
        raise EditorialContractError("article intent_kind must be explicit")
    body = data.get("body")
    sections = data.get("sections", [])
    if not isinstance(sections, list):
        raise EditorialContractError("article sections must be a list")
    if body is not None and not isinstance(body, str):
        raise EditorialContractError("body must be plain text")
    if not (isinstance(body, str) and body.strip()) and not sections:
        raise EditorialContractError("article must contain text body or sections")
    seen = set()
    for section in sections:
        if not isinstance(section, Mapping):
            raise EditorialContractError("article section must be an object")
        sid = _identifier(section.get("section_id"), "section_id")
        if sid in seen:
            raise EditorialContractError("duplicate article section ID")
        seen.add(sid)
        _text(section.get("body"), "section body")
    claims = data.get("factual_claims", [])
    if not isinstance(claims, list):
        raise EditorialContractError("factual_claims must be a list")
    claim_ids = set()
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise EditorialContractError("factual claim must be an object")
        cid = _identifier(claim.get("claim_id"), "claim_id")
        if cid in claim_ids:
            raise EditorialContractError("duplicate factual claim")
        claim_ids.add(cid)
        _text(claim.get("statement"), "factual claim statement")
        refs = claim.get("source_refs", [])
        if not isinstance(refs, list) or any(not isinstance(x, str) or not x for x in refs):
            raise EditorialContractError("factual source refs must be a list")
    visual_slots = data.get("visual_slots", [])
    if not isinstance(visual_slots, list):
        raise EditorialContractError("visual_slots must be a list")
    for item in visual_slots:
        if not isinstance(item, Mapping):
            raise EditorialContractError("visual slot must be an object")
        sid = item.get("section_id")
        if sid is not None and sid not in seen:
            raise EditorialContractError("visual placement references unknown article section")
        _text(item.get("purpose"), "visual purpose")
    return {
        "schema_version": "1.0", "title": title, "locale": locale,
        "intent_kind": kind, "section_count": len(sections),
        "factual_claim_count": len(claims), "visual_slot_count": len(visual_slots),
        "structural_status": "PASS", "fact_check_verified": False,
        "argument_quality_verified": False, "originality_verified": False,
        "native_language_verified": False, "owner_outcome_verified": False,
        "publication_authorized": False,
    }
