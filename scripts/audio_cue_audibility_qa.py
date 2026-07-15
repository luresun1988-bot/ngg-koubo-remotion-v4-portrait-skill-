#!/usr/bin/env python3
"""Measure each rendered SFX cue against its nearby mixed-audio baseline."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any


RENDERED_STATUSES = {"active", "approved", "enabled", "rendered"}
VOLUME_RE = re.compile(r"(mean_volume|max_volume):\s*(-?inf|-?\d+(?:\.\d+)?)\s*dB")


def cue_windows(start_sec: float, duration_sec: float, baseline_sec: float = 0.25) -> dict[str, tuple[float, float] | None]:
    cue_start = max(0.0, start_sec)
    cue_duration = max(0.04, duration_sec)
    before = (max(0.0, cue_start - baseline_sec), min(baseline_sec, cue_start)) if cue_start > 0 else None
    after = (cue_start + cue_duration, baseline_sec)
    return {"before": before, "cue": (cue_start, cue_duration), "after": after}


def evaluate_levels(cue: dict[str, float], baselines: list[dict[str, float]], threshold_db: float) -> dict[str, Any]:
    valid = [item for item in baselines if math.isfinite(item.get("meanDb", float("-inf"))) or math.isfinite(item.get("maxDb", float("-inf")))]
    if not valid:
        return {"status": "undetermined", "meanDeltaDb": None, "peakDeltaDb": None}
    baseline_mean = sum(item["meanDb"] for item in valid) / len(valid)
    baseline_peak = sum(item["maxDb"] for item in valid) / len(valid)
    mean_delta = cue["meanDb"] - baseline_mean
    peak_delta = cue["maxDb"] - baseline_peak
    return {
        "status": "audible" if max(mean_delta, peak_delta) >= threshold_db else "review",
        "meanDeltaDb": round(mean_delta, 2),
        "peakDeltaDb": round(peak_delta, 2),
        "baselineMeanDb": round(baseline_mean, 2),
        "baselinePeakDb": round(baseline_peak, 2),
    }


def _measure(media: Path, start_sec: float, duration_sec: float) -> dict[str, float]:
    command = [
        "ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start_sec:.6f}", "-t", f"{duration_sec:.6f}",
        "-i", str(media), "-vn", "-af", "volumedetect", "-f", "null", "NUL",
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg volumedetect failed")
    values = {name: float("-inf") if raw == "-inf" else float(raw) for name, raw in VOLUME_RE.findall(result.stderr)}
    return {"meanDb": values.get("mean_volume", float("-inf")), "maxDb": values.get("max_volume", float("-inf"))}


def analyze(
    data: dict[str, Any],
    media: Path,
    *,
    threshold_db: float = 1.5,
    include_suggested: bool = False,
) -> dict[str, Any]:
    fps = float(data.get("composition", {}).get("fps", 25) or 25)
    beats = {str(item.get("id") or ""): item for item in data.get("semanticBeats", []) if isinstance(item, dict)}
    items: list[dict[str, Any]] = []
    for cue in data.get("audioCues", []):
        if not isinstance(cue, dict) or str(cue.get("type") or "") != "sfx":
            continue
        status = str(cue.get("status") or "")
        if not include_suggested and status not in RENDERED_STATUSES:
            continue
        start_sec = int(cue.get("startFrame", 0) or 0) / fps
        duration_sec = max(1, int(cue.get("durationFrames", 1) or 1)) / fps
        windows = cue_windows(start_sec, duration_sec)
        cue_level = _measure(media, *windows["cue"])
        baseline_levels = [
            _measure(media, *window)
            for key in ("before", "after")
            if (window := windows[key]) is not None and window[1] >= 0.04
        ]
        evaluation = evaluate_levels(cue_level, baseline_levels, threshold_db)
        source_beat = beats.get(str(cue.get("sourceBeatId") or ""), {})
        items.append(
            {
                "cueId": str(cue.get("id") or ""),
                "sfxIntent": str(cue.get("sfxIntent") or ""),
                "sfxId": str(cue.get("sfxId") or ""),
                "semanticIntent": str(source_beat.get("semanticIntent") or ""),
                "sourceText": str(source_beat.get("text") or ""),
                "startFrame": int(cue.get("startFrame", 0) or 0),
                "durationFrames": int(cue.get("durationFrames", 0) or 0),
                "configuredVolumeDb": cue.get("volumeDb"),
                "cueMeanDb": cue_level["meanDb"],
                "cuePeakDb": cue_level["maxDb"],
                **evaluation,
            }
        )
    return {
        "schema": "ngg-v4-audio-cue-audibility-qa",
        "media": str(media),
        "thresholdDb": threshold_db,
        "cueCount": len(items),
        "audibleCount": sum(item["status"] == "audible" for item in items),
        "reviewCount": sum(item["status"] == "review" for item in items),
        "undeterminedCount": sum(item["status"] == "undetermined" for item in items),
        "items": items,
        "note": "Heuristic mixed-audio measurement; review flags require listening, not automatic volume changes.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", type=Path, required=True)
    parser.add_argument("--media", type=Path, required=True)
    parser.add_argument("--threshold-db", type=float, default=1.5)
    parser.add_argument("--include-suggested", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = json.loads(args.visual_script.read_text(encoding="utf-8-sig"))
    report = analyze(data, args.media, threshold_db=args.threshold_db, include_suggested=args.include_suggested)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
