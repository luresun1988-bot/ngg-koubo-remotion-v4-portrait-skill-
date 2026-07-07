#!/usr/bin/env python3
"""Regression checks for V4 visual density scheduling."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import visual_event_builder  # noqa: E402
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()


def base_script() -> dict[str, Any]:
    return {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "sourceVideoMode": "raw-presenter",
        "packagingDensity": "dense",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 25, "durationFrames": 400},
        "media": [],
        "scenes": [],
        "captionCues": [],
        "semanticBeats": [],
        "visualEvents": [],
        "audioCues": [],
        "qaFrames": [],
    }


def routed_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [event for event in data["visualEvents"] if event.get("type") != "cornerChapterLabel"]


def dense_scene_gets_refreshes() -> bool:
    data = base_script()
    data["scenes"] = [
        {
            "id": "scene-dense",
            "type": "Explanation",
            "startFrame": 0,
            "endFrame": 350,
            "presenterLayout": "large",
            "materialLayout": "none",
        }
    ]
    data["semanticBeats"] = [
        {
            "id": "beat-001",
            "sceneId": "scene-dense",
            "startFrame": 0,
            "endFrame": 80,
            "text": "别再手动做主图",
            "semanticIntent": "negative-friction",
            "visualForm": "redWarningCard",
            "keywords": ["手动"],
            "requiredChecks": ["negative-red-treatment"],
        }
    ]
    visual_event_builder.apply_visual_events(data)
    refreshes = [event for event in routed_events(data) if event.get("semanticRole") == "density-refresh"]
    return len(refreshes) >= 1 and all(event.get("densityMode") == "dense" for event in refreshes)


def proof_scene_stays_clean() -> bool:
    data = base_script()
    data["media"] = [{"id": "proof", "type": "recording", "role": "proof-material", "path": "input/proof.mp4"}]
    data["scenes"] = [
        {
            "id": "scene-proof",
            "type": "Proof",
            "startFrame": 0,
            "endFrame": 350,
            "presenterLayout": "pip",
            "materialLayout": "main",
            "semanticRole": "proof-material",
        }
    ]
    data["semanticBeats"] = [
        {
            "id": "beat-001",
            "sceneId": "scene-proof",
            "startFrame": 0,
            "endFrame": 120,
            "text": "看这段录屏，后台已经跑通了",
            "semanticIntent": "proof-material",
            "visualForm": "materialMain",
            "keywords": ["录屏"],
            "requiredChecks": ["proof-video-must-play"],
        }
    ]
    visual_event_builder.apply_visual_events(data)
    events = routed_events(data)
    return (
        any(event.get("type") == "materialMain" and event.get("densityMode") == "proof-focus" for event in events)
        and not any(event.get("semanticRole") == "density-refresh" for event in events)
    )


def precomposed_scene_is_light() -> bool:
    data = base_script()
    data["sourceVideoMode"] = "precomposed-video"
    data["packagingDensity"] = "light"
    data["scenes"] = [
        {
            "id": "scene-light",
            "type": "Explanation",
            "startFrame": 0,
            "endFrame": 350,
            "presenterLayout": "large",
            "materialLayout": "none",
        }
    ]
    data["semanticBeats"] = [
        {
            "id": "beat-001",
            "sceneId": "scene-light",
            "startFrame": 0,
            "endFrame": 80,
            "text": "流程已经跑完，输出完成",
            "semanticIntent": "positive-confirm",
            "visualForm": "greenConfirmCard",
            "keywords": ["完成"],
            "requiredChecks": ["positive-confirm-treatment"],
        }
    ]
    visual_event_builder.apply_visual_events(data)
    events = routed_events(data)
    return (
        any(event.get("densityMode") == "light" for event in events if event.get("type") != "statusSticker")
        and not any(event.get("semanticRole") == "density-refresh" for event in events)
    )


def global_lane_handoff_keeps_buffer() -> bool:
    data = base_script()
    data["composition"]["durationFrames"] = 320
    data["scenes"] = [
        {"id": "scene-001", "type": "Explanation", "startFrame": 0, "endFrame": 150, "presenterLayout": "large", "materialLayout": "none"},
        {"id": "scene-002", "type": "Explanation", "startFrame": 145, "endFrame": 320, "presenterLayout": "large", "materialLayout": "none"},
    ]
    data["semanticBeats"] = [
        {
            "id": "beat-001",
            "sceneId": "scene-001",
            "startFrame": 60,
            "endFrame": 140,
            "text": "别再手动做主图",
            "semanticIntent": "negative-friction",
            "visualForm": "redWarningCard",
            "keywords": ["手动"],
            "requiredChecks": ["negative-red-treatment"],
        },
        {
            "id": "beat-002",
            "sceneId": "scene-002",
            "startFrame": 145,
            "endFrame": 220,
            "text": "不是写代码，是把流程自动化",
            "semanticIntent": "negative-to-positive",
            "visualForm": "negativeWarningThenConfirm",
            "keywords": ["不是", "自动化"],
            "requiredChecks": ["negative-red-treatment", "positive-confirm-treatment"],
        },
    ]
    visual_event_builder.apply_visual_events(data)
    events = [event for event in routed_events(data) if event.get("type") == "highlightBox"]
    events.sort(key=lambda item: item["startFrame"])
    return len(events) == 2 and int(events[1]["startFrame"]) >= int(events[0]["endFrame"]) + 10


def main() -> int:
    checks = [
        ("dense-scene-refreshes", dense_scene_gets_refreshes),
        ("proof-scene-clean", proof_scene_stays_clean),
        ("precomposed-light", precomposed_scene_is_light),
        ("global-lane-buffer", global_lane_handoff_keeps_buffer),
    ]
    failed: list[str] = []
    for name, fn in checks:
        ok = fn()
        print(f"{'PASS' if ok else 'MISS'} {name}")
        if not ok:
            failed.append(name)
    if failed:
        print(f"failed: {', '.join(failed)}")
        return 1
    print(f"passed: {len(checks)} / {len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
