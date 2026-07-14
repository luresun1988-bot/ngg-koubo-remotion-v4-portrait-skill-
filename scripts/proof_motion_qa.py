#!/usr/bin/env python3
"""Detect recording-proof assets that decode as frozen or effectively static video."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm"}
FRAME_WIDTH = 160
FRAME_HEIGHT = 90
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT
SAMPLE_COUNT = 9


def recording_event_paths(data: dict[str, Any]) -> tuple[dict[str, list[str]], list[str]]:
    paths: dict[str, list[str]] = {}
    missing: list[str] = []
    for index, event in enumerate(data.get("visualEvents", [])):
        if not isinstance(event, dict):
            continue
        style = str(event.get("style") or "")
        motion_type = str(event.get("motionType") or "")
        if "recording-proof" not in style and motion_type != "screen-recording-proof":
            continue
        event_id = str(event.get("id") or f"visualEvents[{index}]")
        values: list[Any] = [event.get("assetPath")]
        asset_stack = event.get("assetStack")
        if isinstance(asset_stack, list):
            values.extend(asset_stack)
        event_paths = [str(value).strip() for value in values if isinstance(value, str) and value.strip()]
        if not event_paths:
            missing.append(event_id)
            continue
        for path_value in event_paths:
            paths.setdefault(path_value, []).append(event_id)
    return paths, missing


def resolve_public_path(remotion_root: Path, path_value: str) -> Path | None:
    public_root = (remotion_root / "public").resolve()
    candidate = (public_root / path_value.replace("\\", "/").lstrip("/")).resolve()
    try:
        candidate.relative_to(public_root)
    except ValueError:
        return None
    return candidate


def probe_duration(path: Path, ffprobe: str) -> float:
    completed = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration:format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "ffprobe failed")
    payload = json.loads(completed.stdout or "{}")
    streams = payload.get("streams", [])
    candidates: list[Any] = []
    if streams and isinstance(streams[0], dict):
        candidates.append(streams[0].get("duration"))
    if isinstance(payload.get("format"), dict):
        candidates.append(payload["format"].get("duration"))
    for candidate in candidates:
        try:
            duration = float(candidate)
        except (TypeError, ValueError):
            continue
        if duration > 0:
            return duration
    raise RuntimeError("video duration is unavailable")


def extract_samples(path: Path, duration: float, ffmpeg: str) -> list[bytes]:
    sampling_rate = SAMPLE_COUNT / max(duration, 1 / SAMPLE_COUNT)
    completed = subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(path), "-an",
            "-vf", f"fps=fps={sampling_rate:.12f}:round=near,scale={FRAME_WIDTH}:{FRAME_HEIGHT}:flags=area,format=gray",
            "-frames:v", str(SAMPLE_COUNT), "-f", "rawvideo", "pipe:1",
        ],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip() or "ffmpeg sample decode failed")
    frame_count = len(completed.stdout) // FRAME_SIZE
    return [completed.stdout[index * FRAME_SIZE : (index + 1) * FRAME_SIZE] for index in range(frame_count)]


def motion_metrics(frames: list[bytes]) -> dict[str, Any]:
    if len(frames) < 2:
        return {"sampledFrames": len(frames), "uniqueFrames": len(set(frames)), "maxChangedPixelRatio": 0.0, "maxMeanAbsDiff": 0.0, "classification": "insufficient-samples"}
    changed_ratios: list[float] = []
    mean_diffs: list[float] = []
    for previous, current in zip(frames, frames[1:]):
        differences = [abs(left - right) for left, right in zip(previous, current)]
        changed_ratios.append(sum(1 for value in differences if value >= 6) / FRAME_SIZE)
        mean_diffs.append(sum(differences) / FRAME_SIZE)
    unique_frames = len(set(frames))
    max_changed_ratio = max(changed_ratios, default=0.0)
    max_mean_diff = max(mean_diffs, default=0.0)
    if unique_frames <= 1 or (max_changed_ratio < 0.0002 and max_mean_diff < 0.02):
        classification = "frozen"
    elif max_changed_ratio < 0.002 and max_mean_diff < 0.15:
        classification = "near-static"
    else:
        classification = "motion-detected"
    return {"sampledFrames": len(frames), "uniqueFrames": unique_frames, "maxChangedPixelRatio": round(max_changed_ratio, 8), "maxMeanAbsDiff": round(max_mean_diff, 6), "classification": classification}


def analyze_asset(path: Path, ffmpeg: str, ffprobe: str) -> dict[str, Any]:
    duration = probe_duration(path, ffprobe)
    return {"durationSec": round(duration, 6), **motion_metrics(extract_samples(path, duration, ffmpeg))}


def evaluate_project(data: dict[str, Any], remotion_root: Path, *, ffmpeg: str | None = None, ffprobe: str | None = None) -> dict[str, Any]:
    ffmpeg = ffmpeg or shutil.which("ffmpeg")
    ffprobe = ffprobe or shutil.which("ffprobe")
    errors: list[str] = []
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    paths, missing_events = recording_event_paths(data)
    for event_id in missing_events:
        errors.append(f"proof-motion-asset failed: {event_id} declares recording proof but has no assetPath/assetStack")
    if paths and (not ffmpeg or not ffprobe):
        errors.append("proof-motion-runtime failed: ffmpeg and ffprobe are required for recording-proof motion QA")
        return {"passed": False, "errors": errors, "warnings": warnings, "items": items}
    for path_value, event_ids in sorted(paths.items()):
        item: dict[str, Any] = {"path": path_value, "eventIds": event_ids}
        candidate = resolve_public_path(remotion_root, path_value)
        if candidate is None:
            item["classification"] = "invalid-path"
            errors.append(f"proof-motion-path failed: {path_value} escapes Remotion public/")
        elif candidate.suffix.lower() not in VIDEO_SUFFIXES:
            item["classification"] = "not-video"
            errors.append(f"proof-motion-type failed: recording proof must use a video file, got {path_value}")
        elif not candidate.is_file():
            item["classification"] = "missing"
            errors.append(f"proof-motion-path failed: recording proof is missing under public/: {path_value}")
        else:
            try:
                item.update(analyze_asset(candidate, str(ffmpeg), str(ffprobe)))
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                item["classification"] = "decode-error"
                item["error"] = str(exc)
                errors.append(f"proof-motion-decode failed: {path_value}: {exc}")
            else:
                classification = str(item.get("classification") or "")
                if classification in {"frozen", "insufficient-samples"}:
                    errors.append(f"proof-motion-frozen failed: {path_value} is declared as recording proof but sampled frames are {classification}")
                elif classification == "near-static":
                    warnings.append(f"proof-motion-near-static warning: {path_value} has very little sampled motion; inspect early/middle/late frames")
        items.append(item)
    return {"passed": not errors, "errors": errors, "warnings": warnings, "items": items}


def markdown_report(report: dict[str, Any]) -> str:
    lines = ["# Proof Motion QA", "", f"Status: {'PASS' if report.get('passed') else 'FAIL'}", ""]
    for item in report.get("items", []):
        lines.append(f"- `{item.get('path')}`: {item.get('classification', 'unknown')}; samples={item.get('sampledFrames', 0)}, unique={item.get('uniqueFrames', 0)}, changedRatio={item.get('maxChangedPixelRatio', 0)}, meanDiff={item.get('maxMeanAbsDiff', 0)}")
    if not report.get("items"):
        lines.append("- No recording-proof video assets were declared.")
    if report.get("errors"):
        lines.extend(["", "## Errors", ""] + [f"- {message}" for message in report["errors"]])
    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""] + [f"- {message}" for message in report["warnings"]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", required=True)
    parser.add_argument("--remotion-root", required=True)
    parser.add_argument("--out", default="qa/proof_motion_qa.md")
    parser.add_argument("--json-out", default="qa/proof_motion_qa.json")
    args = parser.parse_args()
    remotion_root = Path(args.remotion_root).resolve()
    visual_script_path = Path(args.visual_script)
    if not visual_script_path.is_absolute():
        visual_script_path = remotion_root / visual_script_path
    data = json.loads(visual_script_path.read_text(encoding="utf-8-sig"))
    report = evaluate_project(data, remotion_root)
    out_path = Path(args.out)
    json_path = Path(args.json_out)
    if not out_path.is_absolute():
        out_path = remotion_root / out_path
    if not json_path.is_absolute():
        json_path = remotion_root / json_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown_report(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"proof motion QA: {'PASS' if report.get('passed') else 'FAIL'}")
    print(f"wrote {out_path}")
    print(f"wrote {json_path}")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
