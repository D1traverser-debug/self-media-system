"""Real video-only transformation with independently proven original encoded audio packets."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Mapping
from .contracts import ProductionContractError
from .ffmpeg_assembler import _write_json_exclusive, sha256_file

class AudioIdentityError(ProductionContractError):
    pass

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_HASH = re.compile(r"^SHA256:[0-9a-fA-F]{64}$")

def _name(x: Any) -> str:
    if not isinstance(x, str) or not _ID.fullmatch(x):
        raise AudioIdentityError("unsafe or missing artifact ID")
    return x

def _probe(path: Path, *args: str) -> dict[str, Any]:
    try:
        run = subprocess.run(["ffprobe", "-hide_banner", "-v", "error", *args, "-of", "json",
                              str(path)], capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AudioIdentityError("ffprobe unavailable or timed out") from exc
    if run.returncode:
        raise AudioIdentityError("ffprobe failed: " + run.stderr.strip()[:280])
    try:
        return json.loads(run.stdout)
    except json.JSONDecodeError as exc:
        raise AudioIdentityError("malformed ffprobe output") from exc

def _streams(path: Path) -> dict[str, Any]:
    return _probe(path, "-show_streams", "-show_format")

def _packet_hashes(path: Path) -> list[str]:
    packets = _probe(path, "-select_streams", "a:0", "-show_packets", "-show_entries",
                     "packet=data_hash", "-show_data_hash", "sha256").get("packets", [])
    if not isinstance(packets, list) or not packets:
        raise AudioIdentityError("no encoded audio packet evidence")
    hashes = [p.get("data_hash") if isinstance(p, dict) else None for p in packets]
    if any(not isinstance(h, str) or not _HASH.fullmatch(h) for h in hashes):
        raise AudioIdentityError("missing encoded packet SHA256 evidence")
    return hashes

def verify_audio_packet_identity(source: Path, output: Path, *, prefix: bool = False) -> dict[str, Any]:
    a, b = _streams(source), _streams(output)
    x = [s for s in a.get("streams", []) if s.get("codec_type") == "audio"]
    y = [s for s in b.get("streams", []) if s.get("codec_type") == "audio"]
    if len(x) != 1 or len(y) != 1:
        raise AudioIdentityError("audio stream identity requires exactly one track")
    for field in ("codec_name", "sample_rate", "channels", "channel_layout"):
        if str(x[0].get(field)) != str(y[0].get(field)):
            raise AudioIdentityError("audio stream format changed: "+field)
    original, edited = _packet_hashes(source), _packet_hashes(output)
    good = (0 < len(edited) < len(original) and edited == original[:len(edited)]) if prefix else edited == original
    if not good:
        raise AudioIdentityError("audio packet identity not preserved")
    return {"assurance": "ACTUAL_ENCODED_PACKET_SHA256_MATCH",
            "promise": "ORIGINAL_AUDIO_PREFIX_ONLY" if prefix else "BITSTREAM_IDENTITY",
            "packet_count_source": len(original), "packet_count_output": len(edited),
            "audio_packet_sequence_digest": hashlib.sha256("\n".join(edited).encode()).hexdigest(),
            "codec": x[0].get("codec_name"), "listening_test": "NOT_PERFORMED"}

@dataclass(frozen=True)
class VideoOnlyEditSpec:
    source_input: str
    mode: str
    video_output: str
    receipt_output: str
    crop: tuple[int,int,int,int] | None = None
    end_seconds: float | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VideoOnlyEditSpec":
        if not isinstance(data, Mapping) or data.get("schema_version") != "1.0":
            raise AudioIdentityError("schema_version 1.0 required")
        if data.get("audio_promise") != "BITSTREAM_IDENTITY":
            raise AudioIdentityError("this operation only promises encoded audio identity")
        mode = data.get("mode")
        if mode not in {"PASSTHROUGH", "CROP", "TRIM_END_ONLY"}:
            raise AudioIdentityError("unsupported video-only edit; enhancement and restoration are separate")
        crop = None
        if mode == "CROP":
            box = data.get("crop")
            if not isinstance(box, Mapping) or set(box) != {"width","height","x","y"}:
                raise AudioIdentityError("crop width, height, x, y required")
            nums = tuple(box[k] for k in ("width","height","x","y"))
            if any(isinstance(v,bool) or not isinstance(v,int) or v<0 or v%2 for v in nums) or min(nums[:2])<2:
                raise AudioIdentityError("YUV420 requires positive even dimensions and even offsets")
            crop = nums
        elif "crop" in data:
            raise AudioIdentityError("crop is invalid outside CROP mode")
        end = None
        if mode == "TRIM_END_ONLY":
            val = data.get("end_seconds")
            if isinstance(val,bool) or not isinstance(val,(int,float)) or not 0.1 <= float(val) < 86400:
                raise AudioIdentityError("invalid trim end")
            end = float(val)
        elif "end_seconds" in data:
            raise AudioIdentityError("end_seconds is invalid outside end trim")
        return cls(_name(data.get("source_input")), mode, _name(data.get("video_output")),
                   _name(data.get("receipt_output")), crop, end)

class AudioPreservingVideoEditor:
    def render(self, spec: VideoOnlyEditSpec, *, source: Path, source_sha256: str,
               output_dir: Path, expected_outputs: set[str]) -> dict[str, Any]:
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise AudioIdentityError("FFmpeg and FFprobe unavailable")
        if spec.video_output == spec.receipt_output or expected_outputs != {spec.video_output,spec.receipt_output}:
            raise AudioIdentityError("outputs differ from declared artifact names")
        if not source.is_file() or sha256_file(source) != source_sha256:
            raise AudioIdentityError("source missing or digest changed")
        info = _streams(source)
        vs = [s for s in info.get("streams",[]) if s.get("codec_type")=="video"]
        aud = [s for s in info.get("streams",[]) if s.get("codec_type")=="audio"]
        other = [s for s in info.get("streams",[]) if s.get("codec_type") not in {"video","audio"}]
        if len(vs)!=1 or len(aud)!=1 or other:
            raise AudioIdentityError("source must contain one video, one audio, no other streams")
        if spec.mode == "CROP":
            w,h,x,y = spec.crop or (0,0,0,0)
            if x+w > int(vs[0]["width"]) or y+h > int(vs[0]["height"]):
                raise AudioIdentityError("crop exceeds source dimensions")
        if spec.mode == "TRIM_END_ONLY":
            duration = float(info.get("format",{}).get("duration") or 0)
            if spec.end_seconds is None or spec.end_seconds >= duration-0.02:
                raise AudioIdentityError("trim does not produce a shorter clip")
        output_dir.mkdir(parents=True,exist_ok=True)
        output = output_dir / (spec.video_output+".mp4")
        proof_path = output_dir / (spec.receipt_output+".json")
        temporary = output_dir / (spec.video_output+".partial.mp4")
        if any(p.exists() for p in (output,proof_path,temporary)):
            raise AudioIdentityError("target exists; non-destructive retry requires a fresh attempt")
        cmd = ["ffmpeg","-hide_banner","-nostdin","-v","error","-i",str(source),
               "-map","0:v:0","-map","0:a:0"]
        if spec.mode == "CROP":
            w,h,x,y = spec.crop or (0,0,0,0)
            cmd += ["-vf", f"crop={w}:{h}:{x}:{y}"]
        if spec.mode in {"CROP","TRIM_END_ONLY"}:
            cmd += ["-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p"]
        else:
            cmd += ["-c:v","copy"]
        cmd += ["-c:a","copy","-sn","-dn"]
        if spec.mode == "TRIM_END_ONLY":
            cmd += ["-t",str(spec.end_seconds)]
        cmd += ["-movflags","+faststart","-y",str(temporary)]
        try:
            proc = subprocess.run(cmd,capture_output=True,text=True,timeout=900,check=False)
            if proc.returncode or not temporary.is_file() or temporary.stat().st_size<=0:
                raise AudioIdentityError("FFmpeg video edit failed: "+proc.stderr.strip()[:250])
            identity = verify_audio_packet_identity(source,temporary,prefix=spec.mode=="TRIM_END_ONLY")
            edited = _streams(temporary)
            v = next(x for x in edited["streams"] if x.get("codec_type")=="video")
            a = next(x for x in edited["streams"] if x.get("codec_type")=="audio")
            duration = float(edited.get("format",{}).get("duration") or 0)
            vd = float(v.get("duration") or duration)
            ad = float(a.get("duration") or duration)
            if duration<=0 or abs(vd-ad)>0.2:
                raise AudioIdentityError("output audio/video duration mismatch")
            temporary.replace(output)
            receipt = {"schema_version":"1.0","operation":"ffmpeg_video_audio_copy","mode":spec.mode,
                       "source_sha256":source_sha256,"output_sha256":sha256_file(output),
                       "output_width":int(v["width"]),"output_height":int(v["height"]),
                       "duration_seconds":duration,"audio_identity":identity,
                       "quality_assurance":"ENCODED_AUDIO_PACKET_IDENTITY_ONLY",
                       "visual_restoration_verified":False,"owner_outcome_verified":False,
                       "candidate_only":True}
            _write_json_exclusive(proof_path,receipt)
            return {"video_path":str(output),"receipt_path":str(proof_path),"receipt":receipt}
        finally:
            if temporary.exists():
                temporary.unlink()
