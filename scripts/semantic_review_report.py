#!/usr/bin/env python3
"""Create a read-only review report for low-confidence semantic beats."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from presentation_registry import get_registry


def analyze(data: dict[str, Any], threshold: float = 0.75) -> dict[str, Any]:
    registry = get_registry()
    items: list[dict[str, Any]] = []
    for beat in data.get("semanticBeats", []):
        if not isinstance(beat, dict):
            continue
        confidence = float(beat.get("confidence", 0.0) or 0.0)
        if confidence >= threshold:
            continue
        intent = str(beat.get("semanticIntent") or "")
        try:
            fallback = registry.fallback_visual_form(intent)
        except KeyError:
            fallback = ""
        items.append(
            {
                "beatId": str(beat.get("id") or ""),
                "sceneId": str(beat.get("sceneId") or ""),
                "text": str(beat.get("text") or ""),
                "semanticIntent": intent,
                "visualForm": str(beat.get("visualForm") or ""),
                "confidence": confidence,
                "threshold": threshold,
                "sourceCueIds": [str(item) for item in beat.get("sourceCueIds", []) if str(item)],
                "registryFallback": fallback,
                "recommendation": "manual-review-only",
            }
        )
    return {
        "schema": "ngg-v4-semantic-review-report",
        "format": registry.format,
        "threshold": threshold,
        "reviewCount": len(items),
        "items": items,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V4 Semantic Review Report",
        "",
        f"- Format: {report['format']}",
        f"- Threshold: {report['threshold']:.2f}",
        f"- Review items: {report['reviewCount']}",
        "",
    ]
    for item in report["items"]:
        lines.extend(
            [
                f"## {item['beatId']} · {item['semanticIntent']} · {item['confidence']:.2f}",
                "",
                f"- Text: {item['text']}",
                f"- Visual: {item['visualForm']}",
                f"- Registry fallback: {item['registryFallback'] or 'none'}",
                f"- Source cues: {', '.join(item['sourceCueIds']) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.75)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()
    data = json.loads(args.visual_script.read_text(encoding="utf-8-sig"))
    report = analyze(data, args.threshold)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(payload, encoding="utf-8")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(markdown(report), encoding="utf-8")
    if not args.out_json and not args.out_md:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
