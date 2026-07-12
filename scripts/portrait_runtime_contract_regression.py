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

    print("portrait runtime contract regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
