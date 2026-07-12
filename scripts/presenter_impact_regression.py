#!/usr/bin/env python3
"""Regression checks for portrait presenter-impact punches."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from validate_visual_script import validate


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "assets" / "remotion-template" / "config" / "visual_script.example.json"


def validate_data(data: dict) -> list[str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "visual_script.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        errors, _warnings = validate(path)
        return errors


def impact(event_id: str, start: int, end: int) -> dict:
    return {
        "id": event_id,
        "sceneId": "scene-004",
        "type": "presenterReposition",
        "startFrame": start,
        "endFrame": end,
        "semanticRole": "cta-resolve",
        "sourceBeatId": "beat-008",
        "motionType": "presenter-impact-punch",
        "presenterPeakScale": 1.08,
        "presenterSettleScale": 1.04,
    }


def main() -> int:
    base = json.loads(EXAMPLE.read_text(encoding="utf-8-sig"))

    valid = copy.deepcopy(base)
    valid["visualEvents"].append(impact("impact-valid", 650, 670))
    errors = validate_data(valid)
    if errors:
        raise AssertionError(f"valid portrait impact failed: {errors}")

    slow = copy.deepcopy(base)
    slow["visualEvents"].append(impact("impact-slow", 650, 730))
    errors = validate_data(slow)
    if not any("presenter impact impact-slow lasts" in error for error in errors):
        raise AssertionError(f"slow portrait drift was not rejected: {errors}")

    crowded = copy.deepcopy(base)
    crowded["visualEvents"].extend(
        [impact("impact-a", 160, 180), impact("impact-b", 300, 320)]
    )
    errors = validate_data(crowded)
    if not any("presenter impacts impact-a and impact-b" in error for error in errors):
        raise AssertionError(f"crowded portrait impacts were not rejected: {errors}")

    print("portrait presenter impact regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
