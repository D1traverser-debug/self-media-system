from __future__ import annotations

from .common import *
from social_media_studio.legacy.business_metrics import *
from social_media_studio.legacy.business_objects import *
from social_media_studio.legacy.editorial_planning import EpisodeIntent

def business_object_from_dict(object_type: str, payload: Mapping[str, Any]) -> Any:
    classes = {
        "ContentPortfolioItem": (ContentPortfolioItem, ("topic_evidence_refs","commercial_adjacency_categories","distinctive_asset_opportunities")),
        "DistinctiveAssetObservation": (DistinctiveAssetObservation, ("evidence_refs","qualitative_refs")),
        "CommercialFit": (CommercialFit, ("advertiser_categories","integration_surfaces","product_truth_requirements","prohibited_integration_forms","measurement_plan_refs","evidence_refs")),
        "RightsPackage": (RightsPackage, ("territories","exclusivity_categories","usage_constraints","evidence_refs")),
        "CommercialOfferCandidate": (CommercialOfferCandidate, ("deliverables","pricing_evidence_refs")),
        "BusinessHypothesisDecision": (BusinessHypothesisDecision, ("subject_ids","evidence_refs","counterexample_refs","followup_measurement_refs")),
    }
    selected=classes.get(object_type)
    if selected is None: raise DomainAdapterError(f"unsupported shared business object type: {object_type}")
    cls, tuple_fields=selected; data=dict(_mapping(payload,object_type))
    for field_name in tuple_fields:
        raw=data.get(field_name,())
        if not isinstance(raw,(list,tuple)): raise DomainAdapterError(f"{object_type}.{field_name} must be an array")
        data[field_name]=tuple(raw)
    try: return cls(**data)
    except (TypeError,ValueError) as exc: raise DomainAdapterError(f"invalid {object_type}: {exc}") from exc

