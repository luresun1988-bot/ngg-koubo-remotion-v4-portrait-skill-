#!/usr/bin/env python3
"""Format-agnostic semantic guards shared by the V4 landscape/portrait routers."""

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
HANDOFF_ASSERTED_RE = re.compile(
    r"(?:交给|丢给|交由|让|由)[^，。！？]{0,16}(?:Codex|系统|自动化)"
    r"|(?:Codex|系统|自动化)[^，。！？]{0,10}(?:接管|执行|处理)"
)
PROCESS_CONTEXT_RE = re.compile(
    r"(?:输入|填写|上传|选择|设置|点击|确认|提交|搜索|整理|配置)[^，。！？]{0,18}"
    r"(?:生成|导出|发布|提交|保存|标题|关键词|素材|参数|选项|结果|页面|竞品)"
    r"|(?:系统|平台|工具|AI|Codex)[^，。！？]{0,8}(?:会|将|可以|能够)?(?:自动)?(?:生成|导出|处理|执行)"
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
)

COMPLETION_TERMS = (
    "生成完成",
    "生成好了",
    "生成完",
    "全部完成",
    "全都完成",
    "已经完成",
    "已完成",
    "完成了",
    "完成",
    "全部做好",
    "全都做好",
    "已经做好",
    "做好了",
    "做完",
    "输出完成",
    "流程跑完",
    "自动跑完",
    "跑完",
    "搞定",
    "已经交付",
    "已交付",
)
COMPLETION_NEGATION_RE = re.compile(
    r"(?:还没有|还没|尚未|还未|并未|并非|没有|不是|不算|未|没)"
    r"(?:真正|彻底|完全|全部|全都|都|已经|已|自动)?$"
)
COMPLETION_PROSPECTIVE_RE = re.compile(
    r"(?:如果|只要|一旦|稍后|随后|预计|计划|将会|即将|会|将|等到|等|待|需要|可以|能够|能|可|必须|应该|准备|请|务必|确保)"
    r"[^，。；！？!?\n]{0,18}$"
    r"|(?:交给|丢给|交由|让|由)[^，。；！？!?\n]{0,18}(?:自动)?$"
)
COMPLETION_NOMINAL_SUFFIXES = (
    "按钮",
    "状态",
    "字段",
    "标识",
    "文案",
    "选项",
    "页面",
    "率",
    "度",
    "时间",
    "时长",
    "条件",
)
COMPLETION_PROSPECTIVE_SUFFIXES = ("之后", "以后", "后", "之前", "前")
COMPLETION_PARTIAL_RE = re.compile(
    r"(?:只|仅|部分|一部分|一半|基本|大体|差不多|接近|几乎|快|还差|还剩|还需|尚需)"
    r"[^，。！？]{0,10}(?:完成|做完|做好|生成完|跑完|交付|输出)"
    r"|(?:完成|做完|做好|生成完|跑完|交付|输出)[^，。！？]{0,8}(?:一半|一部分|部分|大半|过半|差不多|\d+%)"
)


def future_preview(text: str) -> str:
    match = FUTURE_PREVIEW_RE.search(text)
    return match.group(0).strip() if match else ""


def topic_intro(text: str) -> str:
    match = TOPIC_INTRO_RE.search(text)
    return match.group(0).strip() if match else ""


def handoff_state(text: str) -> str:
    """Return asserted, negated, or none for an automation handoff."""
    if HANDOFF_NEGATED_RE.search(text):
        return "negated"
    if HANDOFF_ASSERTED_RE.search(text):
        return "asserted"
    return "none"


def is_process_context(text: str) -> bool:
    return PROCESS_CONTEXT_RE.search(text) is not None or CONDITIONAL_PROCESS_RE.search(text) is not None


def is_explanation_claim(text: str) -> bool:
    return EXPLANATION_CLAIM_RE.search(text) is not None


def is_proof_context(text: str) -> bool:
    return PROOF_CONTEXT_RE.search(text) is not None


def completion_polarity(text: str) -> str:
    """Return asserted, negated, prospective, or none for completion language."""
    latest: tuple[int, str] | None = None
    ordered_terms = sorted(set(COMPLETION_TERMS), key=len, reverse=True)
    for clause_match in CLAUSE_RE.finditer(text):
        clause = clause_match.group(0)
        mentions: list[tuple[int, int, str]] = []
        for term in ordered_terms:
            mentions.extend((match.start(), match.end(), term) for match in re.finditer(re.escape(term), clause))
        mentions = [
            mention
            for mention in mentions
            if not any(
                other_start <= mention[0]
                and mention[1] <= other_end
                and (other_end - other_start) > (mention[1] - mention[0])
                for other_start, other_end, _other_term in mentions
            )
        ]
        for start, end, _term in sorted(mentions, key=lambda item: (item[1], item[0])):
            global_start = clause_match.start() + start
            global_end = clause_match.start() + end
            prefix = clause[max(0, start - 28):start]
            suffix = clause[end:end + 14]
            sentence_prefix = re.split(r"[。；！？!?\n]", text[:global_start])[-1][-56:]
            if any(suffix.startswith(marker) for marker in COMPLETION_NOMINAL_SUFFIXES):
                state = "none"
            elif any(marker in suffix for marker in ["吗", "么", "没有", "没", "是否"]):
                state = "none"
            elif COMPLETION_PARTIAL_RE.search(clause[max(0, start - 18):min(len(clause), end + 18)]):
                state = "prospective"
            elif COMPLETION_NEGATION_RE.search(prefix):
                state = "negated"
            elif (
                COMPLETION_PROSPECTIVE_RE.search(prefix)
                or any(marker in sentence_prefix for marker in ["如果", "只要", "一旦"])
                or any(suffix.startswith(marker) for marker in COMPLETION_PROSPECTIVE_SUFFIXES)
            ):
                state = "prospective"
            else:
                state = "asserted"
            latest = (global_end, state)
    return latest[1] if latest else "none"


