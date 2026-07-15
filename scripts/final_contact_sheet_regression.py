#!/usr/bin/env python3
"""Regression for final encoded exact-frame contact-sheet planning and extraction."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from make_contact_sheet import generate_contact_sheet


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="v4-final-contact-") as temp_dir:
        root = Path(temp_dir)
        video = root / "final.mp4"
        visual_script = root / "visual_script.json"
        sheet = root / "contact.png"
        manifest = root / "contact.json"
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
                "testsrc2=size=160x90:rate=25:duration=0.4",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(video),
            ],
            check=True,
        )
        data = {
            "composition": {
                "width": 160,
                "height": 90,
                "fps": 25,
                "durationFrames": 10,
            },
            "qaFrames": [{"frame": 1, "reason": "manual QA"}],
            "visualEvents": [
                {
                    "id": "depth",
                    "type": "depthTitle",
                    "startFrame": 2,
                    "endFrame": 5,
                },
                {
                    "id": "proof",
                    "type": "materialMain",
                    "startFrame": 6,
                    "endFrame": 9,
                },
            ],
        }
        visual_script.write_text(json.dumps(data), encoding="utf-8")
        plan = generate_contact_sheet(video, visual_script, sheet, manifest)
        frames = [item["frame"] for item in plan["frames"]]
        expected = [0, 1, 2, 3, 4, 6, 7, 8, 9]
        if frames != expected:
            raise AssertionError(f"unexpected exact-frame plan: {frames}")
        if not sheet.is_file() or sheet.stat().st_size <= 0:
            raise AssertionError("contact sheet was not generated")
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        if [item["frame"] for item in saved["frames"]] != expected:
            raise AssertionError("contact sheet manifest does not match the extracted tile order")

    print("final encoded contact-sheet regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

