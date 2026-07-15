#!/usr/bin/env python3
"""Build V4 visualEvents from semanticBeats."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402
from presentation_registry import get_registry, presentation_sfx_intents  # noqa: E402
from semantic_guardrails import numeric_event_fields  # noqa: E402

configure_utf8()

MIN_MAIN_HUD_FRAMES = 95
PREFERRED_MAIN_HUD_FRAMES = 125
LANE_BUFFER_FRAMES = 10
DEFAULT_FPS = 25
LOW_CONFIDENCE_CLAIM_MAX = 0.65
INTENTIONAL_CLEAN_HOLD = "intentionalCleanHold"
SOURCE_BOUND_STICKER = "sourceBoundSticker"
STRONG_CLAIM_TERMS = [
    "关键", "本质", "真正", "核心", "重点", "重要", "原因", "结论",
    "缺点", "优点", "只能", "救不了", "一定要", "推荐", "更划算",
]
def sfx_manifest_path() -> Path:
    candidates = [
        SCRIPT_DIR.parent / "public" / "input" / "audio" / "sfx_manifest.json",
        SCRIPT_DIR.parent / "assets" / "remotion-template" / "public" / "input" / "audio" / "sfx_manifest.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("missing V4 portrait sfx_manifest.json")


def load_sfx_suggestions() -> dict[str, dict[str, Any]]:
    manifest = json.loads(sfx_manifest_path().read_text(encoding="utf-8-sig"))
    suggestions: dict[str, dict[str, Any]] = {}
    for item in manifest.get("items", []):
        if not isinstance(item, dict):
            continue
        intent = str(item.get("intent") or "")
        if not intent:
            continue
        suggestions[intent] = {
            "sfxId": str(item.get("sfxId") or ""),
            "path": str(item.get("path") or ""),
            "volumeDb": item.get("defaultVolumeDb", -5),
            "durationFrames": int(item.get("durationFrames", 25) or 25),
            "durationSec": float(item.get("durationSec", 0) or 0),
            "preRollSec": (4 / DEFAULT_FPS) if intent == "title_impact" else 0.0,
        }
    return suggestions


SFX_SUGGESTIONS: dict[str, dict[str, Any]] = load_sfx_suggestions()


def load_presenter_layout_policy() -> dict[str, Any]:
    data = get_registry().presentation_rules
    policy = data.get("presenterLayoutPolicy")
    if not isinstance(policy, dict):
        raise ValueError("presentation_rules.json missing presenterLayoutPolicy")
    return policy


PRESENTATION_REGISTRY = get_registry()
PRESENTATION_SFX_INTENTS = presentation_sfx_intents()
PRESENTER_LAYOUT_POLICY = load_presenter_layout_policy()
PUNCTUATION = " ，。？！、；;：:.!?"
NUMERIC_VALUE_RE = re.compile(r"[+\-]?\d+(?:\.\d+)?\s*(?:%|万|亿|倍|[KkMmGg]|个|张|条|分钟|秒)?")

NEGATIVE_TERMS = ["手动", "不是", "麻烦", "低效", "重复", "卡住", "风险", "不值得", "太慢", "人工成本"]
POSITIVE_TERMS = ["自动化", "自动", "完成", "搞定", "跑完", "输出完成", "Codex", "一键", "接管"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def validate_presenter_layout_policy(data: dict[str, Any]) -> None:
    automatic_allowed = {
        str(value) for value in PRESENTER_LAYOUT_POLICY.get("automaticAllowed", [])
    }
    manual_only = {
        str(value) for value in PRESENTER_LAYOUT_POLICY.get("manualOnly", [])
    }
    for index, scene in enumerate(data.get("scenes", [])):
        if not isinstance(scene, dict):
            continue
        layout = str(scene.get("presenterLayout") or "")
        source = str(scene.get("presenterLayoutSource") or "")
        if source == "automatic" and (layout in manual_only or layout not in automatic_allowed):
            raise ValueError(
                f"scenes[{index}] automatic presenter layout cannot use {layout!r}; "
                "portrait side layout is manual/legacy compatibility only"
            )


def normalize_hud_source(text: str) -> str:
    clean = re.sub(r"\s+", "", text).strip(PUNCTUATION)
    for filler in ["但是", "其实", "然后", "那么", "首先", "这件事真正重要的是", "真正重要的是"]:
        clean = clean.replace(filler, "")
    for old, new in [
        ("这一步，应该", "应该"),
        ("这一步应该", "应该"),
        ("这一步，", ""),
        ("而是你把", "把"),
        ("而是把", "把"),
        ("而是", ""),
        ("不是你要", "不是"),
        ("不是要", "不是"),
        ("一个", ""),
        ("生成了", "生成"),
        ("做出来了", "做出"),
        ("自动完成了", "自动完成"),
    ]:
        clean = clean.replace(old, new)
    return clean.strip(PUNCTUATION)


def normalize_for_match(text: str) -> str:
    return re.sub(r"[\s，。？！、；;：:.!?\-_/|]+", "", text)


def caption_cues_by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(cue.get("id") or ""): cue
        for cue in data.get("captionCues", [])
        if isinstance(cue, dict)
    }


def owned_source_cues(beat: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return caption cues explicitly owned by this semantic beat, in source order."""
    cue_map = caption_cues_by_id(data)
    scene_id = str(beat.get("sceneId") or "")
    cues: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in beat.get("sourceCueIds", []):
        cue_id = str(item or "")
        cue = cue_map.get(cue_id)
        if not cue_id or cue_id in seen or cue is None:
            continue
        if scene_id and str(cue.get("sceneId") or "") != scene_id:
            continue
        seen.add(cue_id)
        cues.append(cue)
    return sorted(cues, key=lambda cue: int(cue.get("startFrame", 0) or 0))


