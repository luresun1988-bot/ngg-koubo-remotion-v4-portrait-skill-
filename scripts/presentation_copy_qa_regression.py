#!/usr/bin/env python3
"""Regression coverage for presentation_copy_qa.py."""

from presentation_copy_qa import analyze


def main() -> int:
    risky = analyze({"visualEvents": [{"id": "e1", "type": "infoCard", "text": "很长" * 40}]})
    codes = {item["code"] for item in risky["warnings"]}
    assert "copy-budget" in codes
    assert "safe-area-missing" in codes
    assert risky["hardErrors"] == []

    clean = analyze({"visualEvents": [{"id": "e2", "type": "infoCard", "text": "简短观点", "safeArea": "avoid-face-caption"}]})
    assert clean["warningCount"] == 0
    print("presentation copy QA regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
