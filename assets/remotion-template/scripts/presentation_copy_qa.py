#!/usr/bin/env python3
"""Report copy-budget and safe-area risks without changing visual events."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from presentation_registry import get_registry


def _char_count(value: Any) -> int:
    return len(re.sub(r"\s+", "", str(value or "")))


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    registry = get_registry()
    policy = registry.component_registry.get("qaPolicy", {})
    default_budget = policy.get("defaultCopyBudget", {})
    event_budgets = policy.get("eventCopyBudgets", {})
    safe_required = {str(item) for item in policy.get("safeAreaRequiredEventTypes", [])}
    warnings: list[dict[str, Any]] = []
    for event in data.get("visualEvents", []):
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id") or "")
        event_type = str(event.get("type") or "")
        budget = event_budgets.get(event_type, default_budget)
        for field in ("text", "title", "subtext"):
            limit = int(budget.get(field, 0) or 0) if isinstance(budget, dict) else 0
            count = _char_count(event.get(field))
            if limit and count > limit:
                warnings.append(
                    {
                        "code": "copy-budget",
                        "eventId": event_id,
                        "eventType": event_type,
                        "field": field,
                        "count": count,
                        "limit": limit,
                        "message": f"{event_id}.{field} has {count} chars; review budget {limit}",
                    }
                )
        if event_type in safe_required and not str(event.get("safeArea") or ""):
            warnings.append(
                {
                    "code": "safe-area-missing",
                    "eventId": event_id,
                    "eventType": event_type,
                    "message": f"{event_id} ({event_type}) has no explicit safeArea",
                }
            )
    return {
        "schema": "ngg-v4-presentation-copy-qa",
        "format": registry.format,
        "hardErrors": [],
        "warningCount": len(warnings),
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = json.loads(args.visual_script.read_text(encoding="utf-8-sig"))
    report = analyze(data)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
