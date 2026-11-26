from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from .business import handle_business_object_validate, handle_episode_intent_validate, handle_business_outcome_metrics
from .editorial import handle_editorial_plan_validate, handle_shot_contract_materialize, handle_shot_contract_validate
from .identity import (
    handle_ipos_bundle_inspect, handle_ipos_bundle_import, handle_ipos_shot_bind,
    handle_ipos_continuity_snapshot, handle_ipos_continuity_link,
)
from .lineage import handle_media_graph_initialize
from .media_qa import handle_extended_media_qa
from .motion import handle_timeline_validate, handle_shot_route, handle_continuity_assess
from .visual import handle_programmatic_graphic_render


@dataclass(frozen=True)
class DomainAdapterSpec:
    name: str
    handler: Callable[..., tuple[dict[str, Any], dict[str, Any]]]
    handler_ref: str
    capability_group: str
    required_config: tuple[str, ...]
    output_contract: str
    effect_scope: str
    assurance_ceiling: str
    external_effects: bool
    promotes_candidate: bool
    publishes: bool
    known_gap: str

    def public_record(self) -> dict[str, Any]:
        record = asdict(self)
        record.pop("handler", None)
        record["handler_registered"] = callable(self.handler)
        record["external_effects"] = False
        record["promotes_candidate"] = False
        record["publishes"] = False
        return record


def _spec(name, handler, group, required, output, assurance, gap, *, effect="PROJECT_LOCAL_ARTIFACT_WRITE"):
    return DomainAdapterSpec(
        name=name,
        handler=handler,
        handler_ref=f"{handler.__module__}.{handler.__name__}",
        capability_group=group,
        required_config=tuple(required),
        output_contract=output,
        effect_scope=effect,
        assurance_ceiling=assurance,
        external_effects=False,
        promotes_candidate=False,
        publishes=False,
        known_gap=gap,
    )


