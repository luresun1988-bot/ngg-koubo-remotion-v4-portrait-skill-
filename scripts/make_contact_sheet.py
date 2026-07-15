#!/usr/bin/env python3
"""Create an exact-frame contact sheet from the final encoded video."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()

HIGH_RISK_EVENT_TYPES = {
    "depthTitle",
    "depthKeyword",
    "presenterReposition",
    "materialMain",
    "materialZoom",
    "transitionPushZoom",
    "ctaTitle",
    "ctaRecommend",
}


def load_qa_selection(path: Path) -> tuple[list[int], int]:
    """Backward-compatible qaFrames/FPS loader used by motion-preview tooling."""
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    frames = sorted(
        {
            max(0, int(item["frame"]))
            for item in data.get("qaFrames", [])
            if isinstance(item, dict) and isinstance(item.get("frame"), int)
        }
    )
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    fps = max(1, int(composition.get("fps") or 25))
    return frames, fps


def _add_frame(
    records: dict[int, dict[str, Any]],
    frame: int,
    duration_frames: int,
    *,
    reason: str,
    source: str,
) -> None:
    if duration_frames <= 0:
        return
    bounded = max(0, min(duration_frames - 1, int(frame)))
    record = records.setdefault(
        bounded,
        {"frame": bounded, "reasons": [], "sources": []},
    )
    if reason not in record["reasons"]:
        record["reasons"].append(reason)
    if source not in record["sources"]:
        record["sources"].append(source)


def build_frame_plan(data: dict[str, Any], max_frames: int = 36) -> dict[str, Any]:
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    duration_frames = int(composition.get("durationFrames") or 0)
    fps = int(composition.get("fps") or 0)
    if duration_frames <= 0 or fps <= 0:
        raise ValueError("composition must define positive fps and durationFrames")
    if max_frames < 2:
        raise ValueError("max_frames must be at least 2")

    records: dict[int, dict[str, Any]] = {}
    _add_frame(records, 0, duration_frames, reason="first encoded frame", source="boundary:first")
    _add_frame(
        records,
        duration_frames - 1,
        duration_frames,
        reason="last encoded frame",
        source="boundary:last",
    )

    for index, item in enumerate(data.get("qaFrames", [])):
        if isinstance(item, dict) and isinstance(item.get("frame"), int):
            reason = str(item.get("reason") or "visual_script qaFrames")
            _add_frame(
                records,
                item["frame"],
                duration_frames,
                reason=reason,
                source=f"qaFrames[{index}]",
            )

    for index, event in enumerate(data.get("visualEvents", [])):
        if not isinstance(event, dict) or event.get("type") not in HIGH_RISK_EVENT_TYPES:
            continue
        start = int(event.get("startFrame") or 0)
        end = int(event.get("endFrame") or start + 1)
        if end <= start:
            continue
        event_id = str(event.get("id") or f"visualEvents[{index}]")
        event_type = str(event.get("type") or "unknown")
        positions = {
            "start": start,
            "mid": start + max(0, (end - start - 1) // 2),
            "end": end - 1,
        }
        for phase, frame in positions.items():
            _add_frame(
                records,
                frame,
                duration_frames,
                reason=f"{event_type} {phase}",
                source=event_id,
            )

    ordered = [records[frame] for frame in sorted(records)]
    total_candidates = len(ordered)
    if total_candidates > max_frames:
        indices = {
            round(index * (total_candidates - 1) / (max_frames - 1))
            for index in range(max_frames)
        }
        ordered = [ordered[index] for index in sorted(indices)]

    return {
        "schemaVersion": "ngg-v4-final-contact-sheet-v1",
        "fps": fps,
        "durationFrames": duration_frames,
        "totalCandidates": total_candidates,
        "selectedCount": len(ordered),
        "omittedCount": total_candidates - len(ordered),
        "frames": [
            {
                **record,
                "timeSec": round(record["frame"] / fps, 6),
                "tileIndex": index,
            }
            for index, record in enumerate(ordered)
        ],
    }


def extract_frames(video: Path, frames: list[int], out_dir: Path) -> list[Path]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required but was not found on PATH")
    if not frames:
        raise ValueError("at least one frame is required")
    selector = "+".join(f"eq(n\\,{frame})" for frame in frames)
    pattern = out_dir / "frame_%03d.png"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video),
        "-vf",
        f"select={selector},scale=480:-2:flags=lanczos",
        "-fps_mode",
        "vfr",
        "-start_number",
        "0",
        "-frames:v",
        str(len(frames)),
        str(pattern),
    ]
    subprocess.run(command, check=True)
    images = [out_dir / f"frame_{index:03d}.png" for index in range(len(frames))]
    missing = [str(path) for path in images if not path.is_file()]
    if missing:
        raise RuntimeError(f"exact-frame extraction returned fewer images than planned: {missing}")
    return images


def make_sheet(images: list[Path], out: Path, columns: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required but was not found on PATH")
    rows = math.ceil(len(images) / columns)
    filter_complex = (
        f"tile={columns}x{rows}:nb_frames={len(images)}:"
        "margin=12:padding=8:color=0x111111"
    )
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-framerate",
        "1",
        "-start_number",
        "0",
        "-i",
        str(images[0].parent / "frame_%03d.png"),
        "-vf",
        filter_complex,
        "-frames:v",
        "1",
        str(out),
    ]
    subprocess.run(command, check=True)


def generate_contact_sheet(
    video: Path,
    visual_script: Path,
    out: Path,
    manifest_out: Path,
    *,
    columns: int = 4,
    max_frames: int = 36,
) -> dict[str, Any]:
    data = json.loads(visual_script.read_text(encoding="utf-8-sig"))
    plan = build_frame_plan(data, max_frames=max_frames)
    frames = [int(item["frame"]) for item in plan["frames"]]
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ngg-v4-final-contact-") as temp_dir:
        images = extract_frames(video, frames, Path(temp_dir))
        make_sheet(images, out, columns)
    plan["video"] = str(video.resolve())
    plan["visualScript"] = str(visual_script.resolve())
    plan["contactSheet"] = str(out.resolve())
    manifest_out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--manifest-out", type=Path)
    parser.add_argument("--fps", type=int, help="Deprecated compatibility option; FPS comes from visual_script.")
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--max-frames", type=int, default=36)
    args = parser.parse_args()

    if not args.video.is_file():
        raise SystemExit(f"missing video: {args.video}")
    if not args.visual_script.is_file():
        raise SystemExit(f"missing visual script: {args.visual_script}")
    manifest_out = args.manifest_out or args.out.with_suffix(".json")
    plan = generate_contact_sheet(
        args.video,
        args.visual_script,
        args.out,
        manifest_out,
        columns=args.columns,
        max_frames=args.max_frames,
    )
    print(
        f"final encoded contact sheet: {plan['selectedCount']} exact frames "
        f"({args.out}; manifest {manifest_out})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
