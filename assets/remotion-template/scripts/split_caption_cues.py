#!/usr/bin/env python3
"""Split long V4 caption cues into shorter timed cues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()

PUNCT_RE = re.compile(r"([\uFF0C\u3002\uFF1B\uFF1A\uFF01\uFF1F\u3001,.;:!?])")


def visible_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def split_sentence(text: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    buffer = ""
    parts = PUNCT_RE.split(text)
    for idx in range(0, len(parts), 2):
        phrase = parts[idx]
        punct = parts[idx + 1] if idx + 1 < len(parts) else ""
        candidate = f"{phrase}{punct}".strip()
        if not candidate:
            continue
        if buffer and visible_len(buffer + candidate) > max_chars:
            pieces.append(buffer)
            buffer = candidate
        else:
            buffer = f"{buffer}{candidate}" if buffer else candidate
    if buffer:
        pieces.append(buffer)

    output: list[str] = []
    for piece in pieces or [text.strip()]:
        if visible_len(piece) <= max_chars:
            output.append(piece)
            continue
        chars = list(piece)
        current = ""
        for char in chars:
            if current and visible_len(current + char) > max_chars:
                output.append(current)
                current = char
            else:
                current += char
        if current:
            output.append(current)
    return [part.strip() for part in output if part.strip()]


def distribute_frames(start: int, end: int, parts: list[str], min_frames: int) -> list[tuple[int, int]]:
    duration = max(1, end - start)
    weights = [max(1, visible_len(part)) for part in parts]
    total = sum(weights)
    ranges: list[tuple[int, int]] = []
    cursor = start
    for idx, weight in enumerate(weights):
        if idx == len(weights) - 1:
            part_end = end
        else:
            estimated = round(duration * weight / total)
            part_end = min(end, max(cursor + min_frames, cursor + estimated))
            remaining = len(weights) - idx - 1
            part_end = min(part_end, end - remaining * min_frames)
        ranges.append((cursor, max(cursor + 1, part_end)))
        cursor = max(cursor + 1, part_end)
    return ranges


def split_cues(data: dict[str, Any], max_chars: int, min_frames: int) -> tuple[dict[str, Any], int]:
    output = dict(data)
    new_cues: list[dict[str, Any]] = []
    split_count = 0
    for cue in data.get("captionCues", []):
        if not isinstance(cue, dict):
            new_cues.append(cue)
            continue
        text = cue.get("text")
        start = cue.get("startFrame")
        end = cue.get("endFrame")
        if not isinstance(text, str) or not isinstance(start, int) or not isinstance(end, int):
            new_cues.append(cue)
            continue
        parts = split_sentence(text, max_chars)
        if len(parts) <= 1:
            new_cues.append(cue)
            continue
        frame_ranges = distribute_frames(start, end, parts, min_frames)
        highlights = cue.get("highlightWords", [])
        if not isinstance(highlights, list):
            highlights = []
        split_count += 1
        for idx, (part, frame_range) in enumerate(zip(parts, frame_ranges, strict=True), start=1):
            part_highlights = [
                word for word in highlights if isinstance(word, str) and word and word in part
            ][:3]
            new_cue = dict(cue)
            new_cue["id"] = f"{cue.get('id', 'cap')}-{idx:02d}"
            new_cue["startFrame"] = frame_range[0]
            new_cue["endFrame"] = frame_range[1]
            new_cue["text"] = part
            new_cue["highlightWords"] = part_highlights
            new_cues.append(new_cue)
    output["captionCues"] = new_cues
    return output, split_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-chars", type=int, default=30)
    parser.add_argument("--min-frames", type=int, default=12)
    parser.add_argument(
        "--no-ascii",
        action="store_true",
        help="Write literal UTF-8 instead of ASCII escapes. Default is safer for Windows shells.",
    )
    args = parser.parse_args()

    data = json.loads(args.visual_script.read_text(encoding="utf-8-sig"))
    output, split_count = split_cues(data, args.max_chars, args.min_frames)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(output, ensure_ascii=not args.no_ascii, indent=2),
        encoding="utf-8",
    )
    print(f"split {split_count} caption cues; wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
