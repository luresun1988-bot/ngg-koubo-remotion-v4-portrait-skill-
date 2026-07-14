#!/usr/bin/env python3
"""Run portable structural and optional QA gates against real historical V4 projects."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def load_validator():
    path = SCRIPT_DIR / "validate_visual_script.py"
    spec = importlib.util.spec_from_file_location("v4_real_corpus_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fraction(value: str) -> float:
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator)
    return float(value)


def probe_video(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required for real project corpus media checks")
    completed = subprocess.run(
        [
            ffprobe, "-v", "error", "-count_frames", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "ffprobe failed")
    streams = json.loads(completed.stdout or "{}").get("streams", [])
    if not streams:
        raise RuntimeError("final video has no video stream")
    stream = streams[0]
    return {
        "width": int(stream.get("width") or 0),
        "height": int(stream.get("height") or 0),
        "fps": fraction(str(stream.get("r_frame_rate") or "0")),
        "decodedFrames": int(stream.get("nb_read_frames") or 0),
    }


def lint_project(visual_script: Path, remotion_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ngg-v4-real-corpus-lint-") as temp_dir:
        report_path = Path(temp_dir) / "lint.md"
        completed = subprocess.run(
            [
                shutil.which("python") or "python",
                str(SCRIPT_DIR / "qa_lint_visual_script.py"),
                "--visual-script", str(visual_script),
                "--remotion-root", str(remotion_root),
                "--out", str(report_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        report = report_path.read_text(encoding="utf-8-sig") if report_path.is_file() else ""
    error_lines = [line[2:] for line in report.splitlines() if line.startswith("- ")]
    return {"passed": completed.returncode == 0, "exitCode": completed.returncode, "messages": error_lines[:40]}


def check_expected(data: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    exact_fields = {
        "schemaVersion": data.get("schemaVersion"),
        "sourceVideoMode": data.get("sourceVideoMode"),
        "format": composition.get("format"),
        "width": composition.get("width"),
        "height": composition.get("height"),
        "fps": composition.get("fps"),
        "durationFrames": composition.get("durationFrames"),
        "captionRenderMode": data.get("captionRenderMode"),
    }
    for key, actual in exact_fields.items():
        if key in expected and actual != expected[key]:
            errors.append(f"{key}: expected {expected[key]!r}, got {actual!r}")
    count_fields = {
        "minScenes": len(data.get("scenes", [])),
        "minCaptionCues": len(data.get("captionCues", [])),
        "minSemanticBeats": len(data.get("semanticBeats", [])),
        "minVisualEvents": len(data.get("visualEvents", [])),
    }
    for key, actual in count_fields.items():
        if key in expected and actual < int(expected[key]):
            errors.append(f"{key}: expected at least {expected[key]}, got {actual}")
    event_types = {str(event.get("type") or "") for event in data.get("visualEvents", []) if isinstance(event, dict)}
    intents = {str(beat.get("semanticIntent") or "") for beat in data.get("semanticBeats", []) if isinstance(beat, dict)}
    for event_type in expected.get("requiredEventTypes", []):
        if event_type not in event_types:
            errors.append(f"required event type is missing: {event_type}")
    for intent in expected.get("requiredSemanticIntents", []):
        if intent not in intents:
            errors.append(f"required semantic intent is missing: {intent}")
    return errors


def run_case(case: dict[str, Any], manifest_dir: Path, validator: Any) -> dict[str, Any]:
    case_id = str(case.get("id") or "unnamed")
    root = resolve_path(manifest_dir, str(case.get("remotionRoot") or ""))
    visual_script = resolve_path(root, str(case.get("visualScript") or "visual_script.json"))
    result: dict[str, Any] = {"id": case_id, "enforcement": case.get("enforcement", "gate"), "errors": [], "warnings": []}
    if not visual_script.is_file():
        result["errors"].append(f"visual script is missing: {visual_script}")
        result["passed"] = False
        return result
    try:
        data = json.loads(visual_script.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result["errors"].append(f"cannot read visual script: {exc}")
        result["passed"] = False
        return result
    result["errors"].extend(check_expected(data, case.get("expect", {})))

    if case.get("runValidator", True):
        validator_errors, validator_warnings = validator.validate(visual_script)
        result["validator"] = {"passed": not validator_errors, "errors": validator_errors, "warnings": validator_warnings}
        if case.get("requireValidatorPass", True) and validator_errors:
            result["errors"].append(f"validator failed with {len(validator_errors)} error(s)")
    if case.get("runLint", True):
        lint = lint_project(visual_script, root)
        result["lint"] = lint
        if case.get("requireLintPass", True) and not lint["passed"]:
            result["errors"].append(f"QA lint failed with exit code {lint['exitCode']}")

    final_value = case.get("finalVideo")
    if isinstance(final_value, str) and final_value:
        final_path = resolve_path(root, final_value)
        if not final_path.is_file():
            result["errors"].append(f"final video is missing: {final_path}")
        else:
            try:
                media = probe_video(final_path)
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                result["errors"].append(f"final video probe failed: {exc}")
            else:
                result["finalMedia"] = media
                composition = data.get("composition", {})
                for field in ("width", "height"):
                    if int(media[field]) != int(composition.get(field) or 0):
                        result["errors"].append(f"final {field} differs from composition: {media[field]} vs {composition.get(field)}")
                if abs(float(media["fps"]) - float(composition.get("fps") or 0)) > 0.001:
                    result["errors"].append(f"final fps differs from composition: {media['fps']} vs {composition.get('fps')}")
                if int(media["decodedFrames"]) != int(composition.get("durationFrames") or 0):
                    result["errors"].append(f"final frame count differs: {media['decodedFrames']} vs {composition.get('durationFrames')}")
    result["passed"] = not result["errors"]
    return result


def run_manifest(manifest_path: Path, skill: str) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    validator = load_validator()
    results = [
        run_case(case, manifest_path.parent, validator)
        for case in manifest.get("cases", [])
        if isinstance(case, dict) and str(case.get("skill") or "") in {"", skill}
    ]
    gated = [item for item in results if item.get("enforcement") != "audit"]
    return {"skill": skill, "passed": bool(gated) and all(item.get("passed") for item in gated), "cases": results}


def markdown_report(report: dict[str, Any]) -> str:
    lines = ["# V4 Real Project Corpus", "", f"Skill: {report.get('skill')}", f"Status: {'PASS' if report.get('passed') else 'FAIL'}", ""]
    for case in report.get("cases", []):
        lines.append(f"- {case.get('id')}: {'PASS' if case.get('passed') else 'ISSUES'} ({case.get('enforcement')})")
        for error in case.get("errors", []):
            lines.append(f"  - {error}")
        validator = case.get("validator", {})
        if validator and not validator.get("passed"):
            lines.append(f"  - observed validator errors: {len(validator.get('errors', []))}")
        lint = case.get("lint", {})
        if lint and not lint.get("passed"):
            lines.append(f"  - observed lint exit code: {lint.get('exitCode')}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--skill", choices=["landscape", "portrait"], required=True)
    parser.add_argument("--out")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    manifest_path = Path(args.manifest).resolve()
    report = run_manifest(manifest_path, args.skill)
    out_path = Path(args.out).resolve() if args.out else manifest_path.parent / f"real_project_corpus_{args.skill}.md"
    json_path = Path(args.json_out).resolve() if args.json_out else manifest_path.parent / f"real_project_corpus_{args.skill}.json"
    out_path.write_text(markdown_report(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"real project corpus ({args.skill}): {'PASS' if report.get('passed') else 'FAIL'}")
    print(f"wrote {out_path}")
    print(f"wrote {json_path}")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
