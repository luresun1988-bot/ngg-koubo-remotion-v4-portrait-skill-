#!/usr/bin/env python3
"""Format-agnostic semantic guards shared by V4 landscape and portrait."""

from __future__ import annotations

import re
from typing import Any


CLAUSE_RE = re.compile(r"[^，。；！？!?\n]+")
FUTURE_PREVIEW_RE = re.compile(
    r"(?:下一期|下期|下一集|下集|下一条)[^，。！？]{0,28}(?:会|将|准备|介绍|讲|说|演示|拆解|测试|分享|教)"
)
TOPIC_INTRO_RE = re.compile(
    r"(?:这一期|这期|今天|这次)(?:视频)?(?:我们)?(?:来)?(?:聊聊|聊|讲讲|讲|说说|说|看|拆解|测试|介绍)"
)
HANDOFF_NEGATED_RE = re.compile(
    r"(?:还没有|还没|尚未|并未|没有|未|不再)[^，。！？]{0,10}(?:接管|执行|处理)"
    r"|(?:不要|别|不)[^，。！？]{0,8}(?:交给|丢给|交由)"
)
HANDOFF_PRIOR_RE = re.compile(
    r"(?:(?:交给|丢给|交由|让|由)[^，。！？]{0,16}(?:Codex|系统|自动化)"
    r"|(?:Codex|系统|自动化)[^，。！？]{0,10}(?:接管|执行|处理))"
    r"[^，。！？]{0,8}(?:之前|以前|前)"
)
HANDOFF_ASSERTED_RE = re.compile(
    r"(?:交给|丢给|交由|让|由)[^，。！？]{0,16}(?:Codex|系统|自动化)"
    r"|(?:Codex|系统|自动化)[^，。！？]{0,10}(?:接管|执行|处理)"
)
PROCESS_CONTEXT_RE = re.compile(
    r"(?:输入|填写|上传|选择|设置|点击|确认|提交|搜索|整理|配置)[^，。！？]{0,18}"
    r"(?:生成|导出|发布|提交|保存|标题|关键词|素材|参数|选项|结果|页面|竞品)"
    r"|(?:系统|平台|工具|AI|Codex)[^，。！？]{0,8}(?:会|将|可以|能够)?(?:自动)?(?:生成|导出|处理|执行)"
    r"|(?:首先|然后|接着|随后|最后)[^，。！？]{0,6}(?:读取|判断|写入|检查|整理|生成|导出|提交|发布)"
)
CONDITIONAL_PROCESS_RE = re.compile(
    r"(?:如果|只要|一旦)[^。！？]{0,18}(?:完成|设置|确认)[^。！？]{0,18}(?:导出|提交|继续|发布|保存)"
)
EXPLANATION_CLAIM_RE = re.compile(
    r"(?:是|是一款|属于|用于|主要负责|主要用来|支持|指的是)[^，。！？]{1,28}"
    r"|(?:按钮|入口|字段|选项|工具)[^，。！？]{0,12}(?:在|位于|用于|负责)"
)
PROOF_CONTEXT_RE = re.compile(
    r"(?:页面|后台|录屏|录像|截图|结果)[^，。！？]{0,16}(?:展示|显示|互动|数据|结果|证据|证明)"
    r"|(?:展示|显示|查看)[^，。！？]{0,16}(?:页面|后台|互动数据|生成结果)"
    r"|(?:你|大家|我们)?(?:现在|来|先)?看(?:一下|一眼)?(?:这个|这里的)?(?:后台|页面|结果)"
)


def future_preview(text: str) -> str:
    match = FUTURE_PREVIEW_RE.search(text)
    return match.group(0).strip() if match else ""


def topic_intro(text: str) -> str:
    match = TOPIC_INTRO_RE.search(text)
    return match.group(0).strip() if match else ""


def handoff_state(text: str) -> str:
    """Return asserted, negated, prior, or none for an automation handoff."""
    if HANDOFF_NEGATED_RE.search(text):
        return "negated"
    if HANDOFF_PRIOR_RE.search(text):
        return "prior"
    if HANDOFF_ASSERTED_RE.search(text):
        return "asserted"
    return "none"


def is_process_context(text: str) -> bool:
    return PROCESS_CONTEXT_RE.search(text) is not None or CONDITIONAL_PROCESS_RE.search(text) is not None


def is_explanation_claim(text: str) -> bool:
    return EXPLANATION_CLAIM_RE.search(text) is not None


def is_proof_context(text: str) -> bool:
    return PROOF_CONTEXT_RE.search(text) is not None


RELATION_OPERATORS = ("决定", "驱动", "影响", "带动", "推动", "控制")
RELATION_BLOCKERS = (
    "如果", "假如", "是否", "能否", "可能", "也许", "或许", "避免", "防止",
    "不会", "不能", "没有", "不一定", "变成", "转化成", "转化为", "成为",
)
RELATION_ENTITY_TERMS = (
    "剪辑指令", "逐字稿", "时间戳", "背景音乐", "人物镜头", "文案", "脚本", "语义",
    "画面", "声音", "音频", "组件", "动画", "参数", "素材", "规则", "输出", "结果",
    "音效", "节奏", "镜头", "Codex", "Remotion",
)
REUSABLE_INPUT_RE = re.compile(
    r"(?:换|更换|替换|修改|改动)(?:一份|一个|一套|新的|这份|这个)?"
    r"(?:文案|脚本|素材|参数|输入|图片|视频)"
)
REUSABLE_RESULT_RE = re.compile(
    r"(?:重复执行|重复使用|再次执行|再执行一次|重新生成|再次生成|复用|跟着变化|随之变化|自动更新)"
)


def _relation_endpoint(segment: str, *, prefer_last: bool) -> str:
    """Return a short exact-source endpoint without inventing a noun phrase."""
    matches = [
        (segment.rfind(term), term)
        for term in RELATION_ENTITY_TERMS
        if term in segment
    ]
    if matches:
        position, term = max(matches, key=lambda item: item[0]) if prefer_last else min(
            matches, key=lambda item: item[0]
        )
        return segment[position:position + len(term)]
    clean = segment.strip(" ，。；：:、")
    clean = re.sub(r"^(?:而是|所以|因此|因为|只要|让|由)", "", clean)
    clean = re.sub(r"(?:本身|本身在|会|将|可以|能够|直接|最终|就)$", "", clean)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_.-]*|[\u4e00-\u9fff]{1,8}", clean)
    if not tokens:
        return ""
    token = tokens[-1] if prefer_last else tokens[0]
    return token[-8:] if prefer_last else token[:8]


