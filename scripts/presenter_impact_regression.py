#!/usr/bin/env python3
"""Regression checks for portrait semantic-lifecycle presenter impacts."""

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
        "semanticRole": "positive-confirm",
        "sourceBeatId": "beat-008",
        "motionType": "presenter-impact-punch",
        "presenterPeakScale": 1.08,
    }


def companion(event_id: str, start: int, end: int) -> dict:
    return {
        "id": event_id,
        "sceneId": "scene-004",
        "type": "statusSticker",
        "startFrame": start,
        "endFrame": end,
        "text": "语义重点",
        "sourceBeatId": "beat-008",
        "semanticRole": "positive-confirm",
        "motionType": "confirm-pop",
        "safeArea": "left-safe",
    }


def main() -> int:
    base = json.loads(EXAMPLE.read_text(encoding="utf-8-sig"))

    valid = copy.deepcopy(base)
    valid["visualEvents"].append(impact("impact-valid", 650, 670))
    errors = validate_data(valid)
    if errors:
        raise AssertionError(f"valid portrait impact failed: {errors}")

    synced = copy.deepcopy(base)
    synced["visualEvents"].extend(
        [impact("impact-synced", 650, 730), companion("companion-synced", 650, 730)]
    )
    errors = validate_data(synced)
    if errors:
        raise AssertionError(f"valid portrait lifecycle-synced impact failed: {errors}")

    mismatched = copy.deepcopy(base)
    mismatched["visualEvents"].extend(
        [impact("impact-mismatched", 650, 730), companion("companion-mismatched", 651, 730)]
    )
    errors = validate_data(mismatched)
    if not any("presenter impact impact-mismatched lasts" in error for error in errors):
        raise AssertionError(f"mismatched portrait lifecycle range was not rejected: {errors}")

    too_long = copy.deepcopy(base)
    too_long["composition"]["durationFrames"] = 810
    too_long["scenes"][-1]["endFrame"] = 810
    too_long["visualEvents"].extend(
        [impact("impact-too-long", 650, 801), companion("companion-too-long", 650, 801)]
    )
    errors = validate_data(too_long)
    if not any("presenter impact impact-too-long lasts" in error for error in errors):
        raise AssertionError(f"overlong portrait lifecycle sync was not rejected: {errors}")

    cta = copy.deepcopy(base)
    cta_impact = impact("impact-cta", 650, 670)
    cta_impact["semanticRole"] = "cta-resolve"
    cta["visualEvents"].append(cta_impact)
    errors = validate_data(cta)
    if not any("presenter impact impact-cta must bind" in error for error in errors):
        raise AssertionError(f"portrait CTA camera impact was not rejected: {errors}")

    crowded = copy.deepcopy(base)
    crowded["visualEvents"].extend(
        [impact("impact-a", 160, 180), impact("impact-b", 300, 320)]
    )
    errors = validate_data(crowded)
    if not any("presenter impact starts impact-a and impact-b" in error for error in errors):
        raise AssertionError(f"crowded portrait impacts were not rejected: {errors}")

    print("portrait presenter impact regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