def source_bound_steps(
    beat: dict[str, Any],
    data: dict[str, Any],
    candidates: list[tuple[str, str]],
    prefix: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Build visible rows only from exact words present in beat-owned caption cues."""
    matches: list[tuple[int, int, str, str, str, str]] = []
    for cue_index, cue in enumerate(owned_source_cues(beat, data)):
        cue_id = str(cue.get("id") or "")
        cue_text = str(cue.get("text") or "")
        for label, icon in candidates:
            position = cue_text.find(label)
            if position >= 0:
                matches.append((cue_index, position, label, icon, cue_id, cue_text))
    steps: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for _cue_index, _position, label, icon, cue_id, cue_text in sorted(matches):
        if label in seen_labels:
            continue
        seen_labels.add(label)
        steps.append({
            "id": f"{prefix}-{len(steps) + 1:02d}",
            "label": label,
            "text": label,
            "sourceCueIds": [cue_id],
            "iconName": icon,
        })
        if len(steps) == limit:
            break
    return steps


def validated_beat_internal_steps(
    beat: dict[str, Any], data: dict[str, Any], limit: int = 5,
) -> list[dict[str, Any]]:
    """Keep only beat-owned, exact-source internal rows supplied by the semantic router."""
    raw_steps = beat.get("internalSteps") if isinstance(beat.get("internalSteps"), list) else []
    cue_map = {str(cue.get("id") or ""): cue for cue in owned_source_cues(beat, data)}
    steps: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for raw in raw_steps:
        if not isinstance(raw, dict):
            continue
        label = str(raw.get("label") or "").strip()[:12]
        text = str(raw.get("text") or "").strip()
        source_ids = [str(item) for item in raw.get("sourceCueIds", []) if str(item)]
        if not label or not text or label in seen_labels or label not in text or not source_ids:
            continue
        if any(cue_id not in cue_map for cue_id in source_ids):
            continue
        if not all(text in str(cue_map[cue_id].get("text") or "") for cue_id in source_ids):
            continue
        step = dict(raw)
        step.update({
            "id": str(raw.get("id") or f"source-step-{len(steps) + 1:02d}"),
            "label": label,
            "text": text,
            "sourceCueIds": source_ids,
            "iconName": str(raw.get("iconName") or "Workflow"),
        })
        steps.append(step)
        seen_labels.add(label)
        if len(steps) == limit:
            break
    return steps


def provenance_fallback(
    base: dict[str, Any], intent: str, text: str, reason: str,
) -> dict[str, Any]:
    source_copy = re.sub(r"\s+", "", text).strip(PUNCTUATION)[:18]
    return {
        **base,
        "type": "captionHighlight",
        "semanticRole": "explanation-claim",
        "text": source_copy or "信息不足",
        "status": "SOURCE ONLY",
        "iconName": "Info",
        "motionType": "hud-slide-fade",
        "semanticFallbackFrom": intent,
        "fallbackReason": reason,
    }


def provenance_reason(beat: dict[str, Any], data: dict[str, Any], entity_reason: str) -> str:
    return entity_reason if owned_source_cues(beat, data) else "missing-source-cues"


def cue_anchor_for_event(event: dict[str, Any], beat: dict[str, Any], data: dict[str, Any]) -> tuple[int, str] | None:
    source_ids = [str(item) for item in beat.get("sourceCueIds", []) if str(item)]
    if not source_ids:
        return None
    cue_map = caption_cues_by_id(data)
    cues = [cue_map[cue_id] for cue_id in source_ids if cue_id in cue_map]
    if not cues:
        return None

    phrases: list[str] = []
    is_problem_map = str(event.get("type") or "") in {"semanticProblemMap", "highlightBox"}
    if is_problem_map:
        phrases.append(str(event.get("text") or ""))
        phrases.extend(str(item) for item in event.get("emphasisWords", []) if str(item))
        phrases.extend(str(item) for item in beat.get("keywords", []) if str(item))
        phrases.extend(str(event.get(key) or "") for key in ("title", "status", "subtext") if str(event.get(key) or ""))
    else:
        for key in ("text", "subtext", "title", "status"):
            value = str(event.get(key) or "")
            if value:
                phrases.append(value)
        phrases.extend(str(item) for item in event.get("emphasisWords", []) if str(item))
        phrases.extend(str(item) for item in beat.get("keywords", []) if str(item))
    normalized_phrases = [normalize_for_match(phrase) for phrase in phrases if len(normalize_for_match(phrase)) >= 2]
    if is_problem_map:
        phrases = list(dict.fromkeys(normalized_phrases))
    else:
        phrases = sorted(set(normalized_phrases), key=len, reverse=True)

    for phrase in phrases:
        for cue in cues:
            cue_text = normalize_for_match(str(cue.get("text") or ""))
            if phrase and phrase in cue_text:
                return max(0, int(cue.get("startFrame", 0) or 0) - 3), str(cue.get("id") or "")

    if len(cues) == 1:
        cue = cues[0]
        return max(0, int(cue.get("startFrame", 0) or 0)), str(cue.get("id") or "")
    return None


def anchor_event_to_caption_cue(event: dict[str, Any], beat: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    anchor = cue_anchor_for_event(event, beat, data)
    if not anchor:
        return event
    start, cue_id = anchor
    current_start = int(event.get("startFrame", 0) or 0)
    current_end = int(event.get("endFrame", current_start + MIN_MAIN_HUD_FRAMES) or current_start + MIN_MAIN_HUD_FRAMES)
    if abs(start - current_start) < 2:
        return event
    minimum = (
        round(composition_fps(data) * 1.8)
        if str(event.get("timingClass") or "") == "short-lightweight"
        else MIN_MAIN_HUD_FRAMES
    )
    return {
        **event,
        "startFrame": start,
        "endFrame": start + max(minimum, current_end - current_start),
        "timingAnchor": "captionCueKeyword",
        "anchorCueId": cue_id,
    }


def split_negative_positive(text: str) -> tuple[str, str]:
    for pivot in ["而是", "这一步", "交给", "丢给", "变成", "应该自动", "可以直接", "不用自己"]:
        if pivot in text:
            index = text.find(pivot)
            left = text[:index].strip(PUNCTUATION)
            right = text[index:].strip(PUNCTUATION)
            if left and right:
                return left, right
    return text.strip(), ""


def shorten_hud_copy(text: str, max_chars: int = 18) -> str:
    clean = normalize_hud_source(text)
    if len(clean) <= max_chars:
        return clean
    for marker in ["不是", "手动", "自动化", "Codex", "重复", "字段", "主图", "评论区", "反直觉", "还没有开始"]:
        if marker in clean:
            start = max(0, clean.find(marker) - 2)
            return clean[start : start + max_chars]
    return clean[:max_chars]


def key_message(text: str, max_chars: int = 16, preferred_terms: list[str] | None = None) -> str:
    clean = normalize_hud_source(text)
    if "账号未转正" in clean:
        return "账号未转正"
    if "不可能手动" in clean:
        return "不可能手动做"
    if "AI" in clean and "还没有开始" in clean:
        return "AI 真正的大爆发"
    if "手动" in clean and "主图" in clean:
        return "手动做主图"
    if "Codex" in clean and "主图" in clean:
        return "Codex 生成主图"
    if "字段" in clean or ("标题" in clean and "标签" in clean):
        return "重复填写字段"
    if "评论区" in clean:
        return "评论区告诉我"
    if "小于" in clean and "分钟" in clean:
        return "< 1 分钟"
    if "52" in clean and "道题" in clean:
        return "52 道题"
    for term in preferred_terms or []:
        if term and term in clean:
            start = clean.find(term)
            candidate = clean[start : start + max_chars]
            if start + max_chars < len(clean):
                candidate = candidate.rstrip("有没进再和与把的是也更但所因如用")
            return candidate.rstrip("啊呀吧呢")
    candidate = shorten_hud_copy(clean, max_chars)
    if len(candidate) < len(clean):
        candidate = candidate.rstrip("有没进再和与把的是也更但所因如用")
    return candidate.rstrip("啊呀吧呢")


def focus_words(text: str, terms: list[str], limit: int = 2) -> list[str]:
    hits = [term for term in terms if term and term in text]
    if hits:
        return hits[:limit]
    clean = normalize_hud_source(text)
    if len(clean) <= 4:
        return [clean] if clean else []
    return [clean[-min(4, len(clean)):]]


def compact_negative_positive(text: str) -> tuple[str, str, list[str]]:
    negative, positive = split_negative_positive(text)
    if "不是" in negative:
        negative = negative[negative.rfind("不是"):]
    negative_short = key_message(negative, 16, NEGATIVE_TERMS)
    positive_short = key_message(positive, 16, POSITIVE_TERMS) if positive else ""
    if not any(term in negative_short for term in NEGATIVE_TERMS):
        negative_short = "还在手动" if "手动" in text else negative_short
    emphasis = focus_words(negative_short, NEGATIVE_TERMS, 1)
    if positive_short:
        emphasis += focus_words(positive_short, POSITIVE_TERMS, 1)
    return negative_short, positive_short, emphasis[:2]


def result_title_copy(text: str) -> tuple[str, list[str], bool]:
    clean = normalize_hud_source(text)
    is_contrarian = any(term in clean for term in ["反直觉", "还没有开始", "真正的大爆发"])
    if is_contrarian and "还没有开始" in clean:
        return "AI 真正的大爆发\n其实还没有开始", ["还没有开始"], True
    copy = key_message(text, 18, ["自动", "主图", "分发", "发布", "工作流", "Codex", "一键", "爆发"])
    return copy or "结果已经明确", focus_words(copy, POSITIVE_TERMS + ["一键", "多平台", "主图", "爆发"], 1), is_contrarian


def confirm_copy(text: str) -> tuple[str, str, list[str]]:
    copy = key_message(text, 16, POSITIVE_TERMS)
    return "自动化交接", copy or "交给 Codex 自动执行", focus_words(copy, POSITIVE_TERMS, 1)


def cta_copy(text: str, sourced_provenance: dict[str, Any] | None = None) -> tuple[str, str, str, list[str], dict[str, str]]:
    clean = normalize_hud_source(text)
    provenance_action = str((sourced_provenance or {}).get("action") or "").strip()
    normalized_provenance_action = normalize_hud_source(provenance_action)
    sourced_action = normalized_provenance_action if normalized_provenance_action in clean else ""
    action = provenance_action or next(
        (term for term in ["评论区", "关注", "点赞", "收藏", "私信", "领取", "自提", "告诉我"] if term in clean),
        "",
    )
    keyword = str((sourced_provenance or {}).get("keyword") or "").strip()
    keyword_match = re.search(r"(?:扣|回复|发送)\s*([^，。！？]{1,12})", text)
    if not keyword and keyword_match:
        keyword = keyword_match.group(1).strip()
    elif not keyword:
        keyword_match = re.search(r"关键词(?:是|叫|为|[:：])\s*([^，。！？]{1,12})", text)
        if keyword_match:
            keyword = keyword_match.group(1).strip()

    future_topic_match = re.search(
        r"(?:下一期|下期|下一集|下集|下一条)[^，。！？]{0,12}(?:介绍|讲|拆解|分享|教)(?:如何|怎么)?([^，。！？]{2,18}?)(?=点个关注|关注|点赞|收藏|评论区|私信|领取|自提|$)",
        clean,
    )
    future_topic = future_topic_match.group(1).strip() if future_topic_match else ""
    future_topic = re.sub(r"^(?:如何|怎么|用)", "", future_topic)

    if future_topic and action:
        title = f"下期：{future_topic}"[:14]
    elif sourced_action:
        title = sourced_action[:14]
    elif "评论区" in clean and "告诉我" in clean:
        title = "评论区告诉我"
    elif "点个关注" in clean:
        title = "点个关注"
    elif "关注" in clean:
        title = "关注我"
    elif "收藏" in clean:
        title = "收藏这一条"
    elif "点赞" in clean:
        title = "点个赞"
    elif "私信" in clean:
        title = "私信我"
    elif "领取" in clean:
        title = "直接领取"
    elif "自提" in clean:
        title = "自行提取"
    elif "评论区" in clean:
        title = "评论区"
    else:
        title = key_message(text, 14, ["关注", "点赞", "收藏", "私信", "领取", "自提", "告诉我"]) or "行动提示"

    if future_topic and action:
        action_copy = "点个关注" if "点个关注" in clean else title if action in title else action
        subtext = f"{action_copy} · 下期见" if "下期见" in clean else action_copy
    elif sourced_action:
        subtext = clean.replace(sourced_action, "", 1)
        normalized_keyword = normalize_hud_source(keyword)
        if normalized_keyword:
            subtext = subtext.replace(normalized_keyword, "", 1)
        subtext = subtext.strip(PUNCTUATION)[:18]
    else:
        subtext = key_message(text, 18, ["Codex", "流程", "模板", "下期", "下一条", "自动化"])
    if normalize_for_match(subtext) == normalize_for_match(title):
        subtext = ""
    status = f"关键词：{keyword}" if keyword else action
    emphasis = [item for item in [keyword, action, title] if item and item in f"{title}{subtext}{status}"][:2]
    provenance = dict(sourced_provenance or {})
    provenance["kind"] = "keyword" if keyword else "action" if action else "claim"
    provenance["sourceText"] = str(provenance.get("sourceText") or text).strip()
    if action:
        provenance["action"] = action
    if keyword:
        provenance["keyword"] = keyword
    return title, subtext, status, emphasis, provenance


def numeric_fields(text: str) -> dict[str, Any]:
    return numeric_event_fields(text)


def chapter_label_for_scene(scene: dict[str, Any]) -> tuple[str, str]:
    role = str(scene.get("semanticRole") or "")
    scene_type = str(scene.get("type") or "")
    if scene_type == "Hook":
        return "COLD OPEN", "反直觉开场"
    if scene_type == "CTA" or role == "cta-resolve":
        return "CTA", "行动引导"
    if role in {"semantic-problem-map", "negative-friction"}:
        return "PAIN POINT", "负面判断"
    if role == "platform-fanout":
        return "DISTRIBUTION", "平台分发"
    if role == "automation-handoff":
        return "AUTO HANDOFF", "自动化交接"
    if role in {"proof-material", "proof-focus"}:
        return "PROOF", "素材证明"
    return "PROCESS", "流程推进"


def corner_label(scene: dict[str, Any]) -> dict[str, Any]:
    text, subtext = chapter_label_for_scene(scene)
    scene_id = str(scene["id"])
    return {
        "id": f"ve-{scene_id}-corner-label",
        "sceneId": scene_id,
        "type": "cornerChapterLabel",
        "startFrame": int(scene["startFrame"]),
        "endFrame": int(scene["endFrame"]),
        "text": text,
        "subtext": subtext,
        "semanticRole": "chapter-label",
        "motionType": "corner-slide-fade",
        "style": "top-left-corner-label",
        "safeArea": "top-left-no-shade",
    }


def semantic_role_for_beat(beat: dict[str, Any]) -> str:
    intent = str(beat.get("semanticIntent") or "")
    return {
        "negative-to-positive": "semantic-problem-map",
        "negative-friction": "semantic-problem-map",
        "result-promise": "result-promise",
        "topic-intro": "topic-intro",
        "explanation-claim": "explanation-claim",
        "workflow-step": "workflow-step",
        "paired-inputs": "paired-inputs",
        "parallel-factors": "parallel-factors",
        "causal-driver": "causal-driver",
        "factor-priority": "factor-priority",
        "limitation-boundary": "limitation-boundary",
        "prerequisite": "prerequisite",
        "positive-confirm": "automation-handoff",
        "automation-handoff": "automation-handoff",
        "numeric-metric": "metric-growth",
        "enumeration": "workflow-step",
        "workflow-fields": "workflow-step",
        "manual-field": "manual-field",
        "asset-variants": "workflow-step",
        "platform-fanout": "platform-fanout",
        "proof-material": "proof-material",
        "capability-share": "capability-share",
        "scene-lock": "scene-lock",
        "transformation-stack": "transformation-stack",
        "cta-resolve": "cta-resolve",
        "topic-intro": "topic-intro",
        "explanation-claim": "explanation-claim",
    }.get(intent, "explanation-claim")


def lane_for_event(event: dict[str, Any]) -> str | None:
    event_type = str(event.get("type") or "")
    role = str(event.get("semanticRole") or "")
    safe_area = str(event.get("safeArea") or "").lower()
    if event_type == "cornerChapterLabel":
        return None
    if event_type == "statusSticker":
        return "right" if "top-right" in safe_area or "right" in safe_area else None
    if event_type in {"claimStrip", "quoteSource"}:
        return "right"
    if event_type in {"ctaTitle", "ctaRecommend"}:
        return "left"
    if event_type == "materialMain":
        return "proof"
    if event_type in {"dataPunch", "metricSpotlight"}:
        return "right" if "right" in safe_area else "left"
    if event_type in {"semanticProblemMap", "highlightBox"} or role == "semantic-problem-map":
        return "right" if "right" in safe_area else "left"
    if event_type in {
        "flowPath", "statusStack", "transitionPushZoom", "platformFanout",
        "pairedInputRail", "factorTrinity", "factorPriority", "compactPipeline",
        "priorityConclusion", "historicalGreenConclusion",
    } or role in {"platform-fanout", "workflow-step", "manual-field"}:
        return "right"
    return "left"


def composition_fps(data: dict[str, Any]) -> int:
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    return int(composition.get("fps") or DEFAULT_FPS)


def scene_density_mode(scene: dict[str, Any], data: dict[str, Any]) -> str:
    source_video_mode = str(data.get("sourceVideoMode") or "")
    packaging_density = str(data.get("packagingDensity") or "")
    scene_type = str(scene.get("type") or "")
    presenter_layout = str(scene.get("presenterLayout") or "")
    material_layout = str(scene.get("materialLayout") or "")
    semantic_role = str(scene.get("semanticRole") or "")
    if material_layout in {"main", "clean"} or presenter_layout == "pip" or semantic_role in {"proof-material", "proof-focus"}:
        return "proof-focus"
    if source_video_mode == "precomposed-video" or packaging_density == "light":
        return "light"
    if scene_type in {"Hook", "CTA", "Contrast"}:
        return "dense-strong"
    return "dense"


def annotate_density(event: dict[str, Any], scene: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    mode = scene_density_mode(scene, data)
    event = {**event, "densityMode": mode}
    if mode == "proof-focus":
        event["densityReason"] = "material-readable"
    elif mode == "light":
        event["densityReason"] = "precomposed-or-light-packaging"
    elif mode == "dense-strong":
        event["densityReason"] = "hook-cta-contrast"
    else:
        event["densityReason"] = "default-dense"
    return event


def desired_duration_for_event(event: dict[str, Any], scene: dict[str, Any] | None = None, data: dict[str, Any] | None = None) -> int:
    event_type = str(event.get("type") or "")
    density_mode = str(event.get("densityMode") or "")
    scene_type = str((scene or {}).get("type") or "")
    current = int(event.get("endFrame", 0) or 0) - int(event.get("startFrame", 0) or 0)
    if str(event.get("timingClass") or "") == "short-lightweight":
        fps = composition_fps(data or {})
        return max(current, round(fps * 1.8))
    base = PREFERRED_MAIN_HUD_FRAMES
    if event_type in {
        "highlightBox", "captionHighlight", "flowPath", "statusStack", "capabilityShare",
        "sceneLockGrid", "transformationStack", "pairedInputRail", "factorTrinity",
        "causalDriver", "factorPriority", "compactPipeline", "limitationWarning",
        "priorityConclusion", "historicalGreenConclusion",
    }:
        base = 135
    if event_type in {"kineticTitle", "ctaTitle"}:
        base = 120
    if event_type in {"topicKeyword", "claimStrip"}:
        base = 95
    if density_mode == "dense-strong" and scene_type in {"Hook", "CTA", "Contrast"}:
        base = max(base, 140)
    if density_mode == "light" and event_type not in {"materialMain", "ctaTitle", "kineticTitle"}:
        base = min(base, 115)
    if density_mode == "proof-focus" and event_type not in {"materialMain", "statusSticker"}:
        base = min(base, 90)
    if event_type == "materialMain":
        base = max(PREFERRED_MAIN_HUD_FRAMES, int(event.get("endFrame", 0) or 0) - int(event.get("startFrame", 0) or 0))
    steps = event.get("internalSteps")
    if isinstance(steps, list) and steps:
        base = max(base, 58 + len(steps) * 22)
    return max(base, current, MIN_MAIN_HUD_FRAMES)


def proof_asset_from_media(data: dict[str, Any]) -> str | None:
    media_items = data.get("media", []) if isinstance(data.get("media"), list) else []
    for item in media_items:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "")
        media_type = str(item.get("type") or "")
        role = str(item.get("role") or "")
        if path and (role in {"proof-material", "screen-recording", "recording"} or media_type in {"recording", "screenshot"}):
            return path
    return None


def poster_steps(beat: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    return source_bound_steps(beat, data, [
        ("16:9", "PanelsTopLeft"), ("3:4", "Image"), ("1:1", "Images"),
        ("4:3", "PanelsTopLeft"), ("横屏", "PanelsTopLeft"), ("横版", "PanelsTopLeft"),
        ("竖屏", "Image"), ("竖版", "Image"), ("方图", "Images"), ("方形", "Images"),
    ], "ratio", 4)


def field_steps(beat: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    supplied = validated_beat_internal_steps(beat, data)
    if len(supplied) >= 2:
        return supplied
    return source_bound_steps(beat, data, [
        ("输入", "TextCursorInput"),
        ("关键词", "Hash"),
        ("上传", "UploadCloud"),
        ("标题", "FileText"),
        ("简介", "AlignLeft"),
        ("标签", "Tags"),
        ("封面", "Image"),
        ("字段", "ClipboardList"),
        ("输出", "SendHorizontal"),
        ("视频", "Video"),
    ], "field", 5)


def capability_steps(beat: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    return source_bound_steps(beat, data, [
        ("OpenAI", "Bot"), ("Google", "Network"), ("Anthropic", "BrainCircuit"),
        ("国内", "Landmark"), ("国外", "Globe2"), ("企业客户", "Building2"),
        ("模型能力", "BrainCircuit"), ("市场份额", "BarChart3"), ("排名", "Trophy"),
    ], "cap", 4)


def scene_steps(beat: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    return source_bound_steps(beat, data, [
        ("支付", "CreditCard"),
        ("教育", "GraduationCap"),
        ("政务", "Landmark"),
        ("下沉市场", "MapPinned"),
        ("本地生活", "Store"),
        ("餐饮", "Store"), ("零售", "Store"), ("基础设施", "Landmark"),
    ], "scene", 4)


def transformation_steps(text: str) -> list[dict[str, str]]:
    source = "原状态"
    target = "目标状态"
    relation = re.search(r"从([^，。！？]{1,10}?)(?:变成|转化成|到)([^，。！？]{1,10})", text)
    if relation:
        source = relation.group(1).strip()
        target = relation.group(2).strip()
    elif "一个人" in text and "团队" in text:
        source, target = "一个人", "一个团队"
    elif "个人" in text and "团队" in text:
        source, target = "个人", "团队"
    drivers = [term for term in ["第二大脑", "知识库", "杠杆", "护城河", "可复制流程"] if term in text]
    result = next((term for term in ["能力放大", "长期系统", "团队资产", "可复制流程"] if term in text), "转化结果")
    steps = [
        {"id": "state-01", "label": source[:10], "iconName": "User"},
        {"id": "state-02", "label": target[:10], "iconName": "Users"},
    ]
    steps.extend(
        {"id": f"driver-{index + 1:02d}", "label": driver, "iconName": "BrainCircuit", "status": "驱动"}
        for index, driver in enumerate(drivers[:2])
    )
    steps.append({"id": "result-01", "label": result, "iconName": "TrendingUp", "status": "结果"})
    return steps


_TRUSTED_TRANSFORMATION_PATTERNS = (
    re.compile(
        r"(?:\u4ece|\u7531)\s*(?P<source>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{1,18}?)\s*[,\uFF0C]?\s*"
        r"(?:\u53d8\u6210|\u8f6c\u53d8\u6210|\u8f6c\u5316\u6210|\u8f6c\u4e3a|\u5230)\s*"
        r"(?P<target>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{1,18})"
    ),
    re.compile(
        r"\u628a\s*(?P<source>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{1,18}?)\s*[,\uFF0C]?\s*"
        r"(?:\u53d8\u6210|\u8f6c\u53d8\u6210|\u8f6c\u5316\u6210|\u8f6c\u4e3a)\s*"
        r"(?P<target>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{1,18})"
    ),
    re.compile(
        r"(?P<source>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{1,14}?)\s*(?:\u4f1a|\u80fd)?\s*"
        r"(?:\u53d8\u6210|\u8f6c\u53d8\u6210|\u8f6c\u5316\u6210|\u8f6c\u4e3a)\s*"
        r"(?P<target>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{1,18})"
    ),
)
_TRUSTED_DRIVER_ICONS = {
    "\u6c1b\u56f4": "Sparkles",
    "\u8bbe\u5907": "Monitor",
    "\u642d\u5b50": "Handshake",
    "\u670b\u53cb": "Handshake",
    "\u65b0\u5e97": "Store",
    "AI": "Bot",
    "Codex": "TerminalSquare",
    "\u7cfb\u7edf": "Network",
    "\u81ea\u52a8\u5316": "Bot",
    "\u7b2c\u4e8c\u5927\u8111": "BrainCircuit",
    "\u77e5\u8bc6\u5e93": "Database",
    "\u89c4\u5219": "ListChecks",
    "\u5de5\u5177": "Wrench",
    "\u6d41\u7a0b": "Workflow",
    "\u6760\u6746": "TrendingUp",
    "\u7ecf\u9a8c": "BadgeCheck",
}


def _trusted_transform_label(value: str, limit: int = 10) -> str:
    clean = re.sub(r"\s+", "", value).strip(PUNCTUATION)
    clean = re.sub(r"^(?:\u6765|\u8ba9|\u5c06|\u4f1a|\u80fd)", "", clean)
    return clean[:limit]


def _trusted_transformation_source_cues(
    beat: dict[str, Any],
    data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return only caption cues explicitly owned by the semantic beat."""
    scene_id = str(beat.get("sceneId") or "")
    cue_by_id = {
        str(cue.get("id") or ""): cue
        for cue in data.get("captionCues", [])
        if isinstance(cue, dict)
    }
    cues: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in beat.get("sourceCueIds", []):
        cue_id = str(item or "")
        cue = cue_by_id.get(cue_id)
        if not cue_id or cue_id in seen or cue is None:
            continue
        if str(cue.get("sceneId") or "") != scene_id:
            continue
        seen.add(cue_id)
        cues.append(cue)
    return sorted(cues, key=lambda cue: int(cue.get("startFrame", 0) or 0))


def _trusted_transformation_relation(cues: list[dict[str, Any]]) -> dict[str, Any] | None:
    for cue in cues:
        text = str(cue.get("text") or "")
        for pattern in _TRUSTED_TRANSFORMATION_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            source = _trusted_transform_label(match.group("source"))
            target = _trusted_transform_label(match.group("target"))
            if source and target and source != target and source in text and target in text:
                return {
                    "source": source,
                    "target": target,
                    "text": text,
                    "sourceCueIds": [str(cue.get("id") or "")],
                }
    return None


def _trusted_split_drivers(value: str) -> list[str]:
    clean = re.sub(r"(?:\u90fd|\u5168\u90e8)$", "", re.sub(r"\s+", "", value).strip(PUNCTUATION))
    return [item for item in re.split(r"[\u3001\uFF0C\u548c\u4e0e\u53ca]", clean) if 1 < len(item) <= 10]


def _trusted_transformation_drivers(cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[tuple[int, int, str, str, str]] = []
    patterns = (
        re.compile(
            r"\u628a(?P<items>[^\u3002\uFF01\uFF1F]{2,32}?)(?:\u90fd|\u5168\u90e8)?"
            r"(?:\u51c6\u5907\u597d|\u51c6\u5907\u597d\u4e86|\u914d\u9f50|\u5b89\u6392\u597d|\u505a\u597d)"
        ),
        re.compile(
            r"(?:\u9760|\u901a\u8fc7|\u501f\u52a9|\u4f9d\u9760|\u7528)"
            r"(?P<items>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{2,24})\s*[,\uFF0C]?\s*"
            r"(?:\u63a8\u52a8|\u5b9e\u73b0|\u5b8c\u6210|\u8ba9|\u628a|\u5c06)"
        ),
        re.compile(
            r"(?:\u5173\u952e\u662f|\u6838\u5fc3\u662f|\u9a71\u52a8\u529b\u662f)\s*"
            r"(?P<items>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{2,18})"
        ),
        re.compile(
            r"(?P<items>AI|Codex|\u81ea\u52a8\u5316|\u7cfb\u7edf|\u77e5\u8bc6\u5e93|\u7b2c\u4e8c\u5927\u8111)\s*"
            r"(?:\u4f1a|\u80fd|\u53ef\u4ee5)?\s*\u628a"
        ),
    )
    for cue_index, cue in enumerate(cues):
        cue_id = str(cue.get("id") or "")
        text = str(cue.get("text") or "")
        for pattern_index, pattern in enumerate(patterns):
            for match in pattern.finditer(text):
                candidates.extend(
                    (cue_index, match.start() + pattern_index, item, cue_id, text)
                    for item in _trusted_split_drivers(match.group("items"))
                )

    drivers: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _, _, label, cue_id, text in sorted(candidates, key=lambda item: (item[0], item[1])):
        label = _trusted_transform_label(label)
        if not label or label in seen or label not in text:
            continue
        seen.add(label)
        drivers.append(
            {
                "label": label,
                "iconName": _TRUSTED_DRIVER_ICONS.get(label, "Cog"),
                "text": text,
                "sourceCueIds": [cue_id],
            }
        )
        if len(drivers) == 2:
            break
    return drivers


_TRUSTED_RESULT_PATTERNS = (
    re.compile(
        r"(?P<result>(?:\u6548\u7387|\u901f\u5ea6|\u4ea7\u51fa|\u51c6\u786e\u7387|\u901a\u8fc7\u7387|\u8f6c\u5316\u7387|\u6210\u672c|\u8017\u65f6|\u65f6\u95f4|\u9519\u8bef\u7387|\u5931\u8d25\u9879|\u5b8c\u6210\u7387)\s*"
        r"(?:\u63d0\u5347|\u63d0\u9ad8|\u589e\u957f|\u589e\u52a0|\u964d\u4f4e|\u51cf\u5c11|\u7f29\u77ed|\u8fbe\u5230|\u964d\u5230|\u4e3a|\u662f)?\s*"
        r"\d+(?:\.\d+)?\s*(?:%|\u500d|\u6761|\u5f20|\u4e2a|\u5206\u949f|\u79d2|\u5c0f\u65f6|\u5929|\u9879)?)"
    ),
    re.compile(
        r"(?:\u6700\u7ec8|\u6700\u540e|\u4ece\u800c|\u4e8e\u662f|\u7ed3\u679c(?:\u662f|\u4e3a)?|\u73b0\u5728\u5df2\u7ecf|\u5df2\u7ecf)\s*"
        r"(?:\u53ef\u4ee5|\u80fd\u591f|\u80fd|\u4f1a)?\s*"
        r"(?:\u5b9e\u73b0|\u5f62\u6210|\u5f97\u5230|\u5e26\u6765|\u505a\u5230|\u8fbe\u6210|\u5b8c\u6210)\s*"
        r"(?P<result>[^\uFF0C\u3002\uFF01\uFF1F\uFF1B;]{2,18})"
    ),
)


def _trusted_transformation_result(cues: list[dict[str, Any]]) -> dict[str, Any] | None:
    for cue in cues:
        text = str(cue.get("text") or "")
        for pattern in _TRUSTED_RESULT_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            result = _trusted_transform_label(match.group("result"), 12)
            if result and result in text:
                return {
                    "label": result,
                    "text": text,
                    "sourceCueIds": [str(cue.get("id") or "")],
                }
    return None


def _trusted_transformation_plan(
    beat: dict[str, Any],
    data: dict[str, Any],
) -> tuple[dict[str, Any] | None, str]:
    cues = _trusted_transformation_source_cues(beat, data)
    if not cues:
        return None, "missing-source-cues"
    relation = _trusted_transformation_relation(cues)
    if not relation:
        return None, "missing-source-target"
    drivers = _trusted_transformation_drivers(cues)
    if not drivers:
        return None, "missing-driver"
    result = _trusted_transformation_result(cues)
    if not result:
        return None, "missing-result"

    source = str(relation["source"])
    target = str(relation["target"])
    relation_text = str(relation["text"])
    relation_cue_ids = [str(item) for item in relation["sourceCueIds"]]
    steps: list[dict[str, Any]] = [
        {
            "id": "state-01",
            "role": "source",
            "label": source,
            "text": relation_text,
            "sourceCueIds": relation_cue_ids,
            "iconName": "User",
            "status": "SOURCE",
        },
        {
            "id": "state-02",
            "role": "target",
            "label": target,
            "text": relation_text,
            "sourceCueIds": relation_cue_ids,
            "iconName": "Users",
            "status": "TARGET",
        },
    ]
    steps.extend(
        {
            "id": f"driver-{index + 1:02d}",
            "role": "driver",
            "label": str(driver["label"]),
            "text": str(driver["text"]),
            "sourceCueIds": [str(item) for item in driver["sourceCueIds"]],
            "iconName": str(driver["iconName"]),
            "status": "DRIVER",
        }
        for index, driver in enumerate(drivers)
    )
    steps.append(
        {
            "id": "result-01",
            "role": "result",
            "label": str(result["label"]),
            "text": str(result["text"]),
            "sourceCueIds": [str(item) for item in result["sourceCueIds"]],
            "iconName": "TrendingUp",
            "status": "RESULT",
        }
    )
    source_cue_ids: list[str] = []
    for step in steps:
        for cue_id in step["sourceCueIds"]:
            if cue_id not in source_cue_ids:
                source_cue_ids.append(cue_id)
    return {
        "source": source,
        "target": target,
        "drivers": [str(driver["label"]) for driver in drivers],
        "steps": steps,
        "sourceCueIds": source_cue_ids,
    }, ""


def platform_steps(beat: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    return source_bound_steps(beat, data, [
        ("抖音", "Video"), ("小红书", "Image"), ("B站", "MonitorUp"),
        ("快手", "SendHorizontal"), ("视频号", "PanelsTopLeft"),
    ], "platform", 5)


def automation_steps(beat: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    supplied = validated_beat_internal_steps(beat, data)
    if supplied:
        return supplied
    raw_steps = beat.get("internalSteps") if isinstance(beat.get("internalSteps"), list) else []
    candidates = [
        (str(step.get("text") or step.get("label") or ""), str(step.get("iconName") or "Bot"))
        for step in raw_steps if isinstance(step, dict) and str(step.get("text") or step.get("label") or "")
    ]
    if not candidates:
        candidates = [
            ("任务", "ClipboardList"), ("素材", "Image"), ("文案", "FileText"),
            ("页面", "MonitorUp"), ("标题", "FileText"), ("简介", "AlignLeft"),
            ("标签", "Tags"), ("封面", "Image"), ("视频", "Video"),
            ("流程", "ListChecks"), ("Codex", "Bot"), ("系统", "Bot"),
            ("自动执行", "Play"), ("接管", "Bot"), ("处理", "Cog"),
        ]
    return source_bound_steps(beat, data, candidates, "handoff", 5)


def topic_keyword(text: str, beat: dict[str, Any]) -> str:
    entities = [str(item) for item in beat.get("entities", []) if str(item)]
    for entity in entities:
        clean = re.sub(r"\s+", "", entity)
        if 2 <= len(clean) <= 8 and not NUMERIC_VALUE_RE.search(clean):
            return clean
    match = re.search(r"(?:聊|讲|说|看|拆解|测试|介绍)(?:一下|一讲)?([^，。！？]{2,8})", text)
    if match:
        return match.group(1).strip()
    return key_message(text, 8, ["数字人", "自动化", "工作流", "主图", "详情图", "大模型", "效率"]) or "本期主题"


def append_required_check(beat: dict[str, Any], check: str) -> None:
    checks = [str(item) for item in beat.get("requiredChecks", []) if str(item)]
    if check not in checks:
        checks.append(check)
    beat["requiredChecks"] = checks


def claim_priority(beat: dict[str, Any]) -> float:
    text = str(beat.get("text") or "")
    score = float(beat.get("confidence", 0.0) or 0.0) * 100
    score += sum(18 for term in STRONG_CLAIM_TERMS if term in text)
    if any(mark in text for mark in ["？", "?", "为什么", "有没有"]):
        score += 8
    if beat.get("themeThesisCandidate"):
        score += 40
    return score


def source_bound_sticker_copy(text: str) -> str:
    product = re.search(r"\b[A-Z][A-Za-z0-9.+-]*(?:\s+[A-Z][A-Za-z0-9.+-]*){0,3}\s+AI\b", text)
    if product:
        return product.group(0)
    core_clause = source_bound_core_clause(text)
    if core_clause:
        return core_clause
    clean = normalize_hud_source(text)
    for phrase in [
        "速度更快成本更低",
        "素材质量和参数设置",
        "音色情绪和语速",
        "只能改善画质",
        "参考音频",
        "数字人模型",
    ]:
        if phrase in clean:
            return phrase
    return key_message(text, 16, STRONG_CLAIM_TERMS)


def source_bound_core_clause(text: str) -> str:
    clean = normalize_for_match(normalize_hud_source(text))
    for marker in [
        "真正影响效果的往往是",
        "真正影响效果的是",
        "缺点也很明显",
        "成片之后再用",
        "所以",
    ]:
        if marker not in clean:
            continue
        candidate = clean.split(marker, 1)[1]
        for stop in ["有没有", "进行", "但是", "不过"]:
            if stop in candidate:
                candidate = candidate.split(stop, 1)[0]
        return candidate[:18].rstrip("有没进再和与把的是也更但所因如用啊呀吧呢")
    return ""


def mark_claim_clean(beat: dict[str, Any], reason: str) -> None:
    beat["visualForm"] = INTENTIONAL_CLEAN_HOLD
    beat["timingClass"] = "intentional-clean"
    beat["routingDecision"] = reason
    append_required_check(beat, "intentional-clean-hold")


def mark_claim_lightweight(beat: dict[str, Any], reason: str) -> None:
    beat["visualForm"] = SOURCE_BOUND_STICKER
    beat["timingClass"] = "short-lightweight"
    beat["routingDecision"] = reason
    append_required_check(beat, "source-bound-lightweight")


def curate_explanation_claim_beats(data: dict[str, Any]) -> None:
    """Keep ordinary explanation semantic without forcing repetitive main HUD panels."""
    beats = [beat for beat in data.get("semanticBeats", []) if isinstance(beat, dict)]
    scenes = scene_by_id(data)
    for beat in beats:
        beat_id = str(beat.get("id") or "")
        scene_id = str(beat.get("sceneId") or "")
        if beat_id and scene_id and not beat.get("beatGroupId"):
            beat["beatGroupId"] = f"{scene_id}-{beat_id}"

    # First pass: short claims and tool recommendations use a sourced lightweight sticker.
    for beat in beats:
        if str(beat.get("semanticIntent") or "") != "explanation-claim":
            continue
        if str(beat.get("visualForm") or "") != "claimStrip":
            continue
        start = int(beat.get("startFrame", 0) or 0)
        end = int(beat.get("endFrame", start) or start)
        scene = scenes.get(str(beat.get("sceneId") or ""), {})
        scene_role = str(scene.get("semanticRole") or "")
        if end - start < MIN_MAIN_HUD_FRAMES:
            mark_claim_lightweight(beat, "short-claim-source-sticker")
        elif scene_role == "tool-recommendation":
            mark_claim_lightweight(beat, "tool-recommendation-source-sticker")

    # A claim at the tail of a scene that already has a stronger semantic event
    # should not compete for a full panel when the remaining scene budget is short.
    beats_by_scene: dict[str, list[dict[str, Any]]] = {}
    for beat in beats:
        beats_by_scene.setdefault(str(beat.get("sceneId") or ""), []).append(beat)
    for scene_id, scene_beats in beats_by_scene.items():
        scene = scenes.get(scene_id, {})
        scene_end = int(scene.get("endFrame", 0) or 0)
        ordered = sorted(scene_beats, key=lambda item: int(item.get("startFrame", 0) or 0))
        for index, beat in enumerate(ordered):
            if (
                str(beat.get("semanticIntent") or "") != "explanation-claim"
                or str(beat.get("visualForm") or "") != "claimStrip"
            ):
                continue
            start = int(beat.get("startFrame", 0) or 0)
            has_prior_specific = any(
                str(item.get("semanticIntent") or "") != "explanation-claim"
                for item in ordered[:index]
            )
            if has_prior_specific and scene_end - start < PREFERRED_MAIN_HUD_FRAMES:
                mark_claim_lightweight(beat, "scene-tail-after-specific-event")

    # Second pass: within one scene, keep only the strongest low-confidence claim as main HUD.
    claims_by_scene: dict[str, list[dict[str, Any]]] = {}
    for beat in beats:
        if (
            str(beat.get("semanticIntent") or "") == "explanation-claim"
            and str(beat.get("visualForm") or "") == "claimStrip"
            and float(beat.get("confidence", 0.0) or 0.0) <= LOW_CONFIDENCE_CLAIM_MAX
        ):
            claims_by_scene.setdefault(str(beat.get("sceneId") or ""), []).append(beat)
    for scene_claims in claims_by_scene.values():
        if len(scene_claims) <= 1:
            continue
        winner = max(scene_claims, key=claim_priority)
        for beat in scene_claims:
            if beat is not winner:
                mark_claim_clean(beat, "lower-priority-claim-in-same-scene")

    # Third pass: never allow more than two consecutive low-confidence claim-strip main HUDs.
    claim_run = 0
    for beat in sorted(beats, key=lambda item: (int(item.get("startFrame", 0) or 0), str(item.get("id") or ""))):
        intent = str(beat.get("semanticIntent") or "")
        visual_form = str(beat.get("visualForm") or "")
        if intent != "explanation-claim":
            claim_run = 0
            continue
        if visual_form != "claimStrip":
            continue
        if float(beat.get("confidence", 0.0) or 0.0) > LOW_CONFIDENCE_CLAIM_MAX:
            claim_run = 0
            continue
        if claim_run >= 2:
            mark_claim_clean(beat, "claim-strip-run-limit")
            continue
        claim_run += 1


def event_for_beat(beat: dict[str, Any], data: dict[str, Any]) -> dict[str, Any] | None:
    beat_id = str(beat.get("id") or "beat")
    text = str(beat.get("text") or "")
    intent = str(beat.get("semanticIntent") or "")
    scene_id = str(beat.get("sceneId") or "")
    start = int(beat.get("startFrame", 0) or 0)
    end = int(beat.get("endFrame", start + MIN_MAIN_HUD_FRAMES) or start + MIN_MAIN_HUD_FRAMES)
    base = {
        "id": f"ve-{beat_id}",
        "sceneId": scene_id,
        "startFrame": start,
        "endFrame": end,
        "semanticRole": semantic_role_for_beat(beat),
        "beatGroupId": f"{scene_id}-{beat_id}",
        "style": "dark-fullscreen-semantic-hud",
        "safeArea": "avoid-face-caption",
        "sourceBeatId": beat_id,
    }
    if end - start < MIN_MAIN_HUD_FRAMES:
        base["timingClass"] = "short-lightweight"

    scene = scene_by_id(data).get(scene_id, {})
    material_layout = str(scene.get("materialLayout") or "")
    presenter_layout = str(scene.get("presenterLayout") or "")
    if material_layout in {"main", "clean"} or presenter_layout == "pip":
        asset_path = proof_asset_from_media(data)
        if asset_path:
            return {
                **base,
                "type": "materialMain",
                "semanticRole": "proof-material",
                "text": "素材证明",
                "subtext": "真实录屏 / 页面结果",
                "assetPath": asset_path,
                "style": "recording-proof" if Path(asset_path).suffix.lower() in {".mp4", ".mov", ".m4v", ".webm"} else "single-proof",
                "motionType": "screen-recording-proof" if Path(asset_path).suffix.lower() in {".mp4", ".mov", ".m4v", ".webm"} else "material-zoom-highlight",
            }

    if intent == "explanation-claim" and str(beat.get("visualForm") or "") == INTENTIONAL_CLEAN_HOLD:
        return None

    if intent == "explanation-claim" and str(beat.get("visualForm") or "") == SOURCE_BOUND_STICKER:
        claim = source_bound_sticker_copy(text)
        return {
            **base,
            "type": "statusSticker",
            "text": claim or normalize_hud_source(text)[:16] or "观点提示",
            "status": "重点",
            "iconName": "Sparkles",
            "motionType": "hud-slide-fade",
            "safeArea": "top-right-no-shade",
            "timingClass": "short-lightweight",
        }

    if intent == "paired-inputs":
        steps = validated_beat_internal_steps(beat, data, 2)
        if len(steps) != 2:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "needs-exactly-two-sourced-inputs")
            )
        return {
            **base,
            "type": "pairedInputRail",
            "text": " / ".join(str(step.get("label") or "") for step in steps),
            "title": "两类核心素材",
            "status": "先准备好",
            "internalSteps": steps,
            "motionType": "paired-input-stagger",
            "safeArea": "right avoid-face-caption",
        }

    if intent == "parallel-factors":
        steps = validated_beat_internal_steps(beat, data, 3)
        if len(steps) != 3:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "needs-exactly-three-sourced-factors")
            )
        return {
            **base,
            "type": "factorTrinity",
            "text": " / ".join(str(step.get("label") or "") for step in steps),
            "title": "三个都重要",
            "status": "并列要素",
            "internalSteps": steps,
            "motionType": "factor-trinity-stagger",
            "safeArea": "right avoid-face-caption",
        }

    if intent == "causal-driver":
        steps = validated_beat_internal_steps(beat, data, 2)
        target = next((step for step in steps if str(step.get("role") or "") == "target"), None)
        driver = next((step for step in steps if str(step.get("role") or "") == "driver"), None)
        if len(steps) != 2 or not target or not driver:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-sourced-driver-or-target")
            )
        return {
            **base,
            "type": "causalDriver",
            "text": str(target.get("label") or ""),
            "subtext": str(driver.get("label") or ""),
            "title": "核心机制",
            "status": "因果驱动",
            "internalSteps": steps,
            "motionType": "causal-driver-lock",
            "safeArea": "left avoid-face-caption",
        }

    if intent == "factor-priority":
        steps = validated_beat_internal_steps(beat, data, 3)
        if not 1 <= len(steps) <= 3:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-sourced-priority-factors")
            )
        return {
            **base,
            "type": "factorPriority",
            "text": " / ".join(str(step.get("label") or "") for step in steps),
            "title": "真正影响效果",
            "status": "关键因素",
            "internalSteps": steps,
            "motionType": "factor-priority-build",
            "safeArea": "right avoid-face-caption",
        }

    if intent == "workflow-step" and str(beat.get("visualForm") or "") == "compactPipeline":
        steps = validated_beat_internal_steps(beat, data, 3)
        if len(steps) != 3:
            return provenance_fallback(
                base, "workflow-step", text, provenance_reason(beat, data, "needs-exactly-three-sourced-steps")
            )
        return {
            **base,
            "type": "compactPipeline",
            "text": " → ".join(str(step.get("label") or "") for step in steps),
            "title": "三阶段流程",
            "status": "按顺序推进",
            "internalSteps": steps,
            "motionType": "compact-pipeline-stagger",
            "safeArea": "right avoid-face-caption",
        }

    if intent == "limitation-boundary":
        steps = validated_beat_internal_steps(beat, data, 4)
        capability = next((step for step in steps if str(step.get("role") or "") == "capability"), None)
        limitations = [step for step in steps if str(step.get("role") or "") == "limitation"]
        if not capability or not limitations:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-sourced-capability-or-limitation")
            )
        return {
            **base,
            "type": "limitationWarning",
            "text": str(capability.get("label") or ""),
            "subtext": " / ".join(str(step.get("label") or "") for step in limitations),
            "title": "能力边界",
            "status": "不能解决",
            "emphasisWords": ["不能解决"],
            "internalSteps": steps,
            "motionType": "limitation-warning-stagger",
            "safeArea": "left avoid-face-caption",
            "iconName": "CircleX",
        }

    if intent == "prerequisite":
        steps = validated_beat_internal_steps(beat, data, 1)
        if len(steps) != 1:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-sourced-prerequisite")
            )
        manual_historical = (
            str(beat.get("visualForm") or "") == "historicalGreenConclusion"
            and str(beat.get("presentationVariant") or "") == "manual-approved"
        )
        support_text = str(beat.get("supportText") or "").strip()
        return {
            **base,
            "type": "historicalGreenConclusion" if manual_historical else "priorityConclusion",
            "text": str(steps[0].get("label") or ""),
            "subtext": support_text,
            "title": "前提条件",
            "status": "必须先满足",
            "internalSteps": steps,
            "motionType": "priority-conclusion-build",
            "safeArea": "right avoid-face-caption",
            "presentationVariant": "manual-approved" if manual_historical else "automatic-default",
        }

    if intent in {"negative-to-positive", "negative-friction"}:
        negative, positive, emphasis_words = compact_negative_positive(text)
        event = {
            **base,
            "type": "semanticProblemMap",
            "text": negative or "还在手动",
            "status": "MANUAL BOTTLENECK",
            "emphasisWords": emphasis_words or ["手动"],
            "iconName": "AlertTriangle",
            "motionType": "red-warning-pop-strike",
            "safeArea": "right avoid-face-caption",
        }
        if positive:
            event["subtext"] = positive
        return event

    if intent == "result-promise":
        title_copy, emphasis_words, is_contrarian = result_title_copy(text)
        return {
            **base,
            "type": "kineticTitle",
            "semanticRole": "contrarian-hook" if is_contrarian else "result-promise",
            "text": title_copy,
            "status": "反直觉" if is_contrarian else "RESULT",
            "emphasisWords": emphasis_words,
            "style": "dark-fullscreen-semantic-hud contrarian-hook" if is_contrarian else "dark-fullscreen-semantic-hud",
            "motionType": "crash-rebound-keyword-pop",
        }

    if intent == "positive-confirm":
        title_copy, subtext_copy, emphasis_words = confirm_copy(text)
        return {
            **base,
            "type": "captionHighlight",
            "text": title_copy,
            "subtext": subtext_copy,
            "status": "CONFIRMED",
            "emphasisWords": emphasis_words,
            "iconName": "BadgeCheck",
            "motionType": "field-collapse-to-action",
        }

    if intent == "automation-handoff":
        steps = automation_steps(beat, data)
        if not steps:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-handoff-evidence")
            )
        labels = [str(step.get("label") or "") for step in steps]
        beat["internalSteps"] = steps
        actor = "Codex" if "Codex" in text else "系统" if "系统" in text else labels[0]
        return {
            **base,
            "type": "automationHandoff",
            "text": labels[0],
            "title": actor,
            "subtext": " / ".join(labels[1:3]),
            "status": "AUTO HANDOFF",
            "processingText": "自动执行" if "自动执行" in text else "执行",
            "emphasisWords": [actor],
            "iconName": "Bot",
            "internalSteps": steps,
            "motionType": "field-collapse-to-action",
        }

    if intent == "manual-field":
        steps = field_steps(beat, data)
        if len(steps) < 2:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-field-entities")
            )
        labels = [str(step.get("label") or "") for step in steps]
        return {
            **base,
            "type": "infoCard",
            "semanticRole": "manual-field",
            "text": re.sub(r"\s+", "", text).strip(PUNCTUATION)[:18],
            "title": " / ".join(labels[:3]),
            "subtext": " / ".join(labels[3:5]),
            "status": "FIELDS",
            "iconName": "ClipboardList",
            "internalSteps": steps,
            "motionType": "manual-field-task-stack",
        }

    if intent == "numeric-metric":
        numeric_entities = [
            str(item) for item in beat.get("entities", [])
            if NUMERIC_VALUE_RE.search(str(item))
        ]
        metric_copy = key_message(text, 16, numeric_entities + ["分辨率", "清晰", "提升", "增长", "比例", "指标", "%", "倍", "万", "亿", "K", "k", "分钟", "秒"])
        modifiers = [str(item) for item in beat.get("semanticModifiers", [])]
        incomplete = "incomplete" in modifiers
        return {
            **base,
            "type": "dataPunch",
            "text": metric_copy or "数字指标",
            "subtext": "明确生成结果" if "completed" in modifiers else "尚未生成完成" if incomplete else "数字指标变化",
            "status": "已生成" if "completed" in modifiers else "未完成" if incomplete else "数字结果",
            "style": f"{base['style']} positive-confirm" if "completed" in modifiers else f"{base['style']} negative-incomplete" if incomplete else base["style"],
            "iconName": "AlertTriangle" if incomplete else "TrendingUp",
            "motionType": "count-up-chart",
            **numeric_fields(text),
        }

    if intent in {"workflow-step", "workflow-fields", "enumeration"}:
        steps = field_steps(beat, data)
        if len(steps) < 2:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-workflow-steps")
            )
        title_copy = key_message(text, 14, ["流程", "步骤", "指标", "规则", "发布", "主图", "字段"])
        return {
            **base,
            "type": "statusStack" if intent == "enumeration" else "flowPath",
            "text": "流程推进",
            "title": title_copy or "步骤列表",
            "status": "STEP BY STEP",
            "internalSteps": steps,
            "motionType": "flow-list-stagger",
        }

    if intent == "asset-variants":
        steps = poster_steps(beat, data)
        if len(steps) < 2:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-variant-entities")
            )
        return {
            **base,
            "type": "ratioGallery",
            "text": "多尺寸主图",
            "title": " / ".join(str(step.get("label") or "") for step in steps),
            "status": "ASSET VARIANTS",
            "internalSteps": steps,
            "motionType": "flow-list-stagger",
        }

    if intent == "platform-fanout":
        steps = platform_steps(beat, data)
        if len(steps) < 2:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-platform-entities")
            )
        return {
            **base,
            "type": "platformFanout",
            "text": "一份素材包",
            "subtext": " / ".join(str(step.get("label") or "") for step in steps),
            "iconName": "Network",
            "internalSteps": steps,
            "motionType": "hub-to-platform-flow",
        }

    if intent == "capability-share":
        steps = capability_steps(beat, data)
        if len(steps) < 2:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-comparison-entities")
            )
        return {
            **base,
            "type": "capabilityShare",
            "text": "能力 / 份额 / 排名",
            "title": key_message(text, 16, ["份额", "排名", "领先", "对比", "大模型"]),
            "status": "CAPABILITY SHARE",
            "internalSteps": steps,
            "motionType": "layered-capability-share",
        }

    if intent == "scene-lock":
        steps = scene_steps(beat, data)
        if len(steps) < 2:
            return provenance_fallback(
                base, intent, text, provenance_reason(beat, data, "missing-scene-entities")
            )
        return {
            **base,
            "type": "sceneLockGrid",
            "text": "场景落地",
            "title": key_message(text, 16, ["支付", "教育", "政务", "行业", "场景", "下沉市场"]),
            "status": "SCENE LOCK",
            "internalSteps": steps,
            "motionType": "scene-grid-stagger",
        }

    if intent == "transformation-stack":
        plan, fallback_reason = _trusted_transformation_plan(beat, data)
        if not plan:
            return {
                **base,
                "type": "captionHighlight",
                "semanticRole": "explanation-claim",
                "text": key_message(text, 16, ["\u53d8\u6210", "\u8f6c\u5316", "\u653e\u5927", "\u6539\u53d8"])
                or _trusted_transform_label(text, 16),
                "status": "KEY CHANGE",
                "iconName": "ArrowRightLeft",
                "motionType": "hud-slide-fade",
                "semanticFallbackFrom": "transformation-stack",
                "fallbackReason": fallback_reason,
            }
        return {
            **base,
            "type": "transformationStack",
            "text": f"{plan['source']} \u2192 {plan['target']}",
            "subtext": " \u00b7 ".join(str(item) for item in plan["drivers"]),
            "status": "TRANSFORM",
            "internalSteps": plan["steps"],
            "transformationSourceCueIds": plan["sourceCueIds"],
            "motionType": "state-driver-result-build",
        }

    if intent == "proof-material":
        asset_path = proof_asset_from_media(data)
        if asset_path:
            return {
                **base,
                "type": "materialMain",
                "text": "素材证明",
                "subtext": "真实录屏 / 页面结果",
                "assetPath": asset_path,
                "style": "recording-proof" if Path(asset_path).suffix.lower() in {".mp4", ".mov", ".m4v", ".webm"} else "single-proof",
                "motionType": "screen-recording-proof" if Path(asset_path).suffix.lower() in {".mp4", ".mov", ".m4v", ".webm"} else "material-zoom-highlight",
            }
        return {
            **base,
            "type": "statusSticker",
            "text": "素材证明",
            "subtext": key_message(text, 16, ["素材", "证明", "录屏", "页面", "输出"]),
            "status": "PROOF NEEDED",
            "iconName": "ShieldCheck",
            "motionType": "hud-slide-fade",
        }

    if intent == "cta-resolve":
        sourced_provenance = beat.get("ctaProvenance") if isinstance(beat.get("ctaProvenance"), dict) else None
        title_copy, subtext_copy, status_copy, emphasis_words, provenance = cta_copy(text, sourced_provenance)
        return {
            **base,
            "type": "ctaTitle",
            "text": title_copy,
            "subtext": subtext_copy,
            "status": status_copy,
            "emphasisWords": emphasis_words,
            "ctaProvenance": provenance,
            "motionType": "cta-result-keyword",
        }

    if intent == "topic-intro":
        keyword = topic_keyword(text, beat)
        return {
            **base,
            "type": "topicKeyword",
            "text": keyword,
            "subtext": "本期主题",
            "status": "主题",
            "emphasisWords": [keyword],
            "motionType": "word-by-word-topic-reveal",
        }

    if intent == "explanation-claim":
        claim = source_bound_core_clause(text) or key_message(text, 16, ["关键", "本质", "真正", "核心", "重点", "原因", "方法", "一定要", "救不了", "只能", "缺点", "推荐"])
        return {
            **base,
            "type": "claimStrip",
            "text": claim or normalize_hud_source(text)[:16] or "观点说明",
            "status": "观点",
            "motionType": "lightweight-claim-slide",
        }

    return provenance_fallback(base, intent or "unclassified", text, "unsupported-semantic-component")


