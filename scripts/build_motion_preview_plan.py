#!/usr/bin/env python3
"""Build short dynamic QA preview ranges for presenter motion and depth typography."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
    return normalized or "motion"


def clamp_range(start: int, end: int, duration: int) -> tuple[int, int]:
    start = max(0, min(duration - 1, start))
    end = max(start + 1, min(duration, end))
    return start, end


def build_plan(data: dict[str, Any], max_previews: int = 12) -> list[dict[str, Any]]:
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    fps = max(1, int(composition.get("fps") or 25))
    duration = max(1, int(composition.get("durationFrames") or 1))
    candidates: list[dict[str, Any]] = []

    for event in data.get("visualEvents", []):
        if not isinstance(event, dict):
            continue
        start = int(event.get("startFrame", 0) or 0)
        end = int(event.get("endFrame", start + 1) or start + 1)
        if event.get("motionType") == "presenter-impact-punch":
            preview_start, preview_end = clamp_range(
                start - round(0.4 * fps),
                end + round(0.5 * fps),
                duration,
            )
            candidates.append(
                {
                    "id": safe_id(str(event.get("id") or "presenter-impact")),
                    "kind": "presenter-impact",
                    "startFrame": preview_start,
                    "endFrame": preview_end,
                    "focusStartFrame": start,
                    "focusEndFrame": end,
                    "sourceEventId": event.get("id"),
                }
            )
        elif event.get("type") in {"depthTitle", "depthKeyword"} or event.get("depthTitleCandidate") is True:
            depth_start = int(event.get("depthStartFrame", start) or start)
            depth_end = int(event.get("depthEndFrame", end) or end)
            preview_start, preview_end = clamp_range(
                depth_start - round(0.3 * fps),
                depth_end + round(0.3 * fps),
                duration,
            )
            candidates.append(
                {
                    "id": safe_id(str(event.get("id") or "depth-title")),
                    "kind": "depth-title",
                    "startFrame": preview_start,
                    "endFrame": preview_end,
                    "focusStartFrame": depth_start,
                    "focusEndFrame": depth_end,
                    "sourceEventId": event.get("id"),
                }
            )

    scenes = sorted(
        (scene for scene in data.get("scenes", []) if isinstance(scene, dict)),
        key=lambda scene: int(scene.get("startFrame", 0) or 0),
    )
    for previous, current in zip(scenes, scenes[1:]):
        if previous.get("presenterLayout") == current.get("presenterLayout"):
            continue
        boundary = int(current.get("startFrame", 0) or 0)
        preview_start, preview_end = clamp_range(
            boundary - round(0.9 * fps),
            boundary + round(0.6 * fps),
            duration,
        )
        candidates.append(
            {
                "id": safe_id(f"layout-{previous.get('id')}-to-{current.get('id')}"),
                "kind": "presenter-layout-transition",
                "startFrame": preview_start,
                "endFrame": preview_end,
                "focusStartFrame": max(0, boundary - round(0.8 * fps)),
                "focusEndFrame": boundary,
                "fromLayout": previous.get("presenterLayout"),
                "toLayout": current.get("presenterLayout"),
            }
        )

    priority = {"presenter-impact": 0, "presenter-layout-transition": 1, "depth-title": 2}
    candidates.sort(key=lambda item: (priority.get(str(item.get("kind")), 9), int(item["startFrame"])))
    output = candidates[: max(1, max_previews)]
    for index, item in enumerate(output, start=1):
        item["outputPath"] = f"qa/motion_previews/clips/{index:02d}_{item['id']}.mp4"
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--max-previews", type=int, default=12)
    args = parser.parse_args()

    data = json.loads(args.visual_script.read_text(encoding="utf-8-sig"))
    plan = build_plan(data, args.max_previews)
    out = args.out or args.visual_script.parent / "qa" / "motion_previews" / "plan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"previews": plan}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"motion preview plan: {out} ({len(plan)} clips)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
