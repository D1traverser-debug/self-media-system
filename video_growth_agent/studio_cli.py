"""Compatibility import path; the standalone CLI is :mod:`video_studio.cli`."""
from video_studio.cli import build_parser, main

if __name__ == "__main__":
    raise SystemExit(main())