def directional_relation_evidence(text: str) -> dict[str, Any] | None:
    """Extract an asserted one-way A -> B relation from exact source copy.

    This intentionally excludes equality, bidirectional, conditional and full
    transformation wording.  It is a lightweight relation guard, not a
    transformationStack shortcut.
    """
    for clause_match in CLAUSE_RE.finditer(text):
        clause = clause_match.group(0).strip()
        if not clause or any(blocker in clause for blocker in RELATION_BLOCKERS):
            continue
        for operator in RELATION_OPERATORS:
            position = clause.find(operator)
            if position <= 0:
                continue
            source = _relation_endpoint(clause[:position], prefer_last=True)
            target = _relation_endpoint(clause[position + len(operator):], prefer_last=False)
            if not source or not target or source == target:
                continue
            return {
                "source": source,
                "target": target,
                "operator": operator,
                "sourceText": clause,
            }
    return None


def reusable_execution_evidence(text: str) -> dict[str, Any] | None:
    """Require both a changed input and an explicit reuse/repeat result."""
    input_match = REUSABLE_INPUT_RE.search(text)
    result_match = REUSABLE_RESULT_RE.search(text)
    if not input_match or not result_match or result_match.start() <= input_match.start():
        return None
    result_text = result_match.group(0)
    clause_start = max(text.rfind("，", 0, result_match.start()), text.rfind("。", 0, result_match.start())) + 1
    prefix = text[clause_start:result_match.start()]
    entity_matches = [
        (prefix.rfind(term), term)
        for term in RELATION_ENTITY_TERMS
        if term in prefix
    ]
    if entity_matches:
        entity_position, _entity = max(entity_matches, key=lambda item: item[0])
        expanded = text[clause_start + entity_position:result_match.end()].strip(" ，。；：:、")
        if expanded and expanded in text:
            result_text = expanded
    return {
        "input": input_match.group(0),
        "result": result_text,
        "sourceText": text.strip(),
    }


NUMERIC_METRIC_CHINESE_RE = re.compile(
    r"百分之[零〇一二两三四五六七八九十百千万亿点\d]+"
    r"|[一二两三四五六七八九十百千万亿]+(?:倍|万|亿|人|道题|题|个|条|张|套|页|分钟|秒|份|账号)"
)
NUMERIC_METRIC_ARABIC_RE = re.compile(
    r"[+\-]?\d+(?:\.\d+)?\s*(?:%|倍|万|亿|[KkMmGg]|人|道题|题|个|条|张|套|页|分钟|秒|份|账号)?"
)
NUMERIC_METRIC_CONTEXT_TERMS = [
    "提升", "增长", "比例", "指标", "数据", "效率", "转化率", "数量", "规模",
    "省下", "批量", "处理", "扩到", "生成", "完成", "做好", "产出", "输出",
    "一共", "总共", "共计", "分辨率", "清晰",
]


def numeric_metric_token(text: str) -> str | None:
    """Return the source-authored numeric token without dropping Chinese or K/M/G suffixes."""
    chinese_matches = list(NUMERIC_METRIC_CHINESE_RE.finditer(text))
    candidates: list[tuple[int, int, str]] = [
        (match.start(), match.end(), match.group(0).strip()) for match in chinese_matches
    ]
    for match in NUMERIC_METRIC_ARABIC_RE.finditer(text):
        token = match.group(0).strip()
        if not token:
            continue
        if any(match.start() < item.end() and item.start() < match.end() for item in chinese_matches):
            continue
        has_unit = bool(re.search(
            r"(?:%|倍|万|亿|[KkMmGg]|人|道题|题|个|条|张|套|页|分钟|秒|份|账号)$",
            token,
        ))
        context = text[max(0, match.start() - 10):match.end() + 10]
        if has_unit or any(term in context for term in NUMERIC_METRIC_CONTEXT_TERMS):
            product_prefix = text[max(0, match.start() - 12):match.start()]
            if not re.search(r"(?:Codex|GPT|Claude|OpenAI|版本|\bv)\s*$", product_prefix, re.IGNORECASE):
                candidates.append((match.start(), match.end(), token))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    prefer_target = len(candidates) > 1 and any(
        term in text for term in ["变成", "生成", "扩到", "提升到", "增长到", "增加到", "到"]
    )
    return (candidates[-1] if prefer_target else candidates[0])[2]


def numeric_metric_is_meaningful(text: str, token: str | None = None) -> bool:
    token = token or numeric_metric_token(text)
    if not token:
        return False
    compact_token = re.sub(r"\s+", "", token)
    compact_text = re.sub(r"\s+", "", text)
    if compact_token.endswith("个") and re.search(
        rf"{re.escape(compact_token)}(?:指标|步骤|方向|动作|要点|问题|方法|原因|功能|模块|选项|部分|事项|件事)",
        compact_text,
    ):
        return False
    if compact_token.endswith(("张", "页")):
        if re.search(rf"第\s*{re.escape(compact_token)}", compact_text):
            return False
        if any(term in text for term in NUMERIC_METRIC_CONTEXT_TERMS):
            return True
        number_text = compact_token[:-1]
        if re.fullmatch(r"\d+(?:\.\d+)?", number_text):
            return float(number_text) >= 2
        return any(char in number_text for char in "二两三四五六七八九十百千万亿")
    if re.search(r"(?:%|倍|万|亿|[KkMmGg]|分钟|秒|道题|题|人|账号)$", compact_token):
        return True
    return any(term in text for term in NUMERIC_METRIC_CONTEXT_TERMS)


CHINESE_NUMBER_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CHINESE_NUMBER_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000, "亿": 100000000}
NUMERIC_TOKEN_SUFFIXES = ("道题", "分钟", "账号", "%", "倍", "万", "亿", "K", "k", "M", "m", "G", "g", "人", "题", "个", "条", "张", "套", "页", "秒", "份")


