from __future__ import annotations

from .common import *
from ..legacy.business_metrics import *
from ..legacy.business_objects import *
from ..legacy.editorial_planning import EpisodeIntent

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

def handle_business_object_validate(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    object_type=str(config.get("object_type","")).strip(); input_name=str(config.get("input_name","")).strip()
    obj=business_object_from_dict(object_type,_input_json(packet,input_name)); output_name=str(config.get("output_name",outputs[0]))
    path=output_dir/f"{_safe_filename(output_name)}-attempt-{attempt}.json"; _write_json(path,{"schema_version":"1.0","adapter":name,"object_type":object_type,"object":_jsonable(obj)})
    identity_field={"ContentPortfolioItem":"item_id","DistinctiveAssetObservation":"asset_id","CommercialFit":"fit_id","RightsPackage":"package_id","CommercialOfferCandidate":"offer_id","BusinessHypothesisDecision":"decision_id"}[object_type]
    artifact_outputs={output_name:{"path":str(path),"kind":"business_object","media_type":"application/json","rights_status":"NOT_APPLICABLE","metadata":{"adapter":name,"object_type":object_type,"object_id":getattr(obj,identity_field)}}}
    result={"adapter":name,"object_type":object_type,"object_id":getattr(obj,identity_field)}
    return artifact_outputs, result


def handle_episode_intent_validate(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    handoff_input = str(config.get("handoff_input", "")).strip()
    expected_program_id = str(config.get("program_id") or "").strip() or None
    raw_handoff = _input_json(packet, handoff_input)
    if config.get("require_validated_transfer") is True:
        imported = packet["input_artifacts"].get(handoff_input)
        if imported is None:
            raise DomainAdapterError(f"validated Program handoff input is unavailable: {handoff_input}")
        transfer = _mapping(imported.get("metadata", {}).get("cross_project_transfer"), "cross_project_transfer")
        target_project_id = engine.project(project_id)["project_id"]
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


def handle_business_outcome_metrics(engine, project_id, packet, config, outputs, output_dir, attempt, name):
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
    return artifact_outputs, result


