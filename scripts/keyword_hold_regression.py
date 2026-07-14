#!/usr/bin/env python3
"""Ensure portrait keyword impact enters quickly and holds until event exit."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "assets" / "remotion-template" / "src" / "components" / "V4Primitives.tsx",
]


def main() -> int:
    failed: list[str] = []
    for target in TARGETS:
        source = target.read_text(encoding="utf-8")
        start = source.find("const emphasisScale =")
        end = source.find("\n};", start)
        block = source[start:end + 3] if start >= 0 and end >= 0 else ""
        ok = all(
            token in block
            for token in [
                "const pushFrames = Math.max(3, Math.round((5 * fps) / 25));",
                "return 1 + 0.16 * progress;",
                "extrapolateRight: 'clamp'",
            ]
        ) and "[0, 10, 24, 36]" not in block and "spring({" not in block
        print(f"{'PASS' if ok else 'MISS'} {target.relative_to(ROOT)}")
        if not ok:
            failed.append(str(target))
    if failed:
        print(f"failed: {len(failed)} / {len(TARGETS)}")
        return 1
    print(f"passed: {len(TARGETS)} / {len(TARGETS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
