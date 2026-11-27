"""Non-downgradable artifact release guards, independent of tools and adapters.

An artifact release is not whole-demand acceptance or permission to publish.
This pure rule must run behind every current artifact release path; external
executors, briefs and CLI options cannot relax its safety floor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ReleaseGuards:
    require_rights: bool
    require_rights_evidence: bool
    require_technical_qa: bool
    allowed_rights: frozenset[str]
    disallowed_relaxations: tuple[str, ...]


def resolve_release_guards(
    policy: Mapping[str, Any], *, artifact_kind: str, media_type: str,
    allowed_rights: Iterable[str], caller_require_rights: bool = True,
) -> ReleaseGuards:
    """Resolve the minimum safety floor from actual artifact type, not claims.

    Strict typing matters: string "false" must not become a truthy policy.
    An existing brief may contain a historically accepted downgrade; it is
    blocked at release rather than silently grandfathered into authorization.
    """
    for name in ("require_rights", "require_rights_evidence", "require_technical_qa"):
        if name in policy and type(policy[name]) is not bool:
            raise ValueError(f"release_policy.{name} must be boolean")
    if type(caller_require_rights) is not bool:
        raise ValueError("caller_require_rights must be boolean")

    video = str(artifact_kind or "").lower() == "video" or str(media_type or "").lower().startswith("video/")
    violations: list[str] = []
    if policy.get("require_rights") is False or caller_require_rights is False:
        violations.append("release_rights_requirement_cannot_be_disabled")
    media = (video or str(media_type or "").lower().startswith(("image/", "audio/"))
             or str(artifact_kind or "").lower() in {
                 "image", "media", "audio", "visual_asset", "sound_asset", "font_asset",
             })
    if media and policy.get("require_rights_evidence") is False:
        violations.append("release_media_rights_evidence_cannot_be_disabled")
    if video and policy.get("require_technical_qa") is False:
        violations.append("release_video_technical_qa_cannot_be_disabled")

    return ReleaseGuards(
        require_rights=True,
        require_rights_evidence=True,
        require_technical_qa=video or policy.get("require_technical_qa", False),
        allowed_rights=frozenset(allowed_rights),
        disallowed_relaxations=tuple(violations),
    )
