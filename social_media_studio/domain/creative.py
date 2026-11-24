"""Task-neutral art-direction and image-prompt contract: provenance, intent and visual QA.

The design contract cannot assert that a generator, editor or reviewer ran,
nor that rendered pixels are beautiful, accurate or legible on a phone.
"""
from __future__ import annotations
from collections.abc import Mapping
import re
from typing import Any

class VisualContractError(ValueError):
    pass

_MODES = frozenset({"PROMPT_ONLY", "SINGLE_IMAGE", "MULTI_ASPECT", "EDIT_EXISTING"})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_DIGEST = re.compile(r"^[0-9a-fA-F]{64}$")

def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise VisualContractError(f"{name} must be a nonempty string")
    return value.strip()

def inspect_visual_direction(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping) or data.get("schema_version") != "1.0":
        raise VisualContractError("visual direction requires schema_version 1.0")
    mode = data.get("mode")
    if mode not in _MODES:
        raise VisualContractError("invalid visual delivery mode")
    deliverable_id = _text(data.get("deliverable_id"), "deliverable_id")
    if not _ID.fullmatch(deliverable_id):
        raise VisualContractError("invalid visual deliverable identity")
    # Intent, not a mandatory film storyboard or a forced prompt-length template.
    intent = _text(data.get("owner_intent"), "owner_intent")
    core = _text(data.get("primary_story_or_subject"), "primary_story_or_subject")
    prompt = data.get("draft_prompt")
    if prompt is not None:
        _text(prompt, "draft_prompt")
    if mode == "PROMPT_ONLY" and prompt is None:
        raise VisualContractError("prompt-only deliverable must contain an actual prompt draft")
    references = data.get("references", [])
    if not isinstance(references, list):
        raise VisualContractError("references must be an array of explicit roles")
    seen = set()
    bound = []
    for item in references:
        if not isinstance(item, Mapping):
            raise VisualContractError("reference must be an object")
        ref = _text(item.get("source_ref"), "reference.source_ref")
        if ref in seen:
            raise VisualContractError("duplicate reference identity; describe roles in one binding")
        seen.add(ref)
        purpose = _text(item.get("role"), "reference.role")
        influences = item.get("allowed_influence")
        denied = item.get("excluded_influence", [])
        if not isinstance(influences, list) or not influences or any(not isinstance(x, str) or not x.strip() for x in influences):
            raise VisualContractError("reference needs declared allowed influence")
        if not isinstance(denied, list) or any(not isinstance(x, str) or not x.strip() for x in denied):
            raise VisualContractError("reference excluded influence must be a list")
        if set(influences) & set(denied):
            raise VisualContractError("reference role permissions are contradictory")
        digest = item.get("source_sha256")
        if digest is not None and (not isinstance(digest, str) or not _DIGEST.fullmatch(digest)):
            raise VisualContractError("reference digest must be a SHA256 hex string")
        bound.append({"source_ref": ref, "role": purpose, "allowed_influence": list(influences),
                      "excluded_influence": list(denied), "source_sha256": digest,
                      "source_bytes_verified": False})
    if mode == "EDIT_EXISTING" and not references:
        raise VisualContractError("an existing-image edit needs the exact image reference and allowed influence")
    candidates = data.get("candidates", [])
    if not isinstance(candidates, list):
        raise VisualContractError("candidate IDs must be an array")
    if len(candidates) != len(set(candidates)) or any(not isinstance(x,str) or not _ID.fullmatch(x) for x in candidates):
        raise VisualContractError("candidate identities must be distinct safe identifiers")
    result = {
        "schema_version": "1.0", "deliverable_id": deliverable_id,
        "mode": mode, "owner_intent": intent, "primary_story_or_subject": core,
        "draft_prompt": prompt, "references": bound,
        "candidate_ids": list(candidates),
        "structural_status": "PASS",
        "selected_task_graph": None, "generation_authorized": False,
        "generated_pixels_observed": False, "semantic_goal_verified": False,
        "composition_verified": False, "aesthetic_quality_verified": False,
        "thumbnail_readability_verified": False, "reference_fidelity_verified": False,
        "independent_review_verified": False,
    }
    return result
