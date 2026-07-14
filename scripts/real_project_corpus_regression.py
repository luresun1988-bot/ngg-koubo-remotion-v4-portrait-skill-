#!/usr/bin/env python3
"""Regression checks for the optional historical-project corpus runner."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from real_project_corpus import run_manifest  # noqa: E402


def write_project(root: Path) -> None:
    root.mkdir(parents=True)
    payload = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "sourceVideoMode": "raw-presenter",
        "composition": {"format": "9:16", "width": 1080, "height": 1920, "fps": 25, "durationFrames": 250},
        "captionRenderMode": "none",
        "scenes": [{"id": "scene", "startFrame": 0, "endFrame": 250}],
        "captionCues": [{"id": "cue", "startFrame": 0, "endFrame": 250, "text": "真实项目语料"}],
        "semanticBeats": [{"id": "beat", "semanticIntent": "topic-intro"}],
        "visualEvents": [{"id": "event", "type": "topicKeyword"}],
    }
    (root / "visual_script.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ngg-v4-real-corpus-") as temp_dir:
        base = Path(temp_dir)
        project = base / "真实项目"
        write_project(project)
        good_case = {
            "id": "gate-pass",
            "skill": "portrait",
            "enforcement": "gate",
            "remotionRoot": str(project),
            "runValidator": False,
            "runLint": False,
            "expect": {
                "format": "9:16",
                "width": 1080,
                "height": 1920,
                "fps": 25,
                "durationFrames": 250,
                "minScenes": 1,
                "minCaptionCues": 1,
                "requiredEventTypes": ["topicKeyword"],
                "requiredSemanticIntents": ["topic-intro"],
            },
        }
        manifest = base / "manifest.json"
        manifest.write_text(json.dumps({"version": 1, "cases": [good_case]}), encoding="utf-8")
        passing = run_manifest(manifest, "portrait")
        if not passing.get("passed"):
            raise AssertionError(f"matching gate case must pass: {passing}")

        bad_gate = dict(good_case)
        bad_gate["id"] = "gate-fail"
        bad_gate["expect"] = {**good_case["expect"], "fps": 30}
        manifest.write_text(json.dumps({"version": 1, "cases": [bad_gate]}), encoding="utf-8")
        failing = run_manifest(manifest, "portrait")
        if failing.get("passed"):
            raise AssertionError(f"mismatched gate case must fail: {failing}")

        audit_case = dict(bad_gate)
        audit_case["id"] = "audit-observation"
        audit_case["enforcement"] = "audit"
        manifest.write_text(json.dumps({"version": 1, "cases": [good_case, audit_case]}), encoding="utf-8")
        audited = run_manifest(manifest, "portrait")
        if not audited.get("passed") or audited["cases"][1].get("passed"):
            raise AssertionError(f"audit issue must be reported without failing gated status: {audited}")

    print("real project corpus regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
