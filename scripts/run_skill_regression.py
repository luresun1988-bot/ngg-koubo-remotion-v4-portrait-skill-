#!/usr/bin/env python3
"""Run the maintained V4 Portrait regression surface from one command."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "remotion-template"
REGRESSIONS = [
    "sync_template_mirrors.py",
    "caption_reference_regression.py",
    "semantic_router_regression.py",
    "semantic_contract_regression.py",
    "semantic_guardrails_regression.py",
    "semantic_component_contract_regression.py",
    "sfx_semantic_routing_regression.py",
    "visual_density_regression.py",
    "presenter_impact_regression.py",
    "presenter_media_regression.py",
    "fps_contract_regression.py",
    "final_media_qa_regression.py",
    "render_pipeline_regression.py",
    "upgrade_existing_project_regression.py",
    "motion_preview_regression.py",
    "portrait_runtime_contract_regression.py",
]


def run_check(label: str, command: list[str], cwd: Path | None = None) -> None:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        print(f"FAIL {label}")
        if completed.stdout:
            print(completed.stdout.rstrip())
        if completed.stderr:
            print(completed.stderr.rstrip())
        raise SystemExit(completed.returncode)
    print(f"PASS {label}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gallery", action="store_true")
    parser.add_argument("--skip-typecheck", action="store_true")
    args = parser.parse_args()

    for path in sorted(SCRIPT_DIR.glob("*.py")):
        run_check(f"py-compile:{path.name}", [sys.executable, "-m", "py_compile", str(path)])

    quick_validate = SKILL_ROOT.parent / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
    if quick_validate.is_file():
        run_check("skill-quick-validate", [sys.executable, str(quick_validate), str(SKILL_ROOT)])

    for regression in REGRESSIONS:
        run_check(regression, [sys.executable, str(SCRIPT_DIR / regression)], cwd=SKILL_ROOT)

    npm = shutil.which("npm")
    if not args.skip_typecheck:
        if not npm:
            raise SystemExit("npm is required for Portrait template typecheck")
        run_check("template-typecheck", [npm, "run", "typecheck", "--silent"], cwd=TEMPLATE_ROOT)

    powershell = shutil.which("powershell")
    if not powershell:
        raise SystemExit("powershell is required for Portrait component render smoke")
    if args.gallery:
        run_check(
            "component-gallery",
            [
                powershell,
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SKILL_ROOT / "assets" / "component-gallery" / "render_gallery.ps1"),
                "-SkipVideo",
            ],
            cwd=SKILL_ROOT,
        )
    else:
        run_check(
            "component-render-smoke",
            [powershell, "-ExecutionPolicy", "Bypass", "-File", str(SKILL_ROOT / "assets" / "component-gallery" / "render_gallery.ps1"), "-SkipVideo", "-Smoke"],
            cwd=SKILL_ROOT,
        )

    print("V4 Portrait skill regression suite: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
