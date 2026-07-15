#!/usr/bin/env python3
"""Regression test for final MP4 frame, codec, color, audio, and decode QA."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from final_media_qa import analyze


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        video = root / "final.mp4"
        visual_script = root / "visual_script.json"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=270x480:rate=25:duration=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000:duration=1",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-color_range",
                "tv",
                "-colorspace",
                "bt709",
                "-color_trc",
                "bt709",
                "-color_primaries",
                "bt709",
                "-x264-params",
                "colorprim=bt709:transfer=bt709:colormatrix=bt709",
                "-c:a",
                "aac",
                str(video),
            ],
            check=True,
        )
        data = {
            "composition": {"width": 270, "height": 480, "fps": 25, "durationFrames": 25}
        }
        visual_script.write_text(json.dumps(data), encoding="utf-8")
        report = analyze(video, visual_script)
        if not report.get("passed"):
            raise AssertionError(report)
        levels = report.get("actual", {}).get("audioLevels", {})
        if not levels.get("analyzed") or levels.get("meanVolumeDb") is None or levels.get("maxVolumeDb") is None:
            raise AssertionError(f"final media QA did not record decoded mix levels: {levels}")

        clipped = root / "clipped.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-c:v",
                "copy",
                "-af",
                "volume=20",
                "-c:a",
                "aac",
                str(clipped),
            ],
            check=True,
        )
        clipped_report = analyze(clipped, visual_script)
        if clipped_report.get("passed") or not any(
            "audio clipping risk" in item for item in clipped_report.get("errors", [])
        ):
            raise AssertionError(f"final media QA must reject a clipped decoded mix: {clipped_report}")

        data["composition"]["fps"] = 30
        data["composition"]["durationFrames"] = 30
        visual_script.write_text(json.dumps(data), encoding="utf-8")
        mismatch = analyze(video, visual_script)
        if mismatch.get("passed") or not any("fps mismatch" in item for item in mismatch.get("errors", [])):
            raise AssertionError("final media QA must reject a mismatched project FPS")

    print("portrait final media QA regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
