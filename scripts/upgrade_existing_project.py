#!/usr/bin/env python3
"""Safely refresh reusable V4 runtime scripts/references in an existing 06_remotion project."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


SOURCE_ROOT = Path(__file__).resolve().parents[1]


def source_directories() -> tuple[Path, Path]:
    bundled = SOURCE_ROOT / "assets" / "remotion-template"
    if (bundled / "scripts").is_dir() and (bundled / "references").is_dir():
        return bundled / "scripts", bundled / "references"
    return SOURCE_ROOT / "scripts", SOURCE_ROOT / "references"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def upgrade(remotion_root: Path, *, write: bool) -> dict[str, Any]:
    root = remotion_root.resolve()
    if not (root / "visual_script.json").is_file() or not (root / "src").is_dir():
        raise SystemExit(f"target is not a V4 Remotion root: {root}")
    source_scripts, source_references = source_directories()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_root = root / "qa" / "runtime_upgrade_backup" / timestamp
    operations: list[dict[str, Any]] = []

    source_files = [
        *sorted(path for path in source_scripts.iterdir() if path.is_file() and path.suffix.lower() in {".py", ".ps1", ".json"}),
        *sorted(source_references.glob("*.md")),
    ]
    for source in source_files:
        group = "scripts" if source.parent == source_scripts else "references"
        target = root / group / source.name
        same = target.is_file() and sha256(source) == sha256(target)
        operation = {
            "group": group,
            "name": source.name,
            "source": str(source),
            "target": str(target),
            "action": "unchanged" if same else ("update" if target.exists() else "add"),
            "backup": None,
        }
        if write and not same:
            if target.is_file():
                backup = backup_root / group / source.name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                operation["backup"] = str(backup)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        operations.append(operation)

    report = {
        "schemaVersion": "ngg-v4-portrait-runtime-upgrade-v1",
        "mode": "write" if write else "dry-run",
        "remotionRoot": str(root),
        "sourceRoot": str(SOURCE_ROOT),
        "operations": operations,
        "preserved": [
            "visual_script.json",
            "src/",
            "public/",
            "config/",
            "package.json",
            "package-lock.json",
        ],
    }
    if write:
        report_path = root / "qa" / "runtime_upgrade_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remotion-root", required=True, type=Path)
    parser.add_argument("--write", action="store_true", help="Apply the upgrade. Without this flag, print a dry-run plan.")
    parser.add_argument("--out", type=Path, help="Optional dry-run/write report copy.")
    args = parser.parse_args()
    report = upgrade(args.remotion_root, write=args.write)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered)
    changes = sum(item["action"] != "unchanged" for item in report["operations"])
    print(f"runtime upgrade {'applied' if args.write else 'planned'}: {changes} change(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
