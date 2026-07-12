#!/usr/bin/env python3
"""Regression checks for pre-render presenter/composition FPS contract linting."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from qa_lint_visual_script import fps_contract_checks


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        report_path = root / "qa" / "media" / "presenter_normalization.json"
        report_path.parent.mkdir(parents=True)
        report = {
            "normalizationApplied": True,
            "frameRate": {
                "compositionFps": 25,
                "mixedPresenterFps": False,
                "requiresCfrNormalization": True,
            },
            "verification": {"passed": True},
        }
        report_path.write_text(json.dumps(report), encoding="utf-8")
        errors, _ = fps_contract_checks({"composition": {"fps": 25}}, root)
        if errors:
            raise AssertionError(errors)

        mismatch, _ = fps_contract_checks({"composition": {"fps": 30}}, root)
        if not any("differs from presenter report" in item for item in mismatch):
            raise AssertionError(mismatch)

        report["normalizationApplied"] = False
        report_path.write_text(json.dumps(report), encoding="utf-8")
        missing_cfr, _ = fps_contract_checks({"composition": {"fps": 25}}, root)
        if not any("requires CFR normalization" in item for item in missing_cfr):
            raise AssertionError(missing_cfr)

    print("portrait fps contract regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
