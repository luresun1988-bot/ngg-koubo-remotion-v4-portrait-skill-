#!/usr/bin/env python3
"""Run the shared semantic contract through the current format adapter."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import semantic_router  # noqa: E402
import semantic_guardrails  # noqa: E402
import validate_visual_script  # noqa: E402
import visual_event_builder  # noqa: E402
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()
FORMAT = "portrait" if "portrait" in SKILL_ROOT.name.lower() else "landscape"


def fixture(case: dict[str, Any]) -> dict[str, Any]:
    portrait = FORMAT == "portrait"
    texts = [str(item) for item in case.get("cues", []) if str(item)] or [str(case["text"])]
    cue_frames = 75 if len(texts) > 1 else 150
    cues = [
        {
            "id": f"cap-{index + 1:03d}",
            "sceneId": "scene-001",
            "startFrame": index * cue_frames,
            "endFrame": (index + 1) * cue_frames,
            "text": text,
        }
        for index, text in enumerate(texts)
    ]
    duration = max(180, len(texts) * cue_frames)
    return {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait" if portrait else "ngg-koubo-remotion-v4",
        "sourceVideoMode": "raw-presenter",
        "composition": {"format": "9:16" if portrait else "16:9", "width": 1080 if portrait else 1920, "height": 1920 if portrait else 1080, "fps": 25, "durationFrames": duration},
        "captionTimeline": {"sourceType": "alignment-json", "sourcePath": "qa/semantic_contract_fixture.json", "method": "sentence-timecodes", "generatedBy": "project-alignment"},
        "researchNotes": [],
        "media": [],
        "scenes": [{"id":"scene-001","type":"Explanation","startFrame":0,"endFrame":duration,"semanticRole":"","presenterLayout":"large","materialLayout":"none","sourceVideo":"input/semantic_contract_presenter.mp4","narrationText":"，".join(texts)}],
        "captionCues": cues,
        "semanticBeats": [], "visualEvents": [], "audioCues": [], "qaFrames": [],
    }


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    data = fixture(case)
    semantic_router.apply_semantic_beats(data)
    visual_event_builder.apply_visual_events(data)
    with tempfile.TemporaryDirectory(prefix="ngg-v4-semantic-contract-") as temp_dir:
        fixture_path = Path(temp_dir) / "visual_script.json"
        fixture_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        schema_errors, _schema_warnings = validate_visual_script.validate(fixture_path)
    beat = data["semanticBeats"][0]
    event = next(item for item in data["visualEvents"] if item.get("type") != "cornerChapterLabel" and item.get("sourceBeatId") == beat.get("id"))
    adapter = case["adapters"][FORMAT]
    expected_modifiers = [str(item) for item in case.get("modifiersContain", [])]
    expected_checks = [str(item) for item in case.get("checksContain", [])]
    actual_modifiers = [str(item) for item in beat.get("semanticModifiers", [])]
    actual_checks = [str(item) for item in beat.get("requiredChecks", [])]
    provenance = event.get("ctaProvenance") if isinstance(event.get("ctaProvenance"), dict) else {}
    expected_keyword = str(case.get("ctaKeyword") or "")
    beat_step_labels = [str(item.get("label") or "") for item in beat.get("internalSteps", []) if isinstance(item, dict)]
    event_step_labels = [str(item.get("label") or "") for item in event.get("internalSteps", []) if isinstance(item, dict)]
    sfx_intents = [
        str(item.get("sfxIntent") or "")
        for item in data.get("audioCues", [])
        if isinstance(item, dict) and item.get("sourceBeatId") == beat.get("id")
    ]
    expected_source_cues = [str(item) for item in case.get("sourceCueIds", [])]
    expected_step_labels = [str(item) for item in case.get("stepLabels", [])]
    expected_sfx = [str(item) for item in case.get("sfxIntents", [])]
    forbidden_sfx = [str(item) for item in case.get("forbiddenSfxIntents", [])]
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
        "beatCount": not case.get("expectedBeatCount") or len(data["semanticBeats"]) == int(case["expectedBeatCount"]),
        "sourceCueIds": not expected_source_cues or beat.get("sourceCueIds") == expected_source_cues,
        "beatStepLabels": not expected_step_labels or beat_step_labels == expected_step_labels,
        "eventStepLabels": not expected_step_labels or event_step_labels == expected_step_labels,
        "fallbackRequired": not case.get("fallbackRequired") or accepted_fallback,
        "sfxIntents": "sfxIntents" not in case or sfx_intents == expected_sfx,
        "forbiddenSfx": all(item not in sfx_intents for item in forbidden_sfx),
        "numericValue": "numericValue" not in case or event.get("numericValue") == case.get("numericValue"),
        "numericSuffix": "numericSuffix" not in case or event.get("numericSuffix") == case.get("numericSuffix"),
        "schemaValidation": not schema_errors,
    }
    return {"id":case["id"],"format":FORMAT,"expectedIntent":case["intent"],"actualIntent":beat.get("semanticIntent"),"expectedEventType":adapter["eventType"],"actualEventType":event.get("type"),"acceptedFallback":accepted_fallback,"fallbackReason":str(event.get("fallbackReason") or ""),"sourceCueIds":beat.get("sourceCueIds"),"beatStepLabels":beat_step_labels,"eventStepLabels":event_step_labels,"sfxIntents":sfx_intents,"schemaErrors":schema_errors,"checks":checks,"ok":all(checks.values())}


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
