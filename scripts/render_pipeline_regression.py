#!/usr/bin/env python3
"""Exercise the BT.709 + final-QA path of the one-command render pipeline."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from final_media_qa import analyze


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "remotion-template"
PIPELINE = SKILL_ROOT / "scripts" / "render_final_and_qa.ps1"


def main() -> int:
    powershell = shutil.which("powershell")
    if not powershell:
        raise SystemExit("PowerShell is required for render pipeline regression")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        raw = root / "raw.mp4"
        final = root / "final.mp4"
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
                "sine=frequency=550:sample_rate=48000:duration=1.4",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(raw),
            ],
            check=True,
        )
        visual_script.write_text(
            json.dumps({"composition": {"width": 270, "height": 480, "fps": 25, "durationFrames": 25}}),
            encoding="utf-8",
        )
        raw_report = analyze(raw, visual_script, strict_color=False)
        raw_actual = raw_report.get("actual", {})
        raw_tail = float(raw_actual.get("audioDurationSec") or 0) - float(
            raw_actual.get("videoDurationSec") or 0
        )
        if raw_tail < 0.3:
            raise AssertionError(f"regression fixture must contain a long audio tail: {raw_actual}")
        completed = subprocess.run(
            [
                powershell,
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(PIPELINE),
                "-RemotionRoot",
                str(TEMPLATE_ROOT),
                "-VisualScript",
                str(visual_script),
                "-Output",
                str(final),
                "-RawInput",
                str(raw),
                "-PostprocessOnly",
                "-Force",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"render pipeline failed:\n{completed.stdout}\n{completed.stderr}")
        report = analyze(final, visual_script)
        if not report.get("passed"):
            raise AssertionError(report)
        actual = report.get("actual", {})
        expected_duration = 1.0
        for key in ("videoDurationSec", "audioDurationSec", "formatDurationSec"):
            if abs(float(actual.get(key) or 0) - expected_duration) > 1e-6:
                raise AssertionError(f"pipeline must trim {key} to {expected_duration:.6f}s: {actual}")
        contact_sheet = root / "qa" / "final_encoded_contact_sheet.png"
        contact_manifest = root / "qa" / "final_encoded_contact_sheet.json"
        if not contact_sheet.is_file() or not contact_manifest.is_file():
            raise AssertionError("pipeline did not generate final encoded contact-sheet evidence")
        manifest = json.loads(contact_manifest.read_text(encoding="utf-8"))
        selected = [item.get("frame") for item in manifest.get("frames", [])]
        if selected != [0, 24]:
            raise AssertionError(f"pipeline contact sheet must include exact first/last frames: {selected}")
    print("portrait render pipeline regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