def scene_by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(scene.get("id") or ""): scene
        for scene in data.get("scenes", [])
        if isinstance(scene, dict)
    }


def make_lane_room_for_priority_event(
    scheduled: list[dict[str, Any]],
    lane: str,
    start: int,
) -> int | None:
    """Trim or drop a conflicting earlier HUD so a source CTA is never lost."""
    cutoff = max(0, start - LANE_BUFFER_FRAMES)
    for index in range(len(scheduled) - 1, -1, -1):
        previous = scheduled[index]
        if lane_for_event(previous) != lane:
            continue
        previous_start = int(previous.get("startFrame", 0) or 0)
        previous_end = int(previous.get("endFrame", previous_start) or previous_start)
        if previous_end <= cutoff:
            break
        if cutoff - previous_start >= 24:
            scheduled[index] = {**previous, "endFrame": cutoff}
            break
        scheduled.pop(index)

    remaining_ends = [
        int(item.get("endFrame", 0) or 0)
        for item in scheduled
        if lane_for_event(item) == lane
    ]
    return max(remaining_ends) if remaining_ends else None


def schedule_events(events: list[dict[str, Any]], data: dict[str, Any]) -> list[dict[str, Any]]:
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    composition_end = int(composition.get("durationFrames", 0) or 0)
    scenes = scene_by_id(data)
    ordered_scenes = sorted(scenes.values(), key=lambda item: int(item.get("startFrame", 0) or 0))
    next_scene_start: dict[str, int] = {}
    for index, scene in enumerate(ordered_scenes[:-1]):
        next_scene_start[str(scene.get("id") or "")] = int(ordered_scenes[index + 1].get("startFrame", 0) or 0)
    lane_end: dict[str, int] = {}
    scheduled: list[dict[str, Any]] = []
    beats = {
        str(beat.get("id") or ""): beat
        for beat in data.get("semanticBeats", [])
        if isinstance(beat, dict)
    }
    for event in sorted(events, key=lambda item: (int(item.get("startFrame", 0) or 0), str(item.get("sceneId") or ""))):
        lane = lane_for_event(event)
        if not lane:
            scheduled.append(event)
            continue
        scene_id = str(event.get("sceneId") or "")
        scene = scenes.get(scene_id, {})
        scene_start = int(scene.get("startFrame", 0) or 0)
        scene_end = int(scene.get("endFrame", composition_end) or composition_end or 0)
        if str(event.get("type") or "") in {"semanticProblemMap", "highlightBox"}:
            following_start = next_scene_start.get(scene_id)
            if following_start is not None and following_start > scene_end:
                scene_end = min(composition_end or following_start, following_start)
        if str(event.get("type") or "") in {"dataPunch", "metricSpotlight"} and scene_end:
            scene_end = min(composition_end or scene_end + 60, scene_end + 60)
        start = max(scene_start, int(event.get("startFrame", 0) or 0))
        annotated = annotate_density(event, scene, data)
        duration = desired_duration_for_event(annotated, scene, data)
        previous_end = lane_end.get(lane)
        is_priority_cta = str(event.get("type") or "") in {"ctaTitle", "ctaRecommend"}
        if is_priority_cta and previous_end is not None and start < previous_end + LANE_BUFFER_FRAMES:
            previous_end = make_lane_room_for_priority_event(scheduled, lane, start)
            if previous_end is None:
                lane_end.pop(lane, None)
            else:
                lane_end[lane] = previous_end
        if previous_end is not None and start < previous_end + LANE_BUFFER_FRAMES:
            start = previous_end + LANE_BUFFER_FRAMES
        end = start + duration
        if scene_end and end > scene_end:
            end = scene_end
        if composition_end and end > composition_end:
            overflow = end - composition_end
            start = max(0, start - overflow)
            if previous_end is not None and start < previous_end + LANE_BUFFER_FRAMES:
                start = previous_end + LANE_BUFFER_FRAMES
            end = min(composition_end, start + duration)
        if str(annotated.get("type") or "") in {"claimStrip", "quoteSource"} and end - start < MIN_MAIN_HUD_FRAMES:
            source_beat = beats.get(str(annotated.get("sourceBeatId") or ""))
            if source_beat and str(source_beat.get("semanticIntent") or "") == "explanation-claim":
                mark_claim_lightweight(source_beat, "scheduled-space-source-sticker")
                copy = source_bound_sticker_copy(str(source_beat.get("text") or ""))
                annotated = {
                    **annotated,
                    "type": "statusSticker",
                    "text": copy or "观点提示",
                    "status": "重点",
                    "iconName": "Sparkles",
                    "motionType": "hud-slide-fade",
                    "safeArea": "top-right-no-shade",
                    "timingClass": "short-lightweight",
                }
        if end - start < 24:
            continue
        event = {**annotated, "startFrame": start, "endFrame": end}
        lane_end[lane] = end
        scheduled.append(event)
    return scheduled