def _chinese_integer_value(value: str) -> int | None:
    if not value or any(char not in CHINESE_NUMBER_DIGITS and char not in CHINESE_NUMBER_UNITS for char in value):
        return None
    total = 0
    section = 0
    number = 0
    for char in value:
        if char in CHINESE_NUMBER_DIGITS:
            number = CHINESE_NUMBER_DIGITS[char]
            continue
        unit = CHINESE_NUMBER_UNITS[char]
        if unit < 10000:
            section += (number or 1) * unit
        else:
            section = (section + number) * unit
            total += section
            section = 0
        number = 0
    return total + section + number


def numeric_event_fields(text: str) -> dict[str, Any]:
    """Return source-faithful renderer fields for Arabic or Chinese numeric tokens."""
    token = numeric_metric_token(text)
    if not token:
        return {}
    compact = re.sub(r"\s+", "", token)
    percent = compact.startswith("百分之")
    if percent:
        number_text = compact[3:]
        suffix = "%"
    else:
        suffix = next((item for item in NUMERIC_TOKEN_SUFFIXES if compact.endswith(item)), "")
        number_text = compact[:-len(suffix)] if suffix else compact
    arabic = re.fullmatch(r"([+\-]?)(\d+(?:\.\d+)?)", number_text)
    if arabic:
        value: float | int = float(arabic.group(2))
        if value.is_integer():
            value = int(value)
        normalized_suffix = suffix.upper() if suffix in {"k", "m", "g"} else suffix
        return {"numericValue": value, "numericPrefix": "+" if arabic.group(1) == "+" else "", "numericSuffix": normalized_suffix}
    if "点" in number_text:
        integer_text, decimal_text = number_text.split("点", 1)
        integer_value = _chinese_integer_value(integer_text)
        decimal_digits = "".join(str(CHINESE_NUMBER_DIGITS[char]) for char in decimal_text if char in CHINESE_NUMBER_DIGITS)
        if integer_value is not None and decimal_digits:
            return {"numericValue": float(f"{integer_value}.{decimal_digits}"), "numericPrefix": "", "numericSuffix": suffix}
    chinese_value = _chinese_integer_value(number_text)
    if chinese_value is not None:
        return {"numericValue": chinese_value, "numericPrefix": "", "numericSuffix": suffix}
    return {"numericText": token}


ORDERED_WORKFLOW_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("first", re.compile(r"^\s*(?:首先|第一步|第一|先)(?:是|要|把|将)?\s*")),
    ("middle", re.compile(r"^\s*(?:然后|接着|随后|其次|第二步|第二|再)(?:是|要|把|将)?\s*")),
    ("final", re.compile(r"^\s*(?:最后|最终|第三步|第三)(?:是|要|把|将)?\s*")),
)
ORDERED_WORKFLOW_ICON_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("读取", "逐字稿", "文案", "文件"), "FileText"),
    (("判断", "分析", "识别", "语义"), "BrainCircuit"),
    (("写入", "时间线", "排入", "编排"), "Clock3"),
    (("检查", "确认", "验证"), "ShieldCheck"),
    (("生成", "渲染", "剪辑"), "Cpu"),
    (("输出", "导出", "发布"), "SendHorizontal"),
)
ORDERED_WORKFLOW_FALLBACK_ICONS = ("CircleDot", "Workflow", "CheckCircle2", "ListChecks", "Sparkles")


def _ordered_workflow_marker(text: str) -> tuple[str, re.Match[str]] | None:
    for role, pattern in ORDERED_WORKFLOW_MARKERS:
        match = pattern.search(text)
        if match:
            return role, match
    return None


def _ordered_workflow_icon(label: str, used: set[str]) -> str:
    for terms, icon in ORDERED_WORKFLOW_ICON_RULES:
        if icon not in used and any(term in label for term in terms):
            return icon
    return next((icon for icon in ORDERED_WORKFLOW_FALLBACK_ICONS if icon not in used), "Workflow")


def ordered_workflow_window(
    cues: list[dict[str, Any]],
    cursor: int,
    *,
    max_gap_frames: int,
    max_duration_frames: int,
    max_cues: int = 5,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    """Extract an explicit first/middle/final workflow without crossing hard semantic boundaries."""
    if cursor < 0 or cursor >= len(cues):
        return None
    first_signal = _ordered_workflow_marker(str(cues[cursor].get("text") or ""))
    if not first_signal or first_signal[0] != "first":
        return None
    scene_id = str(cues[cursor].get("sceneId") or "")
    group: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    used_icons: set[str] = set()
    seen_middle = False
    start_frame = int(cues[cursor].get("startFrame", 0) or 0)
    previous_end = start_frame
    for cue in cues[cursor:cursor + max_cues]:
        if str(cue.get("sceneId") or "") != scene_id:
            break
        cue_start = int(cue.get("startFrame", previous_end) or previous_end)
        cue_end = int(cue.get("endFrame", cue_start) or cue_start)
        if group and cue_start > previous_end + max_gap_frames:
            break
        if cue_end - start_frame > max_duration_frames:
            break
        text = str(cue.get("text") or "").strip()
        signal = _ordered_workflow_marker(text)
        if not signal:
            break
        role, marker = signal
        if not group and role != "first":
            return None
        if group and role == "first":
            break
        if role == "middle":
            seen_middle = True
        if role == "final" and not seen_middle:
            return None
        if parse_cta_provenance(text) or is_proof_context(text):
            return None
        token = numeric_metric_token(text)
        if token and numeric_metric_is_meaningful(text, token):
            return None
        label = text[marker.end():].strip(" ，。；：:、")[:12]
        cue_id = str(cue.get("id") or "")
        if not label or not cue_id or label not in text:
            return None
        icon = _ordered_workflow_icon(label, used_icons)
        used_icons.add(icon)
        group.append(cue)
        steps.append({
            "id": f"workflow-step-{len(steps) + 1:02d}",
            "label": label,
            "text": text,
            "sourceCueIds": [cue_id],
            "iconName": icon,
        })
        previous_end = cue_end
        if role == "final":
            return (group, steps) if len(group) >= 3 else None
    return None


AUTOMATION_HANDOFF_ICON_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("网页", "页面", "链接", "网址"), "Link2"),
    (("合同", "文件", "文档", "文案", "脚本"), "FileText"),
    (("图片", "主图", "详情图", "封面", "海报"), "Images"),
    (("视频", "录屏"), "Video"),
    (("素材", "资料"), "Package"),
    (("参数", "数据", "数量"), "Hash"),
    (("读取", "查看", "看"), "ScanSearch"),
    (("提取", "识别", "解析", "分析"), "TextCursorInput"),
    (("检查", "审核", "风险", "确认"), "ShieldCheck"),
    (("整理", "汇总", "答案", "摘要"), "ListChecks"),
    (("生成", "制作", "渲染", "剪辑"), "Cpu"),
    (("输出", "发布", "上传", "提交"), "SendHorizontal"),
    (("接管", "执行", "跑下去", "流程"), "Workflow"),
)
AUTOMATION_HANDOFF_FALLBACK_ICONS = ("FileText", "Link2", "ScanSearch", "ListChecks", "Workflow", "Package", "Bot", "SendHorizontal")
AUTOMATION_HANDOFF_OBJECT_RE = re.compile(
    r"(?P<body>[^，。；！？!?]{1,64}?)(?:都|全部|一起)?"
    r"(?:交给|丢给|发给|提交给|交由)\s*(?:Codex|系统|AI|自动化流程|它)"
)
AUTOMATION_HANDOFF_PRIMARY_SEPARATOR_RE = re.compile(r"(?:以及|并且|、|,|，|/)")
AUTOMATION_HANDOFF_ACTION_RE = re.compile(
    r"(?:自己|自动|继续)?"
    r"(?:读取|查看|解析|提取|检查|审核|整理|汇总|生成|剪辑|输出|发布|上传|确认|填写|补充|制作|渲染|分析|识别|处理|执行|接管|完成|读|看|跑下去)"
    r"[^、，。；！？!?\s并再]{0,8}"
)
AUTOMATION_HANDOFF_OBJECT_TERMS = (
    "网页", "页面", "链接", "合同", "文件", "文档", "文案", "脚本", "图片", "主图", "详情图",
    "封面", "海报", "视频", "录屏", "素材", "资料", "参数", "数据", "卖点", "名单", "题目",
    "答案", "摘要", "标题", "简介", "标签", "检查", "审核", "输出", "发布", "要求", "用户画像", "竞品分析",
)
AUTOMATION_HANDOFF_FALLBACK_TERMS = (
    "交给 Codex", "交给Codex", "丢给 Codex", "丢给Codex", "Codex 接管", "Codex接管",
    "系统执行", "自动接管", "交给系统", "交给自动化", "自动化流程", "接管",
)


