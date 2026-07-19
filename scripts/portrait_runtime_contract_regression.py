#!/usr/bin/env python3
"""Regression checks for portrait caption rendering and continuous presenter playback."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from validate_visual_script import validate


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "assets" / "remotion-template" / "config" / "visual_script.example.json"
COMPOSITION = ROOT / "assets" / "remotion-template" / "src" / "V4Composition.tsx"
PRIMITIVES = ROOT / "assets" / "remotion-template" / "src" / "components" / "V4Primitives.tsx"


def validate_data(data: dict) -> list[str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "visual_script.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        errors, _warnings = validate(path)
        return errors


def main() -> int:
    base = json.loads(EXAMPLE.read_text(encoding="utf-8-sig"))

    no_caption = copy.deepcopy(base)
    no_caption["captionRenderMode"] = "none"
    if errors := validate_data(no_caption):
        raise AssertionError(f"captionRenderMode=none must preserve a valid semantic timeline: {errors}")
    if not no_caption.get("captionCues") or not no_caption.get("captionTimeline"):
        raise AssertionError("captionRenderMode=none must not delete caption timing data")

    invalid = copy.deepcopy(base)
    invalid["captionRenderMode"] = "burned-and-embedded"
    errors = validate_data(invalid)
    if not any("captionRenderMode must be embedded or none" in error for error in errors):
        raise AssertionError(f"invalid caption render mode was not rejected: {errors}")

    source = COMPOSITION.read_text(encoding="utf-8")
    if source.count("<OffthreadVideo") != 1:
        raise AssertionError("portrait template must mount exactly one primary OffthreadVideo")
    if "startFrom=" in source:
        raise AssertionError("portrait presenter must not restart or seek at scene boundaries")
    if "visualScript.captionRenderMode !== 'none'" not in source:
        raise AssertionError("portrait template does not gate the rendered caption layer")
    if "PRESENTER_LAYOUT_TRANSITION_SECONDS = 0.8" not in source:
        raise AssertionError("portrait template lost the confirmed 0.8-second layout transition")
    if "preExitStart" not in source or "presenterMotionStateFor" not in source:
        raise AssertionError("portrait PiP return is not pre-animated to land on the scene boundary")

    primitives = PRIMITIVES.read_text(encoding="utf-8")
    if "isTopRight" not in primitives or "right: isTopRight ? 46 : undefined" not in primitives:
        raise AssertionError("source-bound top-right status stickers must not collide with the top-left chapter label")
    if "top: isPortrait ? 150 : 420" not in primitives:
        raise AssertionError("portrait claim strips must stay above the center eye/face band")
    if "const displayText = text" not in primitives or ".trimEnd();" not in primitives:
        raise AssertionError("portrait captions must derive a display-only terminal-punctuation-trimmed copy")
    if "Array.from(displayText)" not in primitives or ">{displayText}</span>" not in primitives:
        raise AssertionError("portrait caption sizing and rendering must use the display copy")
    if "top: isPortrait ? '75%' : undefined" not in primitives:
        raise AssertionError("portrait captions must be centered one-quarter above the bottom")
    if "transform: isPortrait ? 'translate(-50%, -50%)'" not in primitives:
        raise AssertionError("portrait caption quarter-height placement must anchor the strip center")
    if "whiteSpace: 'nowrap'" not in primitives:
        raise AssertionError("portrait captions must remain on one rendered line")

    print("portrait runtime contract regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
