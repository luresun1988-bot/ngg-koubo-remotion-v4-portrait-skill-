#!/usr/bin/env python3
"""Cross-check semantic routes, data-driven components, and renderer contracts."""

from __future__ import annotations

import re
import sys
import json
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
TEMPLATE_ROOT = ROOT / "assets" / "remotion-template"
if not TEMPLATE_ROOT.is_dir():
    TEMPLATE_ROOT = ROOT
sys.path.insert(0, str(SCRIPT_DIR))

import semantic_router  # noqa: E402
import validate_visual_script  # noqa: E402
import visual_event_builder  # noqa: E402


def sample(text: str, scene_type: str = "Explanation") -> dict[str, Any]:
    data: dict[str, Any] = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 25, "durationFrames": 150},
        "media": [],
        "scenes": [{
            "id": "scene-001", "type": scene_type, "startFrame": 0, "endFrame": 150,
            "semanticRole": "", "presenterLayout": "large", "materialLayout": "none",
            "sourceVideo": "input/presenter.mp4", "narrationText": text,
        }],
        "captionCues": [{"id": "cap-001", "sceneId": "scene-001", "startFrame": 0, "endFrame": 150, "text": text}],
        "semanticBeats": [], "visualEvents": [], "audioCues": [], "qaFrames": [],
    }
    semantic_router.apply_semantic_beats(data)
    visual_event_builder.apply_visual_events(data)
    return data


def main() -> int:
    failures: list[str] = []

    cases = [
        ("发布前先检查文件是否完整", "explanation-claim", "claimStrip"),
        ("从官网下载这个工具就可以了", "explanation-claim", "claimStrip"),
        ("模型文件保存在本地目录", "explanation-claim", "claimStrip"),
        ("这期我们聊一下数字人", "topic-intro", "topicKeyword"),
        ("10 张高清详情图已经自动生成好了", "numeric-metric", "dataPunch"),
    ]
    for text, intent, event_type in cases:
        data = sample(text)
        beat = data["semanticBeats"][0]
        event = next(item for item in data["visualEvents"] if item.get("type") != "cornerChapterLabel")
        if beat.get("semanticIntent") != intent or event.get("type") != event_type:
            failures.append(f"route mismatch: {text} -> {beat.get('semanticIntent')}/{event.get('type')}")

    platform = sample("只分发到抖音和B站")
    platform_event = next(item for item in platform["visualEvents"] if item.get("type") == "platformFanout")
    labels = [str(item.get("label") or "") for item in platform_event.get("internalSteps", [])]
    if labels != ["抖音", "B站"]:
        failures.append(f"platform component invented labels: {labels}")

    ratios = sample("主图同时输出横版、竖版和方图")
    ratio_event = next(item for item in ratios["visualEvents"] if item.get("type") == "ratioGallery")
    ratio_labels = [str(item.get("label") or "") for item in ratio_event.get("internalSteps", [])]
    if ratio_labels != ["横版", "竖版", "方图"]:
        failures.append(f"ratio component invented numeric ratios: {ratio_labels}")

    capability = sample("国内外模型能力差异正在拉大")
    capability_event = next(item for item in capability["visualEvents"] if item.get("type") == "capabilityShare")
    capability_labels = [str(item.get("label") or "") for item in capability_event.get("internalSteps", [])]
    if any(label in {"OpenAI", "Google", "Anthropic"} for label in capability_labels):
        failures.append(f"capability component invented brands: {capability_labels}")

    transform = sample("从模糊画面变成高清画面")
    transform_event = next(item for item in transform["visualEvents"] if item.get("type") == "transformationStack")
    transform_labels = [str(item.get("label") or "") for item in transform_event.get("internalSteps", [])]
    if transform_labels[:2] != ["模糊画面", "高清画面"] or any(label in {"一个人", "一个团队"} for label in transform_labels):
        failures.append(f"transformation component invented states: {transform_labels}")

    thesis = sample("数字人真正的价值，是把内容生产变成稳定工作流", "Hook")
    candidates = [beat for beat in thesis["semanticBeats"] if beat.get("themeThesisCandidate")]
    if len(candidates) != 1 or candidates[0].get("requiresApproval") is not True:
        failures.append("theme thesis must produce exactly one approval-required candidate")
    if any(event.get("type") == "depthKeyword" for event in thesis["visualEvents"]):
        failures.append("theme thesis candidate must not auto-create depthKeyword")
    tool_only = sample("Codex 真正的价值值得重新理解", "Hook")
    if any(beat.get("themeThesisCandidate") for beat in tool_only["semanticBeats"]):
        failures.append("tool name alone must not become a theme thesis depth keyword")

    depth_data = sample("数字人")
    depth_data["captionTimeline"] = {"sourceType": "provided", "method": "word-timecodes"}
    depth_data["researchNotes"] = []
    depth_data["qaFrames"] = [{"frame": 75, "reason": "depth contract", "checks": ["depth-keyword"]}]
    depth_data["visualEvents"] = [{
        "id": "ve-depth", "sceneId": "scene-001", "type": "depthKeyword", "startFrame": 10, "endFrame": 120,
        "text": "数字人", "semanticRole": "theme-thesis", "motionType": "word-by-word-depth-reveal",
    }]
    with tempfile.TemporaryDirectory(prefix="v4-depth-contract-") as temp_dir:
        path = Path(temp_dir) / "visual_script.json"
        path.write_text(json.dumps(depth_data, ensure_ascii=False, indent=2), encoding="utf-8")
        errors, _ = validate_visual_script.validate(path)
        if not any("approvalStatus=approved" in error for error in errors) or not any("foregroundAssetPath" in error for error in errors):
            failures.append(f"depthKeyword rejection contract missing: {errors}")
        depth_data["visualEvents"][0]["approvalStatus"] = "approved"
        depth_data["visualEvents"][0]["foregroundAssetPath"] = "input/presenter_cutout.webm"
        path.write_text(json.dumps(depth_data, ensure_ascii=False, indent=2), encoding="utf-8")
        errors, _ = validate_visual_script.validate(path)
        if any("depthKeyword" in error for error in errors):
            failures.append(f"approved depthKeyword rejected: {errors}")

    types_source = (TEMPLATE_ROOT / "src" / "v4Types.ts").read_text(encoding="utf-8")
    type_block = types_source.split("type:\n", 1)[1].split("startFrame:", 1)[0]
    declared_types = set(re.findall(r"'([^']+)'", type_block))
    if declared_types != validate_visual_script.RENDERABLE_EVENT_TYPES:
        missing = sorted(validate_visual_script.RENDERABLE_EVENT_TYPES - declared_types)
        extra = sorted(declared_types - validate_visual_script.RENDERABLE_EVENT_TYPES)
        failures.append(f"event type contract mismatch: missing={missing}, extra={extra}")

    renderer = (TEMPLATE_ROOT / "src" / "V4Composition.tsx").read_text(encoding="utf-8")
    for canonical in ["semanticProblemMap", "automationHandoff", "platformFanout", "topicKeyword", "claimStrip", "ratioGallery", "depthKeyword"]:
        if canonical not in renderer:
            failures.append(f"renderer missing canonical event type: {canonical}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("semantic/component contract regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