DOMAIN_ADAPTERS: dict[str, DomainAdapterSpec] = {
    "business_object_validate": _spec(
        "business_object_validate", handle_business_object_validate, "growth_commercial",
        (), "task-declared JSON business-object artifact", "STRUCTURAL_TYPE_VALIDATION",
        "Schema-valid business objects are not evidence of commercial success.",
    ),
    "episode_intent_validate": _spec(
        "episode_intent_validate", handle_episode_intent_validate, "growth_commercial",
        (), "task-declared JSON episode-intent evidence", "STRUCTURAL_SOURCE_BINDING",
        "Validates an existing program handoff; does not create a program or prove audience demand.",
    ),
    "editorial_plan_validate": _spec(
        "editorial_plan_validate", handle_editorial_plan_validate, "editorial_writing",
        ("editorial_plan_input",), "task-declared JSON editorial-plan validation receipt",
        "STRUCTURAL_PLAN_VALIDATION", "Plan validation is not professional writing or owner acceptance.",
    ),
    "shot_contract_materialize": _spec(
        "shot_contract_materialize", handle_shot_contract_materialize, "motion_production",
        ("editorial_plan_input", "shot_id", "sequence_id"), "task-declared JSON shot contract",
        "STRUCTURAL_CONTRACT_MATERIALIZATION", "A shot contract is not generated or edited media.",
    ),
    "shot_contract_validate": _spec(
        "shot_contract_validate", handle_shot_contract_validate, "motion_production",
        ("shot_contract_input",), "task-declared JSON shot-contract validation receipt",
        "STRUCTURAL_CONTRACT_VALIDATION", "Validation does not prove visual or cinematic quality.",
    ),
    "ipos_bundle_inspect": _spec(
        "ipos_bundle_inspect", handle_ipos_bundle_inspect, "identity_collaboration",
        ("bundle_input",), "task-declared JSON approved-IPOS-bundle readiness receipt",
        "APPROVED_BUNDLE_READINESS_ONLY", "Requires an owner-approved IPOS bundle; never edits IPOS canon.",
    ),
    "media_graph_initialize": _spec(
        "media_graph_initialize", handle_media_graph_initialize, "motion_production",
        (), "task-declared JSON project-local media-graph state", "STRUCTURAL_PROVENANCE_GRAPH",
        "Initializes local graph metadata; does not authenticate external source truth.",
    ),
    "ipos_bundle_import": _spec(
        "ipos_bundle_import", handle_ipos_bundle_import, "identity_collaboration",
        ("bundle_input", "media_graph_input"), "task-declared JSON local import receipt and graph state",
        "APPROVED_BUNDLE_LOCAL_IMPORT_ONLY", "Imports only into the Studio project; no canonical IPOS mutation.",
    ),
    "ipos_shot_bind": _spec(
        "ipos_shot_bind", handle_ipos_shot_bind, "identity_collaboration",
        ("bundle_input", "import_receipt_input", "media_graph_input", "shot_contract_input"),
        "task-declared JSON shot binding and continuity-rules artifacts",
        "APPROVED_IDENTITY_BINDING_ONLY", "Binding metadata does not establish final rendered identity fidelity.",
    ),
    "ipos_continuity_snapshot": _spec(
        "ipos_continuity_snapshot", handle_ipos_continuity_snapshot, "identity_collaboration",
        ("bundle_input", "shot_id"), "task-declared JSON IPOS continuity snapshot",
        "IDENTITY_CONTINUITY_METADATA_ONLY", "Snapshot is a reference contract, not a frame-by-frame visual review.",
    ),
    "ipos_continuity_link": _spec(
        "ipos_continuity_link", handle_ipos_continuity_link, "identity_collaboration",
        ("bundle_input", "from_shot_id", "to_shot_id"), "task-declared JSON IPOS continuity link",
        "IDENTITY_CONTINUITY_METADATA_ONLY", "Link records declared continuity rules, not achieved visual continuity.",
    ),
    "timeline_validate": _spec(
        "timeline_validate", handle_timeline_validate, "motion_production",
        ("timeline_input", "media_graph_input"), "task-declared JSON timeline validation receipt",
        "TIMELINE_METADATA_VALIDATION", "Timeline metadata validation is not a complete video review.",
    ),
    "shot_route": _spec(
        "shot_route", handle_shot_route, "motion_production",
        ("routing_request_input",), "task-declared JSON evidence-bound routing decision",
        "DECISION_SUPPORT_NOT_PROVIDER_EXECUTION", "Does not invoke a generator or prove provider availability.",
    ),
    "extended_media_qa": _spec(
        "extended_media_qa", handle_extended_media_qa, "verification_delivery",
        ("media_input",), "task-declared JSON technical media-QA report",
        "TECHNICAL_MEASUREMENT_NOT_AESTHETIC", "Technical checks do not replace editorial or aesthetic acceptance.",
    ),
    "continuity_assess": _spec(
        "continuity_assess", handle_continuity_assess, "motion_production",
        ("continuity_input",), "task-declared JSON declared-rule continuity assessment",
        "DECLARED_RULE_CONTINUITY_ASSESSMENT", "Assessment is limited to supplied continuity data and rules.",
    ),
    "business_outcome_metrics": _spec(
        "business_outcome_metrics", handle_business_outcome_metrics, "growth_commercial",
        ("outcome_receipt_input",), "task-declared JSON derived outcome metrics",
        "DERIVED_METRICS_NOT_CAUSAL_GROWTH", "Derived metrics do not prove causal growth or commercial lift.",
    ),
    "programmatic_graphic_render": _spec(
        "programmatic_graphic_render", handle_programmatic_graphic_render, "visual_design",
        ("graphic_spec_input", "shot_contract_input", "font_input", "rights_evidence_input",
         "editorial_plan_input", "video_output", "receipt_output"),
        "candidate MP4 plus JSON receipt and optional graph candidate",
        "CANDIDATE_RENDER_NOT_PROMOTION_OR_RELEASE",
        "Local candidate render only; no provider generation, promotion, publication or aesthetic PASS.",
        effect="PROJECT_LOCAL_CANDIDATE_RENDER",
    ),
}

SUPPORTED_DOMAIN_ADAPTERS = frozenset(DOMAIN_ADAPTERS)


def supports_domain_adapter(name: str) -> bool:
    return name in DOMAIN_ADAPTERS


def public_domain_adapter_registry() -> list[dict[str, Any]]:
    return [DOMAIN_ADAPTERS[name].public_record() for name in sorted(DOMAIN_ADAPTERS)]
