"""Explicit, read-only, per-variant observed artifact conformance.

This probes exact current project artifacts only on demand; it never launches a
creative provider or another scheduler, records an approval or publishes.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from PIL import Image, UnidentifiedImageError

from ..domain.conformance import assess_observation, select_variant_candidate
from ..domain.outcome_traceability import trace_owner_requirements
from ..engine_support import _sha256
from ..production.audio_preserve import AudioIdentityError, verify_audio_packet_identity


_TEXT_TYPES = frozenset({
    "SHORT_COPY", "LONG_ARTICLE", "PLATFORM_PACKAGE", "PROMPT_SPEC", "ANALYSIS_REPORT",
})
_IMAGE_MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp", "GIF": "image/gif", "BMP": "image/bmp"}
_MAX_TEXT_SIZE = 2 * 1024 * 1024


def _probe(path: Path, *, deliverable_type: str, declared_media_type: str) -> dict[str, Any]:
    """Inspect actual bytes, not the registered file extension or media-type claim."""
    try:
        if declared_media_type.startswith("image/") or deliverable_type in {"STATIC_IMAGE", "MULTI_ASPECT_IMAGE_SET"}:
            with Image.open(path) as image:
                width, height, format_name = image.size[0], image.size[1], image.format
                image.verify()
            return {"kind": "IMAGE", "media_type": _IMAGE_MIME.get(str(format_name).upper(), "image/unknown"),
                    "width": width, "height": height, "format": format_name}
        if declared_media_type.startswith(("video/", "audio/")) or deliverable_type in {"ORIGINAL_VIDEO", "MEDIA_TRANSFORM"}:
            if shutil.which("ffprobe") is None:
                return {"error": "PROBE_TOOL_UNAVAILABLE"}
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe",
                 "-show_streams", "-show_format", "-of", "json", str(path)],
                capture_output=True, text=True, timeout=30, check=False,
            )
            if result.returncode != 0:
                return {"error": "MEDIA_DECODE_OR_PROBE_FAILED"}
            payload = json.loads(result.stdout)
            streams = payload.get("streams", [])
            video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
            audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
            formats = str(payload.get("format", {}).get("format_name", ""))
            if video is not None:
                # Verify container as well as the existence of a video stream.
                mime = ("video/mp4" if "mp4" in formats or "mov" in formats
                        else "video/webm" if "webm" in formats
                        else "video/x-matroska" if "matroska" in formats else "video/unknown")
                return {"kind": "VIDEO", "media_type": mime,
                        "width": video.get("width"), "height": video.get("height"),
                        "has_audio_stream": audio is not None, "container": formats}
            if audio is not None:
                mime = ("audio/mpeg" if "mp3" in formats
                        else "audio/wav" if "wav" in formats
                        else "audio/flac" if "flac" in formats else "audio/unknown")
                return {"kind": "AUDIO", "media_type": mime, "container": formats}
            return {"error": "NO_MEDIA_STREAM"}
        if path.stat().st_size > _MAX_TEXT_SIZE:
            return {"error": "FILE_OVER_SIZE_LIMIT"}
        data = path.read_bytes()
        if b"\x00" in data or data.startswith(b"%PDF-"):
            return {"error": "NOT_PLAIN_TEXT_BYTES"}
        text = data.decode("utf-8", errors="strict")
        if declared_media_type == "application/json":
            json.loads(text)
            return {"kind": "JSON", "media_type": "application/json", "utf8": True,
                    "characters": len(text)}
        if declared_media_type.startswith("text/") or deliverable_type in _TEXT_TYPES:
            return {"kind": "TEXT", "media_type": declared_media_type, "utf8": True,
                    "characters": len(text),
                    "non_whitespace_characters": sum(not x.isspace() for x in text)}
        return {"error": "UNSUPPORTED_MEDIA_TYPE"}
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError,
            UnidentifiedImageError, subprocess.TimeoutExpired, Image.DecompressionBombError):
        return {"error": "FILE_FORMAT_OR_PROBE_FAILED"}


def _verify_source_bound_encoded_audio(
    db: Any, project_dir: Path, project_id: str, output_artifact_id: str,
    output_path: Path, output_sha256: str,
) -> dict[str, Any]:
    """Re-read actual source and output packets via original immutable lineage.

    Never trusts a produced JSON receipt or source_sha256 asserted by a task.
    Does not claim PCM/perceptual identity, creative approval, or ownership.
    """
    rows = db.execute(
        "SELECT ai.input_artifact_id, ai.input_sha256, a.sha256, a.relative_path, "
        "a.kind, a.media_type, a.status FROM artifact_inputs ai "
        "JOIN artifacts a ON a.project_id=ai.project_id AND a.artifact_id=ai.input_artifact_id "
        "WHERE ai.project_id=? AND ai.output_artifact_id=?",
        (project_id, output_artifact_id),
    ).fetchall()
    sources = [r for r in rows if r["kind"] in {"video", "media"}
               and str(r["media_type"]).startswith("video/")]
    if len(sources) != 1:
        return {
            "status": "UNVERIFIED",
            "reason": "EXACT_SINGLE_REGISTERED_SOURCE_VIDEO_NOT_AVAILABLE",
            "candidate_source_count": len(sources),
        }
    source = sources[0]
    proof: dict[str, Any] = {
        "source_artifact_id": source["input_artifact_id"],
        "source_sha256": source["input_sha256"],
        "output_artifact_id": output_artifact_id,
        "output_sha256": output_sha256,
    }
    safe_root = project_dir.resolve()
    source_path = (safe_root / source["relative_path"]).resolve()
    if (source["status"] not in {"CURRENT", "ACCEPTED"}
            or source["input_sha256"] != source["sha256"]
            or safe_root not in source_path.parents
            or not source_path.is_file()
            or _sha256(source_path) != source["input_sha256"]):
        return {**proof, "status": "MISMATCH",
                "reason": "SOURCE_INPUT_ARTIFACT_NOT_CURRENT_OR_BYTES_CHANGED"}
    if shutil.which("ffprobe") is None:
        return {**proof, "status": "UNVERIFIED", "reason": "AUDIO_PACKET_PROBE_TOOL_UNAVAILABLE"}
    try:
        measured = verify_audio_packet_identity(source_path, output_path, prefix=False)
    except AudioIdentityError as first_error:
        # A legitimate trim may preserve only the audio packets for the kept
        # duration. Prove that limited fact without promoting the full-promise
        # conformance claim.
        if "unavailable or timed out" in str(first_error):
            return {**proof, "status": "UNVERIFIED", "reason": "AUDIO_PACKET_PROBE_INCONCLUSIVE"}
        try:
            prefix = verify_audio_packet_identity(source_path, output_path, prefix=True)
        except AudioIdentityError as second_error:
            if "unavailable or timed out" in str(second_error) or "ffprobe failed" in str(second_error):
                return {**proof, "status": "UNVERIFIED", "reason": "AUDIO_PACKET_PROBE_INCONCLUSIVE"}
            return {**proof, "status": "MISMATCH",
                    "reason": "SOURCE_ENCODED_AUDIO_PACKETS_DIFFER_FROM_OUTPUT"}
        if (_sha256(source_path) != source["input_sha256"]
                or _sha256(output_path) != output_sha256):
            return {**proof, "status": "MISMATCH", "reason": "AUDIO_SOURCE_OR_OUTPUT_CHANGED_DURING_PROBE"}
        return {**proof, "status": "UNVERIFIED",
                "reason": "ONLY_RETAINED_SOURCE_AUDIO_PREFIX_VERIFIED",
                "retained_packet_count": prefix["packet_count_output"],
                "full_source_packet_count": prefix["packet_count_source"]}
    if (_sha256(source_path) != source["input_sha256"]
            or _sha256(output_path) != output_sha256):
        return {**proof, "status": "MISMATCH", "reason": "AUDIO_SOURCE_OR_OUTPUT_CHANGED_DURING_PROBE"}
    return {**proof, "status": "MATCH", "assurance": "INDEPENDENTLY_RECOMPUTED_ENCODED_AUDIO_PACKET_SHA256_MATCH",
            "packet_count_source": measured["packet_count_source"],
            "packet_count_output": measured["packet_count_output"],
            "packet_sequence_digest": measured["audio_packet_sequence_digest"],
            "codec": measured["codec"],
            "audio_render_quality_verified": False, "owner_outcome_verified": False}


class OutcomeInspectionService:
    def __init__(self, engine: Any):
        self._engine = engine

    def inspect(self, project_id: str) -> dict[str, Any]:
        progress = self._engine.status(project_id)["deliverable_progress"]
        if progress["status"] != "CANDIDATE_COVERAGE_ONLY":
            return {"status": progress["status"], "observed_conformance_complete": False,
                    "owner_outcome_verified": False, "whole_demand_accepted": False,
                    "external_publication_authorized": False}
        project_dir = self._engine._project_dir(project_id)
        variants: list[dict[str, Any]] = []
        with closing(self._engine._connect(project_id)) as db:
            for variant in progress["variants"]:
                observed = []
                for candidate in variant["candidates"]:
                    row = db.execute(
                        "SELECT relative_path, sha256, status, media_type FROM artifacts "
                        "WHERE project_id=? AND artifact_id=?",
                        (project_id, candidate["artifact_id"]),
                    ).fetchone()
                    sample: dict[str, Any] = {
                        "artifact_id": candidate["artifact_id"], "sha256": candidate["sha256"],
                        "artifact_status": candidate["artifact_status"],
                    }
                    if row is None or row["sha256"] != candidate["sha256"] or row["status"] not in {"CURRENT", "ACCEPTED"}:
                        verdict = {"status": "MISMATCH", "failures": ["ARTIFACT_NOT_CURRENT"],
                                   "limitations": [], "creative_quality_verified": False,
                                   "owner_outcome_verified": False}
                    else:
                        path = (project_dir / row["relative_path"]).resolve()
                        if project_dir.resolve() not in path.parents or not path.is_file() or _sha256(path) != row["sha256"]:
                            verdict = {"status": "MISMATCH", "failures": ["ARTIFACT_BYTES_MISSING_OR_CHANGED"],
                                       "limitations": [], "creative_quality_verified": False,
                                       "owner_outcome_verified": False}
                        else:
                            probe = _probe(path, deliverable_type=variant["type"],
                                           declared_media_type=row["media_type"])
                            verdict = assess_observation(
                                deliverable_type=variant["type"],
                                declared_media_type=row["media_type"],
                                expected_shape=variant.get("expected_shape"), observation=probe,
                                constraints=variant.get("constraints"),
                            )
                            # A real registered source + recorded artifact-input
                            # edge lets us independently re-compute encoded audio
                            # identity. A task/LLM-supplied receipt is never proof.
                            constraints = variant.get("constraints") or {}
                            if (variant["type"] == "MEDIA_TRANSFORM"
                                    and constraints.get("original_audio_promise") == "BITSTREAM_IDENTITY"
                                    and verdict["status"] == "UNVERIFIED"
                                    and probe.get("kind") == "VIDEO"
                                    and probe.get("has_audio_stream") is True):
                                proof = _verify_source_bound_encoded_audio(
                                    db, project_dir, project_id, candidate["artifact_id"],
                                    path, row["sha256"],
                                )
                                verdict["source_bound_audio_identity"] = proof
                                if proof["status"] == "MATCH":
                                    verdict["status"] = "MATCH"
                                    verdict["audio_preservation_verified"] = True
                                    verdict["limitations"] = [
                                        reason for reason in verdict["limitations"]
                                        if reason != "ORIGINAL_AUDIO_PROMISE_NEEDS_SOURCE_BOUND_QA_PROOF"
                                    ]
                                elif proof["status"] == "MISMATCH":
                                    verdict["status"] = "MISMATCH"
                                    verdict["failures"].append(proof["reason"])
                                else:
                                    verdict["limitations"].append(proof["reason"])
                    observed.append({**sample, "conformance": verdict})
                selection = select_variant_candidate(observed)
                selected = next(
                    (x for x in observed if x["artifact_id"] == selection["selected_artifact_id"]),
                    None,
                )
                variants.append({
                    "deliverable_id": variant["deliverable_id"], "variant_id": variant["variant_id"],
                    "type": variant["type"], "expected_shape": variant.get("expected_shape"),
                    "candidates": observed,
                    "candidate_selection": selection,
                    "observable_conformance": (
                        selected["conformance"]["status"] if selected is not None
                        else "AMBIGUOUS" if selection["status"] == "AMBIGUOUS" else "UNVERIFIED"
                    ),
                })
        observed_complete = bool(variants) and all(v["observable_conformance"] == "MATCH" for v in variants)
        project = self._engine.project(project_id)
        trace = trace_owner_requirements(project["brief"], variants)
        return {
            "status": "OBSERVED_ONLY_NOT_OWNER_ACCEPTANCE",
            "brief_revision": project["revision"],
            "owner_requirement_trace": trace,
            "project_id": project_id, "variants": variants,
            "declared_variant_count": len(variants),
            "observed_conformance_complete": observed_complete,
            "artifact_release_coverage_complete": progress["artifact_release_coverage_complete"],
            "ambiguous_release_variants": progress.get("ambiguous_release_variants", []),
            "rejected_output_bindings": progress.get("rejected_bindings", []),
            "owner_outcome_verified": False, "whole_demand_accepted": False,
            "external_publication_authorized": False,
            "remaining_assurance": [
                "INDEPENDENT_CREATIVE_QUALITY_REVIEW",
                "OWNER_CONSTRAINT_AND_COMMUNICATION_INTENT_RECONCILIATION",
                "OWNER_OUTCOME_ACCEPTANCE",
                "PUBLICATION_PERMISSION_SEPARATELY_REQUIRED",
            ],
        }