def is_visual_density_change(event: dict[str, Any]) -> bool:
    event_type = str(event.get("type") or "")
    if event_type in {"cornerChapterLabel", "presenterReposition"}:
        return False
    return True


def density_refresh_copy(scene: dict[str, Any], index: int) -> tuple[str, str]:
    scene_type = str(scene.get("type") or "")
    if scene_type == "Hook":
        return "关键判断", "继续推进"
    if scene_type == "CTA":
        return "行动提示", "评论区领取"
    if scene_type == "Process":
        return "流程推进", f"节点 {index:02d}"
    if scene_type == "Contrast":
        return "对比推进", f"阶段 {index:02d}"
    return "语义推进", f"更新 {index:02d}"


def density_refresh_icon(index: int) -> str:
    icons = ["Activity", "CircleDot", "Radio", "Sparkles"]
    return icons[(index - 1) % len(icons)]


def build_density_refresh_event(scene: dict[str, Any], frame: int, index: int, data: dict[str, Any]) -> dict[str, Any]:
    scene_id = str(scene.get("id") or "")
    text, status = density_refresh_copy(scene, index)
    duration = max(round(composition_fps(data) * 1.4), 34)
    scene_end = int(scene.get("endFrame", frame + duration) or frame + duration)
    end = min(scene_end, frame + duration)
    return {
        "id": f"ve-{scene_id}-density-refresh-{index:02d}",
        "sceneId": scene_id,
        "type": "statusSticker",
        "startFrame": frame,
        "endFrame": max(frame + 24, end),
        "text": text,
        "status": status,
        "semanticRole": "density-refresh",
        "motionType": "hud-slide-fade",
        "style": "dark-fullscreen-semantic-hud density-refresh",
        "safeArea": "top-left-no-shade",
        "iconName": density_refresh_icon(index),
        "densityMode": scene_density_mode(scene, data),
        "densityReason": "long-scene-visual-change",
    }


