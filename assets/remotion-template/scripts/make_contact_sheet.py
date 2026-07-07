#!/usr/bin/env python3
"""Create a contact sheet from a rendered video and visual_script qaFrames."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()


def load_frames(path: Path) -> list[int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    frames = []
    for item in data.get("qaFrames", []):
        if isinstance(item, dict) and isinstance(item.get("frame"), int):
            frames.append(max(0, item["frame"]))
    return sorted(set(frames))


def extract_frame(video: Path, frame: int, fps: int, out: Path) -> None:
    timestamp = frame / fps
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-vf",
        "scale=480:-1",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def make_sheet(images: list[Path], out: Path, columns: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required but was not found on PATH")
    rows = math.ceil(len(images) / columns)
    input_dir = images[0].parent
    for idx, image in enumerate(images):
        shutil.copyfile(image, input_dir / f"sheet_{idx:03d}.png")
    input_pattern = input_dir / "sheet_%03d.png"
    filter_complex = (
        f"tile={columns}x{rows}:nb_frames={len(images)}:"
        "margin=12:padding=8:color=0x111111"
    )
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        "1",
        "-i",
        str(input_pattern),
        "-vf",
        filter_complex,
        "-frames:v",
        "1",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--columns", type=int, default=4)
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"missing video: {args.video}")
    if not args.visual_script.exists():
        raise SystemExit(f"missing visual script: {args.visual_script}")

    frames = load_frames(args.visual_script)
    if not frames:
        raise SystemExit("visual script has no qaFrames")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        images = []
        for idx, frame in enumerate(frames):
            image = tmp_path / f"frame_{idx:03d}_{frame}.png"
            extract_frame(args.video, frame, args.fps, image)
            images.append(image)
        make_sheet(images, args.out, args.columns)

    print(f"contact sheet written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
