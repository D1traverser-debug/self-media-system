"""Compatibility import path; media QA lives in :mod:`video_studio.media`."""
from video_studio.media import probe_media, run_claimed_media_qa

__all__ = ["probe_media", "run_claimed_media_qa"]