def apply_density_refreshes(events: list[dict[str, Any]], data: dict[str, Any]) -> list[dict[str, Any]]:
    fps = composition_fps(data)
    warn_gap = round(fps * 4.0)
    target_gap = round(fps * 2.8)
    scenes = [scene for scene in data.get("scenes", []) if isinstance(scene, dict)]
    events_by_scene: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        events_by_scene.setdefault(str(event.get("sceneId") or ""), []).append(event)

    refreshes: list[dict[str, Any]] = []
    for scene in scenes:
        mode = scene_density_mode(scene, data)
        if mode in {"proof-focus", "light"}:
            continue
        scene_id = str(scene.get("id") or "")
        scene_start = int(scene.get("startFrame", 0) or 0)
        scene_end = int(scene.get("endFrame", scene_start) or scene_start)
        if scene_end - scene_start <= round(fps * 7.0):
            continue
        scene_events = sorted(
            [event for event in events_by_scene.get(scene_id, []) if is_visual_density_change(event)],
            key=lambda item: int(item.get("startFrame", 0) or 0),
        )
        cursor = scene_start
        refresh_index = 1
        for event in scene_events:
            event_start = int(event.get("startFrame", cursor) or cursor)
            event_end = int(event.get("endFrame", event_start) or event_start)
            while event_start - cursor > warn_gap:
                frame = min(event_start - 26, cursor + target_gap)
                if frame > cursor + 18:
                    refreshes.append(build_density_refresh_event(scene, frame, refresh_index, data))
                    refresh_index += 1
                    cursor = frame + round(fps * 1.4)
                else:
                    break
            cursor = max(cursor, event_end)
        while scene_end - cursor > warn_gap:
            frame = min(scene_end - 34, cursor + target_gap)
            if frame <= cursor + 18:
                break
            refreshes.append(build_density_refresh_event(scene, frame, refresh_index, data))
            refresh_index += 1
            cursor = frame + round(fps * 1.4)

    return sorted(events + refreshes, key=lambda item: (int(item.get("startFrame", 0) or 0), str(item.get("id") or "")))


