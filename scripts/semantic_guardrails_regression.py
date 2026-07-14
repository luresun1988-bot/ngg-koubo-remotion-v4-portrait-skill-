#!/usr/bin/env python3
"""Regression contract for format-agnostic V4 semantic guards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import semantic_guardrails as guards
from v4_utf8 import configure_utf8


configure_utf8()
SCRIPT_DIR = Path(__file__).resolve().parent


def actual_for(case: dict[str, Any]) -> Any:
    text = str(case["text"])
    check = str(case["check"])
    if check == "completion":
        return guards.completion_polarity(text)
    if check == "result-evaluation":
        evaluation = guards.result_evaluation(text)
        return str((evaluation or {}).get("polarity") or "none")
    if check == "handoff":
        return guards.handoff_state(text)
    if check == "future":
        return bool(guards.future_preview(text))
    if check == "topic":
        return bool(guards.topic_intro(text))
    if check == "process":
        return guards.is_process_context(text)
    if check == "proof":
        return guards.is_proof_context(text)
    if check == "numeric-token":
        return guards.numeric_metric_token(text)
    if check == "numeric-meaningful":
        return guards.numeric_metric_is_meaningful(text)
    if check == "numeric-fields":
        return guards.numeric_event_fields(text)
    if check == "ordered-workflow":
        cues = [
            {"id": "cap-001", "sceneId": "scene-001", "startFrame": 0, "endFrame": 75, "text": "首先读取逐字稿"},
            {"id": "cap-002", "sceneId": "scene-001", "startFrame": 75, "endFrame": 150, "text": "然后判断语义"},
            {"id": "cap-003", "sceneId": "scene-001", "startFrame": 150, "endFrame": 225, "text": "最后写入时间线"},
        ]
        result = guards.ordered_workflow_window(cues, 0, max_gap_frames=65, max_duration_frames=500)
        return [str(item.get("label") or "") for item in (result or ([], []))[1]]
    if check == "explanation":
        return guards.is_explanation_claim(text)
    if check == "cta":
        signal = guards.viewer_cta_signal(text)
        if case["expected"] is None:
            return None if signal is None else signal
        return {
            "actionKind": str((signal or {}).get("actionKind") or ""),
            "action": str((signal or {}).get("action") or ""),
            "keyword": str((signal or {}).get("keyword") or ""),
        }
    raise AssertionError(f"unknown check: {check}")


CASES: list[dict[str, Any]] = [
    {"id": "complete-asserted", "check": "completion", "text": "10张详情图已经全部生成好了", "expected": "asserted"},
    {"id": "complete-negated-numeric", "check": "completion", "text": "10张详情图还没生成完", "expected": "negated"},
    {"id": "complete-negated", "check": "completion", "text": "现在还没有生成完成", "expected": "negated"},
    {"id": "complete-conditional", "check": "completion", "text": "如果完成设置，就可以导出", "expected": "prospective"},
    {"id": "complete-nominal", "check": "completion", "text": "完成按钮在右上角", "expected": "none"},
    {"id": "complete-handoff", "check": "completion", "text": "把素材交给 Codex 自动完成", "expected": "prospective"},
    {"id": "complete-later-incorrect", "check": "completion", "text": "任务完成了，但结果不正确", "expected": "negated"},
    {"id": "complete-latest-wins", "check": "completion", "text": "执行失败，但任务已经完成", "expected": "asserted"},
    {"id": "complete-avoid-error", "check": "completion", "text": "任务完成了，接着检查以免出错", "expected": "asserted"},
    {"id": "result-positive-correct", "check": "result-evaluation", "text": "结果正确", "expected": "positive"},
    {"id": "result-positive-validation", "check": "result-evaluation", "text": "验证通过", "expected": "positive"},
    {"id": "result-positive-execution", "check": "result-evaluation", "text": "执行成功", "expected": "positive"},
    {"id": "result-positive-no-error", "check": "result-evaluation", "text": "没有错误", "expected": "positive"},
    {"id": "result-positive-zero-failure", "check": "result-evaluation", "text": "失败项为0", "expected": "positive"},
    {"id": "result-positive-zero-error", "check": "result-evaluation", "text": "报错数为零", "expected": "positive"},
    {"id": "result-positive-latest", "check": "result-evaluation", "text": "之前执行失败，现在验证通过", "expected": "positive"},
    {"id": "result-negative-error", "check": "result-evaluation", "text": "这一步出错了", "expected": "negative"},
    {"id": "result-negative-failure", "check": "result-evaluation", "text": "执行失败了", "expected": "negative"},
    {"id": "result-negative-incorrect", "check": "result-evaluation", "text": "结果不正确", "expected": "negative"},
    {"id": "result-negative-judgement", "check": "result-evaluation", "text": "这是错误的", "expected": "negative"},
    {"id": "result-negative-validation", "check": "result-evaluation", "text": "验证没有通过", "expected": "negative"},
    {"id": "result-negative-no-success", "check": "result-evaluation", "text": "执行没有成功", "expected": "negative"},
    {"id": "result-negative-latest", "check": "result-evaluation", "text": "验证通过，但最终执行失败", "expected": "negative"},
    {"id": "result-none-question", "check": "result-evaluation", "text": "结果是否正确", "expected": "none"},
    {"id": "result-none-possible", "check": "result-evaluation", "text": "这一步可能出错", "expected": "none"},
    {"id": "result-none-avoid", "check": "result-evaluation", "text": "这里要避免错误", "expected": "none"},
    {"id": "result-none-easy-error", "check": "result-evaluation", "text": "这个环节容易出错", "expected": "none"},
    {"id": "result-none-meta-error", "check": "result-evaluation", "text": "这是错误的示例", "expected": "none"},
    {"id": "result-none-meta-success", "check": "result-evaluation", "text": "成功按钮在右侧", "expected": "none"},
    {"id": "result-none-conditional", "check": "result-evaluation", "text": "如果验证通过，就可以导出", "expected": "none"},
    {"id": "result-none-prospective", "check": "result-evaluation", "text": "验证通过后再发布", "expected": "none"},
    {"id": "handoff-asserted", "check": "handoff", "text": "把素材交给 Codex 自动完成", "expected": "asserted"},
    {"id": "handoff-negated", "check": "handoff", "text": "Codex 还没有接管这一步", "expected": "negated"},
    {"id": "handoff-prior", "check": "handoff", "text": "交给 Codex 之前，先检查素材", "expected": "prior"},
    {"id": "numeric-chinese-token", "check": "numeric-token", "text": "十张详情图还没生成完", "expected": "十张"},
    {"id": "numeric-chinese-meaningful", "check": "numeric-meaningful", "text": "十张详情图还没生成完", "expected": True},
    {"id": "numeric-chinese-fields", "check": "numeric-fields", "text": "十张详情图已经生成好了", "expected": {"numericValue": 10, "numericPrefix": "", "numericSuffix": "张"}},
    {"id": "proof-see-backend", "check": "proof", "text": "你看后台，十张详情图已经生成好了", "expected": True},
    {"id": "ordered-workflow", "check": "ordered-workflow", "text": "首先读取逐字稿，然后判断语义，最后写入时间线", "expected": ["读取逐字稿", "判断语义", "写入时间线"]},
    {"id": "future-preview", "check": "future", "text": "下一期介绍 Codex 自动剪辑", "expected": True},
    {"id": "topic-intro", "check": "topic", "text": "这一期聊聊数字人为什么模糊", "expected": True},
    {"id": "explicit-cta", "check": "cta", "text": "评论区回复数字人领取模板", "expected": {"actionKind": "reply", "action": "评论区回复", "keyword": "数字人"}},
    {"id": "comment-proof-not-cta", "check": "cta", "text": "页面展示了评论区互动数据", "expected": None},
    {"id": "keyword-process-not-cta", "check": "cta", "text": "输入关键词生成标题", "expected": None},
    {"id": "pickup-claim-not-cta", "check": "cta", "text": "这家门店支持到店自提", "expected": None},
    {"id": "conditional-process", "check": "process", "text": "如果完成设置，就可以导出", "expected": True},
    {"id": "keyword-process", "check": "process", "text": "输入关键词生成标题", "expected": True},
    {"id": "comment-proof", "check": "proof", "text": "页面展示了评论区互动数据", "expected": True},
    {"id": "pickup-explanation", "check": "explanation", "text": "这家门店支持到店自提", "expected": True},
    {"id": "tool-explanation", "check": "explanation", "text": "Topaz Video AI 是高清修复工具", "expected": True},
    {"id": "cta-meta-guard", "check": "cta", "text": "测试脚本里用“私信我”作为反例", "expected": None},
    {"id": "cta-follow-description", "check": "cta", "text": "你已经关注我了", "expected": None},
    {"id": "cta-comment-description", "check": "cta", "text": "评论区回复率提高了 30%", "expected": None},
    {"id": "cta-share-description", "check": "cta", "text": "分享给朋友是这个功能的核心", "expected": None},
    {"id": "cta-input-description", "check": "cta", "text": "下方输入框在右侧", "expected": None},
]


def main() -> int:
    results: list[dict[str, Any]] = []
    for case in CASES:
        actual = actual_for(case)
        ok = actual == case["expected"]
        results.append({**case, "actual": actual, "ok": ok})
        print(f"{'PASS' if ok else 'MISS'} {case['id']}: {actual}")
    report = SCRIPT_DIR.parent / "qa" / "semantic_guardrails_regression.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = [item for item in results if not item["ok"]]
    print(f"wrote {report}")
    print(f"passed: {len(results) - len(failed)} / {len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