def _trim_handoff_span(text: str, start: int, end: int) -> tuple[int, int] | None:
    while start < end and text[start] in " \t，把将，。；：:、":
        start += 1
    while end > start and text[end - 1] in " \t，。；：:、":
        end -= 1
    for suffix in ("全部", "一起", "都"):
        if text[start:end].endswith(suffix):
            end -= len(suffix)
            break
    span = text[start:end]
    marker = max(span.rfind("把"), span.rfind("将"))
    if marker >= 0:
        start += marker + 1
    for prefix in ("后面的", "剩下的", "接下来的", "这些", "这份", "这组", "你只负责", "只负责", "我直接"):
        if text.startswith(prefix, start, end):
            start += len(prefix)
            break
    while start < end and text[start] in " \t，。；：:、":
        start += 1
    return (start, end) if start < end else None


def _handoff_icon(text: str, used: set[str]) -> str:
    for terms, icon in AUTOMATION_HANDOFF_ICON_RULES:
        if icon not in used and any(term in text for term in terms):
            return icon
    return next((icon for icon in AUTOMATION_HANDOFF_FALLBACK_ICONS if icon not in used), "Bot")


def _handoff_action_is_prior_or_negated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 16):start]
    if re.search(
        r"(?:不要|不再|不必|无需|不用|禁止|不能|不会|不应|还没|没有|(?:^|[，。；！？!?\s]|先|请|Codex)别(?:再)?).{0,5}$",
        prefix,
    ):
        return True
    return re.search(r"之前.{0,6}$", prefix) is not None


def _looks_like_handoff_object(text: str) -> bool:
    return any(term in text for term in AUTOMATION_HANDOFF_OBJECT_TERMS)


def _split_handoff_object_range(body: str, start: int, end: int) -> list[tuple[int, int]]:
    segment = body[start:end]
    for conjunction in re.finditer(r"[和与及]", segment):
        split_at = start + conjunction.start()
        left = body[start:split_at]
        right = body[split_at + 1:end]
        if _looks_like_handoff_object(left) and _looks_like_handoff_object(right):
            return [
                *_split_handoff_object_range(body, start, split_at),
                *_split_handoff_object_range(body, split_at + 1, end),
            ]
    return [(start, end)]


def extract_automation_handoff_steps(text: str) -> list[dict[str, str]]:
    """Extract ordered handoff objects/actions from exact source text without sample defaults."""
    candidates: list[tuple[int, int]] = []
    for clause_match in CLAUSE_RE.finditer(text):
        clause = clause_match.group(0)
        object_match = AUTOMATION_HANDOFF_OBJECT_RE.search(clause)
        if not object_match:
            continue
        body_start = clause_match.start() + object_match.start("body")
        body = object_match.group("body")
        primary_ranges: list[tuple[int, int]] = []
        part_cursor = 0
        for separator in AUTOMATION_HANDOFF_PRIMARY_SEPARATOR_RE.finditer(body):
            primary_ranges.append((part_cursor, separator.start()))
            part_cursor = separator.end()
        primary_ranges.append((part_cursor, len(body)))
        part_ranges = [
            split_range
            for primary_start, primary_end in primary_ranges
            for split_range in _split_handoff_object_range(body, primary_start, primary_end)
        ]
        for part_start, part_end in part_ranges:
            trimmed = _trim_handoff_span(text, body_start + part_start, body_start + part_end)
            if trimmed and text[trimmed[0]:trimmed[1]].strip() not in {"先", "再", "然后", "接着", "之后", "后面"}:
                candidates.append(trimmed)
    actor_match = re.search(r"Codex|自动化流程|系统|AI|它", text)
    action_start = actor_match.start() if actor_match else 0
    for action_match in AUTOMATION_HANDOFF_ACTION_RE.finditer(text, action_start):
        if _handoff_action_is_prior_or_negated(text, action_match.start()):
            continue
        trimmed = _trim_handoff_span(text, action_match.start(), action_match.end())
        if trimmed:
            candidates.append(trimmed)
    if not candidates:
        for term in AUTOMATION_HANDOFF_FALLBACK_TERMS:
            start = text.find(term)
            if start >= 0:
                candidates.append((start, start + len(term)))
                break
    ordered: list[tuple[int, int]] = []
    for start, end in sorted(candidates, key=lambda item: (item[0], item[1])):
        value = text[start:end].strip()
        if not value or any(start < prior_end and prior_start < end for prior_start, prior_end in ordered):
            continue
        if any(text[prior_start:prior_end].strip() == value for prior_start, prior_end in ordered):
            continue
        ordered.append((start, end))
        if len(ordered) == 5:
            break
    steps: list[dict[str, str]] = []
    used_icons: set[str] = set()
    for start, end in ordered:
        source_text = text[start:end].strip()
        icon = _handoff_icon(source_text, used_icons)
        used_icons.add(icon)
        steps.append({
            "id": f"handoff-step-{len(steps) + 1:02d}",
            "label": source_text[:12],
            "text": source_text,
            "iconName": icon,
        })
    return steps


