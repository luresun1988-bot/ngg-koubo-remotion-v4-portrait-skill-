#!/usr/bin/env python3
"""Regression for the reusable V4 audio renderer and presenter gain contract."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "remotion-template"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_visual_script import validate  # noqa: E402


def assert_source_contract() -> None:
    composition = (TEMPLATE_ROOT / "src" / "V4Composition.tsx").read_text(encoding="utf-8")
    audio = (TEMPLATE_ROOT / "src" / "V4Audio.tsx").read_text(encoding="utf-8")
    if composition.count("<V4AudioLayers") != 1:
        raise AssertionError("V4Composition must mount exactly one V4AudioLayers")
    if "<PresenterAudioLayer" in composition or "<AudioCueLayer" in composition:
        raise AssertionError("V4Composition still contains a second private audio renderer")
    required = [
        "visualScript.presenterAudio",
        "visualScript.audioCues.map",
        "config.volumeDb ?? 0",
        "cue.status === 'suggested'",
        "cue.status === 'disabled'",
        "cue.status === 'muted'",
    ]
    missing = [token for token in required if token not in audio]
    if missing:
        raise AssertionError(f"V4Audio contract is incomplete: {missing}")


def assert_presenter_gain_contract() -> None:
    example_path = TEMPLATE_ROOT / "config" / "visual_script.example.json"
    data = json.loads(example_path.read_text(encoding="utf-8-sig"))
    data["presenterAudio"] = {
        "mode": "embedded",
        "syncOffsetFrames": 0,
        "volumeDb": -1.5,
    }

    with tempfile.TemporaryDirectory(prefix="v4-audio-contract-") as temp_dir:
        valid_path = Path(temp_dir) / "valid.json"
        valid_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        errors, _warnings = validate(valid_path)
        if errors:
            raise AssertionError(f"finite presenter gain should validate: {errors}")

        invalid = copy.deepcopy(data)
        invalid["presenterAudio"]["volumeDb"] = True
        invalid_path = Path(temp_dir) / "invalid.json"
        invalid_path.write_text(json.dumps(invalid, ensure_ascii=False, indent=2), encoding="utf-8")
        errors, _warnings = validate(invalid_path)
        if not any("presenterAudio.volumeDb must be a finite number" in item for item in errors):
            raise AssertionError(f"boolean presenter gain was not rejected: {errors}")


def main() -> int:
    assert_source_contract()
    assert_presenter_gain_contract()
    print("audio runtime contract regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

