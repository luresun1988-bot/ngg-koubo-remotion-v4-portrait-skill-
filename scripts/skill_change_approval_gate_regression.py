#!/usr/bin/env python3
"""Regression tests for the repository-level Skill change approval gate."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


GATE = Path(__file__).resolve().parent / "skill_change_approval_gate.py"


def run(root: Path, *args: str, expected: int = 0) -> str:
    completed = subprocess.run(
        [sys.executable, str(GATE), "--repo-root", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != expected:
        raise AssertionError(
            f"unexpected exit {completed.returncode}, expected {expected}: {' '.join(args)}\n"
            f"{completed.stdout}{completed.stderr}"
        )
    return completed.stdout + completed.stderr


def initialize(root: Path) -> None:
    (root / "references").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    (root / "SKILL.md").write_text("baseline\n", encoding="utf-8")
    (root / "references" / "visual.md").write_text("visual baseline\n", encoding="utf-8")
    run(root, "bootstrap", "--repository", "fixture", "--confirmation", "用户确认安装门禁")
    run(root, "verify")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ngg-v4-change-gate-") as temporary:
        root = Path(temporary)
        initialize(root)

        (root / "SKILL.md").write_text("unauthorized\n", encoding="utf-8")
        output = run(root, "verify", expected=1)
        if "without an approved and sealed change request" not in output:
            raise AssertionError("unapproved repository edit was not refused")
        (root / "SKILL.md").write_text("baseline\n", encoding="utf-8")

        run(
            root,
            "create",
            "--change-id",
            "visual-001",
            "--change-class",
            "visual-semantic",
            "--summary",
            "change visual rule",
            "--scope",
            "references/visual.md",
        )
        no_sample = run(root, "approve", "--confirmation", "确认视觉样片", expected=1)
        if "requires at least one still or motion preview" not in no_sample:
            raise AssertionError("visual approval without a sample was not refused")

        sample = root / "qa" / "approved-preview.png"
        sample.parent.mkdir(parents=True, exist_ok=True)
        sample.write_bytes(b"approved preview bytes")
        run(root, "approve", "--confirmation", "确认视觉样片", "--sample", str(sample))
        (root / "references" / "visual.md").write_text("approved visual change\n", encoding="utf-8")
        run(root, "seal")
        run(root, "verify")

        sample.write_bytes(b"tampered preview bytes")
        changed_sample = run(root, "verify", expected=1)
        if "approved sample changed after confirmation" not in changed_sample:
            raise AssertionError("sample tampering was not refused")

    with tempfile.TemporaryDirectory(prefix="ngg-v4-structural-gate-") as temporary:
        root = Path(temporary)
        initialize(root)
        run(
            root,
            "create",
            "--change-id",
            "structural-001",
            "--change-class",
            "structural-nonvisual",
            "--summary",
            "clarify workflow",
            "--scope",
            "SKILL.md",
        )
        run(root, "approve", "--confirmation", "用户明确确认结构规则")
        (root / "SKILL.md").write_text("approved structural change\n", encoding="utf-8")
        run(root, "seal")
        run(root, "verify")

    print("skill change approval gate regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
