#!/usr/bin/env python3
"""Keep reusable template scripts/references byte-identical to the Skill sources."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ROOT_SCRIPTS = SKILL_ROOT / "scripts"
ROOT_REFERENCES = SKILL_ROOT / "references"
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "remotion-template"
TEMPLATE_SCRIPTS = TEMPLATE_ROOT / "scripts"
TEMPLATE_REFERENCES = TEMPLATE_ROOT / "references"

REQUIRED_TEMPLATE_SCRIPTS = {
    "final_media_qa.py",
    "render_final_and_qa.ps1",
    "semantic_contract_cases.json",
    "semantic_guardrails.py",
    "upgrade_existing_project.py",
}


def mirror_pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    script_names = {
        path.name
        for path in TEMPLATE_SCRIPTS.iterdir()
        if path.is_file() and path.suffix.lower() in {".py", ".ps1", ".json"}
    } | REQUIRED_TEMPLATE_SCRIPTS
    for name in sorted(script_names):
        pairs.append((ROOT_SCRIPTS / name, TEMPLATE_SCRIPTS / name))
    for source in sorted(ROOT_REFERENCES.glob("*.md")):
        pairs.append((source, TEMPLATE_REFERENCES / source.name))
    return pairs


def sync(write: bool) -> list[str]:
    errors: list[str] = []
    for source, target in mirror_pairs():
        relative = target.relative_to(SKILL_ROOT).as_posix()
        if not source.is_file():
            errors.append(f"missing source for template mirror: {source}")
            continue
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            continue
        if not target.is_file():
            errors.append(f"missing template mirror: {relative}")
        elif source.read_bytes() != target.read_bytes():
            errors.append(f"stale template mirror: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Refresh template mirrors from Skill sources.")
    args = parser.parse_args()
    errors = sync(args.write)
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    action = "updated" if args.write else "verified"
    print(f"portrait template mirrors: {action} ({len(mirror_pairs())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
