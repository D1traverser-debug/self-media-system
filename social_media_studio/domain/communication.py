"""Optional audience-value and response hypotheses for public-facing deliverables."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

class CommunicationIntentError(ValueError):
    """Malformed communication-intent declaration."""

_ACTIONS = frozenset({"SHARE","COMMENT","SAVE","FOLLOW","SUBSCRIBE","LIKE","WATCH_TO_END","CLICK","OTHER"})
_FIELDS = frozenset({"schema_version","audience","value_promise","think","feel","do","primary_action","mechanism","action_rationale","speaker_relation","grounding_refs","assumptions","status"})

def _text(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CommunicationIntentError(f"{field} must be nonempty text")
    return value.strip()

def _text_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise CommunicationIntentError(f"{field} must be a list of nonempty strings")
    result = tuple(x.strip() for x in value)
    if len(result) != len(set(result)):
        raise CommunicationIntentError(f"{field} must not contain duplicates")
    return result

@dataclass(frozen=True)
class CommunicationIntent:
    audience: str
    value_promise: str
    think: str | None
    feel: str | None
    actions: tuple[str, ...]
    primary_action: str | None
    mechanism: str | None
    action_rationale: str | None
    speaker_relation: str | None
    grounding_refs: tuple[str, ...]
    assumptions: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CommunicationIntent":
        if not isinstance(value, Mapping) or value.get("schema_version") != "1.0":
            raise CommunicationIntentError("communication_intent needs schema_version 1.0")
        unknown = set(value) - _FIELDS
        if unknown:
            raise CommunicationIntentError(f"unknown communication_intent fields: {sorted(unknown)}")
        if value.get("status") not in (None, "HYPOTHESIS_UNMEASURED"):
            raise CommunicationIntentError("communication_intent status must remain HYPOTHESIS_UNMEASURED")
        audience = _text(value.get("audience"), "audience")
        value_promise = _text(value.get("value_promise"), "value_promise")
        think = _text(value.get("think"), "think", optional=True)
        feel = _text(value.get("feel"), "feel", optional=True)
        actions = _text_list(value.get("do", []), "do")
        invalid = sorted(set(actions) - _ACTIONS)
        if invalid:
            raise CommunicationIntentError(f"unsupported communication actions: {invalid}")
        primary = _text(value.get("primary_action"), "primary_action", optional=True)
        rationale = _text(value.get("action_rationale"), "action_rationale", optional=True)
        if actions:
            if primary not in actions:
                raise CommunicationIntentError("primary_action must be one of the declared do actions")
            if not rationale:
                raise CommunicationIntentError("a declared action requires action_rationale")
        elif primary is not None or rationale is not None:
            raise CommunicationIntentError("primary_action and action_rationale require a declared do action")
        if not (think or feel or actions):
            raise CommunicationIntentError("communication_intent needs at least one think, feel or do response")
        return cls(
            audience=audience, value_promise=value_promise, think=think, feel=feel,
            actions=actions, primary_action=primary,
            mechanism=_text(value.get("mechanism"), "mechanism", optional=True),
            action_rationale=rationale,
            speaker_relation=_text(value.get("speaker_relation"), "speaker_relation", optional=True),
            grounding_refs=_text_list(value.get("grounding_refs", []), "grounding_refs"),
            assumptions=_text_list(value.get("assumptions", []), "assumptions"),
        )

    @property
    def status(self) -> str:
        return "HYPOTHESIS_UNMEASURED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version":"1.0","audience":self.audience,"value_promise":self.value_promise,
            "think":self.think,"feel":self.feel,"do":list(self.actions),
            "primary_action":self.primary_action,"mechanism":self.mechanism,
            "action_rationale":self.action_rationale,"speaker_relation":self.speaker_relation,
            "grounding_refs":list(self.grounding_refs),"assumptions":list(self.assumptions),
            "status":self.status,
        }
