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
    {"id": "handoff-asserted", "check": "handoff", "text": "把素材交给 Codex 自动完成", "expected": "asserted"},
    {"id": "handoff-negated", "check": "handoff", "text": "Codex 还没有接管这一步", "expected": "negated"},
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