# This is the single completion vocabulary used by both routers. Keep longer
# phrases before the broad word "完成" when reading/debugging this list.
WORKFLOW_COMPLETION_TERMS = [
    "生成完成", "生成好了", "生成完", "全部完成", "全都完成", "已经完成", "已完成",
    "明确完成", "任务完成", "交付完成", "完成了", "完成", "全部做好", "全都做好",
    "都做好", "已经做好", "做好了", "做完", "输出完成", "流程跑完", "自动跑完", "跑完",
    "搞定", "全部交付", "都已输出", "已经输出", "已经交付", "已交付", "现在都齐了",
    "全都齐了", "都齐了",
]
COMPLETION_PROSPECTIVE_SUFFIXES = ["之后", "以后", "后", "之前", "前"]
COMPLETION_QUESTION_PREFIXES = ["是否", "有没有", "能否", "可否", "是不是"]
COMPLETION_NOMINAL_SUFFIXES = ["按钮", "状态", "字段", "标识", "文案", "选项", "页面", "率", "度", "时间", "时长", "条件"]
COMPLETION_HARD_FAILURE_TERMS = ["未交付", "没交付", "未输出", "没输出", "不完整", "没有成功"]
COMPLETION_SOFT_FAILURE_TERMS = ["失败", "出错", "报错", "异常", "缺失"]
COMPLETION_META_TERMS = ["这两个字", "这个词", "该词", "字样", "文案", "术语", "说法", "不要出现"]
COMPLETION_NEGATION_RE = re.compile(
    r"(?:尚未|还未|还没|没有|并未|并非|不是|不算|未|没)(?:真正|彻底|完全|全部|全都|都|已经|已)?$"
)
COMPLETION_LOCAL_PROSPECTIVE_PATTERNS = [
    re.compile(r"(?:稍后|随后|预计|计划|等到|需要|必须|应该|应当|准备|尽快|为了|争取|力争|请|务必|确保)[^，。；！？!?\n]{0,10}$"),
    re.compile(r"(?:将会|即将|将|会)(?:自动|很快|马上|随后|最终)?$"),
    re.compile(r"(?:等|待)(?:到)?[^，。；！？!?\n]{0,6}$"),
    re.compile(r"(?:可以|能够)(?:自动|直接|一键|轻松|很快)?$"),
    re.compile(r"(?:交给|丢给|交由|让|由)(?:(?!已经|已|终于|现在)[^，。；！？!?\n]){0,16}(?:自动)?$"),
    re.compile(r"(?:^|这(?:一)?步|系统|流程|任务|工具|用户|平台|服务|程序|模型|他|她|它|我们|你|我|AI|Codex|现在|就|也|都)(?:能|可)(?:自动|直接|一键|轻松|很快)?$"),
]
COMPLETION_REPORT_NEGATION_RE = re.compile(
    r"(?:没有|并未|未|没)(?:明确)?(?:说|表示|说明|确认|宣布|声称|证明|显示|提到)[^，。；！？!?\n]{0,10}$"
)
COMPLETION_PARTIAL_PATTERNS = [
    re.compile(r"(?:只|仅|部分|局部|一部分|一半|半数).{0,6}(?:完成|做完|做好|交付|输出)"),
    re.compile(r"(?:完成|做完|做好|交付|输出).{0,6}(?:\d+%|[一二两三四五六七八九十\d]+成|一半|一部分|部分|半数|大半|过半|得?差不多)"),
    re.compile(r"(?:基本|大体|差不多|接近|几乎|快|快要|马上就|就要|将要|眼看就要).{0,5}(?:完成|做完|做好|交付|输出)"),
    re.compile(r"(?:距离|离).{0,6}(?:完成|做完|做好|交付|输出).{0,8}(?:还有|还差)"),
    re.compile(r"(?:还剩|还差).{0,8}(?:完成|做完|做好|交付|输出)"),
    re.compile(r"(?:尚|还|仍)?差.{0,8}(?:才|才能)?(?:完成|做完|做好|交付|输出)"),
    re.compile(r"(?:还需|仍需|尚需).{0,8}(?:才|才能)?(?:完成|做完|做好|交付|输出)"),
    re.compile(r"(?:完成|做完|做好|交付|输出)(?:进度)?.{0,5}(?:过半|不足|未满)"),
    re.compile(r"(?:还|尚|目前)?(?:不能|无法|未能).{0,8}(?:算|说|确认)?.{0,6}(?:完成|做完|做好|交付|输出)"),
    re.compile(r"(?:已经|已)?完成第[一二两三四五六七八九十\d]+项"),
    re.compile(r"(?:其中)?[一二两三四五六七八九十\d]+项(?:已经|已)?完成"),
]

