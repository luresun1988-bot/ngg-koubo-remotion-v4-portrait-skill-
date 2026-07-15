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
from semantic_guardrails import (  # noqa: E402
    completion_polarity,
    extract_automation_handoff_steps,
    future_preview,
    handoff_state,
    is_explanation_claim,
    is_process_context,
    is_proof_context,
    numeric_metric_is_meaningful,
    numeric_metric_token,
    ordered_workflow_window,
    parse_cta_provenance,
    result_evaluation,
    topic_intro,
)

configure_utf8()

MIN_BEAT_FRAMES = 80
TARGET_BEAT_FRAMES = 115
MAX_BEAT_FRAMES = 165

NUMERIC_RE = re.compile(r"[+\-]?\d+(?:\.\d+)?\s*(?:%|倍|万|亿|[KkMmGg]|人|道|题|个|张|条|分钟|秒|份|账号)?")
ENUMERATION_RE = re.compile(r"(第一|第二|第三|第四|第五|第[一二三四五六七八九十]+|[二三四五六七八九十]\s*(?:个|件|种|步|项|条|点|方向|指标)|一\s*(?:个|件|种|项|条|点|方向|指标)|[0-9]{1,2}\s*(?:个|件|种|步|项|条|点|方向|指标)|[0-9]{2})")