def program_episode_handoff_to_intent(payload: Mapping[str, Any], *, expected_program_id: str | None = None) -> dict[str, Any]:
    data=_mapping(payload,"Program -> Episode handoff")
    if data.get("schema_version")!="1.0" or data.get("handoff_type")!="VIDEO_PROGRAM_TO_EPISODE": raise DomainAdapterError("Program -> Episode handoff must use schema_version 1.0 and VIDEO_PROGRAM_TO_EPISODE")
    program_id=str(data.get("program_id") or "").strip()
    if not program_id or (expected_program_id and program_id!=expected_program_id): raise DomainAdapterError("Program -> Episode handoff has the wrong or missing program_id")
    if str(data.get("source_project_id") or "").strip()!=program_id: raise DomainAdapterError("handoff source_project_id must match program_id")
    bindings=data.get("source_artifact_bindings")
    if not isinstance(bindings,list) or not bindings: raise DomainAdapterError("handoff requires source_artifact_bindings")
    by_name={}
    for raw in bindings:
        item=_mapping(raw,"source_artifact_binding"); name=str(item.get("name") or "").strip(); aid=str(item.get("artifact_id") or "").strip(); digest=str(item.get("sha256") or "").strip().lower(); version=item.get("version")
        if not name or not aid or not isinstance(version,int) or version<1: raise DomainAdapterError("each source artifact binding requires name, artifact_id and positive version")
        if not re.fullmatch(r"[0-9a-f]{64}",digest): raise DomainAdapterError(f"source artifact binding has an invalid SHA-256 digest: {name}")
        if name in by_name: raise DomainAdapterError(f"duplicate source artifact binding: {name}")
        by_name[name]=item
    required={"portfolio-allocation-decision","pilot-topic-slate-decision","production-strategy","commercial-production-constraints","growth-baseline"}
    missing=sorted(required-set(by_name))
    if missing: raise DomainAdapterError(f"handoff is missing required source artifact bindings: {missing}")
    raw_intent=dict(_mapping(data.get("episode_intent"),"episode_intent"))
    for field_name in ("evidence_refs","desired_outcomes","commercial_context_refs","constraints"):
        value=raw_intent.get(field_name,())
        if not isinstance(value,(list,tuple)): raise DomainAdapterError(f"episode_intent.{field_name} must be an array")
        raw_intent[field_name]=tuple(value)
    try: intent=EpisodeIntent(**raw_intent)
    except (TypeError,ValueError) as exc: raise DomainAdapterError(f"invalid EpisodeIntent in Program handoff: {exc}") from exc
    if str(data.get("episode_id") or "").strip()!=intent.episode_id or str(data.get("series_id") or "").strip()!=intent.series_id: raise DomainAdapterError("handoff episode_id/series_id must match EpisodeIntent")
    identity=_mapping(data.get("identity_usage",{}),"identity_usage"); mode=identity.get("mode")
    if mode=="NON_CHARACTER":
        if not str(identity.get("reason") or "").strip(): raise DomainAdapterError("NON_CHARACTER handoff must explain why identity usage is excluded")
        if any(identity.get(k) for k in ("bundle_ref","canon_ref","approval_ref")): raise DomainAdapterError("NON_CHARACTER handoff cannot claim IPOS identity approvals")
    elif mode=="IPOS_APPROVED":
        missing_identity=[k for k in ("bundle_ref","canon_ref","approval_ref","rights_evidence_refs") if not identity.get(k)]
        if missing_identity: raise DomainAdapterError(f"IPOS_APPROVED handoff is missing identity evidence: {missing_identity}")
    else: raise DomainAdapterError("identity_usage.mode must be NON_CHARACTER or IPOS_APPROVED")
    return {"schema_version":"1.0","handoff_type":"VIDEO_PROGRAM_TO_EPISODE","program_id":program_id,"source_project_id":program_id,"episode_id":intent.episode_id,"series_id":intent.series_id,"episode_intent":_jsonable(intent),"identity_usage":dict(identity),"source_artifact_bindings":[dict(by_name[n]) for n in sorted(by_name)],"portfolio_decision_ref":dict(by_name["portfolio-allocation-decision"]),"topic_decision_ref":dict(by_name["pilot-topic-slate-decision"]),"production_strategy_ref":dict(by_name["production-strategy"]),"commercial_constraints_ref":dict(by_name["commercial-production-constraints"])}

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

def handle_business_object_validate(project_id, packet, config, outputs, output_dir, attempt, name):
    object_type=str(config.get("object_type","")).strip(); input_name=str(config.get("input_name","")).strip()
    obj=business_object_from_dict(object_type,_input_json(packet,input_name)); output_name=str(config.get("output_name",outputs[0]))
    path=output_dir/f"{_safe_filename(output_name)}-attempt-{attempt}.json"; _write_json(path,{"schema_version":"1.0","adapter":name,"object_type":object_type,"object":_jsonable(obj)})
    identity_field={"ContentPortfolioItem":"item_id","DistinctiveAssetObservation":"asset_id","CommercialFit":"fit_id","RightsPackage":"package_id","CommercialOfferCandidate":"offer_id","BusinessHypothesisDecision":"decision_id"}[object_type]
    artifact_outputs={output_name:{"path":str(path),"kind":"business_object","media_type":"application/json","rights_status":"NOT_APPLICABLE","metadata":{"adapter":name,"object_type":object_type,"object_id":getattr(obj,identity_field)}}}
    result={"adapter":name,"object_type":object_type,"object_id":getattr(obj,identity_field)}
    return artifact_outputs, result