RESULT_EVALUATION_SUBJECT = (
    r"(?:结果|答案|结论|输出|验证|校验|检查|测试|执行|运行|流程|任务|交付|处理|"
    r"识别|匹配|计算|生成|渲染|导出|发布|状态|确认|这一步|这次|这个结果|最终结果)"
)
RESULT_EVALUATION_POSITIVE_PATTERNS = [
    re.compile(r"(?:没有|并无|无(?:任何)?|未发现|不存在)(?:出现)?(?:任何)?(?:错误|出错|报错|异常|失败)"),
    re.compile(r"(?:错误|报错|异常|失败)(?:项|数|数量)?\s*(?:为|是|[:：])?\s*(?:0|零)(?:个|项|次)?"),
    re.compile(
        RESULT_EVALUATION_SUBJECT
        + r"(?:已经|已|最终|均|都|全部|完全)?(?:是|为)?(?:正确|成功|通过|正常|无误)"
    ),
    re.compile(r"(?:这是|这个结果(?:是|为)?|这个结论(?:是|为)?)(?:正确|成功|通过|正常|无误)的?"),
    re.compile(r"(?:通过|成功完成)了?(?:验证|校验|检查|测试)"),
]
RESULT_EVALUATION_NEGATIVE_PATTERNS = [
    re.compile(
        RESULT_EVALUATION_SUBJECT
        + r"(?:已经|已|最终|均|都|全部|完全)?(?:是|为)?"
        r"(?:没有通过|没通过|未通过|不通过|没有成功|没成功|未成功|不正确|不正常|"
        r"错误|出错|失败|异常|不完整|有缺失|缺失)"
    ),
    re.compile(r"(?:这是|这个结果(?:是|为)?|这个结论(?:是|为)?)(?:不正确|错误|失败|异常|不正常)的?"),
    re.compile(r"(?:系统|程序|工具|页面|接口|这一步|这次|刚才|最终|实际)?(?:报错|出错|失败|异常)(?:了|啦)?"),
    re.compile(r"(?:未|没|没有)(?:交付|输出)"),
    re.compile(r"(?:最终|结果|输出|交付|内容|文件|成片)?(?:并)?不完整"),
    re.compile(r"(?:最终|实际|这次|这一步)?(?:没有|没|未)成功"),
    re.compile(r"(?:结果|输出|交付|内容|文件|素材)?(?:有)?缺失"),
]
RESULT_EVALUATION_RESET_RE = re.compile(r"(?:但|不过|但是|而是|现在|如今|最终)")
RESULT_EVALUATION_NON_ASSERTED_PREFIX_RE = re.compile(
    r"(?:是否|能否|可否|是不是|有没有|可能|也许|或许|大概|预计|担心|容易|避免|防止|"
    r"以免|如果|只要|一旦|等到|待|假如|万一)[^，。；！？!?\n]{0,14}$"
)
RESULT_EVALUATION_QUESTION_RE = re.compile(r"(?:吗|么|呢|是否|没有|没)(?:[？?])?$")
RESULT_EVALUATION_META_SUFFIX_RE = re.compile(
    r"^(?:按钮|状态|字段|标识|文案|选项|页面|率|条件|示例|案例|词|字样|说法|概念|定义|"
    r"教程|方法|规则|名称|类型|原因|分析|记录|日志)"
)
RESULT_EVALUATION_ZERO_SUFFIX_RE = re.compile(
    r"^(?:项|数|数量)?\s*(?:为|是|[:：])?\s*(?:0|零)(?:个|项|次)?"
)


def _result_candidate_is_non_asserted(
    clause: str,
    start: int,
    end: int,
    polarity: str,
) -> bool:
    prefix = RESULT_EVALUATION_RESET_RE.split(clause[:start])[-1]
    near_prefix = prefix[-18:]
    source = clause[start:end]
    suffix = clause[end:end + 14].lstrip()
    question_scope = f"{near_prefix[-6:]}{source}{suffix[:3]}"
    if RESULT_EVALUATION_NON_ASSERTED_PREFIX_RE.search(near_prefix):
        return True
    if any(marker in question_scope for marker in ["是否", "能否", "可否", "是不是", "有没有"]):
        return True
    if RESULT_EVALUATION_QUESTION_RE.search(f"{source}{suffix[:3]}"):
        return True
    if suffix.startswith(("后", "之后", "以后", "前", "之前")):
        return True
    if RESULT_EVALUATION_META_SUFFIX_RE.search(suffix):
        return True
    if polarity == "negative":
        if re.search(r"(?:没有|并无|无(?:任何)?|未发现|不存在|不再|不是|并非|不算)\s*$", near_prefix):
            return True
        if RESULT_EVALUATION_ZERO_SUFFIX_RE.search(suffix):
            return True
    return False


def result_evaluation(text: str) -> dict[str, Any] | None:
    """Return the latest asserted positive/negative result evaluation in spoken text."""
    candidates: list[tuple[int, int, str, str]] = []
    for clause_match in CLAUSE_RE.finditer(text):
        clause = clause_match.group(0)
        for polarity, patterns in (
            ("positive", RESULT_EVALUATION_POSITIVE_PATTERNS),
            ("negative", RESULT_EVALUATION_NEGATIVE_PATTERNS),
        ):
            for pattern in patterns:
                for match in pattern.finditer(clause):
                    if _result_candidate_is_non_asserted(clause, match.start(), match.end(), polarity):
                        continue
                    start = clause_match.start() + match.start()
                    end = clause_match.start() + match.end()
                    candidates.append((end, start, polarity, match.group(0).strip()))
    if not candidates:
        return None
    end, start, polarity, source_text = max(candidates, key=lambda item: (item[0], item[1]))
    return {"polarity": polarity, "sourceText": source_text, "start": start, "end": end}


def _completion_is_partial_or_unresolved(clause: str, start: int, end: int) -> bool:
    scope = clause[max(0, start - 18):min(len(clause), end + 18)]
    if not any(pattern.search(scope) is not None for pattern in COMPLETION_PARTIAL_PATTERNS):
        return False
    if any(
        term in scope
        for term in ["只", "仅", "部分", "局部", "一部分", "一半", "半数", "其中", "距离", "还剩", "还差", "尚差", "还需", "仍需", "尚需", "不能", "无法", "未能", "差不多", "基本", "大体", "接近", "几乎", "快", "马上", "就要", "眼看", "大半", "过半", "八成"]
    ):
        return True
    full_scope = re.search(r"(?:全部|全都|所有|整套|全流程).{0,8}(?:完成|做好|交付|输出|已完成)", scope)
    return full_scope is None


