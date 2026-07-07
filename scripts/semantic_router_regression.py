#!/usr/bin/env python3
"""Regression checks for V4 semantic routing and visual event generation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import semantic_router  # noqa: E402
import visual_event_builder  # noqa: E402
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()


CASES: list[dict[str, str]] = [
    {"id": "negative-01", "text": "别再手动做主图，这件事太慢了", "intent": "negative-friction", "eventType": "highlightBox"},
    {"id": "negative-02", "text": "账号没转正就是一个风险点", "intent": "negative-friction", "eventType": "highlightBox"},
    {"id": "negative-03", "text": "你还在靠人工一条条发布，这就是成本", "intent": "negative-friction", "eventType": "highlightBox"},
    {"id": "negative-04", "text": "重复劳动会把整个流程拖慢", "intent": "negative-friction", "eventType": "highlightBox"},
    {"id": "negative-05", "text": "这里最麻烦的不是拍摄，而是后面处理", "intent": "negative-friction", "eventType": "highlightBox"},
    {"id": "negative-06", "text": "低效的地方会一直卡住你", "intent": "negative-friction", "eventType": "highlightBox"},
    {"id": "contrast-01", "text": "不是你手动剪，而是交给 Codex 自动跑流程", "intent": "negative-to-positive", "eventType": "highlightBox"},
    {"id": "contrast-02", "text": "不是写代码，是把流程自动化", "intent": "negative-to-positive", "eventType": "highlightBox"},
    {"id": "contrast-03", "text": "不是让你多干活，而是让系统自动补齐", "intent": "negative-to-positive", "eventType": "highlightBox"},
    {"id": "contrast-04", "text": "别再手动填表了，这一步可以一键完成", "intent": "negative-to-positive", "eventType": "highlightBox"},
    {"id": "contrast-05", "text": "不是主图难，是重复生成这件事该自动化", "intent": "negative-to-positive", "eventType": "highlightBox"},
    {"id": "contrast-06", "text": "不是靠人盯后台，而是 Codex 接管检查", "intent": "negative-to-positive", "eventType": "highlightBox"},
    {"id": "contrast-07", "text": "不是多做几个版本，是一次自动生成多尺寸", "intent": "negative-to-positive", "eventType": "highlightBox"},
    {"id": "contrast-08", "text": "不是你手动分发，而是把发布任务交给系统", "intent": "negative-to-positive", "eventType": "highlightBox"},
    {"id": "manual-field-01", "text": "每个平台都要重复填写标题简介标签和封面", "intent": "manual-field", "eventType": "infoCard"},
    {"id": "manual-field-02", "text": "这些字段以前都靠人一个个补齐", "intent": "manual-field", "eventType": "infoCard"},
    {"id": "manual-field-03", "text": "标题、简介、标签、封面，全都要统一风格", "intent": "manual-field", "eventType": "infoCard"},
    {"id": "manual-field-04", "text": "表单里最烦的是反复填同一组字段", "intent": "manual-field", "eventType": "infoCard"},
    {"id": "manual-field-05", "text": "先把标题和标签自动补齐", "intent": "manual-field", "eventType": "infoCard"},
    {"id": "manual-field-06", "text": "发布前还要检查简介、封面和话题标签", "intent": "manual-field", "eventType": "infoCard"},
    {"id": "manual-field-07", "text": "不同平台的标题字段不能再手填", "intent": "manual-field", "eventType": "infoCard"},
    {"id": "manual-field-08", "text": "这一步就是把表单字段标准化", "intent": "manual-field", "eventType": "infoCard"},
    {"id": "handoff-01", "text": "把网页丢给 Codex，后面的流程让它接管", "intent": "automation-handoff", "eventType": "captionHighlight"},
    {"id": "handoff-02", "text": "交给 Codex 之后，系统会自动执行", "intent": "automation-handoff", "eventType": "captionHighlight"},
    {"id": "handoff-03", "text": "这一段不用自己盯，让 Codex 接管", "intent": "automation-handoff", "eventType": "captionHighlight"},
    {"id": "handoff-04", "text": "把链接交给系统，它会继续跑下去", "intent": "automation-handoff", "eventType": "captionHighlight"},
    {"id": "handoff-05", "text": "后面的检查和输出都交给 Codex", "intent": "automation-handoff", "eventType": "captionHighlight"},
    {"id": "handoff-06", "text": "你只负责确认，执行交给自动化流程", "intent": "automation-handoff", "eventType": "captionHighlight"},
    {"id": "platform-01", "text": "这份素材要分发到抖音、小红书、B站和视频号", "intent": "platform-fanout", "eventType": "transitionPushZoom"},
    {"id": "platform-02", "text": "一套内容同时适配多个发布渠道", "intent": "platform-fanout", "eventType": "transitionPushZoom"},
    {"id": "platform-03", "text": "同一条视频要发到全平台", "intent": "platform-fanout", "eventType": "transitionPushZoom"},
    {"id": "platform-04", "text": "小红书要封面，B站要标题，抖音要短描述", "intent": "platform-fanout", "eventType": "transitionPushZoom"},
    {"id": "platform-05", "text": "多账号、多平台、多渠道同时发布", "intent": "platform-fanout", "eventType": "transitionPushZoom"},
    {"id": "platform-06", "text": "发完一个平台，还要继续同步到快手和视频号", "intent": "platform-fanout", "eventType": "transitionPushZoom"},
    {"id": "asset-01", "text": "主图要同时出横屏、竖屏和方图", "intent": "asset-variants", "eventType": "flowPath"},
    {"id": "asset-02", "text": "封面和海报需要多尺寸输出", "intent": "asset-variants", "eventType": "flowPath"},
    {"id": "asset-03", "text": "一张素材要变成 16:9、4:3、3:4 三个比例", "intent": "asset-variants", "eventType": "flowPath"},
    {"id": "asset-04", "text": "横版给 B站，竖版给抖音，方图给小红书", "intent": "asset-variants", "eventType": "flowPath"},
    {"id": "asset-05", "text": "不是单张海报，而是一组多规格封面", "intent": "asset-variants", "eventType": "flowPath"},
    {"id": "asset-06", "text": "主视觉要拆成横屏版、竖屏版和方形版", "intent": "asset-variants", "eventType": "flowPath"},
    {"id": "numeric-01", "text": "这次一共转正 52 道题", "intent": "numeric-metric", "eventType": "dataPunch"},
    {"id": "numeric-02", "text": "流程小于 1 分钟就能跑完", "intent": "numeric-metric", "eventType": "dataPunch"},
    {"id": "numeric-03", "text": "效率提升 3 倍，规模增加到 885 万", "intent": "numeric-metric", "eventType": "dataPunch"},
    {"id": "numeric-04", "text": "转化率从 0.04% 提升到 3%", "intent": "numeric-metric", "eventType": "dataPunch"},
    {"id": "numeric-05", "text": "这一步能省下 80% 的重复时间", "intent": "numeric-metric", "eventType": "dataPunch"},
    {"id": "numeric-06", "text": "一天能批量处理 100 条内容", "intent": "numeric-metric", "eventType": "dataPunch"},
    {"id": "numeric-07", "text": "从 1 个人扩到 10 个账号", "intent": "numeric-metric", "eventType": "dataPunch"},
    {"id": "capability-01", "text": "企业大模型份额排名里，OpenAI 仍然领先", "intent": "capability-share", "eventType": "capabilityShare"},
    {"id": "capability-02", "text": "这不是单点功能，而是能力对比", "intent": "capability-share", "eventType": "capabilityShare"},
    {"id": "capability-03", "text": "真正拉开差距的是模型能力", "intent": "capability-share", "eventType": "capabilityShare"},
    {"id": "capability-04", "text": "谁能拿到更多企业客户，谁就更有优势", "intent": "capability-share", "eventType": "capabilityShare"},
    {"id": "capability-05", "text": "国内外的能力差异会越来越明显", "intent": "capability-share", "eventType": "capabilityShare"},
    {"id": "scene-01", "text": "支付、教育、政务这些场景正在落地", "intent": "scene-lock", "eventType": "sceneLockGrid"},
    {"id": "scene-02", "text": "它真正进入了下沉市场和本地生活", "intent": "scene-lock", "eventType": "sceneLockGrid"},
    {"id": "scene-03", "text": "这不是概念，而是已经进到具体行业", "intent": "scene-lock", "eventType": "sceneLockGrid"},
    {"id": "scene-04", "text": "餐饮、零售、教育都会先用起来", "intent": "scene-lock", "eventType": "sceneLockGrid"},
    {"id": "scene-05", "text": "场景一旦固定，工具就会变成基础设施", "intent": "scene-lock", "eventType": "sceneLockGrid"},
    {"id": "transform-01", "text": "从一个人变成一个团队，关键是第二大脑", "intent": "transformation-stack", "eventType": "transformationStack"},
    {"id": "transform-02", "text": "知识库会变成你的护城河和能力杠杆", "intent": "transformation-stack", "eventType": "transformationStack"},
    {"id": "transform-03", "text": "AI 把你的经验转化成可复制流程", "intent": "transformation-stack", "eventType": "transformationStack"},
    {"id": "transform-04", "text": "它不是替代你，而是放大你的能力", "intent": "transformation-stack", "eventType": "transformationStack"},
    {"id": "transform-05", "text": "从个人知识变成团队资产", "intent": "transformation-stack", "eventType": "transformationStack"},
    {"id": "transform-06", "text": "真正的杠杆，是把一次经验变成长期系统", "intent": "transformation-stack", "eventType": "transformationStack"},
    {"id": "proof-01", "text": "看这段录屏，后台已经跑通了", "intent": "proof-material", "eventType": "statusSticker"},
    {"id": "proof-02", "text": "截图就是最后的生成结果", "intent": "proof-material", "eventType": "statusSticker"},
    {"id": "proof-03", "text": "我直接给你看页面结果", "intent": "proof-material", "eventType": "statusSticker"},
    {"id": "proof-04", "text": "这里有完整的后台演示", "intent": "proof-material", "eventType": "statusSticker"},
    {"id": "proof-05", "text": "实测结果已经证明它能跑", "intent": "proof-material", "eventType": "statusSticker"},
    {"id": "cta-01", "text": "评论区扣 Codex 用法，我把流程发你", "intent": "cta-resolve", "eventType": "ctaTitle"},
    {"id": "cta-02", "text": "想要模板可以自提，也可以私信我", "intent": "cta-resolve", "eventType": "ctaTitle"},
    {"id": "cta-03", "text": "关注我，下一条讲怎么搭这个流程", "intent": "cta-resolve", "eventType": "ctaTitle"},
    {"id": "cta-04", "text": "收藏这一条，后面你会用到", "intent": "cta-resolve", "eventType": "ctaTitle"},
    {"id": "cta-05", "text": "你想让 Codex 接管哪一步，评论区告诉我", "intent": "cta-resolve", "eventType": "ctaTitle"},
    {"id": "cta-06", "text": "关键词发你，直接领取这套规则", "intent": "cta-resolve", "eventType": "ctaTitle"},
    {"id": "enum-01", "text": "第一方向是赋能你已经会的手艺", "intent": "enumeration", "eventType": "statusStack"},
    {"id": "enum-02", "text": "第二个动作是整理个人知识库", "intent": "enumeration", "eventType": "statusStack"},
    {"id": "enum-03", "text": "第三步才是把流程交给系统", "intent": "enumeration", "eventType": "statusStack"},
    {"id": "enum-04", "text": "我们先看三个指标", "intent": "enumeration", "eventType": "statusStack"},
    {"id": "enum-05", "text": "这里有五件事需要拆开讲", "intent": "enumeration", "eventType": "statusStack"},
    {"id": "enum-06", "text": "方向 01 是能力放大，方向 02 是市场下沉", "intent": "enumeration", "eventType": "statusStack"},
    {"id": "positive-01", "text": "流程已经跑完，输出完成", "intent": "positive-confirm", "eventType": "captionHighlight"},
    {"id": "positive-02", "text": "这一步可以一键搞定", "intent": "positive-confirm", "eventType": "captionHighlight"},
    {"id": "positive-03", "text": "系统会自动生成最终结果", "intent": "positive-confirm", "eventType": "captionHighlight"},
    {"id": "positive-04", "text": "你只要确认一次，剩下自动完成", "intent": "positive-confirm", "eventType": "captionHighlight"},
    {"id": "hook-01", "text": "AI 真正的大爆发，其实还没有开始", "intent": "result-promise", "eventType": "kineticTitle"},
    {"id": "hook-02", "text": "反直觉的是，最值钱的不是模型本身", "intent": "result-promise", "eventType": "kineticTitle"},
    {"id": "hook-03", "text": "接下来你会看到一个完全不同的用法", "intent": "result-promise", "eventType": "kineticTitle"},
    {"id": "hook-04", "text": "真正的机会，藏在这些重复流程里", "intent": "result-promise", "eventType": "kineticTitle"},
    {"id": "hook-05", "text": "只要这一步跑通，后面就会很轻", "intent": "result-promise", "eventType": "kineticTitle"},
    {"id": "hook-06", "text": "很多人还没意识到，自动化才刚开始", "intent": "result-promise", "eventType": "kineticTitle"},
    {"id": "real-project-account-status", "text": "结果系统突然弹出提示：账号未转正。", "intent": "negative-friction", "eventType": "highlightBox", "eventTextContains": "账号未转正"},
    {"id": "real-project-numeric-question-bank", "text": "我点进后台一看，直接懵了：转正居然要答 100 道题。", "intent": "numeric-metric", "eventType": "dataPunch", "eventTextContains": "100"},
    {"id": "real-project-manual-impossible", "text": "作为一个 Codex 博主，这种事我当然不可能手动做。", "intent": "negative-friction", "eventType": "highlightBox", "eventTextContains": "不可能手动"},
    {"id": "real-project-webpage-handoff", "text": "我直接打开 Codex，把网页丢给它，让它自己读页面、看题目、整理答案。", "intent": "automation-handoff", "eventType": "captionHighlight"},
    {"id": "real-project-flow-transform", "text": "不是它会写代码，而是你把一个麻烦事交给它，它真的能把整套流程跑通。", "intent": "transformation-stack", "eventType": "transformationStack"},
]


def visual_script_for_case(case: dict[str, str], index: int) -> dict[str, Any]:
    start = index * 180
    end = start + 150
    scene_id = f"scene-{index + 1:03d}"
    cue_id = f"cap-{index + 1:03d}"
    return {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 25, "durationFrames": end + 30},
        "media": [],
        "scenes": [
            {
                "id": scene_id,
                "type": "Explanation",
                "startFrame": start,
                "endFrame": end,
                "semanticRole": "",
                "presenterLayout": "large",
                "materialLayout": "none",
                "narrationText": case["text"],
            }
        ],
        "captionCues": [
            {"id": cue_id, "sceneId": scene_id, "startFrame": start, "endFrame": end, "text": case["text"]}
        ],
        "semanticBeats": [],
        "visualEvents": [],
        "audioCues": [],
        "qaFrames": [],
    }


def routed_event(data: dict[str, Any]) -> dict[str, Any]:
    return next(event for event in data["visualEvents"] if event.get("type") != "cornerChapterLabel")


def run_case(case: dict[str, str], index: int) -> dict[str, Any]:
    data = visual_script_for_case(case, index)
    semantic_router.apply_semantic_beats(data)
    visual_event_builder.apply_visual_events(data)
    beat = data["semanticBeats"][0]
    event = routed_event(data)
    event_text = " ".join(
        str(event.get(key) or "")
        for key in ["text", "subtext", "title", "status"]
    )
    if event.get("numericValue") is not None:
        event_text = f"{event_text} {event.get('numericPrefix') or ''}{event.get('numericValue')}{event.get('numericSuffix') or ''}"
    expected_text = case.get("eventTextContains")
    text_ok = True if not expected_text else expected_text in event_text
    ok = beat.get("semanticIntent") == case["intent"] and event.get("type") == case["eventType"] and text_ok
    return {
        "id": case["id"],
        "text": case["text"],
        "expectedIntent": case["intent"],
        "actualIntent": beat.get("semanticIntent"),
        "expectedEventType": case["eventType"],
        "actualEventType": event.get("type"),
        "expectedEventText": expected_text or "",
        "actualEventText": event_text,
        "semanticRole": event.get("semanticRole"),
        "timingAnchor": event.get("timingAnchor", ""),
        "ok": ok,
    }


def run_real_project_opening_case() -> dict[str, Any]:
    data: dict[str, Any] = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 30, "durationFrames": 360},
        "sourceVideoMode": "precomposed-video",
        "packagingDensity": "light",
        "media": [],
        "scenes": [
            {
                "id": "scene-real-hook",
                "type": "Hook",
                "startFrame": 0,
                "endFrame": 328,
                "semanticRole": "result-promise",
                "presenterLayout": "large",
                "materialLayout": "none",
                "narrationText": "我发现 Codex 一个离谱用法。今天我在 B 站刷视频，本来想随手评论一句，结果系统突然弹出提示：账号未转正。",
            }
        ],
        "captionCues": [
            {"id": "cap-real-001", "sceneId": "scene-real-hook", "startFrame": 0, "endFrame": 98, "text": "我发现 Codex 一个离谱用法。"},
            {"id": "cap-real-002", "sceneId": "scene-real-hook", "startFrame": 98, "endFrame": 202, "text": "今天我在 B 站刷视频，本来想随手评论一句，"},
            {"id": "cap-real-003", "sceneId": "scene-real-hook", "startFrame": 202, "endFrame": 328, "text": "结果系统突然弹出提示：账号未转正。"},
        ],
        "semanticBeats": [],
        "visualEvents": [],
        "audioCues": [],
        "qaFrames": [],
    }
    semantic_router.apply_semantic_beats(data)
    visual_event_builder.apply_visual_events(data)
    actual = [beat.get("semanticIntent") for beat in data.get("semanticBeats", [])]
    expected = ["result-promise", "workflow-step", "negative-friction"]
    event_types = [event.get("type") for event in data.get("visualEvents", []) if event.get("type") != "cornerChapterLabel"]
    return {
        "id": "real-project-opening-sequence",
        "text": data["scenes"][0]["narrationText"],
        "expectedIntent": ",".join(expected),
        "actualIntent": ",".join(str(item) for item in actual),
        "expectedEventType": "no-three-big-title-sequence",
        "actualEventType": ",".join(str(item) for item in event_types),
        "semanticRole": "",
        "timingAnchor": "",
        "ok": actual == expected and event_types[:3] != ["kineticTitle", "kineticTitle", "kineticTitle"],
    }


def main() -> int:
    results = [run_case(case, index) for index, case in enumerate(CASES)]
    results.append(run_real_project_opening_case())
    failed = [item for item in results if not item["ok"]]
    for item in results:
        marker = "PASS" if item["ok"] else "MISS"
        print(f"{marker} {item['id']}: {item['actualIntent']} -> {item['actualEventType']}")

    report_path = SCRIPT_DIR.parent / "qa" / "semantic_router_regression.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {report_path}")
    if failed:
        print(f"failed: {len(failed)} / {len(results)}")
        return 1
    print(f"passed: {len(results)} / {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
