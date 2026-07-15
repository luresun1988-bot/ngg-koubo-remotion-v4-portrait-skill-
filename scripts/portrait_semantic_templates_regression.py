#!/usr/bin/env python3
"""Regression contract for the seven approved portrait semantic templates."""

from __future__ import annotations

from typing import Any

import qa_lint_visual_script
import semantic_router
import visual_event_builder


def fixture(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "sourceVideoMode": "raw-presenter",
        "packagingDensity": "dense",
        "composition": {
            "format": "9:16", "width": 1080, "height": 1920,
            "fps": 25, "durationFrames": 150,
        },
        "scenes": [{
            "id": "scene-001", "type": "Explanation", "startFrame": 0, "endFrame": 150,
            "semanticRole": "explanation-claim", "presenterLayout": "large", "materialLayout": "none",
            "sourceVideo": "input/presenter.mp4", "narrationText": text,
        }],
        "captionCues": [{
            "id": "cap-001", "sceneId": "scene-001", "startFrame": 0, "endFrame": 150, "text": text,
        }],
        "semanticBeats": [], "visualEvents": [], "audioCues": [], "media": [],
    }
    semantic_router.apply_semantic_beats(data)
    visual_event_builder.apply_visual_events(data)
    return data


def primary(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    beat = data["semanticBeats"][0]
    event = next(
        item for item in data["visualEvents"]
        if item.get("sourceBeatId") == beat.get("id") and item.get("type") != "cornerChapterLabel"
    )
    return beat, event


def main() -> int:
    failures: list[str] = []
    cases = [
        ("准备一张高清图片和一段参考音频", "paired-inputs", "pairedInputRail", 2),
        ("音色、情绪和语速都很重要", "parallel-factors", "factorTrinity", 3),
        ("数字人是靠声音驱动的", "causal-driver", "causalDriver", 2),
        ("真正影响效果的是素材质量和参数设置", "factor-priority", "factorPriority", 2),
        ("成片之后，再用增强软件做高清放大", "workflow-step", "compactPipeline", 3),
        ("高清放大救不了错误口型和表情", "limitation-boundary", "limitationWarning", 3),
        ("原视频一定要先做好", "prerequisite", "priorityConclusion", 1),
    ]
    for text, expected_intent, expected_type, expected_steps in cases:
        data = fixture(text)
        beat, event = primary(data)
        steps = event.get("internalSteps") if isinstance(event.get("internalSteps"), list) else []
        provenance_errors, _ = qa_lint_visual_script.layered_hud_step_checks(data)
        ok = (
            beat.get("semanticIntent") == expected_intent
            and beat.get("visualForm") == expected_type
            and event.get("type") == expected_type
            and len(steps) == expected_steps
            and not provenance_errors
            and all(
                isinstance(step, dict)
                and str(step.get("label") or "") in text
                and str(step.get("text") or "") in text
                and step.get("sourceCueIds") == ["cap-001"]
                for step in steps
            )
        )
        print(f"{'PASS' if ok else 'MISS'} {expected_intent}: {text} -> {beat.get('semanticIntent')}/{event.get('type')}")
        if not ok:
            failures.append(f"{text}: beat={beat} event={event} provenance={provenance_errors}")

    adversarial = [
        ("只准备一张高清图片", "paired-inputs"),
        ("音色和语速都很重要", "parallel-factors"),
        ("数字人可能靠声音驱动", "causal-driver"),
        ("素材质量和参数设置会影响效果", "factor-priority"),
        ("先上传然后输出", "compactPipeline"),
        ("高清放大可能无法修复错误口型", "limitation-boundary"),
        ("流程已经完成", "prerequisite"),
    ]
    for text, forbidden_intent in adversarial:
        data = fixture(text)
        beat = data["semanticBeats"][0]
        ok = beat.get("visualForm") != forbidden_intent if forbidden_intent == "compactPipeline" else beat.get("semanticIntent") != forbidden_intent
        print(f"{'PASS' if ok else 'MISS'} guard {forbidden_intent}: {text} -> {beat.get('semanticIntent')}")
        if not ok:
            failures.append(f"guard failed: {text} -> {beat}")

    manual_data = fixture("原视频一定要先做好")
    manual_beat = manual_data["semanticBeats"][0]
    manual_beat["visualForm"] = "historicalGreenConclusion"
    manual_beat["presentationVariant"] = "manual-approved"
    manual_data["visualEvents"] = []
    visual_event_builder.apply_visual_events(manual_data)
    _beat, manual_event = primary(manual_data)
    if (
        manual_event.get("type") != "historicalGreenConclusion"
        or manual_event.get("presentationVariant") != "manual-approved"
    ):
        failures.append(f"manual historical variant was not preserved: {manual_event}")

    safe_data = fixture("原视频一定要先做好")
    safe_beat = safe_data["semanticBeats"][0]
    safe_beat["visualForm"] = "historicalGreenConclusion"
    safe_data["visualEvents"] = []
    visual_event_builder.apply_visual_events(safe_data)
    _beat, safe_event = primary(safe_data)
    if safe_event.get("type") != "priorityConclusion":
        failures.append(f"unapproved historical variant did not fall back to C default: {safe_event}")

    if failures:
        print("\n".join(f"FAIL {failure}" for failure in failures))
        return 1
    print("portrait semantic templates regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