CTA_ACTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("reply", re.compile(r"(?:评论区|评论里|评论中|下方)\s*回复|回复关键词")),
    ("comment", re.compile(r"(?:在)?(?:评论区|评论里|评论中|下方)(?:里|中)?\s*(?:扣|留言|告诉我|输入|打(?:个)?|发)")),
    ("direct-message", re.compile(r"(?:可以|欢迎|直接|就)?\s*私信我|私信领取")),
    ("follow", re.compile(r"关注(?:我|一下|账号)|点个关注|点一下关注|(?:记得|别忘了|不要忘记)\s*关注(?:我|一下)?")),
    ("save", re.compile(r"收藏(?:这一条|这条)|(?:记得|别忘了|不要忘记|建议|可以)\s*收藏(?:这一条|这条)?")),
    ("like", re.compile(r"点赞(?:这条|这一条)|点个赞|(?:记得|别忘了|不要忘记|帮我)\s*点赞")),
    ("share", re.compile(r"(?:转发|分享)给(?:需要的)?(?:朋友|同事|家人|团队)")),
    ("claim", re.compile(r"(?:直接|点击)领取|领取(?:这套|这个|模板|流程|规则)")),
    ("claim", re.compile(r"(?:想要|需要)[^，。！？]{0,12}(?:可以|就|可)?\s*(?:自提|自行提取)")),
)
CTA_DESCRIPTION_RE = re.compile(
    r"(?:页面|后台|数据|报表)[^，。！？]{0,16}(?:评论区|互动|回复|留言)"
    r"|(?:评论区|互动|回复|留言)[^，。！？]{0,16}(?:数据|数量|功能|速度|内容|质量|由客服|已经上线)"
    r"|(?:门店|商家|商品)[^，。！？]{0,12}(?:支持|提供)[^，。！？]{0,8}(?:到店)?自提"
    r"|(?:输入|搜索|填写|设置|使用)关键词[^，。！？]{0,18}(?:生成|分析|检索|标题|竞品|搜索引擎)"
)
CTA_META_TERMS = ("脚本", "测试", "示例", "反例", "按钮文案", "违禁词", "词库", "功能名称")
CTA_NON_DIRECTIVE_PREFIX_RE = re.compile(
    r"(?:不要|别|无需|不必|没有|尚未|并未|不是|并不是|从未|并没有|还没有|没必要|没打算|从来没)"
    r"[^，。！？]{0,10}$"
    r"|(?:已经|刚刚|刚才|一直|正在|知道|因为|感谢|看到|都)[^，。！？]{0,8}$"
)
CTA_DESCRIPTION_SUFFIX_RE = re.compile(
    r"^(?:率|功能|数量|速度|内容|质量|按钮|输入框|框|由客服|已经上线|太多|很多|很及时|得很及时|了一条公告|了很多用户|会自动保存|是这个功能|在右上角|在右侧)"
)


def _cta_keyword(text: str, action_kind: str, action_end: int) -> str:
    if action_kind not in {"reply", "comment"}:
        return ""
    tail = text[action_end:]
    tail = re.sub(r"^(?:关键词)?\s*[:：]?\s*", "", tail)
    quoted = re.match(r"[“\"‘']([^”\"’']{1,16})[”\"’']", tail)
    if quoted:
        return quoted.group(1).strip()
    value = re.split(r"(?:领取|获取|拿到|我把|我发|发你|发给|，|。|；|！|？)", tail, maxsplit=1)[0].strip()
    value = re.sub(r"^(?:个|一个)\s*", "", value)
    if 1 <= len(value) <= 12 and value not in {"我", "你的看法", "你的问题", "你的案例"}:
        return value
    return ""


def viewer_cta_signal(text: str) -> dict[str, Any] | None:
    """Parse one explicit viewer action; bare CTA nouns and descriptions return None."""
    if CTA_DESCRIPTION_RE.search(text):
        return None
    candidates: list[tuple[int, str, re.Match[str]]] = []
    for action_kind, pattern in CTA_ACTION_PATTERNS:
        for match in pattern.finditer(text):
            clause_start = max(text.rfind(mark, 0, match.start()) for mark in "，。；！？!?") + 1
            following_marks = [position for mark in "，。；！？!?" if (position := text.find(mark, match.end())) >= 0]
            clause_end = min(following_marks) if following_marks else len(text)
            clause = text[clause_start:clause_end]
            if any(term in clause for term in CTA_META_TERMS):
                continue
            prefix = text[max(0, match.start() - 14):match.start()]
            if CTA_NON_DIRECTIVE_PREFIX_RE.search(prefix):
                continue
            suffix = text[match.end():match.end() + 16].lstrip()
            if CTA_DESCRIPTION_SUFFIX_RE.search(suffix):
                continue
            candidates.append((match.start(), action_kind, match))
    if not candidates:
        return None
    _start, action_kind, match = sorted(candidates, key=lambda item: item[0])[0]
    action = match.group(0).strip()
    keyword = _cta_keyword(text, action_kind, match.end())
    result: dict[str, Any] = {
        "actionKind": action_kind,
        "action": action,
        "sourceText": text.strip(),
    }
    if keyword:
        result["keyword"] = keyword
    return result
