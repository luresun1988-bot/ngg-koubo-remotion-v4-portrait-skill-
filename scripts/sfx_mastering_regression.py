#!/usr/bin/env python3
"""Validate the approved V4 SFX asset mastering and cue-volume contract."""

from __future__ import annotations

from array import array
import json
import math
from pathlib import Path
import sys
import wave


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import qa_lint_visual_script  # noqa: E402


EXPECTED_IDS = {
    "automation_handoff_01",
    "confirm_ding_01",
    "data_count_01",
    "negative_warning_01",
    "proof_reveal_01",
    "title_impact_whoosh_01",
}
APPROVED_CUE_DB = -5.0


def dbfs(value: float) -> float:
    return 20.0 * math.log10(max(value, 1e-12))


def analyze_wav(path: Path) -> dict[str, float | int]:
    with wave.open(str(path), "rb") as reader:
        channels = reader.getnchannels()
        sample_width = reader.getsampwidth()
        sample_rate = reader.getframerate()
        frame_count = reader.getnframes()
        samples = array("h", reader.readframes(frame_count))
    if sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        raise AssertionError(f"empty WAV: {path}")
    peak = max(abs(sample) for sample in samples) / 32768.0
    rms = math.sqrt(sum(float(sample) * float(sample) for sample in samples) / len(samples)) / 32768.0
    return {
        "channels": channels,
        "sampleWidth": sample_width,
        "sampleRate": sample_rate,
        "frameCount": frame_count,
        "durationSec": frame_count / sample_rate,
        "peakDbfs": dbfs(peak),
        "rmsDbfs": dbfs(rms),
    }


def assert_qa_ceiling(sfx_id: str, volume_db: float, should_pass: bool) -> None:
    data = {
        "composition": {"fps": 25},
        "visualEvents": [{"id": "event", "startFrame": 0, "endFrame": 5}],
        "audioCues": [{
            "id": "cue",
            "type": "sfx",
            "sfxId": sfx_id,
            "startFrame": 0,
            "durationFrames": 5,
            "volumeDb": volume_db,
            "status": "active",
        }],
    }
    errors, _warnings = qa_lint_visual_script.audio_policy_checks(data)
    has_volume_error = any("audio-sfx-volume" in error for error in errors)
    if should_pass == has_volume_error:
        raise AssertionError(
            f"QA ceiling mismatch for sfxId={sfx_id or 'unregistered'} volumeDb={volume_db}: {errors}"
        )


def assert_duration_policy(sfx_id: str, duration_frames: int, should_warn: bool) -> None:
    data = {
        "composition": {"fps": 25},
        "visualEvents": [{"id": "event", "startFrame": 0, "endFrame": 5}],
        "audioCues": [{
            "id": "cue",
            "type": "sfx",
            "sfxId": sfx_id,
            "startFrame": 0,
            "durationFrames": duration_frames,
            "volumeDb": -14 if sfx_id not in EXPECTED_IDS else APPROVED_CUE_DB,
            "status": "active",
        }],
    }
    _errors, warnings = qa_lint_visual_script.audio_policy_checks(data)
    has_duration_warning = any("audio-sfx-duration" in warning for warning in warnings)
    if should_warn != has_duration_warning:
        raise AssertionError(
            f"QA duration mismatch for sfxId={sfx_id or 'unregistered'} "
            f"durationFrames={duration_frames}: {warnings}"
        )


def main() -> int:
    manifest_path = SKILL_ROOT / "assets" / "remotion-template" / "public" / "input" / "audio" / "sfx_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    policy = manifest.get("defaultPolicy", {})
    mastering = manifest.get("mastering", {})
    if float(policy.get("defaultVolumeDb")) != APPROVED_CUE_DB:
        raise AssertionError(f"manifest defaultVolumeDb must be {APPROVED_CUE_DB:g}")
    if float(policy.get("prominentMaxVolumeDb")) != APPROVED_CUE_DB:
        raise AssertionError(f"manifest prominentMaxVolumeDb must be {APPROVED_CUE_DB:g}")
    expected_mastering = {
        "preGainDb": 18,
        "limiterPeakDb": -1,
        "cueVolumeDb": -5,
        "approvedByUser": True,
        "approvedDate": "2026-07-14",
    }
    if mastering != expected_mastering:
        raise AssertionError(f"unexpected mastering record: {mastering}")

    items = {str(item.get("sfxId")): item for item in manifest.get("items", [])}
    if set(items) != EXPECTED_IDS:
        raise AssertionError(f"manifest SFX IDs differ: expected={sorted(EXPECTED_IDS)} actual={sorted(items)}")

    for sfx_id in sorted(EXPECTED_IDS):
        item = items[sfx_id]
        if float(item.get("defaultVolumeDb")) != APPROVED_CUE_DB:
            raise AssertionError(f"{sfx_id} defaultVolumeDb must be {APPROVED_CUE_DB:g}")
        wav_path = manifest_path.parent.parent.parent / str(item["path"])
        metrics = analyze_wav(wav_path)
        if metrics["sampleRate"] != 48_000 or metrics["channels"] != 2 or metrics["sampleWidth"] != 2:
            raise AssertionError(f"{sfx_id} must be 48 kHz stereo PCM16: {metrics}")
        if abs(float(metrics["durationSec"]) - float(item["durationSec"])) > 1 / 48_000:
            raise AssertionError(f"{sfx_id} duration differs from manifest: {metrics}")
        if not -1.2 <= float(metrics["peakDbfs"]) <= -0.8:
            raise AssertionError(f"{sfx_id} mastered peak must be about -1 dBFS: {metrics}")
        if not -17.0 <= float(metrics["rmsDbfs"]) <= -7.5:
            raise AssertionError(f"{sfx_id} mastered RMS outside approved envelope: {metrics}")
        post_cue_peak = float(metrics["peakDbfs"]) + APPROVED_CUE_DB
        if not -6.2 <= post_cue_peak <= -5.8:
            raise AssertionError(f"{sfx_id} post-cue peak must be about -6 dBFS: {post_cue_peak:.2f}")
        print(
            f"PASS {sfx_id}: peak={metrics['peakDbfs']:.2f} dBFS "
            f"rms={metrics['rmsDbfs']:.2f} dBFS postCuePeak={post_cue_peak:.2f} dBFS"
        )

    assert_qa_ceiling("confirm_ding_01", -5.0, True)
    assert_qa_ceiling("confirm_ding_01", -4.9, False)
    assert_qa_ceiling("custom_unregistered_01", -14.0, True)
    assert_qa_ceiling("custom_unregistered_01", -13.9, False)
    assert_duration_policy("confirm_ding_01", 50, False)
    assert_duration_policy("custom_unregistered_01", 50, True)
    print("sfx mastering regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
