from __future__ import annotations

from .common import *
from social_media_studio.legacy.ip_identity import *
from social_media_studio.legacy.media_graph import AssetRef, MediaGraph
from social_media_studio.legacy.production_os import ReferenceBinding
from social_media_studio.legacy.programmatic_graphics import shot_contract_from_dict

def ipos_import_receipt_from_dict(payload: Mapping[str, Any]) -> IPIdentityImportReceipt:
    data = _mapping(payload, "IPOS import receipt")
    return IPIdentityImportReceipt(
        bundle_ref=str(data["bundle_ref"]),
        canon_ref=str(data["canon_ref"]),
        bundle_digest=str(data["bundle_digest"]),
        bundle_asset_ref=AssetRef(**_mapping(data["bundle_asset_ref"], "bundle_asset_ref")),
        asset_refs=tuple(AssetRef(**_mapping(item, "asset_ref")) for item in data.get("asset_refs", [])),
        reference_bindings=tuple(ReferenceBinding(**_mapping(item, "reference_binding")) for item in data.get("reference_bindings", [])),
        imported_asset_refs=tuple(AssetRef(**_mapping(item, "imported_asset_ref")) for item in data.get("imported_asset_refs", [])),
        invalidated_refs=tuple(AssetRef(**_mapping(item, "invalidated_ref")) for item in data.get("invalidated_refs", [])),
    )

def handle_ipos_bundle_inspect(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    input_name = str(config["bundle_input"])
    readiness = inspect_ipos_bundle(_input_json(packet, input_name))
    if not readiness.ready:
        raise DomainAdapterError("IPOS bundle is not video-ready: " + "; ".join(readiness.reasons))
    import_validation = None
    receipt_input = str(config.get("import_receipt_input", "")).strip()
    graph_input = str(config.get("media_graph_input", "")).strip()
    if bool(receipt_input) != bool(graph_input):
        raise DomainAdapterError("IPOS import verification requires both import_receipt_input and media_graph_input")
    if receipt_input and graph_input:
        receipt = ipos_import_receipt_from_dict(_input_json(packet, receipt_input))
        graph = MediaGraph.from_dict(_input_json(packet, graph_input))
        if receipt.bundle_ref != readiness.bundle_ref or receipt.canon_ref != readiness.canon_ref:
            raise DomainAdapterError("IPOS import receipt does not match the inspected bundle/canon")
        bundle_asset = graph.assets.get(receipt.bundle_asset_ref)
        if bundle_asset is None or graph.asset_state(receipt.bundle_asset_ref) != "PROMOTED":
            raise DomainAdapterError("IPOS bundle asset is missing or not promoted in MediaGraph")
        if bundle_asset.digest != receipt.bundle_digest:
            raise DomainAdapterError("IPOS bundle asset digest does not match the import receipt")
        verified_refs = 0
        for ref in receipt.imported_asset_refs:
            asset = graph.assets.get(ref)
            if asset is None or graph.asset_state(ref) != "PROMOTED":
                raise DomainAdapterError(f"IPOS imported asset is missing or not promoted: {ref.key()}")
            verified_refs += 1
        for binding in receipt.reference_bindings:
            ref = AssetRef(binding.asset_id, binding.version_id)
            asset = graph.assets.get(ref)
            if asset is None or graph.asset_state(ref) != "PROMOTED" or asset.digest != binding.digest:
                raise DomainAdapterError(f"IPOS reference binding does not match the exact promoted digest: {ref.key()}")
        import_validation = {
            "bundle_asset_ref": receipt.bundle_asset_ref.key(),
            "bundle_digest": receipt.bundle_digest,
            "imported_asset_count": verified_refs,
            "reference_binding_count": len(receipt.reference_bindings),
            "media_graph_context_id": bundle_asset.context_id,
        }
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    payload = {"adapter": name, "readiness": _jsonable(readiness), "import_validation": import_validation}
    _write_json(path, payload)
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {
                "adapter": name, "ipos_ready": True, "bundle_ref": readiness.bundle_ref,
                "import_verified": import_validation is not None,
                "imported_asset_count": import_validation["imported_asset_count"] if import_validation else 0,
            },
        }
    }
    result = {
        "adapter": name, "ipos_ready": True, "bundle_ref": readiness.bundle_ref,
        "import_verified": import_validation is not None,
        "imported_asset_count": import_validation["imported_asset_count"] if import_validation else 0,
    }
    return artifact_outputs, result


