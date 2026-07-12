#!/usr/bin/env python3
"""Regression checks for dynamic motion preview planning."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from build_motion_preview_plan import build_plan
from make_contact_sheet import load_qa_selection


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "assets" / "remotion-template" / "config" / "visual_script.example.json"


def main() -> int:
    data = json.loads(EXAMPLE.read_text(encoding="utf-8-sig"))
    data = copy.deepcopy(data)
    frames, contact_sheet_fps = load_qa_selection(EXAMPLE)
    if not frames or contact_sheet_fps != int(data["composition"]["fps"]):
        raise AssertionError("contact sheet must derive FPS from visual_script.json")
    data["visualEvents"].append(
        {
            "id": "impact-test",
            "sceneId": "scene-004",
            "type": "presenterReposition",
            "startFrame": 650,
            "endFrame": 670,
            "semanticRole": "cta-resolve",
            "sourceBeatId": "beat-008",
            "motionType": "presenter-impact-punch",
        }
    )
    plan = build_plan(data)
    kinds = [item.get("kind") for item in plan]
    if kinds.count("presenter-impact") != 1:
        raise AssertionError(plan)
    if kinds.count("presenter-layout-transition") != 2:
        raise AssertionError(plan)
    impact = next(item for item in plan if item.get("kind") == "presenter-impact")
    if not (impact["startFrame"] < impact["focusStartFrame"] < impact["endFrame"]):
        raise AssertionError(impact)
    if not all(str(item.get("outputPath", "")).endswith(".mp4") for item in plan):
        raise AssertionError(plan)
    print("portrait motion preview regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
