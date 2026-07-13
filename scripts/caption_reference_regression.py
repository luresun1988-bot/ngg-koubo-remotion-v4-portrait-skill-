#!/usr/bin/env python3
"""Regression coverage for split-first caption and semantic reference integrity."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from init_v4_project import finalize_visual_script, starter_visual_script
from validate_visual_script import validate


def validate_payload(payload: dict) -> tuple[list[str], list[str]]:
    with tempfile.TemporaryDirectory(prefix="v4-portrait-caption-ref-") as temp_dir:
        path = Path(temp_dir) / "visual_script.json"
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return validate(path)


def main() -> int:
    text = "这是一个需要先拆分成长短合适字幕的完整中文句子，然后才能建立可靠的语义引用关系。"
    starter = starter_visual_script(
        "../project_config.json",
        "public/input/video/presenter.mp4",
        [{"durationSec": 8.0, "hasAudio": True}],
        [text],
        25,
        timeline_cues=[{"id": "cap-long", "startFrame": 0, "endFrame": 200, "text": text}],
        timeline_meta={
            "sourceType": "srt",
            "sourcePath": "input/captions/test.srt",
            "method": "source-timecodes",
            "generatedBy": "caption_reference_regression.py",
        },
    )
    finalized, split_count = finalize_visual_script(starter)
    if split_count != 1:
        raise SystemExit(f"expected one split cue, got {split_count}")

    cue_ids = {str(cue.get("id") or "") for cue in finalized.get("captionCues", [])}
    if "cap-long" in cue_ids or cue_ids != {"cap-long-01", "cap-long-02"}:
        raise SystemExit(f"unexpected split cue ids: {sorted(cue_ids)}")

    for beat in finalized.get("semanticBeats", []):
        dangling = set(beat.get("sourceCueIds") or []) - cue_ids
        if dangling:
            raise SystemExit(f"semantic beat keeps dangling cue ids: {sorted(dangling)}")
    for event in finalized.get("visualEvents", []):
        anchor = str(event.get("anchorCueId") or "")
        if anchor and anchor not in cue_ids:
            raise SystemExit(f"visual event keeps dangling anchorCueId: {anchor}")

    errors, _ = validate_payload(finalized)
    if errors:
        raise SystemExit("finalized split-first payload failed validation:\n" + "\n".join(errors))

    corrupted = copy.deepcopy(finalized)
    corrupted["semanticBeats"][0]["sourceCueIds"] = ["cap-long"]
    errors, _ = validate_payload(corrupted)
    if not any("unknown caption cue: cap-long" in error for error in errors):
        raise SystemExit("validator accepted a dangling semantic caption reference")

    corrupted = copy.deepcopy(finalized)
    corrupted["visualEvents"][0]["anchorCueId"] = "cap-long"
    errors, _ = validate_payload(corrupted)
    if not any("unknown anchorCueId: cap-long" in error for error in errors):
        raise SystemExit("validator accepted a dangling visual-event anchor")

    print("caption reference regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
