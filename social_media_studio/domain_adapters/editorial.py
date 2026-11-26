from __future__ import annotations

from .common import *
from ..legacy.editorial_planning import *
from ..legacy.production_os import ReferenceBinding, ShotContract
from ..legacy.programmatic_graphics import shot_contract_from_dict

def editorial_plan_from_dict(payload: Mapping[str, Any]) -> EditorialPlan:
    data = _mapping(payload, "EditorialPlan")
    intent_data = _mapping(data.get("intent"), "EditorialPlan.intent")
    for field in ("evidence_refs", "desired_outcomes", "constraints", "commercial_context_refs"):
        if field in intent_data:
            intent_data[field] = _string_tuple(intent_data[field], f"EditorialPlan.intent.{field}")
    intent = EpisodeIntent(**intent_data)

    claims = []
    for raw in data.get("claims", []):
        item = _mapping(raw, "EditorialPlan.claim")
        item["evidence_refs"] = _string_tuple(item.get("evidence_refs", []), "EditorialPlan.claim.evidence_refs") if item.get("evidence_refs", []) else ()
        claims.append(ClaimSpec(**item))

    beats = []
    for raw in data.get("beats", []):
        item = _mapping(raw, "EditorialPlan.beat")
        for field in ("claim_ids", "depends_on"):
            item[field] = _string_tuple(item.get(field, []), f"EditorialPlan.beat.{field}") if item.get(field, []) else ()
        beats.append(BeatSpec(**item))

    shots = []
    for raw in data.get("shots", []):
        item = _mapping(raw, "EditorialPlan.shot")
        for field in ("source_claim_ids", "continuity_dimensions", "reference_intents", "must_show", "must_avoid"):
            item[field] = _string_tuple(item.get(field, []), f"EditorialPlan.shot.{field}") if item.get(field, []) else ()
        item["allowed_production_modes"] = frozenset(_string_tuple(item.get("allowed_production_modes", []), "EditorialPlan.shot.allowed_production_modes"))
        item["value_vector"] = dict(item.get("value_vector", {}))
        shots.append(ShotIntent(**item))

    return EditorialPlan(
        intent=intent,
        claims=tuple(claims),
        beats=tuple(beats),
        shots=tuple(shots),
        plan_version=str(data["plan_version"]),
        derived_from_version=data.get("derived_from_version"),
        revision_reason=str(data.get("revision_reason", "")),
    )

def validate_shot_against_editorial_plan(plan: EditorialPlan, shot: Any) -> None:
    planned = plan.shot(shot.shot_id)
    if shot.editorial_plan_ref != plan.plan_ref:
        raise DomainAdapterError("ShotContract editorial_plan_ref does not match the exact supplied EditorialPlan")
    if shot.beat_id != planned.beat_id:
        raise DomainAdapterError("ShotContract beat_id does not match the supplied EditorialPlan")
    if tuple(shot.source_claim_ids) != tuple(planned.source_claim_ids):
        raise DomainAdapterError("ShotContract source_claim_ids do not match the supplied EditorialPlan")
    if abs(float(shot.duration_seconds) - float(planned.target_duration_seconds)) > 0.01:
        raise DomainAdapterError("ShotContract duration does not match the supplied EditorialPlan")
    if shot.truth_mode != planned.truth_mode or shot.risk != planned.risk:
        raise DomainAdapterError("ShotContract truth_mode/risk do not match the supplied EditorialPlan")
    permitted_modes = set(planned.allowed_production_modes)
    contract_modes = set(shot.allowed_modes)
    if not contract_modes or not contract_modes.issubset(permitted_modes):
        raise DomainAdapterError(
            "ShotContract allowed_modes exceed the exact EditorialPlan permissions: "
            f"contract={sorted(contract_modes)}, plan={sorted(permitted_modes)}"
        )

def handle_editorial_plan_validate(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    input_name = str(config["editorial_plan_input"])
    plan = editorial_plan_from_dict(_input_json(packet, input_name))
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    summary = {
        "adapter": name,
        "valid": True,
        "plan_ref": plan.plan_ref,
        "episode_id": plan.intent.episode_id,
        "claim_count": len(plan.claims),
        "beat_count": len(plan.beats),
        "shot_count": len(plan.shots),
        "editorial_plan": _jsonable(plan),
    }
    _write_json(path, summary)
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, "valid": True, "plan_ref": plan.plan_ref},
        }
    }
    result = {"adapter": name, "valid": True, "plan_ref": plan.plan_ref}
    return artifact_outputs, result


def handle_shot_contract_materialize(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    plan_name = str(config["editorial_plan_input"])
    plan = editorial_plan_from_dict(_input_json(packet, plan_name))
    references = config.get("references", [])
    references_input = str(config.get("references_input", "")).strip()
    if references_input:
        reference_payload = _input_json(packet, references_input)
        references = reference_payload.get("references", [])
    if not isinstance(references, list) or not all(isinstance(item, dict) for item in references):
        raise DomainAdapterError("shot materialization references must be an array of objects")
    shot = materialize_shot_contract(
        plan,
        shot_id=str(config["shot_id"]),
        sequence_id=str(config["sequence_id"]),
        required_capabilities=frozenset(config.get("required_capabilities", [])),
        quality_targets=dict(config.get("quality_targets", {})),
        references=tuple(ReferenceBinding(**item) for item in references),
        continuity_ref=str(config.get("continuity_ref", "")),
        graceful_degradation=tuple(config.get("graceful_degradation", [])),
        stop_conditions=tuple(config.get("stop_conditions", [])),
        budget_usd=config.get("budget_usd"),
        disclosure_required=bool(config.get("disclosure_required", False)),
    )
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    payload = {"adapter": name, "valid": True, "shot_contract": _jsonable(shot)}
    _write_json(path, payload)
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, "valid": True, "shot_id": shot.shot_id, "editorial_plan_ref": shot.editorial_plan_ref},
        }
    }
    result = {"adapter": name, "valid": True, "shot_id": shot.shot_id, "editorial_plan_ref": shot.editorial_plan_ref}
    return artifact_outputs, result


def handle_shot_contract_validate(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    input_name = str(config["shot_contract_input"])
    shot = shot_contract_from_dict(_input_json(packet, input_name))
    editorial_plan_name = str(config.get("editorial_plan_input", "")).strip()
    if editorial_plan_name:
        plan = editorial_plan_from_dict(_input_json(packet, editorial_plan_name))
        validate_shot_against_editorial_plan(plan, shot)
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    payload = {"adapter": name, "valid": True, "shot_contract": _jsonable(shot)}
    _write_json(path, payload)
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, "valid": True, "shot_id": shot.shot_id},
        }
    }
    result = {"adapter": name, "valid": True, "shot_id": shot.shot_id}
    return artifact_outputs, result


