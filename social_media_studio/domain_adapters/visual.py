from __future__ import annotations

from .common import *
from ..legacy.media_graph import MediaGraph
from ..legacy.programmatic_graphics import (
    graphic_spec_from_dict, register_graph_candidate, render_programmatic_graphic,
    shot_contract_from_dict,
)
from .editorial import editorial_plan_from_dict, validate_shot_against_editorial_plan

def handle_programmatic_graphic_render(engine, project_id, packet, config, outputs, output_dir, attempt, name):
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
    font_artifact = packet["input_artifacts"].get(font_name)
    rights_artifact = packet["input_artifacts"].get(rights_name)
    if font_artifact is None or font_artifact.get("rights_status") not in {"OWNED", "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN"}:
        raise DomainAdapterError(f"font input must have an allowed, evidenced rights status: {font_name}")
    if rights_artifact is None or rights_artifact.get("kind") not in {"document", "evidence", "rights_record"}:
        raise DomainAdapterError(f"rights evidence input must be a declared document/evidence artifact: {rights_name}")
    if rights_artifact.get("rights_status") not in {"OWNED", "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN"}:
        raise DomainAdapterError(f"rights evidence artifact itself is not rights-cleared: {rights_name}")
    input_names = set(packet["input_artifacts"])
    font_rights_refs = font_artifact.get("metadata", {}).get("rights_evidence_refs", [])
    if not isinstance(font_rights_refs, list) or rights_name not in font_rights_refs:
        raise DomainAdapterError(f"font metadata.rights_evidence_refs must include the exact rights evidence artifact: {rights_name}")
    for binding in shot.references:
        rights_binding = packet["input_artifacts"].get(binding.rights_ref)
        if (
            rights_binding is None
            or rights_binding.get("kind") not in {"document", "evidence", "rights_record"}
            or rights_binding.get("rights_status") not in {"OWNED", "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN"}
        ):
            raise DomainAdapterError(f"ShotContract rights_ref must resolve to a rights-cleared evidence artifact: {binding.rights_ref}")
        if binding.consent_ref:
            consent_binding = packet["input_artifacts"].get(binding.consent_ref)
            if (
                consent_binding is None
                or consent_binding.get("kind") not in {"document", "evidence", "rights_record"}
                or consent_binding.get("rights_status") not in {"OWNED", "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN"}
            ):
                raise DomainAdapterError(f"ShotContract consent_ref must resolve to a rights-cleared consent evidence artifact: {binding.consent_ref}")
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
    return artifact_outputs, result


