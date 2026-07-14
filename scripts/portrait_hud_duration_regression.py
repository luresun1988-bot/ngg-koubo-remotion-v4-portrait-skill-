#!/usr/bin/env python3
"""Regression checks for portrait long-card monotony limits."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from qa_lint_visual_script import hud_duration_budget_checks  # noqa: E402
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()


def script_for(*, duration_frames: int, motion_type: str = "hud-slide-fade") -> dict[str, Any]:
    return {
        "composition": {"fps": 25},
        "visualEvents": [
            {
                "id": "card-001",
                "type": "captionHighlight",
                "startFrame": 0,
                "endFrame": duration_frames,
                "motionType": motion_type,
            }
        ],
    }


def has_message(messages: list[str], marker: str) -> bool:
    return any(marker in message for message in messages)


def main() -> int:
    errors, warnings = hud_duration_budget_checks(script_for(duration_frames=150))
    if has_message(errors + warnings, "long-card-monotony"):
        raise AssertionError(f"exactly 6s must not trigger long-card monotony: {errors} {warnings}")

    errors, warnings = hud_duration_budget_checks(script_for(duration_frames=175))
    if errors or not has_message(warnings, "long-card-monotony warning"):
        raise AssertionError(f"7s static portrait card must warn, not fail: {errors} {warnings}")

    errors, warnings = hud_duration_budget_checks(script_for(duration_frames=200))
    if has_message(errors, "long-card-monotony failed"):
        raise AssertionError(f"exactly 8s must remain warning-only: {errors} {warnings}")

    errors, warnings = hud_duration_budget_checks(script_for(duration_frames=225))
    if not has_message(errors, "long-card-monotony failed"):
        raise AssertionError(f"9s static portrait card must fail: {errors} {warnings}")

    progressive = script_for(duration_frames=250, motion_type="workflow-progressive")
    errors, warnings = hud_duration_budget_checks(progressive)
    if has_message(errors + warnings, "long-card-monotony"):
        raise AssertionError(f"source-bound progressive workflow must be exempt: {errors} {warnings}")

    non_card = deepcopy(script_for(duration_frames=250))
    non_card["visualEvents"][0]["type"] = "kineticTitle"
    errors, warnings = hud_duration_budget_checks(non_card)
    if has_message(errors + warnings, "long-card-monotony"):
        raise AssertionError(f"non-card main HUD must not trigger card monotony: {errors} {warnings}")

    print("portrait HUD duration regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