def build_visual_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    curate_explanation_claim_beats(data)
    scenes = [scene for scene in data.get("scenes", []) if isinstance(scene, dict)]
    beats = [beat for beat in data.get("semanticBeats", []) if isinstance(beat, dict)]
    events: list[dict[str, Any]] = [corner_label(scene) for scene in scenes]
    for beat in beats:
        event = event_for_beat(beat, data)
        if event:
            events.append(anchor_event_to_caption_cue(event, beat, data))
    return apply_density_refreshes(schedule_events(events, data), data)


def sfx_intent_for_event(beat: dict[str, Any], event: dict[str, Any]) -> str | None:
    semantic_intent = str(beat.get("semanticIntent") or "")
    event_type = str(event.get("type") or "")
    semantic_role = str(event.get("semanticRole") or "")
    if semantic_intent == "result-promise" and event_type in {"kineticTitle", "bigJudgement"}:
        return PRESENTATION_SFX_INTENTS.get("result-promise")
    if semantic_intent in {"negative-friction", "negative-to-positive"}:
        return PRESENTATION_SFX_INTENTS.get(semantic_intent)
    if semantic_intent == "limitation-boundary":
        return PRESENTATION_SFX_INTENTS.get("limitation-boundary")
    if semantic_intent == "positive-confirm":
        return PRESENTATION_SFX_INTENTS.get("positive-confirm")
    if semantic_intent == "automation-handoff":
        return PRESENTATION_SFX_INTENTS.get("automation-handoff")
    if semantic_intent == "numeric-metric" and "completed" in [str(item) for item in beat.get("semanticModifiers", [])]:
        return PRESENTATION_SFX_INTENTS.get("positive-confirm")
    if semantic_intent == "numeric-metric" or event_type in {"dataPunch", "metricSpotlight"}:
        return PRESENTATION_SFX_INTENTS.get("numeric-metric")
    if semantic_intent == "proof-material" or semantic_role in {"proof-material", "proof-focus", "material-main"}:
        return PRESENTATION_SFX_INTENTS.get("proof-material")
    return None


