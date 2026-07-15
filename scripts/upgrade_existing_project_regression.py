#!/usr/bin/env python3
"""Regression test for non-destructive existing-project runtime upgrades."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from upgrade_existing_project import source_directories, upgrade


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "06_remotion"
        (root / "src").mkdir(parents=True)
        (root / "public" / "input").mkdir(parents=True)
        (root / "scripts").mkdir(parents=True)
        visual = root / "visual_script.json"
        source_code = root / "src" / "custom.tsx"
        asset = root / "public" / "input" / "asset.bin"
        stale = root / "scripts" / "final_media_qa.py"
        visual.write_text('{"composition":{"fps":25}}', encoding="utf-8")
        source_code.write_text("export const custom = true;", encoding="utf-8")
        asset.write_bytes(b"project-asset")
        stale.write_text("old runtime", encoding="utf-8")

        dry_run = upgrade(root, write=False)
        if not any(item["name"] == "final_media_qa.py" and item["action"] == "update" for item in dry_run["operations"]):
            raise AssertionError(dry_run)
        for required_name in ["semantic_guardrails.py", "semantic_contract_cases.json"]:
            if not any(item["name"] == required_name and item["action"] == "add" for item in dry_run["operations"]):
                raise AssertionError(f"dry-run omitted shared semantic dependency: {required_name}")
        if not any(
            item["group"] == "src" and item["name"] == "V4Audio.tsx" and item["action"] == "add"
            for item in dry_run["operations"]
        ):
            raise AssertionError("dry-run omitted managed src/V4Audio.tsx")
        if stale.read_text(encoding="utf-8") != "old runtime":
            raise AssertionError("dry-run modified the project")

        report = upgrade(root, write=True)
        source_scripts, _ = source_directories()
        if stale.read_bytes() != (source_scripts / "final_media_qa.py").read_bytes():
            raise AssertionError("runtime file was not upgraded")
        for required_name in ["semantic_guardrails.py", "semantic_contract_cases.json"]:
            copied = root / "scripts" / required_name
            if copied.read_bytes() != (source_scripts / required_name).read_bytes():
                raise AssertionError(f"shared semantic dependency was not upgraded: {required_name}")
        managed_audio = root / "src" / "V4Audio.tsx"
        managed_source = next(
            Path(item["source"])
            for item in report["operations"]
            if item["group"] == "src" and item["name"] == "V4Audio.tsx"
        )
        if not managed_audio.is_file() or managed_audio.read_bytes() != managed_source.read_bytes():
            raise AssertionError("managed src/V4Audio.tsx was not installed")
        imported = subprocess.run(
            [sys.executable, "-c", "import semantic_router; print(semantic_router.classify_text('我刚刚关注你了', 75, 150)['semanticIntent'])"],
            cwd=root / "scripts",
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if imported.returncode != 0 or "explanation-claim" not in imported.stdout:
            raise AssertionError(f"upgraded semantic router import failed: {imported.stdout} {imported.stderr}")
        updated = next(item for item in report["operations"] if item["name"] == "final_media_qa.py")
        backup = Path(str(updated.get("backup") or ""))
        if not backup.is_file() or backup.read_text(encoding="utf-8") != "old runtime":
            raise AssertionError("stale runtime file was not backed up")
        if visual.read_text(encoding="utf-8") != '{"composition":{"fps":25}}':
            raise AssertionError("visual_script.json was overwritten")
        if source_code.read_text(encoding="utf-8") != "export const custom = true;":
            raise AssertionError("project src was overwritten")
        if asset.read_bytes() != b"project-asset":
            raise AssertionError("project asset was overwritten")
        report_path = root / "qa" / "runtime_upgrade_report.json"
        if not report_path.is_file() or json.loads(report_path.read_text(encoding="utf-8"))["mode"] != "write":
            raise AssertionError("upgrade report is missing")

    print("portrait existing-project upgrade regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
