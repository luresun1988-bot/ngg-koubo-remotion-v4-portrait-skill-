#!/usr/bin/env python3
"""Regression checks for recording-proof motion detection."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from proof_motion_qa import evaluate_project  # noqa: E402
import semantic_router  # noqa: E402
import semantic_router_regression  # noqa: E402
import visual_event_builder  # noqa: E402


def make_video(path: Path, source: str) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required for proof motion regression")
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", source, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))


def visual_script(path_value: str) -> dict:
    return {"visualEvents": [{"id": "proof-001", "type": "materialMain", "style": "recording-proof", "motionType": "screen-recording-proof", "assetPath": path_value}]}


def assert_builder_media_truth() -> None:
    case = next(item for item in semantic_router_regression.CASES if item.get("id") == "proof-01")
    for suffix, expected_style, expected_motion in (
        ("png", "single-proof", "material-zoom-highlight"),
        ("mp4", "recording-proof", "screen-recording-proof"),
    ):
        data = semantic_router_regression.visual_script_for_case(case, 0)
        data["media"] = [{"id": "proof", "type": "recording" if suffix == "mp4" else "screenshot", "role": "proof-material", "path": f"input/proof.{suffix}"}]
        semantic_router.apply_semantic_beats(data)
        visual_event_builder.apply_visual_events(data)
        proof_event = next(event for event in data["visualEvents"] if event.get("type") == "materialMain")
        if proof_event.get("style") != expected_style or proof_event.get("motionType") != expected_motion:
            raise AssertionError(f"proof material routing mismatch for {suffix}: {proof_event}")


def main() -> int:
    assert_builder_media_truth()
    with tempfile.TemporaryDirectory(prefix="ngg-v4-portrait-proof-motion-") as temp_dir:
        root = Path(temp_dir)
        media_dir = root / "public" / "input" / "assets"
        media_dir.mkdir(parents=True)
        static_path = media_dir / "静止录屏.mp4"
        moving_path = media_dir / "动态录屏.mp4"
        make_video(static_path, "color=c=blue:s=320x180:r=25:d=2")
        make_video(moving_path, "testsrc2=size=320x180:rate=25:duration=2")
        frozen = evaluate_project(visual_script("input/assets/静止录屏.mp4"), root)
        if frozen.get("passed") or not any("proof-motion-frozen" in error for error in frozen.get("errors", [])):
            raise AssertionError(f"static video must fail recording-proof motion QA: {frozen}")
        moving = evaluate_project(visual_script("input/assets/动态录屏.mp4"), root)
        if not moving.get("passed") or moving.get("errors") or moving["items"][0].get("classification") != "motion-detected":
            raise AssertionError(f"moving recording must pass proof motion QA: {moving}")
        missing = evaluate_project(visual_script("input/assets/missing.mp4"), root)
        if missing.get("passed") or not any("proof-motion-path" in error for error in missing.get("errors", [])):
            raise AssertionError(f"missing recording must fail: {missing}")
        escaped = evaluate_project(visual_script("../outside.mp4"), root)
        if escaped.get("passed") or not any("escapes Remotion public" in error for error in escaped.get("errors", [])):
            raise AssertionError(f"escaped recording path must fail: {escaped}")
        no_recording = evaluate_project({"visualEvents": [{"id": "still", "type": "materialMain", "style": "static-proof", "assetPath": "input/assets/still.png"}]}, root)
        if not no_recording.get("passed") or no_recording.get("items"):
            raise AssertionError(f"static proof image must be outside recording motion QA: {no_recording}")
    print("portrait proof motion QA regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
