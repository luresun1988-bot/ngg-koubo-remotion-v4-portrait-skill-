#!/usr/bin/env python3
"""Regression checks for portrait no-auto-side presenter layout policy."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from validate_visual_script import validate
from visual_event_builder import apply_visual_events, validate_presenter_layout_policy


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "assets" / "remotion-template" / "config" / "visual_script.example.json"
COMPOSITION = ROOT / "assets" / "remotion-template" / "src" / "V4Composition.tsx"
INITIALIZER = ROOT / "scripts" / "init_v4_project.py"


def validate_data(data: dict) -> tuple[list[str], list[str]]:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "visual_script.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return validate(path)


def side_case(base: dict, source: str | None) -> dict:
    data = copy.deepcopy(base)
    scene = data["scenes"][0]
    scene["presenterLayout"] = "side"
    if source is None:
        scene.pop("presenterLayoutSource", None)
    else:
        scene["presenterLayoutSource"] = source
    return data


def main() -> int:
    base = json.loads(EXAMPLE.read_text(encoding="utf-8-sig"))

    automatic_side = side_case(base, "automatic")
    errors, _warnings = validate_data(automatic_side)
    if not any("automatic presenterLayout=side is forbidden" in error for error in errors):
        raise AssertionError(f"automatic portrait side layout was not rejected: {errors}")
    try:
        validate_presenter_layout_policy(automatic_side)
    except ValueError as error:
        if "manual/legacy compatibility only" not in str(error):
            raise
    else:
        raise AssertionError("visual event builder accepted automatic portrait side layout")

    for approved_source in ("manual-approved", "legacy-project"):
        approved = side_case(base, approved_source)
        errors, warnings = validate_data(approved)
        if errors:
            raise AssertionError(f"{approved_source} portrait side layout failed: {errors}")
        if any("unmarked presenterLayout=side" in warning for warning in warnings):
            raise AssertionError(f"{approved_source} side layout was incorrectly marked unapproved")
        validate_presenter_layout_policy(approved)

    unmarked_legacy = side_case(base, None)
    errors, warnings = validate_data(unmarked_legacy)
    if errors:
        raise AssertionError(f"unmarked legacy side layout lost compatibility: {errors}")
    if not any("unmarked presenterLayout=side" in warning for warning in warnings):
        raise AssertionError("unmarked legacy side layout did not receive a migration warning")
    validate_presenter_layout_policy(unmarked_legacy)

    invalid_source = side_case(base, "semantic-router")
    errors, _warnings = validate_data(invalid_source)
    if not any("invalid presenterLayoutSource" in error for error in errors):
        raise AssertionError(f"invalid presenter layout provenance was not rejected: {errors}")

    routed = copy.deepcopy(base)
    for scene in routed["scenes"]:
        scene["presenterLayoutSource"] = "automatic"
    before = [scene["presenterLayout"] for scene in routed["scenes"]]
    apply_visual_events(routed)
    after = [scene["presenterLayout"] for scene in routed["scenes"]]
    if after != before or "side" in after:
        raise AssertionError(f"automatic event building changed presenter layout: {before} -> {after}")

    source = COMPOSITION.read_text(encoding="utf-8")
    if "if (layout === 'side')" not in source:
        raise AssertionError("portrait template lost legacy/manual side rendering compatibility")
    presenter_block = source[source.index("const ContinuousPresenter"):source.index("const GridOverlay")]
    if "scale: impactScale" not in presenter_block or "translateX" in presenter_block:
        raise AssertionError("presenter impact must remain scale-only without horizontal translation")
    initializer_source = INITIALIZER.read_text(encoding="utf-8")
    if '"presenterLayoutSource": "automatic"' not in initializer_source:
        raise AssertionError("new portrait projects must mark generated presenter layouts as automatic")

    print("portrait presenter layout policy regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
