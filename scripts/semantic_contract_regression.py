#!/usr/bin/env python3
"""Run the shared semantic contract through the current format adapter."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import semantic_router  # noqa: E402
import semantic_guardrails  # noqa: E402
import visual_event_builder  # noqa: E402
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()
FORMAT = "portrait" if "portrait" in SKILL_ROOT.name.lower() else "landscape"


def fixture(text: str) -> dict[str, Any]:
    portrait = FORMAT == "portrait"
    return {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait" if portrait else "ngg-koubo-remotion-v4",
        "composition": {"format": "9:16" if portrait else "16:9", "width": 1080 if portrait else 1920, "height": 1920 if portrait else 1080, "fps": 25, "durationFrames": 180},
        "media": [],
        "scenes": [{"id":"scene-001","type":"Explanation","startFrame":0,"endFrame":150,"semanticRole":"","presenterLayout":"large","materialLayout":"none","narrationText":text}],
        "captionCues": [{"id":"cap-001","sceneId":"scene-001","startFrame":0,"endFrame":150,"text":text}],
        "semanticBeats": [], "visualEvents": [], "audioCues": [], "qaFrames": [],
    }


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    data = fixture(str(case["text"]))
    semantic_router.apply_semantic_beats(data)
    visual_event_builder.apply_visual_events(data)
    beat = data["semanticBeats"][0]
    event = next(item for item in data["visualEvents"] if item.get("type") != "cornerChapterLabel")
    adapter = case["adapters"][FORMAT]
    expected_modifiers = [str(item) for item in case.get("modifiersContain", [])]
    expected_checks = [str(item) for item in case.get("checksContain", [])]
    actual_modifiers = [str(item) for item in beat.get("semanticModifiers", [])]
    actual_checks = [str(item) for item in beat.get("requiredChecks", [])]
    provenance = event.get("ctaProvenance") if isinstance(event.get("ctaProvenance"), dict) else {}
    expected_keyword = str(case.get("ctaKeyword") or "")
    accepted_fallback = (
        event.get("type") == "captionHighlight"
        and event.get("semanticFallbackFrom") == case["intent"]
        and bool(str(event.get("fallbackReason") or ""))
    )
    checks = {
        "intent": beat.get("semanticIntent") == case["intent"],
        "visualForm": beat.get("visualForm") == adapter["visualForm"],
        "eventType": event.get("type") == adapter["eventType"] or accepted_fallback,
        "modifiers": all(item in actual_modifiers for item in expected_modifiers),
        "requiredChecks": all(item in actual_checks for item in expected_checks),
        "ctaKeyword": not expected_keyword or provenance.get("keyword") == expected_keyword,
        "eventStatus": not adapter.get("eventStatus") or event.get("status") == adapter["eventStatus"],
        "eventText": not adapter.get("eventText") or event.get("text") == adapter["eventText"],
        "eventSubtext": not adapter.get("eventSubtext") or event.get("subtext") == adapter["eventSubtext"],
    }
    return {"id":case["id"],"format":FORMAT,"expectedIntent":case["intent"],"actualIntent":beat.get("semanticIntent"),"expectedEventType":adapter["eventType"],"actualEventType":event.get("type"),"acceptedFallback":accepted_fallback,"fallbackReason":str(event.get("fallbackReason") or ""),"checks":checks,"ok":all(checks.values())}


def main() -> int:
    if semantic_router.completion_polarity is not semantic_guardrails.completion_polarity:
        raise AssertionError("router completion logic is not bound to the shared semantic core")
    if semantic_router.parse_cta_provenance is not semantic_guardrails.parse_cta_provenance:
        raise AssertionError("router CTA logic is not bound to the shared semantic core")
    if semantic_router.result_evaluation is not semantic_guardrails.result_evaluation:
        raise AssertionError("router result-evaluation logic is not bound to the shared semantic core")
    contract = json.loads((SCRIPT_DIR / "semantic_contract_cases.json").read_text(encoding="utf-8-sig"))
    results = [run_case(case) for case in contract.get("cases", [])]
    for item in results:
        print(f"{'PASS' if item['ok'] else 'MISS'} {item['id']}: {item['actualIntent']} -> {item['actualEventType']}")
    report = SKILL_ROOT / "qa" / f"semantic_contract_{FORMAT}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = [item for item in results if not item["ok"]]
    print(f"shared semantic contract: {len(results) - len(failed)} / {len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
