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
    if any(term in text for term in COMPLETION_HARD_FAILURE_TERMS):
        return True
    for term in COMPLETION_SOFT_FAILURE_TERMS:
        for match in re.finditer(re.escape(term), text):
            prefix = text[max(0, match.start() - 10):match.start()]
            suffix = text[match.end():match.end() + 10]
            if re.search(r"(?:没有|并无|无(?:任何)?|未发现|不存在|不再)\s*$", prefix):
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
