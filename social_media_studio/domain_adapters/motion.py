from __future__ import annotations

from .common import *
from ..legacy.continuity import *
from ..legacy.model_registry import *
from ..legacy.timeline import *
from ..legacy.media_graph import AssetRef, MediaGraph

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

def route_shot(payload: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Route a shot through the one evidence-bound provider contract used by Studio tasks."""
    try:
        request, engines = _model_routing_request(payload)
        decision = EvidenceBoundModelRouter().route(request, engines, now=now)
    except DomainAdapterError as exc:
        raise DomainAdapterError(f"invalid evidence-bound shot routing contract: {exc}") from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise DomainAdapterError(f"invalid evidence-bound shot routing contract: {exc}") from exc
    route = _jsonable(decision)
    route["blocked"] = decision.blocked
    return route

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

def _string_sequence(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        raise DomainAdapterError(f"{label} must be an array of non-empty strings")
    items = tuple(value)
    if not all(isinstance(item, str) and item.strip() for item in items):
        raise DomainAdapterError(f"{label} must be an array of non-empty strings")
    if len(items) != len(set(items)):
        raise DomainAdapterError(f"{label} must not contain duplicates")
    return items

def _model_routing_request(payload: Mapping[str, Any]) -> tuple[ShotRoutingRequest, tuple[ModelObservation, ...]]:
    data = _mapping(payload, "evidence-bound model routing request")
    request_data = dict(_mapping(data.get("request"), "routing request"))
    request_data["required_capabilities"] = frozenset(
        _string_sequence(request_data.get("required_capabilities", []), "request.required_capabilities")
    )
    request_data["quality_priorities"] = _string_sequence(
        request_data.get("quality_priorities", []), "request.quality_priorities"
    )
    request_data["minimum_quality"] = dict(
        _mapping(request_data.get("minimum_quality"), "request.minimum_quality")
    )
    request_data["quality_weights"] = dict(
        _mapping(request_data.get("quality_weights", {}), "request.quality_weights")
    )
    try:
        request = ShotRoutingRequest(**request_data)
    except (TypeError, ValueError) as exc:
        raise DomainAdapterError(f"invalid routing request: {exc}") from exc

    raw_engines = data.get("engines")
    if not isinstance(raw_engines, list) or not raw_engines:
        raise DomainAdapterError("shot routing requires a non-empty engines array")
    engines = []
    for index, raw_engine in enumerate(raw_engines):
        engine_data = dict(_mapping(raw_engine, f"model observation[{index}]"))
        engine_data["capabilities"] = frozenset(
            _string_sequence(engine_data.get("capabilities", []), f"engines[{index}].capabilities")
        )
        engine_data["resolutions"] = frozenset(
            _string_sequence(engine_data.get("resolutions", []), f"engines[{index}].resolutions")
        )
        for field_name in (
            "quality_evidence_refs", "pricing_evidence_refs", "terms_evidence_refs",
            "availability_evidence_refs",
        ):
            engine_data[field_name] = _string_sequence(
                engine_data.get(field_name, []), f"engines[{index}].{field_name}"
            )
        profiles = []
        raw_profiles = engine_data.get("operation_profiles", [])
        if not isinstance(raw_profiles, list):
            raise DomainAdapterError(f"engines[{index}].operation_profiles must be an array")
        for profile_index, raw_profile in enumerate(raw_profiles):
            profile_data = dict(_mapping(raw_profile, f"operation profile[{profile_index}]"))
            profile_data["capabilities"] = frozenset(
                _string_sequence(profile_data.get("capabilities", []), "operation_profile.capabilities")
            )
            durations = profile_data.get("allowed_durations_seconds", [])
            if not isinstance(durations, (list, tuple)):
                raise DomainAdapterError("operation_profile.allowed_durations_seconds must be a numeric array")
            if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in durations):
                raise DomainAdapterError("operation_profile.allowed_durations_seconds must be a numeric array")
            profile_data["allowed_durations_seconds"] = frozenset(durations)
            profile_data["resolutions"] = frozenset(
                _string_sequence(profile_data.get("resolutions", []), "operation_profile.resolutions")
            )
            profile_data["allowed_source_origins"] = frozenset(
                _string_sequence(profile_data.get("allowed_source_origins", []), "operation_profile.allowed_source_origins")
            )
            profile_data["conditions"] = _string_sequence(
                profile_data.get("conditions", []), "operation_profile.conditions"
            )
            try:
                profiles.append(OperationProfile(**profile_data))
            except (TypeError, ValueError) as exc:
                raise DomainAdapterError(f"invalid operation profile: {exc}") from exc
        engine_data["operation_profiles"] = tuple(profiles)
        observations = {}
        for dimension, raw_observation in _mapping(
            engine_data.get("quality_observations", {}), "quality_observations"
        ).items():
            observation_data = dict(_mapping(raw_observation, f"quality observation {dimension}"))
            observation_data["evidence_refs"] = _string_sequence(
                observation_data.get("evidence_refs", []), f"quality_observation[{dimension}].evidence_refs"
            )
            try:
                observations[str(dimension)] = QualityObservation(**observation_data)
            except (TypeError, ValueError) as exc:
                raise DomainAdapterError(f"invalid quality observation {dimension}: {exc}") from exc
        engine_data["quality_observations"] = observations
        try:
            engines.append(ModelObservation(**engine_data))
        except (TypeError, ValueError) as exc:
            raise DomainAdapterError(f"invalid model observation {index}: {exc}") from exc
    return request, tuple(engines)

def handle_timeline_validate(engine, project_id, packet, config, outputs, output_dir, attempt, name):
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
    return artifact_outputs, result


def handle_shot_route(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    now_value = str(config.get("now", "")).strip()
    now = datetime.fromisoformat(now_value.replace("Z", "+00:00")) if now_value else None
    route = route_shot(
        _input_json(packet, str(config["routing_request_input"])),
        now=now,
    )
    if route["blocked"] and config.get("block_if_no_engine", True):
        raise DomainAdapterError(
            "shot routing blocked: no current model observation satisfies operation profile, "
            "commercial terms, provenance, calibrated quality, evidence freshness and budget policy: "
            + str(route.get("blocked_reason"))
        )
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    _write_json(path, {"adapter": name, **route})
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "decision", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {
                "adapter": name, "selected_engine_id": route.get("selected_engine_id"),
                "blocked": route["blocked"], "blocked_reason": route.get("blocked_reason"),
                "pareto_front": route.get("pareto_front", []),
            },
        }
    }
    result = {
        "adapter": name, "selected_engine_id": route.get("selected_engine_id"),
        "blocked": route["blocked"], "blocked_reason": route.get("blocked_reason"),
        "pareto_front": route.get("pareto_front", []),
    }
    return artifact_outputs, result


def handle_continuity_assess(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    continuity = assess_shot_continuity(_input_json(packet, str(config["continuity_input"])))
    if not continuity["hard_pass"] and config.get("block_on_hard_fail", True):
        violations = continuity["assessment"]["violations"]
        raise DomainAdapterError("hard continuity violation(s): " + json.dumps(violations, ensure_ascii=False))
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
    return artifact_outputs, result


