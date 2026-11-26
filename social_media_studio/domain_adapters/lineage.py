from __future__ import annotations

from .common import *
from social_media_studio.legacy.media_graph import ContextRecord, MediaGraph

def handle_media_graph_initialize(engine, project_id, packet, config, outputs, output_dir, attempt, name):
    contexts = config.get("contexts", [])
    if not isinstance(contexts, list) or not contexts:
        raise DomainAdapterError("media_graph_initialize requires a non-empty contexts array")
    graph = MediaGraph()
    for raw_context in contexts:
        context_data = _mapping(raw_context, "MediaGraph context")
        graph.add_context(ContextRecord(**context_data))
    output_name = str(config.get("output_name", outputs[0]))
    if outputs != [output_name]:
        raise DomainAdapterError("media_graph_initialize must declare exactly its output_name")
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    _write_json(path, graph.to_dict())
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "domain_state", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {"adapter": name, "context_count": len(graph.contexts), "asset_count": 0},
        }
    }
    result = {"adapter": name, "context_count": len(graph.contexts), "asset_count": 0}
    return artifact_outputs, result


