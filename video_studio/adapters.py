from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from video_growth_agent.continuity import (
    ContinuityLink,
    ContinuityRule,
    ContinuitySnapshot,
    assess_continuity,
)
from video_growth_agent.business_metrics import (
    CommercialOutcome,
    EpisodeOutcomeReceipt,
    PlatformPerformanceReceipt,
    ProductionEconomics,
)
from video_growth_agent.editorial_planning import (
    BeatSpec,
    ClaimSpec,
    EditorialPlan,
    EpisodeIntent,
    ShotIntent,
    materialize_shot_contract,
)
from video_growth_agent.engine_routing import (
    CostAwareShotRouter,
    EngineProfile,
    ShotRequest,
)
from video_growth_agent.ip_identity import import_ipos_bundle, inspect_ipos_bundle
from video_growth_agent.production_os import ReferenceBinding
from video_growth_agent.media_graph import MediaGraph
from video_growth_agent.programmatic_graphics import (
    graphic_spec_from_dict,
    register_graph_candidate,
    render_programmatic_graphic,
    shot_contract_from_dict,
)
from video_growth_agent.timeline import (
    TimelineClip,
    TimelineMarker,
    TimelineSpec,
    assert_platform_variant_lineage,
)
from video_growth_agent.media_graph import AssetRef

from .engine import ContractError, StudioEngine, StudioError


