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
        ("生成时把分辨率调到 2K，画面会更清晰", "numeric-metric", "dataPunch"),
        ("下一期我会介绍如何用 Codex 自动剪辑", "explanation-claim", "claimStrip"),
    ]
    for text, intent, event_type in cases:
        data = sample(text)
        beat = data["semanticBeats"][0]
        event = next(item for item in data["visualEvents"] if item.get("type") != "cornerChapterLabel")
        if beat.get("semanticIntent") != intent or event.get("type") != event_type:
            failures.append(f"route mismatch: {text} -> {beat.get('semanticIntent')}/{event.get('type')}")
        if beat.get("beatGroupId") != f"{beat.get('sceneId')}-{beat.get('id')}":
            failures.append(f"semantic beat missing stable beatGroupId: {beat}")

    numeric_2k = sample("生成时把分辨率调到 2K，画面会更清晰")
    numeric_2k_beat = numeric_2k["semanticBeats"][0]
    numeric_2k_event = next(item for item in numeric_2k["visualEvents"] if item.get("type") == "dataPunch")
    if (
        "2K" not in numeric_2k_beat.get("entities", [])
        or numeric_2k_event.get("numericSuffix") != "K"
        or not str(numeric_2k_event.get("text") or "").startswith("2K")
    ):
        failures.append(
            f"numeric entity lost K suffix: entities={numeric_2k_beat.get('entities')} event={numeric_2k_event}"
        )

    numeric_1k = sample("我更推荐先生成 1K 视频啊")
    numeric_1k_event = next(item for item in numeric_1k["visualEvents"] if item.get("type") == "dataPunch")
    if numeric_1k_event.get("numericSuffix") != "K" or numeric_1k_event.get("text") != "1K视频":
        failures.append(f"numeric HUD copy is not entity-bound or left a spoken filler tail: {numeric_1k_event}")

    core_clause_cases = {
        "差别不大，真正影响效果的往往是素材质量和参数设置": "素材质量和参数设置",
        "缺点也很明显，耗时更久、成本更高，有没有更划算的方案": "耗时更久成本更高",
        "成片之后再用剪映或视频增强软件进行高清放大": "剪映或视频增强软件",
        "救不了错误口型，所以原视频一定要先做好": "原视频一定要先做好",
    }
    for source, expected in core_clause_cases.items():
        actual = visual_event_builder.source_bound_core_clause(source)
        if actual != expected:
            failures.append(f"source-bound core clause mismatch: {source!r} -> {actual!r}, expected {expected!r}")

    cta = sample("点个关注，我们下期见", "CTA")
    cta_event = next((item for item in cta["visualEvents"] if item.get("type") == "ctaTitle"), None)
    if not cta_event:
        failures.append("source CTA was dropped by scheduling")
    else:
        visible = " ".join(str(cta_event.get(key) or "") for key in ["text", "subtext", "status"])
        provenance = cta_event.get("ctaProvenance") or {}
        if "评论区" in visible or "关键词：Codex 用法" in visible:
            failures.append(f"CTA invented comment/keyword copy: {visible}")
        if provenance.get("sourceText") != "点个关注，我们下期见":
            failures.append(f"CTA provenance mismatch: {provenance}")

    collision_data = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 30, "durationFrames": 240},
        "media": [],
        "scenes": [{
            "id": "scene-cta", "type": "CTA", "startFrame": 0, "endFrame": 240,
            "semanticRole": "cta-resolve", "presenterLayout": "large", "materialLayout": "none",
            "sourceVideo": "input/presenter.mp4", "narrationText": "下一期我会介绍如何用 Codex 自动剪辑。点个关注，我们下期见。",
        }],
        "captionCues": [
            {"id": "cap-preview", "sceneId": "scene-cta", "startFrame": 0, "endFrame": 170, "text": "下一期我会介绍如何用 Codex 自动剪辑。"},
            {"id": "cap-action", "sceneId": "scene-cta", "startFrame": 170, "endFrame": 240, "text": "点个关注，我们下期见。"},
        ],
        "semanticBeats": [], "visualEvents": [], "audioCues": [], "qaFrames": [],
    }
    semantic_router.apply_semantic_beats(collision_data)
    visual_event_builder.apply_visual_events(collision_data)
    collision_intents = [str(item.get("semanticIntent") or "") for item in collision_data["semanticBeats"]]
    collision_ctas = [item for item in collision_data["visualEvents"] if item.get("type") == "ctaTitle"]
    if collision_intents != ["cta-resolve"] or len(collision_ctas) != 1:
        failures.append(f"future preview / CTA collision regression: intents={collision_intents} ctas={collision_ctas}")
    elif int(collision_ctas[0].get("endFrame", 0)) - int(collision_ctas[0].get("startFrame", 0)) < 95:
        failures.append(f"merged future-preview CTA is too short: {collision_ctas[0]}")

    priority_data = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 30, "durationFrames": 240},
        "media": [],
        "scenes": [{
            "id": "scene-priority", "type": "CTA", "startFrame": 0, "endFrame": 240,
            "semanticRole": "cta-resolve", "presenterLayout": "large", "materialLayout": "none",
            "sourceVideo": "input/presenter.mp4", "narrationText": "流程已经完成。点个关注，我们下期见。",
        }],
        "captionCues": [
            {"id": "cap-confirm", "sceneId": "scene-priority", "startFrame": 0, "endFrame": 190, "text": "流程已经完成。"},
            {"id": "cap-cta", "sceneId": "scene-priority", "startFrame": 170, "endFrame": 240, "text": "点个关注，我们下期见。"},
        ],
        "semanticBeats": [
            {
                "id": "beat-confirm", "sceneId": "scene-priority", "startFrame": 0, "endFrame": 190,
                "text": "流程已经完成。", "semanticIntent": "positive-confirm", "visualForm": "greenConfirmCard",
                "requiredChecks": ["positive-confirm-treatment"], "sourceCueIds": ["cap-confirm"],
            },
            {
                "id": "beat-cta", "sceneId": "scene-priority", "startFrame": 170, "endFrame": 240,
                "text": "点个关注，我们下期见。", "semanticIntent": "cta-resolve", "visualForm": "ctaTitle",
                "requiredChecks": ["cta-visual-treatment"], "sourceCueIds": ["cap-cta"],
            },
        ],
        "visualEvents": [], "audioCues": [], "qaFrames": [],
    }
    visual_event_builder.apply_visual_events(priority_data)
    priority_events = [item for item in priority_data["visualEvents"] if item.get("type") != "cornerChapterLabel"]
    priority_ctas = [item for item in priority_events if item.get("type") == "ctaTitle"]
    same_lane_overlap = any(
        left.get("id") != right.get("id")
        and visual_event_builder.lane_for_event(left) == visual_event_builder.lane_for_event(right) == "left"
        and int(left.get("startFrame", 0)) < int(right.get("endFrame", 0))
        and int(right.get("startFrame", 0)) < int(left.get("endFrame", 0))
        for left in priority_events
        for right in priority_events
    )
    if len(priority_ctas) != 1 or same_lane_overlap:
        failures.append(f"priority CTA scheduling failed: events={priority_events}")

    rhythm_data = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 25, "durationFrames": 540},
        "media": [],
        "scenes": [
            {"id": "scene-short", "type": "Explanation", "startFrame": 0, "endFrame": 90, "semanticRole": "explanation-claim", "presenterLayout": "large", "materialLayout": "none", "sourceVideo": "input/presenter.mp4", "narrationText": "这句话很短"},
            {"id": "scene-a", "type": "Explanation", "startFrame": 90, "endFrame": 240, "semanticRole": "explanation-claim", "presenterLayout": "large", "materialLayout": "none", "sourceVideo": "input/presenter.mp4", "narrationText": "第一条普通说明"},
            {"id": "scene-b", "type": "Explanation", "startFrame": 240, "endFrame": 390, "semanticRole": "explanation-claim", "presenterLayout": "large", "materialLayout": "none", "sourceVideo": "input/presenter.mp4", "narrationText": "第二条普通说明"},
            {"id": "scene-c", "type": "Explanation", "startFrame": 390, "endFrame": 540, "semanticRole": "explanation-claim", "presenterLayout": "large", "materialLayout": "none", "sourceVideo": "input/presenter.mp4", "narrationText": "第三条普通说明"},
        ],
        "captionCues": [],
        "semanticBeats": [
            {"id": "beat-short", "sceneId": "scene-short", "startFrame": 0, "endFrame": 70, "text": "这句话很短", "semanticIntent": "explanation-claim", "visualForm": "claimStrip", "confidence": 0.55, "requiredChecks": ["lightweight-claim-treatment"]},
            {"id": "beat-a", "sceneId": "scene-a", "startFrame": 90, "endFrame": 220, "text": "第一条普通说明", "semanticIntent": "explanation-claim", "visualForm": "claimStrip", "confidence": 0.55, "requiredChecks": ["lightweight-claim-treatment"]},
            {"id": "beat-b", "sceneId": "scene-b", "startFrame": 240, "endFrame": 370, "text": "第二条普通说明", "semanticIntent": "explanation-claim", "visualForm": "claimStrip", "confidence": 0.55, "requiredChecks": ["lightweight-claim-treatment"]},
            {"id": "beat-c", "sceneId": "scene-c", "startFrame": 390, "endFrame": 520, "text": "第三条普通说明", "semanticIntent": "explanation-claim", "visualForm": "claimStrip", "confidence": 0.55, "requiredChecks": ["lightweight-claim-treatment"]},
        ],
        "visualEvents": [], "audioCues": [], "qaFrames": [],
    }
    visual_event_builder.apply_visual_events(rhythm_data)
    rhythm_beats = {str(item.get("id") or ""): item for item in rhythm_data["semanticBeats"]}
    rhythm_events = [item for item in rhythm_data["visualEvents"] if item.get("type") != "cornerChapterLabel"]
    rhythm_claims = [item for item in rhythm_events if item.get("type") == "claimStrip"]
    short_sticker = next((item for item in rhythm_events if item.get("sourceBeatId") == "beat-short"), None)
    if not short_sticker or short_sticker.get("type") != "statusSticker" or rhythm_beats["beat-short"].get("visualForm") != "sourceBoundSticker":
        failures.append(f"short claim did not downgrade to a source-bound sticker: beats={rhythm_beats} events={rhythm_events}")
    if len(rhythm_claims) != 2 or rhythm_beats["beat-c"].get("visualForm") != "intentionalCleanHold":
        failures.append(f"claim-strip run was not capped at two: beats={rhythm_beats} events={rhythm_events}")
    if any(item.get("sourceBeatId") == "beat-c" for item in rhythm_events):
        failures.append(f"intentional clean hold unexpectedly rendered a HUD: {rhythm_events}")

    same_scene_data = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 25, "durationFrames": 300},
        "media": [],
        "scenes": [{"id": "scene-multi", "type": "Explanation", "startFrame": 0, "endFrame": 300, "semanticRole": "explanation-claim", "presenterLayout": "large", "materialLayout": "none", "sourceVideo": "input/presenter.mp4", "narrationText": "普通铺垫，真正影响效果的是素材质量"}],
        "captionCues": [],
        "semanticBeats": [
            {"id": "beat-setup", "sceneId": "scene-multi", "startFrame": 0, "endFrame": 130, "text": "这是普通铺垫", "semanticIntent": "explanation-claim", "visualForm": "claimStrip", "confidence": 0.55, "requiredChecks": ["lightweight-claim-treatment"]},
            {"id": "beat-core", "sceneId": "scene-multi", "startFrame": 140, "endFrame": 290, "text": "真正影响效果的是素材质量", "semanticIntent": "explanation-claim", "visualForm": "claimStrip", "confidence": 0.55, "requiredChecks": ["lightweight-claim-treatment"]},
        ],
        "visualEvents": [], "audioCues": [], "qaFrames": [],
    }
    visual_event_builder.apply_visual_events(same_scene_data)
    same_scene_events = [item for item in same_scene_data["visualEvents"] if item.get("type") == "claimStrip"]
    same_scene_beats = {str(item.get("id") or ""): item for item in same_scene_data["semanticBeats"]}
    if len(same_scene_events) != 1 or same_scene_events[0].get("sourceBeatId") != "beat-core":
        failures.append(f"same-scene claim curation did not keep the strongest claim: beats={same_scene_beats} events={same_scene_events}")

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

    transform = sample("AI把模糊画面变成高清画面，最终实现稳定交付")
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
