#!/usr/bin/env python3
"""Optionally normalize Chinese text files from Traditional to Simplified."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()


def convert_text(text: str) -> tuple[str, str]:
    try:
        from opencc import OpenCC  # type: ignore
    except Exception:  # noqa: BLE001
        return text, "opencc-not-installed"

    return OpenCC("t2s").convert(text), "converted-with-opencc"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True, type=Path)
    parser.add_argument("--out", dest="output", required=True, type=Path)
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8")
    converted, status = convert_text(text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(converted, encoding="utf-8")
    print(status)
    if status == "opencc-not-installed":
        print("WARN: install opencc-python-reimplemented or opencc for Traditional-to-Simplified conversion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
