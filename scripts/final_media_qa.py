#!/usr/bin/env python3
"""Validate a final V4 Portrait MP4 against its visual_script composition contract."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def ratio_to_float(value: str) -> float:
    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)
            return float(numerator) / float(denominator) if float(denominator) else 0.0
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-print_format",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads(result.stdout)


def stream_duration(stream: dict[str, Any]) -> float:
    try:
        return float(stream.get("duration") or 0)
    except (TypeError, ValueError):
        return 0.0


def decoded_frame_count(stream: dict[str, Any]) -> int:
    value = stream.get("nb_read_frames") or stream.get("nb_frames") or 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def decode_ok(path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-map", "0:a?", "-f", "null", "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode == 0, result.stderr.strip()


def analyze(
    video: Path,
    visual_script: Path,
    *,
    require_audio: bool = True,
    strict_color: bool = True,
) -> dict[str, Any]:
    data = json.loads(visual_script.read_text(encoding="utf-8-sig"))
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    expected = {
        "width": int(composition.get("width") or 0),
        "height": int(composition.get("height") or 0),
        "fps": int(composition.get("fps") or 0),
        "durationFrames": int(composition.get("durationFrames") or 0),
    }
    errors: list[str] = []
    warnings: list[str] = []
    if min(expected.values()) <= 0:
        errors.append("visual_script composition must define positive width, height, fps, and durationFrames")

    raw = probe(video)
    streams = raw.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), {})
    actual_fps_text = str(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "")
    actual_fps = ratio_to_float(actual_fps_text)
    actual_frames = decoded_frame_count(video_stream)
    format_duration = float(raw.get("format", {}).get("duration") or 0)
    expected_duration = expected["durationFrames"] / expected["fps"] if expected["fps"] else 0
    audio_duration = stream_duration(audio_stream)

    if (int(video_stream.get("width") or 0), int(video_stream.get("height") or 0)) != (
        expected["width"],
        expected["height"],
    ):
        errors.append(
            f"resolution mismatch: expected {expected['width']}x{expected['height']}, "
            f"got {video_stream.get('width')}x{video_stream.get('height')}"
        )
    if abs(actual_fps - expected["fps"]) > 0.05:
        errors.append(f"fps mismatch: expected {expected['fps']}, got {actual_fps_text or 'unknown'}")
    if actual_frames != expected["durationFrames"]:
        errors.append(f"decoded frame mismatch: expected {expected['durationFrames']}, got {actual_frames}")
    if video_stream.get("codec_name") != "h264":
        errors.append(f"video codec must be h264, got {video_stream.get('codec_name') or 'missing'}")
    if video_stream.get("pix_fmt") != "yuv420p":
        errors.append(f"pixel format must be yuv420p, got {video_stream.get('pix_fmt') or 'missing'}")

    color_actual = {
        "range": video_stream.get("color_range"),
        "space": video_stream.get("color_space"),
        "transfer": video_stream.get("color_transfer"),
        "primaries": video_stream.get("color_primaries"),
    }
    color_expected = {"range": "tv", "space": "bt709", "transfer": "bt709", "primaries": "bt709"}
    for key, value in color_expected.items():
        if color_actual.get(key) != value:
            message = f"color {key} must be {value}, got {color_actual.get(key) or 'missing'}"
            (errors if strict_color else warnings).append(message)

    if require_audio and not audio_stream:
        errors.append("final video must contain an audio stream")
    if audio_stream and audio_stream.get("codec_name") != "aac":
        errors.append(f"audio codec must be aac, got {audio_stream.get('codec_name') or 'missing'}")
    duration_tolerance = max(0.12, 3 / expected["fps"]) if expected["fps"] else 0.12
    if format_duration + duration_tolerance < expected_duration:
        errors.append(
            f"container duration is truncated: expected {expected_duration:.3f}s, got {format_duration:.3f}s"
        )
    if require_audio and audio_stream and audio_duration and audio_duration + duration_tolerance < expected_duration:
        errors.append(f"audio is truncated: expected {expected_duration:.3f}s, got {audio_duration:.3f}s")

    passed_decode, decode_error = decode_ok(video)
    if not passed_decode:
        errors.append(f"full-file decode failed: {decode_error or 'unknown ffmpeg error'}")

    return {
        "schemaVersion": "ngg-v4-portrait-final-media-qa-v1",
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "expected": expected,
        "actual": {
            "width": int(video_stream.get("width") or 0),
            "height": int(video_stream.get("height") or 0),
            "fpsText": actual_fps_text,
            "fps": actual_fps,
            "decodedFrames": actual_frames,
            "videoCodec": video_stream.get("codec_name"),
            "pixelFormat": video_stream.get("pix_fmt"),
            "audioCodec": audio_stream.get("codec_name") if audio_stream else None,
            "audioDurationSec": audio_duration,
            "formatDurationSec": format_duration,
            "color": color_actual,
            "fullDecodePassed": passed_decode,
        },
    }


def markdown_report(report: dict[str, Any], video: Path, visual_script: Path) -> str:
    lines = [
        "# Final Media QA",
        "",
        f"- Status: {'PASS' if report['passed'] else 'FAIL'}",
        f"- Video: `{video}`",
        f"- Visual script: `{visual_script}`",
        "",
        "## Expected",
        "",
        f"- {report['expected']['width']}x{report['expected']['height']}",
        f"- {report['expected']['fps']} fps",
        f"- {report['expected']['durationFrames']} frames",
        "",
        "## Actual",
        "",
        f"- {report['actual']['width']}x{report['actual']['height']}",
        f"- {report['actual']['fpsText']} fps",
        f"- {report['actual']['decodedFrames']} decoded frames",
        f"- {report['actual']['videoCodec']} / {report['actual']['audioCodec']}",
        f"- Full decode: {'PASS' if report['actual']['fullDecodePassed'] else 'FAIL'}",
    ]
    if report["errors"]:
        lines.extend(["", "## Errors", ""] + [f"- {item}" for item in report["errors"]])
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""] + [f"- {item}" for item in report["warnings"]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="Markdown report path; defaults to qa/final_media_qa.md.")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--allow-no-audio", action="store_true")
    parser.add_argument("--relaxed-color", action="store_true")
    args = parser.parse_args()
    if not args.video.is_file():
        raise SystemExit(f"missing video: {args.video}")
    if not args.visual_script.is_file():
        raise SystemExit(f"missing visual script: {args.visual_script}")

    report = analyze(
        args.video,
        args.visual_script,
        require_audio=not args.allow_no_audio,
        strict_color=not args.relaxed_color,
    )
    out = args.out or args.visual_script.parent / "qa" / "final_media_qa.md"
    json_out = args.json_out or out.with_suffix(".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown_report(report, args.video, args.visual_script), encoding="utf-8")
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"final media QA: {'PASS' if report['passed'] else 'FAIL'} ({out})")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