class DomainAdapterError(StudioError):
    """A deterministic Video-domain capability adapter rejected its input."""


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_jsonable(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    return value


def _mapping(payload: Any, label: str) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise DomainAdapterError(f"{label} must be a JSON object")
    return dict(payload)


def editorial_plan_from_dict(payload: Mapping[str, Any]) -> EditorialPlan:
    data = _mapping(payload, "EditorialPlan")
    intent_data = _mapping(data.get("intent"), "EditorialPlan.intent")
    for field in ("evidence_refs", "desired_outcomes", "constraints", "commercial_context_refs"):
        if field in intent_data:
            intent_data[field] = tuple(intent_data[field])
    intent = EpisodeIntent(**intent_data)

    claims = []
    for raw in data.get("claims", []):
        item = _mapping(raw, "EditorialPlan.claim")
        item["evidence_refs"] = tuple(item.get("evidence_refs", ()))
        claims.append(ClaimSpec(**item))

    beats = []
    for raw in data.get("beats", []):
        item = _mapping(raw, "EditorialPlan.beat")
        for field in ("claim_ids", "depends_on"):
            item[field] = tuple(item.get(field, ()))
        beats.append(BeatSpec(**item))

    shots = []
    for raw in data.get("shots", []):
        item = _mapping(raw, "EditorialPlan.shot")
        for field in ("source_claim_ids", "continuity_dimensions", "reference_intents", "must_show", "must_avoid"):
            item[field] = tuple(item.get(field, ()))
        item["allowed_production_modes"] = frozenset(item.get("allowed_production_modes", ()))
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


def timeline_spec_from_dict(payload: Mapping[str, Any]) -> TimelineSpec:
    data = _mapping(payload, "TimelineSpec")
    clips = []
    for raw in data.get("clips", []):
        item = _mapping(raw, "TimelineClip")
        ref = item.get("asset_ref")
        if isinstance(ref, str):
            item["asset_ref"] = AssetRef.from_key(ref)
        else:
            item["asset_ref"] = AssetRef(**_mapping(ref, "TimelineClip.asset_ref"))
        item["transform"] = dict(item.get("transform", {}))
        clips.append(TimelineClip(**item))
    markers = tuple(TimelineMarker(**_mapping(raw, "TimelineMarker")) for raw in data.get("markers", []))
    return TimelineSpec(
        timeline_id=str(data["timeline_id"]),
        version_id=str(data["version_id"]),
        context_id=str(data["context_id"]),
        clips=tuple(clips),
        markers=markers,
        derived_from_version=data.get("derived_from_version"),
        edit_reason=str(data.get("edit_reason", "")),
        metadata=dict(data.get("metadata", {})),
    )


def route_shot(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = _mapping(payload, "shot routing request")
    request_data = _mapping(data.get("request"), "request")
    request_data["required_capabilities"] = frozenset(request_data.get("required_capabilities", ()))
    request = ShotRequest(**request_data)
    engines = []
    for raw in data.get("engines", []):
        item = _mapping(raw, "engine profile")
        item["capabilities"] = frozenset(item.get("capabilities", ()))
        item["quality_evidence_refs"] = tuple(item.get("quality_evidence_refs", ()))
        item["pricing_evidence_refs"] = tuple(item.get("pricing_evidence_refs", ()))
        engines.append(EngineProfile(**item))
    if not engines:
        raise DomainAdapterError("shot routing requires at least one measured engine profile")
    decision = CostAwareShotRouter().route(request, engines)
    return _jsonable(decision)


def assess_shot_continuity(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = _mapping(payload, "continuity assessment")
    before_data = _mapping(data.get("before"), "before snapshot")
    after_data = _mapping(data.get("after"), "after snapshot")
    link_data = _mapping(data.get("link"), "continuity link")
    before = ContinuitySnapshot(
        shot_id=str(before_data["shot_id"]),
        dimensions=dict(before_data["dimensions"]),
        canon_refs=tuple(before_data.get("canon_refs", ())),
        evidence_refs=tuple(before_data.get("evidence_refs", ())),
    )
    after = ContinuitySnapshot(
        shot_id=str(after_data["shot_id"]),
        dimensions=dict(after_data["dimensions"]),
        canon_refs=tuple(after_data.get("canon_refs", ())),
        evidence_refs=tuple(after_data.get("evidence_refs", ())),
    )
    rules = tuple(
        ContinuityRule(**{**dict(item), "reason": str(dict(item).get("reason", ""))})
        for item in link_data.get("rules", [])
    )
    link = ContinuityLink(
        from_shot_id=str(link_data["from_shot_id"]),
        to_shot_id=str(link_data["to_shot_id"]),
        rules=rules,
        rationale_refs=tuple(link_data.get("rationale_refs", ())),
    )
    assessment = assess_continuity(
        before, after, link, evidence_refs=tuple(data.get("evidence_refs", ())),
    )
    return {
        "hard_pass": assessment.hard_pass,
        "assessment": _jsonable(assessment),
    }


def outcome_metrics(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = _mapping(payload, "EpisodeOutcomeReceipt")
    platforms = []
    for raw in data.get("platform_receipts", []):
        item = _mapping(raw, "PlatformPerformanceReceipt")
        item["evidence_refs"] = tuple(item.get("evidence_refs", ()))
        platforms.append(PlatformPerformanceReceipt(**item))
    production = ProductionEconomics(**_mapping(data.get("production"), "production"))
    commercial_data = _mapping(data.get("commercial", {}), "commercial")
    commercial_data["evidence_refs"] = tuple(commercial_data.get("evidence_refs", ()))
    commercial = CommercialOutcome(**commercial_data)
    receipt = EpisodeOutcomeReceipt(
        episode_id=str(data["episode_id"]),
        platform_receipts=tuple(platforms),
        production=production,
        commercial=commercial,
        qualitative_evidence_refs=tuple(data.get("qualitative_evidence_refs", ())),
        learning_candidate_refs=tuple(data.get("learning_candidate_refs", ())),
    )
    return {
        "episode_id": receipt.episode_id,
        "derived_metrics": receipt.derived_metrics(),
        "objective_vector": _jsonable(receipt.objective_vector()),
    }


def _input_json(packet: Mapping[str, Any], name: str) -> dict[str, Any]:
    artifact = packet["input_artifacts"].get(name)
    if artifact is None:
        raise DomainAdapterError(f"required declared JSON input is unavailable: {name}")
    path = Path(artifact["path"])
    try:
        return _mapping(json.loads(path.read_text(encoding="utf-8")), f"input {name}")
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainAdapterError(f"cannot read JSON input {name}: {exc}") from exc


def _input_path(packet: Mapping[str, Any], name: str) -> Path:
    artifact = packet["input_artifacts"].get(name)
    if artifact is None:
        raise DomainAdapterError(f"required declared input is unavailable: {name}")
    path = Path(artifact["path"])
    if not path.is_file():
        raise DomainAdapterError(f"declared input file is missing: {name}")
    return path


def _safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    if not safe:
        raise DomainAdapterError("output name cannot be converted to a safe filename")
    return safe[:100]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise DomainAdapterError(f"adapter output already exists; refusing overwrite: {path.name}")
    path.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_claimed_domain_adapter(
    engine: StudioEngine,
    project_id: str,
    task_id: str,
    worker_id: str,
    claim_token: str,
) -> dict[str, Any]:
    """Run one declared local domain adapter inside a current Studio task lease.

    Inputs must be declared task artifacts. Outputs are written into the project
    workspace and registered by the same immutable artifact/lineage transaction
    as any other task completion. This function never promotes a candidate or
    publishes media.
    """
    packet = engine.claimed_packet(project_id, task_id, worker_id, claim_token)
    task = packet["task"]
    requirements = _mapping(task.get("requirements", {}), "task.requirements")
    config = _mapping(requirements.get("domain_adapter"), "task.requirements.domain_adapter")
    name = str(config.get("name", "")).strip()
    if not name:
        raise DomainAdapterError("domain_adapter.name is required")
    outputs = list(task.get("outputs", []))
    if not outputs:
        raise DomainAdapterError("domain adapter task must declare at least one output")
    output_dir = engine._project_dir(project_id) / "artifacts" / "domain-adapters" / _safe_filename(task_id)
    attempt = int(task.get("attempt", 1))
    result: dict[str, Any]

    try:
        if name == "editorial_plan_validate":
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

        elif name == "shot_contract_materialize":
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

        elif name == "shot_contract_validate":
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

        elif name == "ipos_bundle_inspect":
            input_name = str(config["bundle_input"])
            readiness = inspect_ipos_bundle(_input_json(packet, input_name))
            if not readiness.ready:
                raise DomainAdapterError("IPOS bundle is not video-ready: " + "; ".join(readiness.reasons))
            output_name = str(config.get("output_name", outputs[0]))
            path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
            payload = {"adapter": name, "readiness": _jsonable(readiness)}
            _write_json(path, payload)
            artifact_outputs = {
                output_name: {
                    "path": str(path), "kind": "evidence", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE",
                    "metadata": {"adapter": name, "ipos_ready": True, "bundle_ref": readiness.bundle_ref},
                }
            }
            result = {"adapter": name, "ipos_ready": True, "bundle_ref": readiness.bundle_ref}

        elif name == "ipos_bundle_import":
            bundle_name = str(config["bundle_input"])
            graph_name = str(config["media_graph_input"])
            graph = MediaGraph.from_dict(_input_json(packet, graph_name))
            receipt = import_ipos_bundle(
                _input_json(packet, bundle_name),
                graph,
                program_context_id=str(config["program_context_id"]),
            )
            graph_output = str(config["media_graph_output"])
            receipt_output = str(config["receipt_output"])
            if set(outputs) != {graph_output, receipt_output}:
                raise DomainAdapterError("ipos_bundle_import must declare exactly media_graph_output and receipt_output")
            graph_path = output_dir / f"{_safe_filename(graph_output)}-attempt-{attempt}.json"
            receipt_path = output_dir / f"{_safe_filename(receipt_output)}-attempt-{attempt}.json"
            _write_json(graph_path, graph.to_dict())
            _write_json(receipt_path, receipt)
            artifact_outputs = {
                graph_output: {
                    "path": str(graph_path), "kind": "domain_state", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE", "metadata": {"adapter": name, "canon_ref": receipt.canon_ref},
                },
                receipt_output: {
                    "path": str(receipt_path), "kind": "evidence", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE", "metadata": {"adapter": name, "bundle_digest": receipt.bundle_digest},
                },
            }
            result = {"adapter": name, "bundle_ref": receipt.bundle_ref, "imported_asset_count": len(receipt.imported_asset_refs)}

        elif name == "timeline_validate":
            timeline = timeline_spec_from_dict(_input_json(packet, str(config["timeline_input"])))
            graph = MediaGraph.from_dict(_input_json(packet, str(config["media_graph_input"])))
            timeline.validate_against_graph(
                graph, require_promoted_assets=bool(config.get("require_promoted_assets", True)),
            )
            platform = str(config.get("platform", "")).strip()
            master_input = str(config.get("master_timeline_input", "")).strip()
            if platform or master_input:
                if not platform or not master_input:
                    raise DomainAdapterError("platform and master_timeline_input must be supplied together")
                master = timeline_spec_from_dict(_input_json(packet, master_input))
                assert_platform_variant_lineage(master=master, variant=timeline, platform=platform)
            output_name = str(config.get("output_name", outputs[0]))
            path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
            receipt = {
                "adapter": name, "valid": True, "timeline_id": timeline.timeline_id,
                "version_id": timeline.version_id, "duration_seconds": timeline.duration_seconds,
                "clip_count": len(timeline.clips), "asset_refs": [ref.key() for ref in timeline.asset_refs()],
                "platform": platform or None, "derived_from_version": timeline.derived_from_version,
            }
            _write_json(path, receipt)
            artifact_outputs = {
                output_name: {
                    "path": str(path), "kind": "evidence", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE", "metadata": {"adapter": name, "valid": True, "timeline_id": timeline.timeline_id},
                }
            }
            result = receipt

        elif name == "shot_route":
            route = route_shot(_input_json(packet, str(config["routing_request_input"])))
            output_name = str(config.get("output_name", outputs[0]))
            path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
            _write_json(path, {"adapter": name, **route})
            artifact_outputs = {
                output_name: {
                    "path": str(path), "kind": "decision", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE",
                    "metadata": {"adapter": name, "selected_engine_id": route.get("selected_engine_id"), "blocked": route.get("selected_engine_id") is None},
                }
            }
            result = {"adapter": name, "selected_engine_id": route.get("selected_engine_id"), "blocked": route.get("selected_engine_id") is None}

        elif name == "continuity_assess":
            continuity = assess_shot_continuity(_input_json(packet, str(config["continuity_input"])))
            output_name = str(config.get("output_name", outputs[0]))
            path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
            _write_json(path, {"adapter": name, **continuity})
            artifact_outputs = {
                output_name: {
                    "path": str(path), "kind": "evidence", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE",
                    "metadata": {"adapter": name, "hard_pass": continuity["hard_pass"]},
                }
            }
            result = {"adapter": name, "hard_pass": continuity["hard_pass"]}

        elif name == "business_outcome_metrics":
            metrics = outcome_metrics(_input_json(packet, str(config["outcome_receipt_input"])))
            output_name = str(config.get("output_name", outputs[0]))
            path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
            _write_json(path, {"adapter": name, **metrics})
            artifact_outputs = {
                output_name: {
                    "path": str(path), "kind": "evidence", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE",
                    "metadata": {"adapter": name, "episode_id": metrics["episode_id"]},
                }
            }
            result = {"adapter": name, "episode_id": metrics["episode_id"], "derived_metrics": metrics["derived_metrics"]}

        elif name == "programmatic_graphic_render":
            spec_name = str(config["graphic_spec_input"])
            shot_name = str(config["shot_contract_input"])
            font_name = str(config["font_input"])
            rights_name = str(config["rights_evidence_input"])
            spec = graphic_spec_from_dict(_input_json(packet, spec_name))
            shot = shot_contract_from_dict(_input_json(packet, shot_name))
            editorial_plan_name = str(config["editorial_plan_input"])
            editorial_plan = editorial_plan_from_dict(_input_json(packet, editorial_plan_name))
            validate_shot_against_editorial_plan(editorial_plan, shot)
            font_path = _input_path(packet, font_name)
            rights_artifact = packet["input_artifacts"].get(rights_name)
            if rights_artifact is None:
                raise DomainAdapterError(f"rights evidence input is not declared/available: {rights_name}")
            input_names = set(packet["input_artifacts"])
            for binding in shot.references:
                if binding.rights_ref not in input_names:
                    raise DomainAdapterError(f"ShotContract rights_ref must resolve to a declared input artifact: {binding.rights_ref}")
                if binding.consent_ref and binding.consent_ref not in input_names:
                    raise DomainAdapterError(f"ShotContract consent_ref must resolve to a declared input artifact: {binding.consent_ref}")
            video_output = str(config["video_output"])
            receipt_output = str(config["receipt_output"])
            graph_input = str(config.get("media_graph_input", "")).strip()
            graph_output = str(config.get("media_graph_output", "")).strip()
            expected = {video_output, receipt_output}
            if graph_input or graph_output:
                if not graph_input or not graph_output:
                    raise DomainAdapterError("media_graph_input and media_graph_output must be supplied together")
                expected.add(graph_output)
            if shot.references and not graph_input:
                raise DomainAdapterError("referenced shots require media_graph_input for exact promoted-asset validation")
            if set(outputs) != expected:
                raise DomainAdapterError(f"programmatic_graphic_render outputs must be {sorted(expected)}")
            media_path = output_dir / f"{_safe_filename(video_output)}-attempt-{attempt}.mp4"
            receipt = render_programmatic_graphic(shot, spec, output_path=media_path, font_path=font_path)
            receipt_path = output_dir / f"{_safe_filename(receipt_output)}-attempt-{attempt}.json"
            _write_json(receipt_path, receipt)
            artifact_outputs = {
                video_output: {
                    "path": str(media_path), "kind": "video", "media_type": "video/mp4",
                    "rights_status": "OWNED",
                    "metadata": {
                        "adapter": name, "candidate_only": True, "promotion_authorized": False,
                        "release_authorized": False, "media_sha256": receipt["media_sha256"],
                        "shot_contract_digest": receipt["shot_contract_digest"],
                        "graphic_spec_digest": receipt["graphic_spec_digest"],
                        "rights_evidence_refs": [rights_name],
                    },
                },
                receipt_output: {
                    "path": str(receipt_path), "kind": "evidence", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE",
                    "metadata": {"adapter": name, "candidate_only": True, "media_sha256": receipt["media_sha256"]},
                },
            }
            graph_candidate_ref = None
            if graph_input:
                graph = MediaGraph.from_dict(_input_json(packet, graph_input))
                graph_candidate_ref = register_graph_candidate(graph, shot, spec, receipt)
                graph_path = output_dir / f"{_safe_filename(graph_output)}-attempt-{attempt}.json"
                _write_json(graph_path, graph.to_dict())
                artifact_outputs[graph_output] = {
                    "path": str(graph_path), "kind": "domain_state", "media_type": "application/json",
                    "rights_status": "NOT_APPLICABLE",
                    "metadata": {"adapter": name, "candidate_ref": graph_candidate_ref, "candidate_only": True},
                }
            result = {
                "adapter": name, "candidate_only": True, "media_sha256": receipt["media_sha256"],
                "duration_seconds": receipt["duration_seconds"], "width": receipt["width"],
                "height": receipt["height"], "fps": receipt["fps"], "graph_candidate_ref": graph_candidate_ref,
            }

        else:
            raise DomainAdapterError(f"unsupported domain adapter: {name}")

        if set(artifact_outputs) != set(outputs):
            raise DomainAdapterError(f"adapter {name} produced {sorted(artifact_outputs)} but task declares {sorted(outputs)}")
        completed = engine.complete_task(project_id, task_id, worker_id, claim_token, artifact_outputs, result=result)
        return {"status": "COMPLETED", "adapter": name, "result": result, "completion": completed}

    except Exception as exc:
        try:
            engine.fail_task(
                project_id, task_id, worker_id, claim_token,
                {"category": "domain_adapter_failed", "adapter": name, "exception": type(exc).__name__, "message": str(exc)},
                retryable=False,
            )
        except Exception:
            pass
        if isinstance(exc, StudioError):
            raise
        raise DomainAdapterError(f"domain adapter {name} failed: {exc}") from exc