def _has_unresolved_completion_failure(text: str) -> bool:
    evaluation = result_evaluation(text)
    if evaluation is not None:
        return evaluation.get("polarity") == "negative"
    if any(term in text for term in COMPLETION_HARD_FAILURE_TERMS):
        return True
    for term in COMPLETION_SOFT_FAILURE_TERMS:
        for match in re.finditer(re.escape(term), text):
            prefix = text[max(0, match.start() - 10):match.start()]
            suffix = text[match.end():match.end() + 10]
            if re.search(r"(?:没有|并无|无(?:任何)?|未发现|不存在|不再|避免|防止|以免|可能|容易)\s*$", prefix):
                continue
            if re.match(r"(?:项|数|数量)?\s*(?:为|是|[:：])?\s*(?:0|零)(?:\D|$)", suffix):
                continue
            return True
    return False


def completion_polarity(text: str) -> str:
    """Return asserted, negated, prospective, or none for completion language."""
    ordered_terms = sorted(set(WORKFLOW_COMPLETION_TERMS), key=len, reverse=True)
    last_state = "none"
    last_end = -1
    for clause_match in CLAUSE_RE.finditer(text):
        clause = clause_match.group(0)
        mentions: list[tuple[int, int, str]] = []
        for term in ordered_terms:
            mentions.extend((match.start(), match.end(), term) for match in re.finditer(re.escape(term), clause))
        mentions = [
            mention for mention in mentions
            if not any(
                other_start <= mention[0] and mention[1] <= other_end
                and (other_end - other_start) > (mention[1] - mention[0])
                for other_start, other_end, _other_term in mentions
            )
        ]
        for local_start, local_end, term in sorted(mentions, key=lambda item: (item[1], item[0])):
            global_start = clause_match.start() + local_start
            global_end = clause_match.start() + local_end
            local_prefix = clause[max(0, local_start - 24):local_start]
            local_suffix = clause[local_end:local_end + 12]
            sentence_prefix = re.split(r"[。；！？!?\n]", text[:global_start])[-1][-48:]
            clause_prefix = clause[:local_start]
            quoted_term = local_start > 0 and clause[local_start - 1] in "“\"‘'" and local_suffix.startswith(("”", "\"", "’", "'"))
            if any(marker in sentence_prefix for marker in COMPLETION_QUESTION_PREFIXES) or any(marker in local_suffix for marker in ["吗", "么", "没有", "没", "是否"]):
                last_state = "none"
            elif quoted_term or any(local_suffix.startswith(marker) for marker in COMPLETION_NOMINAL_SUFFIXES) or any(marker in local_suffix[:12] for marker in COMPLETION_META_TERMS):
                last_state = "none"
            elif COMPLETION_REPORT_NEGATION_RE.search(local_prefix):
                last_state = "none"
            elif _completion_is_partial_or_unresolved(clause, local_start, local_end):
                last_state = "prospective"
            elif COMPLETION_NEGATION_RE.search(local_prefix):
                last_state = "negated"
            else:
                explicit_asserted = any(marker in f"{local_prefix[-10:]}{term}" for marker in ["已经", "已", "现在", "如今", "终于"])
                conditional_in_clause = any(marker in clause_prefix for marker in ["如果", "只要", "一旦"])
                conditional_before_clause = any(marker in sentence_prefix for marker in ["如果", "只要", "一旦"])
                conditional_scope = conditional_in_clause or (conditional_before_clause and not explicit_asserted)
                prospective_prefix = any(pattern.search(local_prefix) is not None for pattern in COMPLETION_LOCAL_PROSPECTIVE_PATTERNS)
                prospective_suffix = any(local_suffix.startswith(marker) for marker in COMPLETION_PROSPECTIVE_SUFFIXES)
                last_state = "prospective" if conditional_scope or prospective_prefix or prospective_suffix else "asserted"
            last_end = global_end
    if last_state == "asserted" and last_end >= 0 and _has_unresolved_completion_failure(text[last_end:]):
        return "negated"
    return last_state


CTA_META_TERMS = ["按钮文案", "反例", "违禁词", "词库", "写成", "不要写", "加入", "作为"]
CTA_SOFT_META_TERMS = ["脚本", "测试", "示例"]
CTA_NEGATION_TERMS = ["别", "不要", "不用", "不必", "禁止", "不能", "避免", "无需", "并非", "不是", "不需要", "可以不", "不想", "不打算", "不建议", "没必要", "没打算", "从未", "还没有", "尚未", "并没有", "从来没"]
CTA_FOLLOW_OBJECT_TERMS = ["模型", "输出", "指标", "结果", "成本", "差异", "稳定", "质量", "数据", "能力"]
CTA_VIEWER_CONTEXT_TERMS = ["你", "大家", "想要", "需要", "可以", "欢迎", "记得", "别忘", "不要忘记", "请", "直接", "就", "来", "也可以"]
CTA_DIRECTIVE_CONTEXT_TERMS = ["想要", "需要", "可以", "欢迎", "记得", "别忘", "不要忘记", "请", "直接", "就", "来", "也可以"]
CTA_NON_DIRECTIVE_PREFIX_TERMS = ["已经", "刚刚", "刚才", "曾经", "之前", "感谢", "谢谢", "从未", "没必要", "没打算", "不需要", "可以不", "一直", "正在", "知道", "因为", "都", "看到", "还没有", "尚未", "并没有", "从来没"]
CTA_DESCRIPTION_SUFFIX_RE = re.compile(r"^(?:了|过|得|很|由|太|需|的|框|速度|内容|质量|率|功能|数量|数(?!字人)|是|按钮|名称|字段|入口|页面|选项|文案|公告|作为)")
CTA_FREEFORM_KEYWORD_PREFIXES = ["你的", "您", "告诉我", "一下", "问题", "看法", "案例", "想法", "意见", "内容", "答案"]
CTA_ACTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("reply", re.compile(r"(?:评论区|评论里|评论下|下方)\s*回复(?:关键词)?(?!率|功能|数量|数(?!字人)|是|按钮|名称)|回复关键词(?!率|功能|数量|数(?!字人)|是|按钮|名称)|^回复(?=[“\"‘'])")),
    ("comment", re.compile(r"(?:在)?(?:评论区|评论里|评论下|下方)(?:里|中)?\s*(?:留言(?!率|功能|数量|数|是|按钮|名称)|告诉我(?!们)|打个?\s*\d+|扣(?:下|个)?|输入|发)")),
    ("comment", re.compile(r"评论区见(?=$|[吧哦哈啦呀]|下期|明天|下一条)")),
    ("comment", re.compile(r"(?<!不要)(?<!禁止)(?<!避免)留言(?=[“\"‘']|[^，。；！？!?]{0,10}(?:我把|我发|发给))")),
    ("direct-message", re.compile(r"私信我(?!功能|入口|按钮|页面|记录|消息)|私信(?!我|功能|入口|按钮|页面|记录|消息)")),
    ("follow", re.compile(r"关注我|关注账号|点个关注|关注一下|点一下关注|(?:记得|别忘了?|不要忘记|别忘记)关注")),
    ("save", re.compile(r"(?:(?:记得|别忘了?|不要忘记|别忘记|建议|可以)\s*)?收藏(?:这一条|这条|一下)?(?!夹|功能|数量|数|率|是|按钮)")),
    ("like", re.compile(r"点赞这|点个赞|帮我点赞|记得点赞|点赞关注")),
    ("share", re.compile(r"(?:转发|分享)给(?:需要的)?(?:朋友|同事|家人|身边的人|他|她|他们)")),
    ("claim", re.compile(r"评论区领取|直接领取|点击领取|领取(?:这|模板|流程|规则)|自提")),
    ("respond", re.compile(r"告诉我(?!们)")),
]


