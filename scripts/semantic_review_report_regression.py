#!/usr/bin/env python3
"""Regression coverage for semantic_review_report.py."""

from semantic_review_report import analyze


def main() -> int:
    report = analyze(
        {
            "semanticBeats": [
                {"id": "low", "semanticIntent": "explanation-claim", "visualForm": "infoCard", "confidence": 0.60, "text": "待复核", "sourceCueIds": ["c1"]},
                {"id": "high", "semanticIntent": "explanation-claim", "visualForm": "infoCard", "confidence": 0.90, "text": "已确认"},
            ]
        },
        0.75,
    )
    assert report["reviewCount"] == 1
    assert report["items"][0]["beatId"] == "low"
    assert report["items"][0]["registryFallback"]
    assert report["items"][0]["recommendation"] == "manual-review-only"
    print("semantic review report regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
