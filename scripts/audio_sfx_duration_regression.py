#!/usr/bin/env python3
"""Regression for active SFX duration against the real source asset."""

from __future__ import annotations

import copy
import tempfile
import wave
from pathlib import Path

from qa_lint_visual_script import media_checks


def write_silence(path: Path, duration_sec: float = 2.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 48_000
    sample_count = round(sample_rate * duration_sec)
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(2)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(b"\x00\x00\x00\x00" * sample_count)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="v4-sfx-duration-") as temp_dir:
        root = Path(temp_dir)
        write_silence(root / "public" / "input" / "long.wav")
        data = {
            "composition": {"fps": 25},
            "scenes": [],
            "semanticBeats": [],
            "visualEvents": [],
            "audioCues": [
                {
                    "id": "active-too-short",
                    "type": "sfx",
                    "path": "input/long.wav",
                    "startFrame": 0,
                    "durationFrames": 25,
                    "status": "active",
                }
            ],
        }
        errors, _warnings = media_checks(data, root)
        if not any("audio-sfx-truncation failed" in item for item in errors):
            raise AssertionError(f"active truncated SFX was not rejected: {errors}")

        suggested = copy.deepcopy(data)
        suggested["audioCues"][0]["status"] = "suggested"
        errors, _warnings = media_checks(suggested, root)
        if any("audio-sfx-truncation failed" in item for item in errors):
            raise AssertionError(f"silent suggested SFX must not be treated as rendered: {errors}")

        exact = copy.deepcopy(data)
        exact["audioCues"][0]["durationFrames"] = 50
        errors, _warnings = media_checks(exact, root)
        if any("audio-sfx-truncation failed" in item for item in errors):
            raise AssertionError(f"frame-exact active SFX should pass: {errors}")

    print("active SFX duration regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

