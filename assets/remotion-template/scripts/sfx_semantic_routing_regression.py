#!/usr/bin/env python3
"""Regression checks for V4 semantic SFX suggestions."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import semantic_router  # noqa: E402
import semantic_router_regression  # noqa: E402
import visual_event_builder  # noqa: E402
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()


EXPECTED: dict[str, dict[str, str]] = {
    "hook-01": {"intent": "title_impact", "sfxId": "title_impact_whoosh_01"},
    "negative-01": {"intent": "negative_warning", "sfxId": "negative_warning_01"},
    "positive-01": {"intent": "confirm", "sfxId": "confirm_ding_01"},
    "handoff-01": {"intent": "automation_handoff", "sfxId": "automation_handoff_01"},
    "numeric-01": {"intent": "data_count", "sfxId": "data_count_01"},
    "proof-01": {"intent": "proof_reveal", "sfxId": "proof_reveal_01"},
}

DIRECT_RESULT_CASES: list[dict[str, str]] = [
    {"id": "result-confirm-correct", "text": "结果正确", "semanticIntent": "positive-confirm", "sfxIntent": "confirm", "sfxId": "confirm_ding_01"},
    {"id": "result-confirm-validation", "text": "验证通过", "semanticIntent": "positive-confirm", "sfxIntent": "confirm", "sfxId": "confirm_ding_01"},
    {"id": "result-confirm-success", "text": "执行成功", "semanticIntent": "positive-confirm", "sfxIntent": "confirm", "sfxId": "confirm_ding_01"},
    {"id": "result-confirm-no-error", "text": "没有错误", "semanticIntent": "positive-confirm", "sfxIntent": "confirm", "sfxId": "confirm_ding_01"},
    {"id": "result-confirm-zero-failure", "text": "失败项为0", "semanticIntent": "positive-confirm", "sfxIntent": "confirm", "sfxId": "confirm_ding_01"},
    {"id": "result-warning-error", "text": "这一步出错了", "semanticIntent": "negative-friction", "sfxIntent": "negative_warning", "sfxId": "negative_warning_01"},
    {"id": "result-warning-failure", "text": "执行失败了", "semanticIntent": "negative-friction", "sfxIntent": "negative_warning", "sfxId": "negative_warning_01"},
    {"id": "result-warning-incorrect", "text": "结果不正确", "semanticIntent": "negative-friction", "sfxIntent": "negative_warning", "sfxId": "negative_warning_01"},
    {"id": "result-none-question", "text": "结果是否正确", "semanticIntent": "", "sfxIntent": "", "sfxId": ""},
    {"id": "result-none-possible", "text": "这一步可能出错", "semanticIntent": "", "sfxIntent": "", "sfxId": ""},
    {"id": "result-none-avoid", "text": "这里要避免错误", "semanticIntent": "", "sfxIntent": "", "sfxId": ""},
]


def case_by_id(case_id: str) -> dict[str, str]:
    for case in semantic_router_regression.CASES:
        if case.get("id") == case_id:
            return case
    raise KeyError(case_id)


def first_sfx_cue(data: dict[str, Any], expected_intent: str) -> dict[str, Any] | None:
    for cue in data.get("audioCues", []):
        if isinstance(cue, dict) and cue.get("type") == "sfx" and cue.get("sfxIntent") == expected_intent:
            return cue
    return None


def assert_fps_duration_scaling() -> None:
    case = case_by_id("hook-01")
    duration_sec = float(visual_event_builder.SFX_SUGGESTIONS["title_impact"]["durationSec"])
    if duration_sec <= 0:
        raise AssertionError("title_impact manifest must define durationSec")
    for index, fps in enumerate((25, 30, 60), start=100):
        data = semantic_router_regression.visual_script_for_case(case, index)
        data["composition"]["fps"] = fps
        semantic_router.apply_semantic_beats(data)
        visual_event_builder.apply_visual_events(data)
        cue = first_sfx_cue(data, "title_impact")
        expected_frames = math.ceil(duration_sec * fps - 1e-9)
        actual_frames = int((cue or {}).get("durationFrames", 0) or 0)
        if actual_frames != expected_frames:
            raise AssertionError(
                f"title_impact duration must follow composition fps: "
                f"fps={fps} expected={expected_frames} actual={actual_frames}"
            )
        print(f"PASS fps-duration-{fps}: {duration_sec:.3f}s -> {actual_frames}f")


def run_case(case_id: str, index: int) -> dict[str, Any]:
    case = case_by_id(case_id)
    expected = EXPECTED[case_id]
    data = semantic_router_regression.visual_script_for_case(case, index)
    semantic_router.apply_semantic_beats(data)
    visual_event_builder.apply_visual_events(data)
    cue = first_sfx_cue(data, expected["intent"])
    actual_sfx_id = str((cue or {}).get("sfxId") or "")
    actual_status = str((cue or {}).get("status") or "")
    actual_path = str((cue or {}).get("path") or "")
    actual_volume_db = (cue or {}).get("volumeDb")
    ok = (
        cue is not None
        and actual_sfx_id == expected["sfxId"]
        and actual_status == "suggested"
        and bool(actual_path)
        and actual_volume_db == -5
    )
    return {
        "id": case_id,
        "semanticIntent": data["semanticBeats"][0].get("semanticIntent"),
        "expectedSfxIntent": expected["intent"],
        "actualSfxIntent": str((cue or {}).get("sfxIntent") or ""),
        "expectedSfxId": expected["sfxId"],
        "actualSfxId": actual_sfx_id,
        "status": actual_status,
        "path": actual_path,
        "volumeDb": actual_volume_db,
        "ok": ok,
    }


def run_direct_result_case(case: dict[str, str], index: int) -> dict[str, Any]:
    data = semantic_router_regression.visual_script_for_case(case, index)
    semantic_router.apply_semantic_beats(data)
    visual_event_builder.apply_visual_events(data)
    sfx_cues = [
        cue for cue in data.get("audioCues", [])
        if isinstance(cue, dict) and cue.get("type") == "sfx"
    ]
    expected_intent = case["sfxIntent"]
    cue = first_sfx_cue(data, expected_intent) if expected_intent else None
    actual_semantic_intent = str(data["semanticBeats"][0].get("semanticIntent") or "")
    actual_sfx_intent = str((cue or {}).get("sfxIntent") or "")
    actual_sfx_id = str((cue or {}).get("sfxId") or "")
    actual_volume_db = (cue or {}).get("volumeDb")
    if expected_intent:
        ok = (
            actual_semantic_intent == case["semanticIntent"]
            and actual_sfx_intent == expected_intent
            and actual_sfx_id == case["sfxId"]
            and str((cue or {}).get("status") or "") == "suggested"
            and actual_volume_db == -5
        )
    else:
        ok = not sfx_cues
    return {
        "id": case["id"],
        "semanticIntent": actual_semantic_intent,
        "expectedSfxIntent": expected_intent or "none",
        "actualSfxIntent": actual_sfx_intent,
        "expectedSfxId": case["sfxId"],
        "actualSfxId": actual_sfx_id,
        "status": str((cue or {}).get("status") or ""),
        "path": str((cue or {}).get("path") or ""),
        "volumeDb": actual_volume_db,
        "ok": ok,
    }


def main() -> int:
    assert_fps_duration_scaling()
    results = [run_case(case_id, index) for index, case_id in enumerate(EXPECTED)]
    direct_start = len(results)
    results.extend(
        run_direct_result_case(case, direct_start + index)
        for index, case in enumerate(DIRECT_RESULT_CASES)
    )
    failed = [item for item in results if not item["ok"]]
    for item in results:
        marker = "PASS" if item["ok"] else "MISS"
        print(f"{marker} {item['id']}: {item['actualSfxIntent']} -> {item['actualSfxId']} ({item['status']})")

    report_path = SCRIPT_DIR.parent / "qa" / "sfx_semantic_routing_regression.json"
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