def handle_ipos_bundle_import(engine, project_id, packet, config, outputs, output_dir, attempt, name):
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
    return artifact_outputs, result


def handle_ipos_shot_bind(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    bundle = _input_json(packet, str(config["bundle_input"]))
    receipt = ipos_import_receipt_from_dict(_input_json(packet, str(config["import_receipt_input"])))
    graph = MediaGraph.from_dict(_input_json(packet, str(config["media_graph_input"])))
    for binding in receipt.reference_bindings:
        ref = AssetRef(binding.asset_id, binding.version_id)
        asset = graph.assets.get(ref)
        if asset is None or graph.asset_state(ref) != "PROMOTED" or asset.digest != binding.digest:
            raise DomainAdapterError(f"IPOS reference is not present as the exact promoted MediaGraph version: {ref.key()}")
    shot = shot_contract_from_dict(_input_json(packet, str(config["shot_contract_input"])))
    bound = bind_ipos_identity_to_shot(
        shot, bundle, receipt, required=bool(config.get("required", True)),
    )
    rules = build_ipos_continuity_rules(bundle)
    shot_output = str(config["shot_contract_output"])
    rules_output = str(config["continuity_rules_output"])
    if set(outputs) != {shot_output, rules_output}:
        raise DomainAdapterError("ipos_shot_bind must declare exactly shot_contract_output and continuity_rules_output")
    shot_path = output_dir / f"{_safe_filename(shot_output)}-attempt-{attempt}.json"
    rules_path = output_dir / f"{_safe_filename(rules_output)}-attempt-{attempt}.json"
    _write_json(shot_path, {"adapter": name, "shot_contract": _jsonable(bound)})
    _write_json(rules_path, {"adapter": name, "continuity_rules": _jsonable(rules)})
    artifact_outputs = {
        shot_output: {
            "path": str(shot_path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, "shot_id": bound.shot_id, "ip_identity_required": bound.ip_identity_required, "ip_identity_bundle_ref": bound.ip_identity_bundle_ref},
        },
        rules_output: {
            "path": str(rules_path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, "canon_ref": receipt.canon_ref, "rule_count": len(rules)},
        },
    }
    result = {"adapter": name, "shot_id": bound.shot_id, "ip_identity_required": bound.ip_identity_required, "canon_ref": receipt.canon_ref, "reference_count": len(bound.references)}
    return artifact_outputs, result


def handle_ipos_continuity_snapshot(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    bundle = _input_json(packet, str(config["bundle_input"]))
    shot_id = str(config["shot_id"])
    snapshot = build_ipos_continuity_snapshot(shot_id, bundle)
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    _write_json(path, {"adapter": name, "snapshot": _jsonable(snapshot)})
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, "shot_id": shot_id, "canon_refs": list(snapshot.canon_refs)},
        }
    }
    result = {"adapter": name, "shot_id": shot_id, "dimension_count": len(snapshot.dimensions)}
    return artifact_outputs, result


def handle_ipos_continuity_link(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    bundle = _input_json(packet, str(config["bundle_input"]))
    link = build_ipos_continuity_link(
        str(config["from_shot_id"]), str(config["to_shot_id"]), bundle,
    )
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    _write_json(path, {"adapter": name, "link": _jsonable(link)})
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "evidence", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, "from_shot_id": link.from_shot_id, "to_shot_id": link.to_shot_id, "rule_count": len(link.rules)},
        }
    }
    result = {"adapter": name, "from_shot_id": link.from_shot_id, "to_shot_id": link.to_shot_id, "rule_count": len(link.rules)}
    return artifact_outputs, result


