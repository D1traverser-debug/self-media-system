from __future__ import annotations

from .common import *
from ..legacy.media_qa import MediaQAChecker

def handle_extended_media_qa(project_id, packet, config, outputs, output_dir, attempt, name):
    media_name = str(config["media_input"])
    media_path = _input_path(packet, media_name)
    report = MediaQAChecker().inspect(media_path).to_dict()
    if report.get("hard_pass") is not True and config.get("block_on_hard_fail", True):
        raise DomainAdapterError("supplementary media QA hard-failed: " + json.dumps(report.get("checks", []), ensure_ascii=False))
    output_name = str(config.get("output_name", outputs[0]))
    path = output_dir / f"{_safe_filename(output_name)}-attempt-{attempt}.json"
    payload = {"adapter": name, **report}
    _write_json(path, payload)
    artifact_outputs = {
        output_name: {
            "path": str(path), "kind": "qa_report", "media_type": "application/json",
            "rights_status": "NOT_APPLICABLE",
            "metadata": {
                "adapter": name, "checker": report.get("metadata", {}).get("checker"),
                "media_sha256": report.get("metadata", {}).get("sha256"),
                "hard_pass": report.get("hard_pass"),
            },
        }
    }
    result = {"adapter": name, "hard_pass": report.get("hard_pass"), "check_count": len(report.get("checks", []))}
    return artifact_outputs, result