def build_sfx_suggestions(data: dict[str, Any]) -> list[dict[str, Any]]:
    fps = max(1, int(data.get("composition", {}).get("fps") or DEFAULT_FPS))
    beats_by_id = {
        str(beat.get("id") or ""): beat
        for beat in data.get("semanticBeats", [])
        if isinstance(beat, dict)
    }
    suggestions: list[dict[str, Any]] = []
    for event in data.get("visualEvents", []):
        if not isinstance(event, dict):
            continue
        beat_id = str(event.get("sourceBeatId") or "")
        if not beat_id:
            continue
        beat = beats_by_id.get(beat_id)
        if not beat:
            continue
        sfx_intent = sfx_intent_for_event(beat, event)
        if not sfx_intent:
            continue
        sfx = SFX_SUGGESTIONS[sfx_intent]
        pre_roll_frames = round(float(sfx.get("preRollSec", 0) or 0) * fps)
        start = max(0, int(event.get("startFrame", 0) or 0) - pre_roll_frames)
        duration_sec = float(sfx.get("durationSec", 0) or 0)
        duration = (
            max(1, math.ceil(duration_sec * fps - 1e-9))
            if duration_sec > 0
            else max(1, int(sfx["durationFrames"]))
        )
        long_cue = duration_sec > 1.0 if duration_sec > 0 else duration > round(fps * 1.0)
        suggestions.append(
            {
                "id": f"aud-sfx-{beat_id}-{sfx_intent}",
                "type": "sfx",
                "startFrame": start,
                "durationFrames": duration,
                "sfxIntent": sfx_intent,
                "sfxId": sfx["sfxId"],
                "path": sfx["path"],
                "volumeDb": sfx["volumeDb"],
                "duckUnderVoice": True,
                "fadeInFrames": max(1, round(0.04 * fps)) if long_cue else 0,
                "fadeOutFrames": max(1, round((0.16 if long_cue else 0.08) * fps)),
                "status": "suggested",
                "confidence": round(float(beat.get("confidence", 0.75) or 0.75), 2),
                "sourceBeatId": beat_id,
                "sourceEventId": str(event.get("id") or ""),
                "suggestedBy": "semantic-sfx-router",
                "notes": "Suggested only; confirm before changing status to active.",
            }
        )
    return suggestions