RULES: dict[str, dict[str, Any]] = {
    "topic-intro": {
        "visualForm": "topicKeyword",
        "terms": ["这期", "今天聊", "今天讲", "这次讲", "我们聊", "我们讲", "主题是"],
        "checks": ["lightweight-topic-treatment", "no-generic-flow-fallback"],
    },
    "explanation-claim": {
        "visualForm": "claimStrip",
        "terms": [],
        "checks": ["lightweight-claim-treatment", "no-generic-flow-fallback"],
    },
    "cta-resolve": {
        "visualForm": "ctaTitle",
        "terms": [],
        "checks": ["cta-visual-treatment", "no-generic-card-fallback"],
    },
    "workflow-step": {
        "visualForm": "flowPath",
        "terms": [],
        "checks": ["workflow-not-generic-card"],
    },
    "paired-inputs": {
        "visualForm": "pairedInputRail",
        "terms": ["准备", "提供", "上传", "输入"],
        "checks": ["paired-inputs-source-binding", "no-generic-card-fallback"],
    },
    "parallel-factors": {
        "visualForm": "factorTrinity",
        "terms": ["都很重要", "同样重要", "缺一不可", "三要素", "三项"],
        "checks": ["factor-trinity-source-binding", "no-generic-card-fallback"],
    },
    "causal-driver": {
        "visualForm": "causalDriver",
        "terms": ["驱动", "带动", "决定"],
        "checks": ["causal-driver-source-binding", "no-generic-card-fallback"],
    },
    "factor-priority": {
        "visualForm": "factorPriority",
        "terms": ["真正影响", "关键在于", "核心因素", "决定结果"],
        "checks": ["factor-priority-source-binding", "no-generic-card-fallback"],
    },
    "limitation-boundary": {
        "visualForm": "limitationWarning",
        "terms": ["不能", "无法", "救不了", "解决不了", "不支持"],
        "checks": ["limitation-source-binding", "negative-red-treatment"],
    },
    "prerequisite": {
        "visualForm": "priorityConclusion",
        "terms": ["必须", "一定要", "前提", "先满足", "先做好", "才能"],
        "checks": ["prerequisite-source-binding", "prerequisite-non-green-default"],
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
        "checks": ["automation-handoff-source-steps", "automation-handoff-processing-treatment", "no-generic-card-fallback"],
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
TOPIC_INTRO_RE = re.compile(r"(?:这期|今天|这次|接下来)(?:视频)?(?:我们)?(?:来)?(?:聊|讲|说|看|拆解|测试|介绍)")
FUTURE_EPISODE_PREVIEW_RE = re.compile(
    r"(?:下一期|下期|下一集|下集|下一条)[^，。！？]{0,24}(?:会|将|准备|介绍|讲|说|演示|拆解|测试|分享|教)"
)
COMPLETION_TERMS = ["已经完成", "生成好了", "已经生成", "输出完成", "流程跑完", "搞定", "跑通", "完成了"]
AUTOMATED_TERMS = ["自动化", "自动生成", "自动完成", "一键", "系统执行", "Codex 接管", "交给 Codex"]
ENTITY_TERMS = [
    "Codex", "OpenAI", "Google", "Anthropic", "抖音", "小红书", "B站", "快手", "视频号",
    "数字人", "详情图", "主图", "封面", "海报", "工作流", "大模型", "Topaz Video AI", "Topaz",
]
INELIGIBLE_DEPTH_KEYWORDS = {"Codex", "OpenAI", "Google", "Anthropic", "Topaz", "TopazVideoAI", "Topaz Video AI"}

STRUCTURED_UNCERTAINTY_TERMS = ["可能", "也许", "或许", "大概", "如果", "假设", "不一定"]
INPUT_TRIGGER_RE = re.compile(r"(?:准备|提供|上传|输入|需要)(?P<body>[^，。！？]{2,34})")
PARALLEL_FACTOR_END_RE = re.compile(r"(?P<body>[^，。！？]{3,36}?)(?:都很重要|同样重要|缺一不可|是三要素|是三个要素)")
PRIORITY_FACTOR_RE = re.compile(
    r"(?:真正影响[^，。！？]{0,12}的是|决定[^，。！？]{0,12}的是|关键(?:因素)?在于|核心因素是)(?P<body>[^，。！？]{2,32})"
)
LIMITATION_RE = re.compile(
    r"(?P<subject>[^，。！？]{1,14}?)(?P<marker>不能|无法|救不了|解决不了|不支持)(?P<body>[^，。！？]{1,30})"
)
CAUSAL_BY_RE = re.compile(
    r"(?P<target>[^，。！？]{1,14}?)(?:是)?(?:靠|依靠)(?P<driver>[^，。！？]{1,12}?)(?:来)?(?:驱动|带动|决定)"
)
CAUSAL_DIRECT_RE = re.compile(
    r"(?P<driver>[^，。！？]{1,12}?)(?:直接)?(?:驱动|带动|决定)(?P<target>[^，。！？]{1,14})"
)
PREREQUISITE_SUBJECT_RE = re.compile(
    r"(?P<label>[^，。！？]{1,14}?)(?:必须|一定要|需要)先(?P<action>[^，。！？]{1,14})"
)
PREREQUISITE_EXPLICIT_RE = re.compile(
    r"(?:前提(?:条件)?是|必须先满足)(?P<label>[^，。！？]{1,16})"
)
PREREQUISITE_BEFORE_RE = re.compile(
    r"先(?P<label>[^，。！？]{1,16}?)(?:，|,)?才(?:能|可以|会)"
)

PIPELINE_KNOWN_ITEMS: list[tuple[str, str]] = [
    ("读取逐字稿", "FileText"), ("判断语义", "BrainCircuit"), ("写入时间线", "Workflow"),
    ("上传素材", "UploadCloud"), ("填写标题", "FileText"), ("输出视频", "Video"),
    ("高清放大", "Maximize2"), ("增强软件", "WandSparkles"), ("成片", "Film"),
]

SEMANTIC_ICON_HINTS: list[tuple[str, str]] = [
    ("图片", "Image"), ("照片", "Image"), ("画面", "Image"), ("音频", "AudioLines"),
    ("声音", "AudioWaveform"), ("音色", "AudioWaveform"), ("情绪", "HeartPulse"),
    ("语速", "Gauge"), ("视频", "Video"), ("成片", "Film"), ("软件", "WandSparkles"),
    ("放大", "Maximize2"), ("口型", "ScanFace"), ("表情", "CircleX"),
    ("参数", "SlidersHorizontal"), ("模型", "Boxes"), ("文案", "FileText"),
    ("脚本", "FileText"), ("素材", "Package"), ("流程", "Workflow"),
]


def semantic_icon(label: str, fallback: str = "CircleDot") -> str:
    return next((icon for term, icon in SEMANTIC_ICON_HINTS if term in label), fallback)


def _trim_source_item(value: str) -> str:
    item = value.strip(" \t\r\n，。！？、；;：:,.!?/")
    item = re.sub(r"^(?:先|再|然后|接着|最后|以及|还有|并且|把|用|使用|准备|提供|上传|输入|需要)+", "", item)
    item = re.sub(r"^(?:一张|一段|一个|一份|一种|一条|两类|两个|三个|三项)", "", item)
    item = re.sub(r"(?:都很重要|同样重要|缺一不可|这三项|三个要素)$", "", item)
    return item.strip(" \t\r\n，。！？、；;：:,.!?/")[:12]


def _split_source_items(body: str, limit: int = 4) -> list[str]:
    normalized = re.sub(r"(?:以及|还有|并且|或者|和|与)", "、", body)
    raw_items = re.split(r"[、,/；;]", normalized)
    items: list[str] = []
    for raw in raw_items:
        item = _trim_source_item(raw)
        if 1 < len(item) <= 12 and item not in items:
            items.append(item)
        if len(items) == limit:
            break
    return items


def _structured_items(labels: list[str], *, roles: list[str] | None = None) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for index, label in enumerate(labels):
        item = {"label": label, "iconName": semantic_icon(label)}
        if roles and index < len(roles):
            item["role"] = roles[index]
        items.append(item)
    return items


def structured_rule_result(
    intent: str,
    labels: list[str],
    *,
    roles: list[str] | None = None,
    confidence: float = 0.94,
) -> dict[str, Any]:
    result = rule_result(intent, labels, confidence)
    result["structuredItems"] = _structured_items(labels, roles=roles)
    return result


def extract_paired_inputs(text: str) -> list[str]:
    match = INPUT_TRIGGER_RE.search(text)
    if not match:
        return []
    body = re.split(r"(?:作为|用于|就能|即可|就可以)", match.group("body"), maxsplit=1)[0]
    items = _split_source_items(body, 3)
    if len(items) != 2:
        return []
    asset_evidence = sum(
        any(term in item for term in ["图", "照片", "音频", "声音", "视频", "文案", "脚本", "素材", "录屏", "文件", "模型"])
        for item in items
    )
    return items if asset_evidence == 2 else []


def extract_parallel_factors(text: str) -> list[str]:
    match = PARALLEL_FACTOR_END_RE.search(text)
    if not match:
        explicit = re.search(r"(?:三要素|三个要素|三项)(?:是|包括|分别是)?(?P<body>[^，。！？]{3,30})", text)
        if not explicit:
            return []
        body = explicit.group("body")
    else:
        body = match.group("body")
    if "包括" in body:
        body = body.split("包括", 1)[1]
    items = _split_source_items(body, 4)
    return items if len(items) == 3 else []


def extract_causal_pair(text: str) -> tuple[str, str] | None:
    if any(term in text for term in STRUCTURED_UNCERTAINTY_TERMS + ["不是靠", "并非靠", "不能靠", "无法靠"]):
        return None
    match = CAUSAL_BY_RE.search(text)
    if match:
        target = _trim_source_item(match.group("target"))
        driver = _trim_source_item(match.group("driver"))
        return (target, driver) if target and driver else None
    match = CAUSAL_DIRECT_RE.search(text)
    if match:
        driver = _trim_source_item(match.group("driver"))
        target = _trim_source_item(match.group("target"))
        return (target, driver) if target and driver else None
    return None


def extract_priority_factors(text: str) -> list[str]:
    match = PRIORITY_FACTOR_RE.search(text)
    if not match:
        return []
    return _split_source_items(match.group("body"), 4)


def extract_compact_pipeline(text: str) -> list[str]:
    known = [
        (position, label, icon)
        for label, icon in PIPELINE_KNOWN_ITEMS
        for position in [text.find(label)]
        if position >= 0
    ]
    known.sort(key=lambda item: item[0])
    labels = [label for _position, label, _icon in known]
    if len(labels) == 3:
        return labels
    if not all(marker in text for marker in ["首先", "最后"]) or not any(marker in text for marker in ["然后", "接着", "其次"]):
        return []
    parts = re.split(r"(?:首先|然后|接着|其次|最后)", text)
    labels = [_trim_source_item(part) for part in parts if _trim_source_item(part)]
    return labels if len(labels) == 3 else []


def extract_limitation_items(text: str) -> list[tuple[str, str]]:
    if any(term in text for term in STRUCTURED_UNCERTAINTY_TERMS):
        return []
    match = LIMITATION_RE.search(text)
    if not match:
        return []
    subject = _trim_source_item(match.group("subject"))
    targets = _split_source_items(match.group("body"), 3)
    if not subject or not targets:
        return []
    body = match.group("body")
    if any(phrase in text for phrase in ["不能再手填", "不能手填", "不能再手动"]):
        return []
    capability_terms = ["工具", "功能", "模型", "软件", "算法", "放大", "增强", "剪辑", "生成", "修复", "系统", "能力"]
    limited_target_terms = ["口型", "表情", "问题", "错误", "画质", "声音", "字幕", "内容", "文件", "数据", "缺陷", "故障"]
    if not any(term in subject for term in capability_terms) or not any(term in body for term in limited_target_terms):
        return []
    return [(subject, "capability"), *[(target, "limitation") for target in targets]]


def extract_prerequisite(text: str) -> tuple[str, str] | None:
    if any(term in text for term in STRUCTURED_UNCERTAINTY_TERMS):
        return None
    match = PREREQUISITE_SUBJECT_RE.search(text)
    if match:
        label = _trim_source_item(match.group("label"))
        action = ("先" + match.group("action").strip(" ，。！？"))[:12]
        return (label, action) if label and action else None
    match = PREREQUISITE_EXPLICIT_RE.search(text)
    if match:
        label = _trim_source_item(match.group("label"))
        return (label, "") if label else None
    match = PREREQUISITE_BEFORE_RE.search(text)
    if match:
        label = _trim_source_item(match.group("label"))
        return (label, "") if label else None
    return None


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


def automation_handoff_result(text: str, keywords: list[str], confidence: float = 0.9) -> dict[str, Any]:
    result = rule_result("automation-handoff", keywords, confidence)
    result["internalSteps"] = extract_automation_handoff_steps(text)
    return result


def bind_structured_items(
    cues: list[dict[str, Any]], structured_items: list[dict[str, Any]], prefix: str,
) -> list[dict[str, Any]]:
    """Bind every proposed label to the exact caption cue that contains it."""
    bound: list[dict[str, Any]] = []
    for raw in structured_items:
        if not isinstance(raw, dict):
            continue
        label = str(raw.get("label") or "").strip()
        if not label:
            continue
        cue = next((item for item in cues if label in str(item.get("text") or "")), None)
        if cue is None or not cue.get("id"):
            continue
        step = {
            "id": f"{prefix}-{len(bound) + 1:02d}",
            "label": label,
            "text": label,
            "sourceCueIds": [str(cue["id"])],
            "iconName": str(raw.get("iconName") or semantic_icon(label)),
        }
        if raw.get("role"):
            step["role"] = str(raw["role"])
        bound.append(step)
    return bound


def classify_text(text: str, frame_midpoint: int, duration_frames: int) -> dict[str, Any]:
    matched = {intent: contains_any(text, rule["terms"]) for intent, rule in RULES.items()}
    matched = {intent: hits for intent, hits in matched.items() if hits}
    solution_hits = list(matched.get("positive-confirm", [])) + list(matched.get("automation-handoff", []))
    completion_state = completion_polarity(text)
    evaluated_result = result_evaluation(text)
    handoff = handoff_state(text)
    cta_signal = parse_cta_provenance(text)

    if cta_signal:
        actions = [item for item in cta_signal.get("actions", []) if isinstance(item, dict)]
        first_action = actions[0] if actions else {}
        action_text = str(first_action.get("sourceText") or "").strip()
        result = rule_result("cta-resolve", [action_text], 0.94)
        provenance: dict[str, str] = {
            "kind": "keyword" if cta_signal.get("keyword") else "action",
            "sourceText": text.strip(),
            "action": action_text,
        }
        if cta_signal.get("keyword"):
            provenance["keyword"] = str(cta_signal["keyword"])
        result["ctaProvenance"] = provenance
        return result
    matched.pop("cta-resolve", None)
    if completion_state != "asserted":
        matched.pop("positive-confirm", None)
    if completion_state == "prospective":
        matched.pop("result-promise", None)

    # A future episode preview describes planned content. It is neither a
    # completed result nor an automation handoff, even when it contains words
    # such as "自动" or a tool name. Keep a source keyword so CTA scene fallback
    # cannot overwrite this decision.
    future_source = future_preview(text)
    if future_source:
        return {
            "semanticIntent": "explanation-claim",
            "visualForm": "claimStrip",
            "keywords": [future_source],
            "requiredChecks": ["future-preview-not-complete", "lightweight-claim-treatment"],
            "confidence": 0.94,
        }

    topic_source = topic_intro(text)
    if topic_source:
        return {
            "semanticIntent": "topic-intro",
            "visualForm": "topicKeyword",
            "keywords": [topic_source],
            "requiredChecks": RULES["topic-intro"]["checks"],
            "confidence": 0.9,
        }

    paired_inputs = extract_paired_inputs(text)
    if paired_inputs:
        return structured_rule_result("paired-inputs", paired_inputs, confidence=0.96)

    parallel_factors = extract_parallel_factors(text)
    if parallel_factors:
        return structured_rule_result("parallel-factors", parallel_factors, confidence=0.96)

    causal_pair = extract_causal_pair(text)
    if causal_pair:
        target, driver = causal_pair
        return structured_rule_result(
            "causal-driver", [target, driver], roles=["target", "driver"], confidence=0.96
        )

    priority_factors = extract_priority_factors(text)
    if priority_factors:
        return structured_rule_result("factor-priority", priority_factors, confidence=0.96)

    compact_pipeline = extract_compact_pipeline(text)
    if compact_pipeline:
        result = structured_rule_result("workflow-step", compact_pipeline, confidence=0.96)
        result["visualForm"] = "compactPipeline"
        result["requiredChecks"] = ["compact-pipeline-three-steps", "workflow-source-steps"]
        return result

    limitation_items = extract_limitation_items(text)
    if limitation_items:
        labels = [label for label, _role in limitation_items]
        roles = [role for _label, role in limitation_items]
        return structured_rule_result(
            "limitation-boundary", labels, roles=roles, confidence=0.97
        )

    prerequisite = extract_prerequisite(text)
    if prerequisite:
        label, action = prerequisite
        result = structured_rule_result(
            "prerequisite", [label], roles=["prerequisite"], confidence=0.97
        )
        if action:
            result["supportText"] = action
        return result

    if handoff == "negated":
        return {
            "semanticIntent": "negative-friction",
            "visualForm": "redWarningCard",
            "keywords": ["未接管"],
            "requiredChecks": RULES["negative-friction"]["checks"],
            "confidence": 0.94,
        }

    if handoff == "prior":
        return {
            "semanticIntent": "workflow-step",
            "visualForm": "flowPath",
            "keywords": ["先检查" if "先检查" in text else "前置检查"],
            "requiredChecks": ["workflow-not-generic-card", "handoff-prerequisite-not-complete"],
            "semanticModifiers": ["prerequisite"],
            "confidence": 0.94,
        }

    explicit_contrast = re.search(r"不是[^，。！？]{1,24}而是[^，。！？]{1,24}", text)
    if explicit_contrast and not any(term in text for term in FLOW_TRANSFORMATION_TERMS):
        return {
            "semanticIntent": "negative-to-positive",
            "visualForm": "negativeWarningThenConfirm",
            "keywords": ["不是", "而是"],
            "requiredChecks": ["negative-red-treatment", "positive-confirm-treatment", "no-generic-card-fallback"],
            "confidence": 0.96,
        }

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

    if "negative-friction" in matched and completion_state == "prospective":
        return rule_result("negative-friction", matched["negative-friction"], 0.92)

    if "negative-friction" in matched and solution_hits and completion_state not in {"negated", "prospective"}:
        return {
            "semanticIntent": "negative-to-positive",
            "visualForm": "negativeWarningThenConfirm",
            "keywords": (matched["negative-friction"][:2] + solution_hits[:2])[:4],
            "requiredChecks": ["negative-red-treatment", "positive-confirm-treatment", "no-generic-card-fallback"],
            "confidence": 0.95,
        }

    if "asset-variants" in matched and any(term in text for term in ["横屏", "竖屏", "方图", "多尺寸", "三尺寸", "多规格", "16:9", "4:3", "3:4", "比例", "横版", "竖版", "方形"]):
        return rule_result("asset-variants", matched["asset-variants"], 0.9)

    numeric_match = numeric_metric_token(text)
    if numeric_match and numeric_metric_is_meaningful(text, numeric_match):
        checks = ["numeric-countup-required", "no-generic-card-fallback"]
        modifiers = ["numeric"]
        if is_proof_context(text):
            modifiers.append("proof-bound")
            checks.append("material-main-or-proof")
        if completion_state == "asserted":
            checks.append("positive-confirm-treatment")
            modifiers.append("completed")
        elif completion_state in {"negated", "prospective"}:
            checks.append("negative-incomplete-treatment")
            modifiers.append("incomplete")
        return {
            "semanticIntent": "numeric-metric",
            "visualForm": "dataPunch",
            "keywords": [numeric_match],
            "requiredChecks": checks,
            "semanticModifiers": modifiers,
            "confidence": 0.92,
        }

    if is_proof_context(text):
        return rule_result("proof-material", contains_any(text, RULES["proof-material"]["terms"]) or ["页面展示"], 0.88)

    if completion_state == "negated":
        return {
            "semanticIntent": "negative-friction",
            "visualForm": "redWarningCard",
            "keywords": ["未完成"],
            "requiredChecks": RULES["negative-friction"]["checks"],
            "confidence": 0.94,
        }

    if completion_state == "asserted":
        completion_keywords = [term for term in COMPLETION_TERMS if term in text]
        return rule_result("positive-confirm", completion_keywords or ["完成"], 0.92)

    if evaluated_result:
        evaluation_intent = (
            "positive-confirm"
            if evaluated_result.get("polarity") == "positive"
            else "negative-friction"
        )
        source_text = str(evaluated_result.get("sourceText") or "").strip()
        return rule_result(evaluation_intent, [source_text] if source_text else [], 0.94)

    if handoff == "asserted" and ENUMERATION_RE.search(text) is None:
        return automation_handoff_result(text, matched.get("automation-handoff", []) or ["自动交接"], 0.92)

    if ("关键词" in text and is_process_context(text)) or completion_state == "prospective":
        return rule_result("workflow-step", ["流程"], 0.86)

    if any(term in text for term in AUTOMATION_HANDOFF_ACTION_TERMS):
        return automation_handoff_result(
            text,
            [term for term in AUTOMATION_HANDOFF_ACTION_TERMS if term in text][:4],
            0.9,
        )

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

    has_transformation_relation = bool(re.search(r"从[^，。！？]{1,12}(?:到|变成|转化成)[^，。！？]{1,12}", text))
    if "transformation-stack" in matched and (has_transformation_relation or any(term in text for term in ["放大你的能力", "放大能力", "转化成", "变成", "团队", "第二大脑", "杠杆", "护城河"])):
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
        return automation_handoff_result(text, matched["automation-handoff"], 0.9)

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

    # Broad single words are not enough to justify a heavy component. Route only
    # after the sentence satisfies the intent-specific relation below.
    if "negative-friction" in matched:
        return rule_result("negative-friction", matched["negative-friction"])
    if "positive-confirm" in matched and any(term in text for term in ["自动", "完成", "搞定", "跑完", "一键", "补齐", "跑通"]):
        return rule_result("positive-confirm", matched["positive-confirm"])
    if "manual-field" in matched and any(term in text for term in ["字段", "表单", "标题", "简介", "标签", "封面"]):
        return rule_result("manual-field", matched["manual-field"])
    if "platform-fanout" in matched and any(term in text for term in ["多平台", "全平台", "渠道", "抖音", "小红书", "B站", "快手", "视频号"]):
        return rule_result("platform-fanout", matched["platform-fanout"])
    if "capability-share" in matched and any(term in text for term in ["份额", "排名", "领先", "对比", "占比", "差异", "差距", "企业客户", "优势"]):
        return rule_result("capability-share", matched["capability-share"])
    if "scene-lock" in matched and any(term in text for term in ["支付", "教育", "政务", "行业", "场景", "落地", "下沉市场", "本地生活"]):
        return rule_result("scene-lock", matched["scene-lock"])
    if "transformation-stack" in matched and any(term in text for term in ["变成", "转化成", "从一个", "从个人", "团队", "第二大脑", "杠杆", "护城河", "能力放大", "放大你的能力"]):
        return rule_result("transformation-stack", matched["transformation-stack"])
    if "result-promise" in matched and any(term in text for term in ["反直觉", "真正的大爆发", "还没有开始", "真正的机会", "完全不同", "刚开始"]):
        return rule_result("result-promise", matched["result-promise"])
    if TOPIC_INTRO_RE.search(text) or any(term in text for term in RULES["topic-intro"]["terms"]):
        return rule_result("topic-intro", contains_any(text, RULES["topic-intro"]["terms"]), 0.78)

    if is_process_context(text):
        return rule_result("workflow-step", ["流程"], 0.8)

    if is_explanation_claim(text):
        return rule_result("explanation-claim", [], 0.8)

    return {
        "semanticIntent": "explanation-claim",
        "visualForm": "claimStrip",
        "keywords": [],
        "requiredChecks": ["lightweight-claim-treatment", "no-generic-flow-fallback"],
        "confidence": 0.55,
    }


def semantic_metadata(text: str) -> dict[str, Any]:
    modifiers: list[str] = []
    completion_state = completion_polarity(text)
    numeric_token = numeric_metric_token(text)
    if numeric_token and numeric_metric_is_meaningful(text, numeric_token):
        modifiers.append("numeric")
    if completion_state == "asserted":
        modifiers.append("completed")
    elif completion_state in {"negated", "prospective"}:
        modifiers.append("incomplete")
    if any(term in text for term in AUTOMATED_TERMS):
        modifiers.append("automated")
    if is_proof_context(text) or any(term in text for term in PROOF_STRONG_TERMS):
        modifiers.append("proof-bound")
    if any(term in text for term in ["不是", "别再", "风险", "手动", "低效", "麻烦"]):
        modifiers.append("negative")
    entities = [term for term in ENTITY_TERMS if term in text]
    numbers = [numeric_token.upper() if numeric_token and numeric_token[-1:] in "kmg" else numeric_token] if numeric_token else []
    return {
        "semanticModifiers": list(dict.fromkeys(modifiers)),
        "entities": list(dict.fromkeys(entities + numbers))[:8],
    }


def suggested_depth_keyword(text: str, keywords: list[str]) -> str | None:
    candidates = [
        *[term for term in ENTITY_TERMS if term in text],
        *keywords,
        *[term for term in ["自动化", "工作流", "效率提升", "能力放大", "批量生成"] if term in text],
    ]
    for candidate in candidates:
        clean = re.sub(r"[\s，。？！、；;：:.!?]", "", str(candidate))
        if clean in INELIGIBLE_DEPTH_KEYWORDS:
            continue
        if 2 <= len(clean) <= 6:
            return clean
    return None


def annotate_theme_thesis(beats: list[dict[str, Any]], scenes: list[dict[str, Any]]) -> None:
    scene_map = {str(scene.get("id") or ""): scene for scene in scenes}
    for beat in beats:
        intent = str(beat.get("semanticIntent") or "")
        scene = scene_map.get(str(beat.get("sceneId") or ""), {})
        if intent not in {"result-promise", "negative-to-positive", "negative-friction", "transformation-stack", "explanation-claim"}:
            continue
        if str(scene.get("presenterLayout") or "") not in {"fullscreen", "large"}:
            continue
        if str(scene.get("materialLayout") or "") in {"main", "clean"}:
            continue
        keyword = suggested_depth_keyword(str(beat.get("text") or ""), list(beat.get("keywords") or []))
        if not keyword:
            continue
        beat["themeThesisCandidate"] = True
        beat["suggestedDepthKeyword"] = keyword
        beat["requiresApproval"] = True
        break


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
            fps = int(data.get("composition", {}).get("fps") or 25)
            ordered = ordered_workflow_window(
                cues,
                cursor,
                max_gap_frames=round(fps * 2.6),
                max_duration_frames=round(fps * 20.0),
            )
            if ordered:
                group, internal_steps = ordered
                start = int(group[0].get("startFrame", 0) or 0)
                end = int(group[-1].get("endFrame", start + 1) or start + 1)
                text = "，".join(str(cue.get("text") or "") for cue in group)
                beat_id = f"beat-{beat_index:03d}"
                compact = len(internal_steps) == 3
                beats.append(
                    {
                        "id": beat_id,
                        "sceneId": scene_id,
                        "beatGroupId": f"{scene_id}-{beat_id}",
                        "startFrame": max(int(scene.get("startFrame", start) or start), start),
                        "endFrame": min(int(scene.get("endFrame", end) or end), end),
                        "text": text,
                        "semanticIntent": "workflow-step",
                        "visualForm": "compactPipeline" if compact else "flowPath",
                        "confidence": 0.96,
                        "keywords": [str(step.get("label") or "") for step in internal_steps[:3]],
                        "requiredChecks": (
                            ["compact-pipeline-three-steps", "workflow-source-steps"]
                            if compact
                            else ["workflow-not-generic-card", "workflow-source-steps"]
                        ),
                        "semanticModifiers": ["ordered-workflow"],
                        "sourceCueIds": [str(cue.get("id") or "") for cue in group if cue.get("id")],
                        "internalSteps": internal_steps,
                    }
                )
                cursor += len(group)
                beat_index += 1
                continue

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
            beat_id = f"beat-{beat_index:03d}"
            beat = {
                "id": beat_id,
                "sceneId": scene_id,
                "beatGroupId": f"{scene_id}-{beat_id}",
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
            if isinstance(info.get("ctaProvenance"), dict):
                beat["ctaProvenance"] = info["ctaProvenance"]
            if isinstance(info.get("semanticModifiers"), list):
                beat["semanticModifiers"] = info["semanticModifiers"]
            if isinstance(info.get("internalSteps"), list):
                beat["internalSteps"] = info["internalSteps"]
            if isinstance(info.get("structuredItems"), list):
                beat["internalSteps"] = bind_structured_items(group, info["structuredItems"], info["semanticIntent"])
            if info.get("supportText"):
                beat["supportText"] = str(info["supportText"])
            beats.append(beat)
            beat_index += 1

    merged = merge_short_tail_beats(beats, scenes)
    for beat in merged:
        metadata = semantic_metadata(str(beat.get("text") or ""))
        beat["semanticModifiers"] = list(dict.fromkeys(
            [str(item) for item in beat.get("semanticModifiers", []) if str(item)]
            + [str(item) for item in metadata.get("semanticModifiers", []) if str(item)]
        ))
        beat["entities"] = list(dict.fromkeys(
            [str(item) for item in beat.get("entities", []) if str(item)]
            + [str(item) for item in metadata.get("entities", []) if str(item)]
        ))[:8]
    annotate_theme_thesis(merged, scenes)
    return merged


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
        if (
            previous
            and previous_intent == "explanation-claim"
            and FUTURE_EPISODE_PREVIEW_RE.search(str(previous.get("text") or ""))
            and current_intent == "cta-resolve"
        ):
            previous["endFrame"] = max(int(previous.get("endFrame", 0) or 0), end)
            previous["text"] = str(previous.get("text") or "") + str(beat.get("text") or "")
            previous["semanticIntent"] = "cta-resolve"
            previous["visualForm"] = "ctaTitle"
            previous["keywords"] = list(dict.fromkeys(list(previous.get("keywords") or []) + list(beat.get("keywords") or [])))[:4]
            previous["requiredChecks"] = ["cta-visual-treatment", "future-preview-not-complete", "no-generic-card-fallback"]
            previous["confidence"] = max(float(previous.get("confidence", 0) or 0), float(beat.get("confidence", 0) or 0))
            previous["sourceCueIds"] = list(previous.get("sourceCueIds") or []) + list(beat.get("sourceCueIds") or [])
            continue
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
        if (
            duration < MIN_BEAT_FRAMES
            and previous
            and previous_intent == current_intent
            and current_intent in {"explanation-claim", "workflow-step", "topic-intro"}
        ):
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
