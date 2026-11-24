from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import pytest

from video_studio.production.audio_preserve import (
    AudioIdentityError, VideoOnlyEditSpec, AudioPreservingVideoEditor, verify_audio_packet_identity,
)
from video_studio.production.ffmpeg_assembler import sha256_file
from video_studio.production.registry import PRODUCTION_EXECUTORS

def source_clip(root: Path) -> Path:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("real ffmpeg/ffprobe required")
    source=root/"source.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-v","error","-y",
        "-f","lavfi","-i","color=c=blue:s=160x120:d=3:r=15",
        "-f","lavfi","-i","sine=frequency=440:duration=3:sample_rate=48000",
        "-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
        "-shortest",str(source)],check=True,capture_output=True,timeout=60)
    return source

def spec(mode: str, **fields) -> VideoOnlyEditSpec:
    return VideoOnlyEditSpec.from_dict({"schema_version":"1.0","audio_promise":"BITSTREAM_IDENTITY",
        "source_input":"source","mode":mode,"video_output":"result","receipt_output":"proof",**fields})

def test_true_ffmpeg_cropped_video_keeps_all_audio_payload_packets(tmp_path):
    source=source_clip(tmp_path)
    for mode,options in (("PASSTHROUGH",{}),
                         ("CROP",{"crop":{"width":120,"height":80,"x":20,"y":20}})):
        obj=AudioPreservingVideoEditor().render(spec(mode,**options),source=source,
            source_sha256=sha256_file(source),output_dir=tmp_path/mode,
            expected_outputs={"result","proof"})
        receipt=obj["receipt"]
        assert receipt["audio_identity"]["promise"]=="BITSTREAM_IDENTITY"
        assert receipt["audio_identity"]["packet_count_source"]==receipt["audio_identity"]["packet_count_output"]
        assert receipt["owner_outcome_verified"] is False
        assert Path(obj["video_path"]).is_file()
        if mode=="CROP":
            assert (receipt["output_width"],receipt["output_height"])==(120,80)

def test_true_shortened_video_preserves_encoded_audio_prefix(tmp_path):
    source=source_clip(tmp_path)
    obj=AudioPreservingVideoEditor().render(spec("TRIM_END_ONLY",end_seconds=1.6),
        source=source,source_sha256=sha256_file(source),output_dir=tmp_path/"short",
        expected_outputs={"result","proof"})
    proof=obj["receipt"]["audio_identity"]
    assert proof["promise"]=="ORIGINAL_AUDIO_PREFIX_ONLY"
    assert 0 < proof["packet_count_output"] < proof["packet_count_source"]

def test_actual_audio_reencode_is_detected_not_passed_as_original(tmp_path):
    source=source_clip(tmp_path)
    changed=tmp_path/"transcoded.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-v","error","-y","-i",str(source),
                    "-map","0:v:0","-map","0:a:0","-c:v","copy",
                    "-c:a","aac","-b:a","64k",str(changed)],
                   check=True,capture_output=True,timeout=60)
    with pytest.raises(AudioIdentityError,match="packet identity"):
        verify_audio_packet_identity(source,changed)

def test_disallowed_edit_and_untrusted_source_are_blocked(tmp_path):
    assert PRODUCTION_EXECUTORS.supports("ffmpeg_video_audio_copy")
    for fields in [
        {"mode":"AI_BLOOD_REMOVAL"},
        {"mode":"ENHANCE_4K"},
        {"mode":"CROP","crop":{"width":119,"height":80,"x":20,"y":20}},
        {"mode":"TRIM_END_ONLY","end_seconds":0},
        {"mode":"PASSTHROUGH","audio_promise":"PERCEPTUAL_SIMILARITY"},
    ]:
        with pytest.raises(AudioIdentityError):
            VideoOnlyEditSpec.from_dict({"schema_version":"1.0","audio_promise":"BITSTREAM_IDENTITY",
                "source_input":"source","video_output":"result","receipt_output":"proof",**fields})
    source=source_clip(tmp_path)
    with pytest.raises(AudioIdentityError,match="digest changed"):
        AudioPreservingVideoEditor().render(spec("PASSTHROUGH"),source=source,
            source_sha256="0"*64,output_dir=tmp_path/"bad",
            expected_outputs={"result","proof"})