def handle_episode_intent_validate(project_id, packet, config, outputs, output_dir, attempt, name):
    handoff_input = str(config.get("handoff_input", "")).strip()
    expected_program_id = str(config.get("program_id") or "").strip() or None
    raw_handoff = _input_json(packet, handoff_input)
    if config.get("require_validated_transfer") is True:
        imported = packet["input_artifacts"].get(handoff_input)
        if imported is None:
            raise DomainAdapterError(f"validated Program handoff input is unavailable: {handoff_input}")
        transfer = _mapping(imported.get("metadata", {}).get("cross_project_transfer"), "cross_project_transfer")
        target_project_id = project_id
        if transfer.get("schema_version") != "1.0" or transfer.get("transfer_mode") != "IMMUTABLE_COPY":
            raise DomainAdapterError("Episode handoff must arrive through a schema 1.0 immutable cross-project transfer")
        if transfer.get("source_project_id") != expected_program_id:
            raise DomainAdapterError("transferred Episode handoff has the wrong source Program")
        if transfer.get("target_project_id") != target_project_id or transfer.get("target_artifact_name") != handoff_input:
            raise DomainAdapterError("transferred Episode handoff target identity does not match this Episode project/input")
        if transfer.get("source_artifact_name") != str(config.get("source_artifact_name", "validated-episode-intent")):
            raise DomainAdapterError("transferred Episode handoff is not the validated Program artifact")
        if transfer.get("source_sha256") != imported.get("sha256"):
            raise DomainAdapterError("transferred Episode handoff digest does not match its source transfer receipt")
        if not str(transfer.get("source_artifact_id") or "").strip() or not isinstance(transfer.get("source_artifact_version"), int):
            raise DomainAdapterError("transferred Episode handoff is missing exact source artifact identity")
        source_validation = _mapping(raw_handoff.get("source_validation"), "source_validation")
        if source_validation.get("schema_version") != "1.0" or source_validation.get("status") != "PASS":
            raise DomainAdapterError("Episode handoff lacks a passing source Program validation receipt")
        if source_validation.get("validator") != "social_media_studio.adapters.episode_intent_validate":
            raise DomainAdapterError("Episode handoff source validation was not produced by the registered Program validator")
        if source_validation.get("source_project_id") != expected_program_id:
            raise DomainAdapterError("Episode handoff source validation belongs to a different Program")
        if source_validation.get("source_artifact_bindings") != raw_handoff.get("source_artifact_bindings"):
            raise DomainAdapterError("Episode handoff source validation does not match the embedded artifact bindings")
        handoff = program_episode_handoff_to_intent(raw_handoff, expected_program_id=expected_program_id)
        handoff["source_validation"] = source_validation
        handoff["cross_project_transfer"] = transfer
    else:
        handoff = program_episode_handoff_to_intent(raw_handoff, expected_program_id=expected_program_id)
        source_names = config.get("source_artifact_inputs")
        if not isinstance(source_names, list) or not source_names or len(source_names) != len(set(source_names)):
            raise DomainAdapterError("Program handoff validation requires unique source_artifact_inputs")
        bindings = {item["name"]: item for item in handoff["source_artifact_bindings"]}
        if set(source_names) != set(bindings):
            raise DomainAdapterError("source_artifact_inputs must exactly match the handoff's source_artifact_bindings")
        verified = []
        for source_name in sorted(source_names):
            actual = packet["input_artifacts"].get(source_name)
            binding = bindings[source_name]
            if actual is None:
                raise DomainAdapterError(f"Program source artifact is not bound as a declared input: {source_name}")
            if (
                binding["artifact_id"] != actual.get("artifact_id")
                or binding["version"] != actual.get("version")
                or binding["sha256"].lower() != str(actual.get("sha256", "")).lower()
            ):
                raise DomainAdapterError(f"Program handoff source binding does not match the exact current artifact: {source_name}")
            verified.append({
                "name": source_name, "artifact_id": actual["artifact_id"],
                "version": actual["version"], "sha256": actual["sha256"],
            })
        handoff["source_validation"] = {
            "schema_version": "1.0", "status": "PASS",
            "validator": "social_media_studio.adapters.episode_intent_validate",
            "source_project_id": handoff["program_id"],
            "source_artifact_bindings": verified,
        }
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    _write_json(path, handoff)
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "episode_intent", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {
                "adapter": name, "program_id": handoff["program_id"],
                "episode_id": handoff["episode_id"], "series_id": handoff["series_id"],
                "identity_usage_mode": handoff["identity_usage"]["mode"],
                "source_validation_status": handoff["source_validation"]["status"],
                "cross_project_transfer_verified": bool(handoff.get("cross_project_transfer")),
            },
        }
    }
    result = {
        "adapter": name, "program_id": handoff["program_id"],
        "episode_id": handoff["episode_id"], "series_id": handoff["series_id"],
        "identity_usage_mode": handoff["identity_usage"]["mode"],
        "source_validation_status": handoff["source_validation"]["status"],
        "cross_project_transfer_verified": bool(handoff.get("cross_project_transfer")),
    }
    return artifact_outputs, result


