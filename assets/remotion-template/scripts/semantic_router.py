#!/usr/bin/env python3
"""Build semanticBeats for NGG Koubo Remotion V4 visual scripts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()

MIN_BEAT_FRAMES = 80
TARGET_BEAT_FRAMES = 115
MAX_BEAT_FRAMES = 165

NUMERIC_RE = re.compile(r"[+\-]?\d+(?:\.\d+)?\s*(?:%|倍|万|亿|人|道|题|个|条|分钟|秒|份|账号)?")
ENUMERATION_RE = re.compile(r"(第一|第二|第三|第四|第五|第[一二三四五六七八九十]+|[二三四五六七八九十]\s*(?:个|件|种|步|项|条|点|方向|指标)|一\s*(?:个|件|种|项|条|点|方向|指标)|[0-9]{1,2}\s*(?:个|件|种|步|项|条|点|方向|指标)|[0-9]{2})")

RULES: dict[str, dict[str, Any]] = {
    "cta-resolve": {
        "visualForm": "ctaTitle",
        "terms": ["评论区", "扣", "领取", "想要", "自提", "告诉我", "私信", "关注", "点赞", "收藏", "关键词"],
        "checks": ["cta-visual-treatment", "no-generic-card-fallback"],
    },
    "negative-friction": {
        "visualForm": "redWarningCard",
        "terms": ["还在", "手动", "不是", "别再", "麻烦", "重复", "低效", "卡住", "风险", "不值得", "太慢", "人工成本"],
        "checks": ["negative-red-treatment", "no-generic-card-fallback"],
    },
    "positive-confirm": {
        "visualForm": "greenConfirmCard",
        "terms": ["自动化", "自动", "完成", "搞定", "跑完", "输出完成", "一键", "不用自己", "补齐", "跑通"],
        "checks": ["positive-confirm-treatment", "no-generic-card-fallback"],
    },
    "automation-handoff": {
        "visualForm": "automationHandoff",
        "terms": ["交给 Codex", "交给Codex", "丢给 Codex", "丢给Codex", "Codex 接管", "Codex接管", "接管", "系统执行", "自动接管", "交给系统", "交给自动化", "自动化流程"],
        "checks": ["workflow-not-generic-card", "positive-confirm-treatment", "no-generic-card-fallback"],
    },
    "manual-field": {
        "visualForm": "infoCard",
        "terms": ["标题", "简介", "标签", "封面", "字段", "每个平台", "重复填写", "填字段", "补齐字段", "表单"],
        "checks": ["workflow-not-generic-card", "small-card-has-icon"],
    },
    "platform-fanout": {
        "visualForm": "platformFanout",
        "terms": ["抖音", "小红书", "B站", "快手", "视频号", "多平台", "分发", "发布", "渠道", "全平台"],
        "checks": ["platform-fanout-treatment", "no-generic-card-fallback"],
    },
    "asset-variants": {
        "visualForm": "ratioGallery",
        "terms": ["横屏", "竖屏", "方图", "多尺寸", "三尺寸", "主图", "封面", "海报", "缩略图", "比例", "16:9", "4:3", "3:4", "横版", "竖版", "方形"],
        "checks": ["asset-ratio-preserved", "no-generic-card-fallback"],
    },
    "proof-material": {
        "visualForm": "materialMain",
        "terms": ["录屏", "截图", "看这", "生成结果", "后台", "页面", "演示", "证明", "跑通", "实测"],
        "checks": ["proof-video-must-play", "material-main-or-proof"],
    },
    "capability-share": {
        "visualForm": "capabilityShare",
        "terms": ["份额", "排名", "领先", "排第一", "对比", "模型", "大模型", "企业大模型", "谁在", "占比", "企业客户", "优势", "国内外", "差异", "差距"],
        "checks": ["capability-share-treatment", "no-generic-card-fallback"],
    },
    "scene-lock": {
        "visualForm": "sceneLockGrid",
        "terms": ["支付", "教育", "政务", "行业", "场景", "落地", "进入生活", "下沉市场", "本地生活"],
        "checks": ["scene-lock-treatment", "small-card-has-icon"],
    },
    "transformation-stack": {
        "visualForm": "transformationStack",
        "terms": ["从", "变成", "一个人", "团队", "第二大脑", "知识库", "杠杆", "护城河", "能力放大", "转化成", "放大"],
        "checks": ["transformation-stack-treatment", "no-generic-card-fallback"],
    },
    "result-promise": {
        "visualForm": "bigJudgement",
        "terms": ["反直觉", "还没有开始", "真正的大爆发", "其实", "只要", "就能", "得到", "爆发", "关键", "接下来", "完全不同", "机会", "刚开始"],
        "checks": ["no-generic-card-fallback"],
    },
}

PRIORITY = [
    "cta-resolve",
    "automation-handoff",
    "positive-confirm",
    "negative-friction",
    "manual-field",
    "platform-fanout",
    "asset-variants",
    "proof-material",
    "capability-share",
    "scene-lock",
    "transformation-stack",
    "result-promise",
]

ACCOUNT_STATUS_NEGATIVE_TERMS = ["账号未转正", "未转正", "弹出提示", "不可能手动", "手动做"]
AUTOMATION_HANDOFF_ACTION_TERMS = [
    "打开 Codex",
    "把网页丢给",
    "丢给 Codex",
    "丢给它",
    "自己读页面",
    "读页面",
    "看题目",
    "整理答案",
]
PROOF_STRONG_TERMS = ["录屏", "截图", "生成结果", "后台演示", "证明", "实测", "看这段", "页面结果"]
FLOW_TRANSFORMATION_TERMS = ["不是它会写代码", "不是会写代码", "麻烦事交给它", "整套流程跑通", "流程跑通"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def contains_any(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term and term in text]


def rule_result(intent: str, keywords: list[str], confidence: float = 0.82) -> dict[str, Any]:
    rule = RULES[intent]
    return {
        "semanticIntent": intent,
        "visualForm": rule["visualForm"],
        "keywords": keywords[:4],
        "requiredChecks": rule["checks"],
        "confidence": confidence,
    }


def classify_text(text: str, frame_midpoint: int, duration_frames: int) -> dict[str, Any]:
    matched = {intent: contains_any(text, rule["terms"]) for intent, rule in RULES.items()}
    matched = {intent: hits for intent, hits in matched.items() if hits}

    if any(term in text for term in FLOW_TRANSFORMATION_TERMS):
        return {
            "semanticIntent": "transformation-stack",
            "visualForm": "transformationStack",
            "keywords": [term for term in FLOW_TRANSFORMATION_TERMS if term in text][:4],
            "requiredChecks": RULES["transformation-stack"]["checks"],
            "confidence": 0.9,
        }

    if any(term in text for term in ACCOUNT_STATUS_NEGATIVE_TERMS):
        return {
            "semanticIntent": "negative-friction",
            "visualForm": "redWarningCard",
            "keywords": [term for term in ACCOUNT_STATUS_NEGATIVE_TERMS if term in text][:4],
            "requiredChecks": RULES["negative-friction"]["checks"],
            "confidence": 0.92,
        }

    if any(term in text for term in AUTOMATION_HANDOFF_ACTION_TERMS):
        return {
            "semanticIntent": "automation-handoff",
            "visualForm": "automationHandoff",
            "keywords": [term for term in AUTOMATION_HANDOFF_ACTION_TERMS if term in text][:4],
            "requiredChecks": RULES["automation-handoff"]["checks"],
            "confidence": 0.9,
        }

    if "cta-resolve" in matched and any(term in text for term in ["评论区", "领取", "自提", "告诉我", "私信", "关键词", "关注", "点赞", "收藏"]):
        return rule_result("cta-resolve", matched["cta-resolve"], 0.9)

    if "negative-friction" in matched and ("positive-confirm" in matched or "automation-handoff" in matched):
        positive_hits = matched.get("positive-confirm", []) + matched.get("automation-handoff", [])
        return {
            "semanticIntent": "negative-to-positive",
            "visualForm": "negativeWarningThenConfirm",
            "keywords": (matched["negative-friction"][:2] + positive_hits[:2])[:4],
            "requiredChecks": ["negative-red-treatment", "positive-confirm-treatment", "no-generic-card-fallback"],
            "confidence": 0.95,
        }

    if "asset-variants" in matched and any(term in text for term in ["横屏", "竖屏", "方图", "多尺寸", "三尺寸", "多规格", "16:9", "4:3", "3:4", "比例", "横版", "竖版", "方形"]):
        return rule_result("asset-variants", matched["asset-variants"], 0.9)

    enumeration_match = ENUMERATION_RE.search(text)
    if enumeration_match and any(term in text for term in ["方向 01", "方向 02", "方向01", "方向02"]):
        return {
            "semanticIntent": "enumeration",
            "visualForm": "stepList",
            "keywords": [enumeration_match.group(0).strip()],
            "requiredChecks": ["workflow-not-generic-card", "small-card-has-icon"],
            "confidence": 0.9,
        }

    if "scene-lock" in matched and any(term in text for term in ["支付", "教育", "政务", "行业", "场景", "落地", "下沉市场", "本地生活", "餐饮", "零售", "基础设施"]):
        return rule_result("scene-lock", matched["scene-lock"], 0.88)

    numeric_match = NUMERIC_RE.search(text)
    if numeric_match and any(term in text for term in ["提升", "增长", "比例", "指标", "数据", "%", "倍", "万", "亿", "道题", "题", "数量", "规模", "分钟", "秒", "小于", "省下", "批量", "处理", "账号", "扩到"]):
        return {
            "semanticIntent": "numeric-metric",
            "visualForm": "dataPunch",
            "keywords": [numeric_match.group(0).strip()],
            "requiredChecks": ["numeric-countup-required", "no-generic-card-fallback"],
            "confidence": 0.9,
        }

    if "transformation-stack" in matched and any(term in text for term in ["放大你的能力", "放大能力", "放大", "转化成", "变成", "从", "团队", "第二大脑", "杠杆", "护城河"]):
        return rule_result("transformation-stack", matched["transformation-stack"], 0.88)

    if enumeration_match and any(term in text for term in ["第一", "第二", "第三", "第四", "第五", "三个", "五件", "方向 01", "方向 02"]):
        return {
            "semanticIntent": "enumeration",
            "visualForm": "stepList",
            "keywords": [enumeration_match.group(0).strip()],
            "requiredChecks": ["workflow-not-generic-card", "small-card-has-icon"],
            "confidence": 0.9,
        }

    if "positive-confirm" in matched and any(term in text for term in ["一键", "搞定", "自动完成", "输出完成", "流程已经跑完", "剩下自动完成", "确认一次"]):
        return rule_result("positive-confirm", matched["positive-confirm"], 0.88)

    if "result-promise" in matched and any(term in text for term in ["反直觉", "接下来", "真正的机会", "只要", "还没意识到", "刚开始", "完全不同"]):
        return rule_result("result-promise", matched["result-promise"], 0.88)

    if "platform-fanout" in matched and any(term in text for term in ["抖音", "小红书", "B站", "快手", "视频号", "多平台", "全平台", "渠道"]):
        return rule_result("platform-fanout", matched["platform-fanout"], 0.88)

    if "automation-handoff" in matched and any(term in text for term in ["交给", "丢给", "接管", "系统执行", "自动化流程"]):
        return rule_result("automation-handoff", matched["automation-handoff"], 0.9)

    if "manual-field" in matched and ("negative-friction" in matched or "positive-confirm" in matched):
        return rule_result("manual-field", matched["manual-field"], 0.9)

    if "capability-share" in matched and any(term in text for term in ["份额", "排名", "领先", "排第一", "对比", "占比", "大模型"]):
        return rule_result("capability-share", matched["capability-share"], 0.88)

    if "proof-material" in matched and any(term in text for term in PROOF_STRONG_TERMS):
        return rule_result("proof-material", matched["proof-material"], 0.88)

    if enumeration_match and any(term in text for term in ["件", "种", "步", "项", "指标", "事情", "方向", "第一", "第二", "第三"]):
        return {
            "semanticIntent": "enumeration",
            "visualForm": "stepList",
            "keywords": [enumeration_match.group(0).strip()],
            "requiredChecks": ["workflow-not-generic-card", "small-card-has-icon"],
            "confidence": 0.86,
        }

    for intent in PRIORITY:
        if intent in matched:
            return rule_result(intent, matched[intent])

    return {
        "semanticIntent": "workflow-step",
        "visualForm": "flowPath",
        "keywords": [],
        "requiredChecks": ["workflow-not-generic-card"],
        "confidence": 0.55,
    }


def scene_fallback_info(scene: dict[str, Any], info: dict[str, Any], start_frame: int | None = None) -> dict[str, Any]:
    """Use scene-level intent when transcript keywords are too sparse."""
    scene_type = str(scene.get("type") or "").lower()
    scene_role = str(scene.get("semanticRole") or "")
    presenter_layout = str(scene.get("presenterLayout") or "")
    material_layout = str(scene.get("materialLayout") or "")
    if material_layout in {"main", "clean"} or presenter_layout == "pip" or scene_role in {"proof-material", "material-main"}:
        return {
            "semanticIntent": "proof-material",
            "visualForm": "materialMain",
            "keywords": [],
            "requiredChecks": ["proof-video-must-play", "material-main-or-proof"],
            "confidence": 0.72,
        }
    if info.get("keywords"):
        return info
    scene_start = int(scene.get("startFrame", 0) or 0)
    is_opening_beat = start_frame is None or start_frame <= scene_start + 45
    if is_opening_beat and (scene_type == "hook" or scene_role in {"result-promise", "pain-question", "contrarian-hook"}):
        return {
            "semanticIntent": "result-promise",
            "visualForm": "bigJudgement",
            "keywords": [],
            "requiredChecks": ["no-generic-card-fallback"],
            "confidence": 0.68,
        }
    if scene_type == "cta" or scene_role == "cta-resolve":
        return {
            "semanticIntent": "cta-resolve",
            "visualForm": "ctaTitle",
            "keywords": [],
            "requiredChecks": ["cta-visual-treatment", "no-generic-card-fallback"],
            "confidence": 0.7,
        }
    return info


def scene_for_cue(cue: dict[str, Any], scenes: list[dict[str, Any]]) -> dict[str, Any] | None:
    scene_id = str(cue.get("sceneId") or "")
    if scene_id:
        found = next((scene for scene in scenes if str(scene.get("id") or "") == scene_id), None)
        if found:
            return found
    start = int(cue.get("startFrame", 0) or 0)
    end = int(cue.get("endFrame", start) or start)
    midpoint = (start + end) // 2
    return next(
        (scene for scene in scenes if int(scene.get("startFrame", 0) or 0) <= midpoint < int(scene.get("endFrame", 0) or 0)),
        None,
    )


def build_semantic_beats(data: dict[str, Any]) -> list[dict[str, Any]]:
    scenes = [scene for scene in data.get("scenes", []) if isinstance(scene, dict)]
    caption_cues = [cue for cue in data.get("captionCues", []) if isinstance(cue, dict)]
    by_scene: dict[str, list[dict[str, Any]]] = {str(scene.get("id") or ""): [] for scene in scenes}

    for cue in caption_cues:
        scene = scene_for_cue(cue, scenes)
        if not scene:
            continue
        by_scene.setdefault(str(scene.get("id") or ""), []).append(cue)

    beats: list[dict[str, Any]] = []
    beat_index = 1
    for scene in scenes:
        scene_id = str(scene.get("id") or "")
        cues = sorted(by_scene.get(scene_id, []), key=lambda item: int(item.get("startFrame", 0) or 0))
        if not cues and scene.get("narrationText"):
            cues = [
                {
                    "id": f"synthetic-{scene_id}",
                    "sceneId": scene_id,
                    "startFrame": int(scene.get("startFrame", 0) or 0),
                    "endFrame": int(scene.get("endFrame", 0) or 0),
                    "text": str(scene.get("narrationText") or ""),
                }
            ]

        cursor = 0
        while cursor < len(cues):
            group = [cues[cursor]]
            start = int(cues[cursor].get("startFrame", 0) or 0)
            end = int(cues[cursor].get("endFrame", start + 1) or start + 1)
            text = str(cues[cursor].get("text") or "")
            cursor += 1

            while cursor < len(cues):
                next_cue = cues[cursor]
                next_end = int(next_cue.get("endFrame", end) or end)
                next_text = str(next_cue.get("text") or "")
                candidate = text + next_text
                duration = next_end - start
                current_info = classify_text(text, (start + end) // 2, end - start)
                next_info = classify_text(next_text, (end + next_end) // 2, next_end - end)
                candidate_info = classify_text(candidate, (start + next_end) // 2, duration)
                should_merge_negative_positive = (
                    current_info["semanticIntent"] == "negative-friction"
                    and next_info["semanticIntent"] in {"positive-confirm", "automation-handoff"}
                )
                if duration <= MIN_BEAT_FRAMES or should_merge_negative_positive:
                    group.append(next_cue)
                    text = candidate
                    end = next_end
                    cursor += 1
                    continue
                if duration <= TARGET_BEAT_FRAMES and candidate_info["semanticIntent"] == current_info["semanticIntent"]:
                    group.append(next_cue)
                    text = candidate
                    end = next_end
                    cursor += 1
                    continue
                if duration > MAX_BEAT_FRAMES:
                    break
                break

            scene_start = int(scene.get("startFrame", start) or start)
            scene_end = int(scene.get("endFrame", end) or end)
            visual_end = max(end, min(scene_end, start + MIN_BEAT_FRAMES))
            info = scene_fallback_info(scene, classify_text(text, (start + visual_end) // 2, visual_end - start), start)
            beat = {
                "id": f"beat-{beat_index:03d}",
                "sceneId": scene_id,
                "startFrame": max(scene_start, start),
                "endFrame": min(scene_end, visual_end),
                "text": text,
                "semanticIntent": info["semanticIntent"],
                "visualForm": info["visualForm"],
                "confidence": info["confidence"],
                "keywords": info["keywords"],
                "requiredChecks": info["requiredChecks"],
                "sourceCueIds": [str(cue.get("id") or "") for cue in group if cue.get("id")],
            }
            beats.append(beat)
            beat_index += 1

    return merge_short_tail_beats(beats, scenes)


def merge_short_tail_beats(beats: list[dict[str, Any]], scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scene_by_id_map = {str(scene.get("id") or ""): scene for scene in scenes}
    merged: list[dict[str, Any]] = []
    for beat in beats:
        scene_id = str(beat.get("sceneId") or "")
        start = int(beat.get("startFrame", 0) or 0)
        end = int(beat.get("endFrame", start) or start)
        duration = end - start
        previous = merged[-1] if merged and str(merged[-1].get("sceneId") or "") == scene_id else None
        previous_intent = str((previous or {}).get("semanticIntent") or "")
        current_intent = str(beat.get("semanticIntent") or "")
        if previous and previous_intent == "result-promise" and current_intent in {"negative-friction", "negative-to-positive"}:
            previous["endFrame"] = max(int(previous.get("endFrame", 0) or 0), end)
            previous["text"] = str(previous.get("text") or "") + str(beat.get("text") or "")
            previous["semanticIntent"] = current_intent
            previous["visualForm"] = beat.get("visualForm")
            previous["keywords"] = beat.get("keywords", [])
            previous["requiredChecks"] = beat.get("requiredChecks", [])
            previous["confidence"] = max(float(previous.get("confidence", 0) or 0), float(beat.get("confidence", 0) or 0))
            previous["sourceCueIds"] = list(previous.get("sourceCueIds") or []) + list(beat.get("sourceCueIds") or [])
            continue
        if previous and previous_intent in {"negative-friction", "negative-to-positive"} and current_intent in {"negative-friction", "negative-to-positive"}:
            previous["endFrame"] = max(int(previous.get("endFrame", 0) or 0), end)
            previous["text"] = str(previous.get("text") or "") + str(beat.get("text") or "")
            if current_intent == "negative-to-positive":
                previous["semanticIntent"] = current_intent
                previous["visualForm"] = beat.get("visualForm")
                previous["keywords"] = beat.get("keywords", [])
                previous["requiredChecks"] = beat.get("requiredChecks", [])
            previous["sourceCueIds"] = list(previous.get("sourceCueIds") or []) + list(beat.get("sourceCueIds") or [])
            continue
        if previous and previous_intent == current_intent and current_intent in {"automation-handoff", "transformation-stack"}:
            previous["endFrame"] = max(int(previous.get("endFrame", 0) or 0), end)
            previous["text"] = str(previous.get("text") or "") + str(beat.get("text") or "")
            previous["sourceCueIds"] = list(previous.get("sourceCueIds") or []) + list(beat.get("sourceCueIds") or [])
            continue
        if previous and previous_intent == "proof-material" and current_intent == "proof-material":
            previous["endFrame"] = max(int(previous.get("endFrame", 0) or 0), end)
            previous["text"] = str(previous.get("text") or "") + str(beat.get("text") or "")
            previous["sourceCueIds"] = list(previous.get("sourceCueIds") or []) + list(beat.get("sourceCueIds") or [])
            continue
        if duration < MIN_BEAT_FRAMES and previous:
            previous["endFrame"] = max(int(previous.get("endFrame", 0) or 0), end)
            previous["text"] = str(previous.get("text") or "") + str(beat.get("text") or "")
            previous["sourceCueIds"] = list(previous.get("sourceCueIds") or []) + list(beat.get("sourceCueIds") or [])
            continue
        if duration < MIN_BEAT_FRAMES:
            scene = scene_by_id_map.get(scene_id, {})
            scene_end = int(scene.get("endFrame", end) or end)
            beat = {**beat, "endFrame": min(scene_end, start + MIN_BEAT_FRAMES)}
        merged.append(beat)
    return merged


def apply_semantic_beats(data: dict[str, Any]) -> dict[str, Any]:
    data["semanticBeats"] = build_semantic_beats(data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    data = load_json(args.visual_script)
    apply_semantic_beats(data)
    out = args.out or args.visual_script
    save_json(out, data)
    print(f"semantic beats: {len(data.get('semanticBeats', []))}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
