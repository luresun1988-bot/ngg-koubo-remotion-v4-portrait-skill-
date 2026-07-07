#!/usr/bin/env python3
"""Convert visual_script.json into the Remotion template TS data module."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--no-ascii",
        action="store_true",
        help="Write literal UTF-8 text instead of ASCII \\u escapes. Default uses ASCII escapes to avoid shell/codepage corruption.",
    )
    args = parser.parse_args()

    data = json.loads(args.visual_script.read_text(encoding="utf-8-sig"))
    rendered = json.dumps(data, ensure_ascii=not args.no_ascii, indent=2)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "import type {VisualScript} from './v4Types';\n\n"
        f"export const visualScript = {rendered} satisfies VisualScript;\n",
        encoding="utf-8",
    )
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