def merge_sfx_suggestions(existing_cues: list[Any], suggestions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    retained: list[dict[str, Any]] = []
    claimed: set[tuple[str, str]] = set()
    for cue in existing_cues:
        if not isinstance(cue, dict):
            continue
        if cue.get("suggestedBy") == "semantic-sfx-router" and cue.get("status") == "suggested":
            continue
        retained.append(cue)
        if cue.get("type") == "sfx":
            claimed.add((str(cue.get("sourceBeatId") or ""), str(cue.get("sfxIntent") or "")))
    for cue in suggestions:
        key = (str(cue.get("sourceBeatId") or ""), str(cue.get("sfxIntent") or ""))
        if key not in claimed:
            retained.append(cue)
            claimed.add(key)
    return retained


def apply_visual_events(data: dict[str, Any]) -> dict[str, Any]:
    validate_presenter_layout_policy(data)
    data["visualEvents"] = build_visual_events(data)
    data["audioCues"] = merge_sfx_suggestions(data.get("audioCues", []), build_sfx_suggestions(data))
    qa_frames = [frame for frame in data.get("qaFrames", []) if isinstance(frame, dict)]
    existing = {int(frame.get("frame", -1) or -1) for frame in qa_frames}
    for event in data["visualEvents"]:
        if event.get("type") == "cornerChapterLabel":
            continue
        frame = int(event["startFrame"]) + max(1, (int(event["endFrame"]) - int(event["startFrame"])) // 2)
        if frame not in existing:
            qa_frames.append(
                {
                    "frame": frame,
                    "reason": f"Semantic routed event: {event.get('semanticRole')} / {event.get('type')}",
                    "checks": ["semantic-intent-fulfilled", "caption-safe", "face-safe"],
                }
            )
            existing.add(frame)
    data["qaFrames"] = qa_frames
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    data = load_json(args.visual_script)
    if not data.get("semanticBeats"):
        raise SystemExit("visual_script.json has no semanticBeats; run semantic_router.py first")
    apply_visual_events(data)
    out = args.out or args.visual_script
    save_json(out, data)
    print(f"visual events: {len(data.get('visualEvents', []))}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
