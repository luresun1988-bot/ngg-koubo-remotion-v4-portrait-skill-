#!/usr/bin/env python3
"""Regression checks for source-bound component facts and safe downgrade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import qa_lint_visual_script
from visual_event_builder import event_for_beat


SCHEMA = "ngg-koubo-remotion-v4-portrait"
FORMAT = "9:16"
WIDTH, HEIGHT = 1080, 1920

CASES = [
    ("manual-field", "需要处理重复字段", False, "missing-field-entities", 2),
    ("manual-field", "标题、简介和标签需要重复填写", True, "", 2),
    ("workflow-fields", "首先处理，然后完成", False, "missing-workflow-steps", 2),
    ("workflow-fields", "首先上传，然后填写标题，最后输出视频", True, "", 2),
    ("asset-variants", "生成多尺寸主图", False, "missing-variant-entities", 2),
    ("asset-variants", "生成16:9、3:4和1:1三种主图", True, "", 2),
    ("platform-fanout", "发布到多个平台", False, "missing-platform-entities", 2),
    ("platform-fanout", "发布到抖音、小红书和B站", True, "", 2),
    ("capability-share", "企业大模型能力正在变化", False, "missing-comparison-entities", 2),
    ("capability-share", "OpenAI、Google和Anthropic的能力对比", True, "", 2),
    ("scene-lock", "这些场景正在落地", False, "missing-scene-entities", 2),
    ("scene-lock", "支付、教育和政务场景正在落地", True, "", 2),
    ("automation-handoff", "这一步需要自动化", False, "missing-handoff-evidence", 1),
    ("automation-handoff", "把任务交给系统自动执行", True, "", 1),
]

BANNED = {
    "定义规则", "自动执行", "输出结果", "渠道适配", "多端发布", "统一交付",
    "比较对象", "能力指标", "差异结论", "OpenAI", "Google", "Anthropic",
}


def fixture(intent: str, text: str, index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    cue_id = f"cap-{index:03d}"
    beat = {
        "id": f"beat-{index:03d}",
        "sceneId": "scene-001",
        "startFrame": 0,
        "endFrame": 150,
        "text": text,
        "semanticIntent": intent,
        "visualForm": intent,
        "sourceCueIds": [cue_id],
    }
    data = {
        "schemaVersion": SCHEMA,
        "composition": {
            "format": FORMAT, "width": WIDTH, "height": HEIGHT,
            "fps": 25, "durationFrames": 150,
        },
        "scenes": [{
            "id": "scene-001", "type": "Explanation", "startFrame": 0, "endFrame": 150,
            "presenterLayout": "large", "materialLayout": "none",
        }],
        "captionCues": [{
            "id": cue_id, "sceneId": "scene-001", "startFrame": 0, "endFrame": 150,
            "text": text,
        }],
        "semanticBeats": [beat],
        "visualEvents": [],
        "audioCues": [],
        "media": [],
    }
    return beat, data


def main() -> int:
    failures: list[str] = []
    for index, (intent, source, should_render, reason, minimum) in enumerate(CASES, 1):
        beat, data = fixture(intent, source, index)
        event = event_for_beat(beat, data)
        if event is None:
            failures.append(f"{intent}: event missing")
            continue
        steps = event.get("internalSteps") if isinstance(event.get("internalSteps"), list) else []
        data["visualEvents"] = [event]
        provenance_errors, _ = qa_lint_visual_script.layered_hud_step_checks(data)
        if should_render:
            valid_steps = len(steps) >= minimum and all(
                isinstance(step, dict)
                and str(step.get("label") or "") in source
                and str(step.get("text") or "") in source
                and step.get("sourceCueIds") == [f"cap-{index:03d}"]
                for step in steps
            )
            ok = (
                not event.get("semanticFallbackFrom")
                and valid_steps
                and not provenance_errors
            )
        else:
            serialized = str(event)
            ok = (
                event.get("type") == "captionHighlight"
                and event.get("semanticFallbackFrom") == intent
                and event.get("fallbackReason") == reason
                and not steps
                and not any(term in serialized for term in BANNED if term not in source)
                and not provenance_errors
            )
        print(f"{'PASS' if ok else 'MISS'} {intent}: {source} -> {event.get('type')}")
        if not ok:
            failures.append(f"{intent}: {source} -> {event}")
    beat, data = fixture("platform-fanout", "发布到抖音、小红书和B站", 999)
    tampered = event_for_beat(beat, data)
    assert tampered is not None
    tampered["internalSteps"][0]["text"] = "虚构平台"
    data["visualEvents"] = [tampered]
    tamper_errors, _ = qa_lint_visual_script.layered_hud_step_checks(data)
    if not any("component-step-source-binding" in error for error in tamper_errors):
        failures.append(f"QA did not reject tampered component provenance: {tamper_errors}")

    renderer = (Path(__file__).resolve().parents[1] / "assets" / "remotion-template" / "src" / "components" / "V4Primitives.tsx").read_text(encoding="utf-8")
    for banned in ["defaultCapabilitySteps", "defaultSceneLockSteps", "defaultTransformationSteps", "{label: '渠道适配'"]:
        if banned in renderer:
            failures.append(f"renderer still contains factual fallback: {banned}")

    if failures:
        print("\n".join(failures))
        print(f"failed: {len(failures)} / {len(CASES)}")
        return 1
    print(f"passed: {len(CASES)} / {len(CASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