def business_observation_metrics(payload, packet, receipt_input):
    """Derive scoped non-video observations from exact imported JSON inputs.

    A source value and byte binding is not proof of platform authenticity,
    metric semantics, causation, performance improvement or commercial success.
    """
    import math

    data = _mapping(payload, "business observation")
    allowed = {"schema_version", "subject", "window", "metrics", "ratios"}
    if set(data) - allowed or data.get("schema_version") != "SMS_BUSINESS_OBSERVATION_V1":
        raise DomainAdapterError("invalid business observation schema")
    subject = _mapping(data.get("subject"), "observation subject")
    if set(subject) - {"kind", "id", "platform"} or subject.get("kind") not in (
        "ACCOUNT", "CONTENT", "CAMPAIGN", "OFFER", "PORTFOLIO",
    ):
        raise DomainAdapterError("invalid observation subject kind or fields")
    def required_text(value, label):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise DomainAdapterError(f"{label} must be nonempty exact text")
        return value
    required_text(subject.get("id"), "subject id")
    if "platform" in subject:
        required_text(subject["platform"], "subject platform")
    window = _mapping(data.get("window"), "observation window")
    if set(window) != {"start", "end"}:
        raise DomainAdapterError("observation window requires exact start/end")
    try:
        start, end = (datetime.fromisoformat(required_text(window[k], k)) for k in ("start", "end"))
        if start.utcoffset() is None or end.utcoffset() is None or end <= start:
            raise ValueError("invalid window")
    except (ValueError, OverflowError) as exc:
        raise DomainAdapterError("observation window must have timezone-aware increasing ISO timestamps") from exc

    entries = data.get("metrics")
    if not isinstance(entries, list) or not entries:
        raise DomainAdapterError("business observation requires declared metric entries")
    source_cache = {}
    by_id = {}
    for raw in entries:
        metric = _mapping(raw, "metric")
        if set(metric) - {"id", "unit", "semantics", "source", "unavailable_reason"}:
            raise DomainAdapterError("unknown metric fields")
        key = required_text(metric.get("id"), "metric id")
        if key in by_id:
            raise DomainAdapterError("duplicate metric id")
        unit = required_text(metric.get("unit"), "metric unit")
        semantics = required_text(metric.get("semantics"), "metric semantics")
        record = {"id": key, "unit": unit, "semantics": semantics}
        if ("source" in metric) == ("unavailable_reason" in metric):
            raise DomainAdapterError("metric requires either exact source or explicit unavailable reason")
        if "unavailable_reason" in metric:
            record.update(value=None, status="UNAVAILABLE",
                          reason=required_text(metric["unavailable_reason"], "unavailable reason"))
        else:
            source = _mapping(metric["source"], "metric source")
            if set(source) != {"input", "path"}:
                raise DomainAdapterError("metric source requires exact input and JSON path")
            name = required_text(source["input"], "metric source input")
            if name == receipt_input:
                raise DomainAdapterError("observation specification cannot be its own metric source")
            artifact = packet["input_artifacts"].get(name)
            if artifact is None:
                raise DomainAdapterError(f"metric source not a declared input: {name}")
            if name not in source_cache:
                source_cache[name] = _input_json(packet, name)
            value = source_cache[name]
            path = source["path"]
            if not isinstance(path, list) or not path:
                raise DomainAdapterError("metric source path requires exact JSON keys/indices")
            for part in path:
                if isinstance(part, str) and isinstance(value, dict) and part in value:
                    value = value[part]
                elif type(part) is int and isinstance(value, list) and 0 <= part < len(value):
                    value = value[part]
                else:
                    raise DomainAdapterError(f"metric source path missing or incompatible: {key}")
            try:
                finite = type(value) in (int, float) and math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise DomainAdapterError(f"metric source is not a finite JSON number: {key}")
            record.update(value=value, status="EXTRACTED_FROM_DECLARED_SOURCE",
                          source_binding={"input": name, "path": path,
                                          "artifact_id": artifact["artifact_id"],
                                          "version": artifact["version"], "sha256": artifact["sha256"]})
        by_id[key] = record

    ratios = data.get("ratios", [])
    if not isinstance(ratios, list):
        raise DomainAdapterError("ratios must be an array")
    derived = {}
    for raw in ratios:
        ratio = _mapping(raw, "derived ratio")
        if set(ratio) != {"id", "numerator", "denominator", "semantics"}:
            raise DomainAdapterError("derived ratio requires exact id, operands and semantics")
        key = required_text(ratio["id"], "ratio id")
        num_key = required_text(ratio["numerator"], "numerator")
        den_key = required_text(ratio["denominator"], "denominator")
        if key in derived or key in by_id or num_key not in by_id or den_key not in by_id:
            raise DomainAdapterError("ratio must use unique identity and known raw metrics")
        num, den = by_id[num_key], by_id[den_key]
        record = {"id": key, "numerator": num_key, "denominator": den_key,
                  "semantics": required_text(ratio["semantics"], "ratio semantics"),
                  "unit": f'{num["unit"]}/{den["unit"]}', "value": None}
        if num["value"] is None or den["value"] is None:
            record["status"] = "UNAVAILABLE_OPERAND"
        elif den["value"] <= 0:
            record["status"] = "NONPOSITIVE_DENOMINATOR"
        else:
            result = num["value"] / den["value"]
            if not math.isfinite(result):
                raise DomainAdapterError("derived ratio is not finite")
            record.update(value=result, status="DERIVED_FROM_EXTRACTED_VALUES")
        derived[key] = record
    return {"schema_version": "SMS_BUSINESS_OBSERVATION_V1", "subject": subject,
            "window": window, "raw_metrics": by_id, "derived_metrics": derived,
            "evidence_status": "EXACT_DECLARED_JSON_VALUES_AND_INPUT_BYTES_ONLY",
            "platform_authenticity_verified": False, "metric_semantics_verified": False,
            "causal_effect_verified": False, "owner_outcome_verified": False,
            "effect_authorized": False}


def handle_business_outcome_metrics(project_id, packet, config, outputs, output_dir, attempt, name):
    receipt_input = str(config["outcome_receipt_input"])
    payload = _input_json(packet, receipt_input)
    if payload.get("schema_version") == "SMS_BUSINESS_OBSERVATION_V1":
        metrics = business_observation_metrics(payload, packet, receipt_input)
        identity = {"subject": metrics["subject"], "observation_schema": metrics["schema_version"]}
    else:
        metrics = outcome_metrics(payload)
        identity = {"episode_id": metrics["episode_id"]}
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    _write_json(path, {"adapter": name, **metrics})
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, **identity},
        }
    }
    result = {"adapter": name, **identity, "derived_metrics": metrics["derived_metrics"]}
    if "evidence_status" in metrics:
        result.update(evidence_status=metrics["evidence_status"], owner_outcome_verified=False)
    return artifact_outputs, result


