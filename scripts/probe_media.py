#!/usr/bin/env python3
"""Probe media files with ffprobe and emit JSON metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()


def run_ffprobe(path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as exc:
        raise SystemExit("ffprobe is required but was not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffprobe failed for {path}: {exc.stderr}") from exc
    return json.loads(result.stdout)


def summarize(path: Path, raw: dict) -> dict:
    streams = raw.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    fmt = raw.get("format", {})

    return {
        "path": str(path),
        "durationSec": float(fmt.get("duration", 0) or 0),
        "sizeBytes": int(fmt.get("size", 0) or 0),
        "hasVideo": bool(video_stream),
        "hasAudio": bool(audio_streams),
        "width": int(video_stream.get("width", 0) or 0),
        "height": int(video_stream.get("height", 0) or 0),
        "fps": video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "",
        "videoCodec": video_stream.get("codec_name", ""),
        "audioCodecs": [s.get("codec_name", "") for s in audio_streams],
        "audioStreamCount": len(audio_streams),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("media", nargs="+", type=Path)
    parser.add_argument("--raw", action="store_true", help="Include raw ffprobe output")
    args = parser.parse_args()

    output = []
    for path in args.media:
        if not path.exists():
            print(f"WARN: missing file: {path}", file=sys.stderr)
            continue
        raw = run_ffprobe(path)
        item = summarize(path, raw)
        if args.raw:
            item["raw"] = raw
        output.append(item)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