def _cta_clause_is_meta(clause: str) -> bool:
    return any(term in clause for term in CTA_META_TERMS) or (
        any(term in clause for term in CTA_SOFT_META_TERMS)
        and any(term in clause for term in ["用作", "用来", "写", "文案", "词", "反例", "作为"])
    )


def _cta_action_is_negated(clause: str, start: int) -> bool:
    prefix = clause[:start]
    if re.search(r"(?:别忘了?|不要忘记|别忘记)\s*$", prefix):
        return False
    for term in CTA_NEGATION_TERMS:
        position = prefix.rfind(term)
        if position >= 0 and len(prefix[position + len(term):]) <= 24 and not re.search(r"(?:但|不过|而是|可是|只是)", prefix[position + len(term):]):
            return True
    return False


def _cta_action_has_viewer_context(clause: str, kind: str, start: int, source_text: str) -> bool:
    if kind in {"reply", "comment"} and any(term in source_text for term in ["评论", "下方", "回复关键词"]):
        return True
    if any(term in source_text for term in CTA_DIRECTIVE_CONTEXT_TERMS):
        return True
    prefix = clause[:start].strip()
    if not prefix:
        return True
    tail = prefix[-18:]
    last_non_directive = max((tail.rfind(term) for term in CTA_NON_DIRECTIVE_PREFIX_TERMS), default=-1)
    last_directive = max((tail.rfind(term) for term in CTA_DIRECTIVE_CONTEXT_TERMS), default=-1)
    if last_non_directive >= 0 and last_non_directive > last_directive:
        return False
    return any(term in tail for term in CTA_VIEWER_CONTEXT_TERMS)


def _cta_keyword(text: str, actions: list[dict[str, str]]) -> str:
    if not any(action.get("kind") in {"reply", "comment"} for action in actions):
        return ""
    match = re.search(
        r"(?:回复(?:关键词)?|留言|打个?|扣(?:下|个)?|输入|发)\s*[:：]?\s*(?:[“\"‘']([^”\"’']{1,16})[”\"’']|([A-Za-z0-9_\-\u4e00-\u9fff]+(?:\s+[A-Za-z0-9_\-\u4e00-\u9fff]+){0,2}))",
        text,
    )
    if not match:
        return ""
    value = (match.group(1) or match.group(2) or "").strip()
    value = re.split(r"(?:我把|我发|发你|发给|领取|可以|，|。|；)", value)[0].strip()
    if value in {"", "我", "我把", "我发", "一下", "告诉我"} or len(value) > 12:
        return ""
    return "" if any(value.startswith(prefix) for prefix in CTA_FREEFORM_KEYWORD_PREFIXES) else value


def parse_cta_provenance(text: str) -> dict[str, Any] | None:
    """Parse at most two explicit viewer actions; descriptions and past actions are not CTA."""
    actions_with_pos: list[tuple[int, dict[str, str]]] = []
    for clause_match in CLAUSE_RE.finditer(text):
        clause = clause_match.group(0)
        if _cta_clause_is_meta(clause):
            continue
        for kind, pattern in CTA_ACTION_PATTERNS:
            for match in pattern.finditer(clause):
                source_text = match.group(0).strip()
                if not source_text or _cta_action_is_negated(clause, match.start()):
                    continue
                if CTA_DESCRIPTION_SUFFIX_RE.search(clause[match.end():].lstrip()):
                    continue
                if not _cta_action_has_viewer_context(clause, kind, match.start(), source_text):
                    continue
                if kind == "follow" and any(clause[match.end():].lstrip().startswith(term) for term in CTA_FOLLOW_OBJECT_TERMS):
                    continue
                actions_with_pos.append((clause_match.start() + match.start(), {"kind": kind, "sourceText": source_text}))
    actions: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for _position, action in sorted(actions_with_pos, key=lambda item: item[0]):
        key = (action["kind"], action["sourceText"])
        if key in seen:
            continue
        seen.add(key)
        actions.append(action)
        if len(actions) == 2:
            break
    if not actions:
        return None
    provenance: dict[str, Any] = {"actions": actions}
    keyword = _cta_keyword(text, actions)
    if keyword:
        provenance["keyword"] = keyword
    return provenance


def viewer_cta_signal(text: str) -> dict[str, Any] | None:
    """Portrait adapter for the shared multi-action CTA provenance."""
    provenance = parse_cta_provenance(text)
    if not provenance:
        return None
    action = provenance["actions"][0]
    result: dict[str, Any] = {
        "actionKind": action["kind"],
        "action": action["sourceText"],
        "sourceText": text.strip(),
    }
    if provenance.get("keyword"):
        result["keyword"] = provenance["keyword"]
    return result


def has_cta_action_signal(text: str) -> bool:
    return parse_cta_provenance(text) is not None


def cta_action_keywords(text: str) -> list[str]:
    provenance = parse_cta_provenance(text)
    if not provenance:
        return []
    values = [str(action.get("sourceText") or "") for action in provenance.get("actions", []) if isinstance(action, dict)]
    if provenance.get("keyword"):
        values.append(str(provenance["keyword"]))
    return [value for value in values if value][:4]
