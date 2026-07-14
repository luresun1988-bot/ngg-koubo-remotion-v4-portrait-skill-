#!/usr/bin/env python3
"""Regression coverage for source-bound transformation events."""

from __future__ import annotations

from copy import deepcopy

from qa_lint_visual_script import layered_hud_step_checks, semantic_beat_fulfillment_checks
from visual_event_builder import event_for_beat


def fixture(
    cue_texts: list[tuple[str, str]],
    *,
    source_ids: list[str] | None = None,
) -> tuple[dict, dict]:
    cues = [
        {
            "id": cue_id,
            "sceneId": "scene-01",
            "startFrame": index * 80,
            "endFrame": (index + 1) * 80,
            "text": text,
        }
        for index, (cue_id, text) in enumerate(cue_texts)
    ]
    owned_ids = source_ids or [str(cue["id"]) for cue in cues]
    owned_texts = [str(cue["text"]) for cue in cues if str(cue["id"]) in owned_ids]
    beat = {
        "id": "beat-transform",
        "sceneId": "scene-01",
        "startFrame": 0,
        "endFrame": max(120, len(cues) * 80),
        "text": "。".join(owned_texts),
        "semanticIntent": "transformation-stack",
        "visualForm": "transformationStack",
        "sourceCueIds": owned_ids,
        "confidence": 0.95,
    }
    data = {
        "captionCues": cues,
        "semanticBeats": [beat],
        "visualEvents": [],
        "scenes": [{"id": "scene-01", "startFrame": 0, "endFrame": beat["endFrame"]}],
        "media": [],
    }
    return beat, data


def full_evidence_fixture() -> tuple[dict, dict]:
    return fixture(
        [
            ("cap-driver", "通过自动化推动这次升级"),
            ("cap-relation", "把个人经验变成团队流程"),
            ("cap-result", "最终实现稳定交付"),
        ]
    )


def assert_full_evidence_event() -> None:
    beat, data = full_evidence_fixture()
    event = event_for_beat(beat, data)
    assert event is not None
    assert event["type"] == "transformationStack", event
    assert event["text"] == "个人经验 → 团队流程", event
    assert event["subtext"] == "自动化", event
    assert event["transformationSourceCueIds"] == ["cap-relation", "cap-driver", "cap-result"], event
    assert [step.get("role") for step in event["internalSteps"]] == [
        "source",
        "target",
        "driver",
        "result",
    ]
    assert event["internalSteps"][-1]["label"] == "稳定交付"
    assert "达成" not in str(event)
    caption_texts = {str(cue["id"]): str(cue["text"]) for cue in data["captionCues"]}
    for step in event["internalSteps"]:
        assert step["sourceCueIds"], step
        assert step["label"] in step["text"], step
        assert any(step["text"] in caption_texts[cue_id] for cue_id in step["sourceCueIds"]), step
    data["visualEvents"] = [event]
    assert layered_hud_step_checks(data)[0] == []
    assert semantic_beat_fulfillment_checks(data)[0] == []


def assert_customer_case_falls_back_without_result() -> None:
    beat, data = fixture(
        [
            ("cap-driver", "我们把氛围、设备和搭子都准备好了"),
            ("cap-relation", "来我们新店，把一个人的熬夜，变成一群人的主场！"),
        ]
    )
    event = event_for_beat(beat, data)
    assert event is not None
    assert event["type"] == "captionHighlight", event
    assert event["fallbackReason"] == "missing-result", event
    assert "主场达成" not in str(event)


def assert_uncited_previous_cue_is_ignored() -> None:
    beat, data = fixture(
        [
            ("cap-previous", "我们通过自动化推动这次升级"),
            ("cap-current", "把个人经验变成团队流程，最终实现稳定交付"),
        ],
        source_ids=["cap-current"],
    )
    event = event_for_beat(beat, data)
    assert event is not None
    assert event["type"] == "captionHighlight", event
    assert event["fallbackReason"] == "missing-driver", event
    assert "cap-previous" not in str(event)


def assert_incomplete_evidence_fallbacks() -> None:
    cases = [
        ("把个人经验变成团队流程", "missing-driver"),
        ("通过自动化，把个人经验变成团队流程", "missing-result"),
        ("把个人经验变成团队流程，最终实现稳定交付", "missing-driver"),
        ("通过自动化推动升级，最终实现稳定交付", "missing-source-target"),
    ]
    for text, expected_reason in cases:
        beat, data = fixture([("cap-only", text)])
        event = event_for_beat(beat, data)
        assert event is not None
        assert event["type"] == "captionHighlight", event
        assert event["semanticFallbackFrom"] == "transformation-stack"
        assert event["fallbackReason"] == expected_reason, event
        assert "自动执行" not in str(event)
        assert "能力转化" not in str(event)
        data["visualEvents"] = [event]
        errors, warnings = semantic_beat_fulfillment_checks(data)
        assert errors == [], errors
        assert any(expected_reason in item for item in warnings), warnings


def assert_qa_rejects_provenance_tampering() -> None:
    beat, data = full_evidence_fixture()
    event = event_for_beat(beat, data)
    assert event is not None and event["type"] == "transformationStack"

    invented = deepcopy(event)
    invented["internalSteps"][-1]["label"] = "稳定交付达成"
    data["visualEvents"] = [invented]
    errors, _ = layered_hud_step_checks(data)
    assert any("transformation-label-source-binding" in item for item in errors), errors

    uncited = deepcopy(event)
    uncited["internalSteps"][2]["sourceCueIds"] = ["cap-outside"]
    data["visualEvents"] = [uncited]
    errors, _ = layered_hud_step_checks(data)
    assert any("not owned by its source beat" in item for item in errors), errors
    assert any("missing caption" in item for item in errors), errors

    wrong_union = deepcopy(event)
    wrong_union["transformationSourceCueIds"] = ["cap-relation"]
    data["visualEvents"] = [wrong_union]
    errors, _ = layered_hud_step_checks(data)
    assert any("transformation-source-union" in item for item in errors), errors


def main() -> int:
    assert_full_evidence_event()
    assert_customer_case_falls_back_without_result()
    assert_uncited_previous_cue_is_ignored()
    assert_incomplete_evidence_fallbacks()
    assert_qa_rejects_provenance_tampering()
    print("transformation evidence regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
