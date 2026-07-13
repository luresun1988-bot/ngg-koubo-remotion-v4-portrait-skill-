#!/usr/bin/env python3
"""Route shared semantic cases through visual-script generation and real Remotion stills."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "remotion-template"
FORMAT = "portrait" if "portrait" in SKILL_ROOT.name.lower() else "landscape"
SELECTED_CASE_IDS = [
    "numeric-complete",
    "numeric-incomplete",
    "automation-handoff",
    "keyword-process",
    "tool-explanation",
    "explicit-cta",
]
CASE_SCENE_TYPES = {
    "numeric-complete": "Process",
    "numeric-incomplete": "Contrast",
    "automation-handoff": "Process",
    "keyword-process": "Process",
    "tool-explanation": "Explanation",
    "explicit-cta": "CTA",
}
FRAMES_PER_CASE = 125
FPS = 25


def format_config() -> dict[str, Any]:
    portrait = FORMAT == "portrait"
    return {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait" if portrait else "ngg-koubo-remotion-v4",
        "format": "9:16" if portrait else "16:9",
        "width": 1080 if portrait else 1920,
        "height": 1920 if portrait else 1080,
        "compositionId": "NGGKouboV4Portrait" if portrait else "NGGKouboV4",
    }


def run_checked(label: str, command: list[str], cwd: Path | None = None) -> str:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
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
        details = "\n".join(part.rstrip() for part in [completed.stdout, completed.stderr] if part)
        raise RuntimeError(f"{label} failed with exit code {completed.returncode}\n{details}")
    return completed.stdout.strip()


def resolve_node_executable() -> str:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node is required for semantic render regression")
    resolved = run_checked("resolve node executable", [node, "-p", "process.execPath"]).splitlines()[-1].strip()
    return resolved if Path(resolved).is_file() else node


def resolve_browser_executable() -> str:
    candidates = [os.environ.get("REMOTION_BROWSER_EXECUTABLE", "")]
    if os.name == "nt":
        candidates.extend(
            [
                str(Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"),
                str(Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe"),
                str(Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe"),
                str(Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe"),
            ]
        )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    return ""


def mirror_template_public_assets(target_root: Path) -> None:
    source_root = TEMPLATE_ROOT / "public"
    skipped_fixture = Path("input") / "semantic_render_presenter.mp4"
    for source in source_root.rglob("*"):
        relative = source.relative_to(source_root)
        if relative == skipped_fixture:
            continue
        target = target_root / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, target)
        except (OSError, NotImplementedError):
            shutil.copy2(source, target)


def load_selected_cases() -> list[dict[str, Any]]:
    contract_path = SCRIPT_DIR / "semantic_contract_cases.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
    cases_by_id = {str(item.get("id")): item for item in contract.get("cases", []) if isinstance(item, dict)}
    missing = [case_id for case_id in SELECTED_CASE_IDS if case_id not in cases_by_id]
    if missing:
        raise AssertionError(f"shared semantic contract is missing selected cases: {missing}")
    return [cases_by_id[case_id] for case_id in SELECTED_CASE_IDS]


def build_visual_script(cases: list[dict[str, Any]]) -> dict[str, Any]:
    config = format_config()
    duration_frames = FRAMES_PER_CASE * len(cases)
    scenes: list[dict[str, Any]] = []
    cues: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        case_id = str(case["id"])
        scene_id = f"scene-{index + 1:02d}-{case_id}"
        cue_id = f"cap-{index + 1:02d}-{case_id}"
        start = index * FRAMES_PER_CASE
        end = start + FRAMES_PER_CASE
        text = str(case["text"])
        scenes.append(
            {
                "id": scene_id,
                "type": CASE_SCENE_TYPES[case_id],
                "segmentId": f"semantic-render-{index + 1:02d}",
                "startFrame": start,
                "endFrame": end,
                "semanticRole": str(case["intent"]),
                "presenterLayout": "fullscreen",
                "materialLayout": "none",
                "intent": f"Semantic render regression case: {case_id}",
                "sourceVideo": "input/semantic_render_presenter.mp4",
                "narrationText": text,
            }
        )
        cues.append(
            {
                "id": cue_id,
                "sceneId": scene_id,
                "startFrame": start + 5,
                "endFrame": end - 5,
                "text": text,
                "highlightWords": [],
            }
        )
    return {
        "schemaVersion": config["schemaVersion"],
        "sourceVideoMode": "raw-presenter",
        "projectConfigPath": "semantic-render-regression",
        "metadata": {"purpose": "semantic-to-render end-to-end regression", "version": 1},
        "composition": {
            "format": config["format"],
            "width": config["width"],
            "height": config["height"],
            "fps": FPS,
            "durationFrames": duration_frames,
        },
        "captionRenderMode": "embedded",
        "captionTimeline": {
            "sourceType": "provided",
            "sourcePath": "scripts/semantic_contract_cases.json",
            "method": "fixed-semantic-regression-cue-timecodes",
            "generatedBy": "semantic_render_regression.py",
            "notes": "Each shared contract sentence owns one fixed 125-frame scene; no proportional text timing is used.",
        },
        "researchNotes": [
            {
                "id": "semantic-render-regression",
                "topic": "semantic renderer contract",
                "summary": "Shared semantic contract cases rendered through the active format adapter.",
                "visualUse": "Regression evidence only.",
            }
        ],
        "media": [
            {
                "id": "semantic-render-presenter",
                "type": "video",
                "path": "input/semantic_render_presenter.mp4",
                "role": "presenter",
                "hasAudio": False,
            }
        ],
        "scenes": scenes,
        "captionCues": cues,
        "semanticBeats": [],
        "visualEvents": [],
        "audioCues": [],
        "qaFrames": [],
    }


def cue_id_for(case_id: str, cases: list[dict[str, Any]]) -> str:
    index = next(index for index, case in enumerate(cases) if str(case["id"]) == case_id)
    return f"cap-{index + 1:02d}-{case_id}"


def source_bound_beat(data: dict[str, Any], cue_id: str) -> dict[str, Any]:
    matches = [
        beat
        for beat in data.get("semanticBeats", [])
        if isinstance(beat, dict) and cue_id in [str(item) for item in beat.get("sourceCueIds", [])]
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one semantic beat for {cue_id}, found {len(matches)}")
    return matches[0]


def source_bound_event(data: dict[str, Any], beat_id: str, expected_type: str) -> dict[str, Any]:
    matches = [
        event
        for event in data.get("visualEvents", [])
        if isinstance(event, dict)
        and str(event.get("sourceBeatId") or "") == beat_id
        and str(event.get("type") or "") == expected_type
    ]
    if len(matches) != 1:
        actual = [
            str(event.get("type") or "")
            for event in data.get("visualEvents", [])
            if isinstance(event, dict) and str(event.get("sourceBeatId") or "") == beat_id
        ]
        raise AssertionError(f"expected one {expected_type} event for {beat_id}, found {actual}")
    return matches[0]


def render_frame_for(event: dict[str, Any], duration_frames: int) -> int:
    start = int(event.get("startFrame", 0) or 0)
    end = int(event.get("endFrame", start + 1) or start + 1)
    if end <= start:
        raise AssertionError(f"invalid event range: {event.get('id')} [{start},{end})")
    frame = start + max(1, round((end - start) * 0.58))
    return min(max(start, frame), min(end - 1, duration_frames - 1))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_dimensions(ffprobe: str, path: Path) -> str:
    return run_checked(
        f"ffprobe {path.name}",
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            str(path),
        ],
    ).strip()


def verify_case(case: dict[str, Any], beat: dict[str, Any], event: dict[str, Any]) -> dict[str, bool]:
    adapter = case["adapters"][FORMAT]
    modifiers = [str(item) for item in beat.get("semanticModifiers", [])]
    required_checks = [str(item) for item in beat.get("requiredChecks", [])]
    provenance = event.get("ctaProvenance") if isinstance(event.get("ctaProvenance"), dict) else {}
    expected_keyword = str(case.get("ctaKeyword") or "")
    return {
        "intent": beat.get("semanticIntent") == case["intent"],
        "visualForm": beat.get("visualForm") == adapter["visualForm"],
        "eventType": event.get("type") == adapter["eventType"],
        "modifiers": all(str(item) in modifiers for item in case.get("modifiersContain", [])),
        "requiredChecks": all(str(item) in required_checks for item in case.get("checksContain", [])),
        "ctaKeyword": not expected_keyword or provenance.get("keyword") == expected_keyword,
        "eventStatus": not adapter.get("eventStatus") or event.get("status") == adapter["eventStatus"],
        "eventText": not adapter.get("eventText") or event.get("text") == adapter["eventText"],
        "eventSubtext": not adapter.get("eventSubtext") or event.get("subtext") == adapter["eventSubtext"],
    }


def write_markdown_report(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# V4 {FORMAT.title()} Semantic-to-Render Regression",
        "",
        f"- Result: **{'PASS' if report['ok'] else 'FAIL'}**",
        f"- Composition: `{report['composition']['width']}x{report['composition']['height']} / {report['composition']['fps']}fps / {report['composition']['durationFrames']} frames`",
        f"- Cases rendered: `{len(report['cases'])}`",
        f"- Unique PNG hashes: `{report['uniqueStillHashes']}`",
        "",
        "| Case | Intent | Event | Frame | PNG |",
        "|---|---|---|---:|---|",
    ]
    for item in report["cases"]:
        lines.append(
            f"| `{item['id']}` | `{item['actualIntent']}` | `{item['actualEventType']}` | {item['renderFrame']} | `{item['stillPath']}` |"
        )
    lines.extend(
        [
            "",
            "Pipeline: shared contract text → caption cues → semantic router → visual event builder → schema validation → QA lint → Remotion still render.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    config = format_config()
    cases = load_selected_cases()
    output_root = SKILL_ROOT / "qa" / "semantic_render_regression" / FORMAT
    still_root = output_root / "stills"
    public_root = output_root / "public"
    presenter_root = public_root / "input"
    if output_root.exists():
        shutil.rmtree(output_root)
    still_root.mkdir(parents=True, exist_ok=True)
    mirror_template_public_assets(public_root)
    presenter_root.mkdir(parents=True, exist_ok=True)

    source_path = output_root / "visual_script.source.json"
    visual_script_path = output_root / "visual_script.generated.json"
    source_path.write_text(json.dumps(build_visual_script(cases), ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(source_path, visual_script_path)

    run_checked(
        "semantic router",
        [sys.executable, str(SCRIPT_DIR / "semantic_router.py"), "--visual-script", str(visual_script_path)],
        cwd=SKILL_ROOT,
    )
    run_checked(
        "visual event builder",
        [sys.executable, str(SCRIPT_DIR / "visual_event_builder.py"), "--visual-script", str(visual_script_path)],
        cwd=SKILL_ROOT,
    )
    run_checked(
        "visual script validation",
        [sys.executable, str(SCRIPT_DIR / "validate_visual_script.py"), str(visual_script_path)],
        cwd=SKILL_ROOT,
    )
    run_checked(
        "visual script QA lint",
        [
            sys.executable,
            str(SCRIPT_DIR / "qa_lint_visual_script.py"),
            "--visual-script",
            str(visual_script_path),
            "--out",
            str(output_root / "pre_render_lint.md"),
        ],
        cwd=SKILL_ROOT,
    )
    run_checked(
        "generated TypeScript writer",
        [
            sys.executable,
            str(SCRIPT_DIR / "write_generated_visual_script.py"),
            "--visual-script",
            str(visual_script_path),
            "--out",
            str(output_root / "generatedVisualScript.ts"),
        ],
        cwd=SKILL_ROOT,
    )

    data = json.loads(visual_script_path.read_text(encoding="utf-8-sig"))
    props_path = output_root / "remotion.props.json"
    props_path.write_text(json.dumps({"visualScript": data}, ensure_ascii=False), encoding="utf-8")

    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm is required for semantic render regression")
    if not (TEMPLATE_ROOT / "node_modules" / "@remotion" / "cli").is_dir():
        run_checked("npm install", [npm, "install"], cwd=TEMPLATE_ROOT)
    node = resolve_node_executable()
    remotion_cli = TEMPLATE_ROOT / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
    browser_executable = resolve_browser_executable()
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not remotion_cli.is_file() or not ffmpeg or not ffprobe:
        raise RuntimeError("Remotion CLI, ffmpeg, and ffprobe are required for semantic render regression")
    presenter_fixture = presenter_root / "semantic_render_presenter.mp4"
    run_checked(
        "deterministic presenter fixture",
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x16181d:s={config['width']}x{config['height']}:r={FPS}:d={len(cases) * FRAMES_PER_CASE / FPS}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(presenter_fixture),
        ],
        cwd=SKILL_ROOT,
    )

    case_results: list[dict[str, Any]] = []
    hashes: list[str] = []
    duration_frames = int(data["composition"]["durationFrames"])
    expected_dimensions = f"{config['width']}x{config['height']}"
    for index, case in enumerate(cases):
        case_id = str(case["id"])
        cue_id = cue_id_for(case_id, cases)
        beat = source_bound_beat(data, cue_id)
        adapter = case["adapters"][FORMAT]
        event = source_bound_event(data, str(beat.get("id") or ""), str(adapter["eventType"]))
        checks = verify_case(case, beat, event)
        if not all(checks.values()):
            raise AssertionError(f"semantic/event contract failed for {case_id}: {checks}")
        render_frame = render_frame_for(event, duration_frames)
        still_path = still_root / f"{index + 1:02d}_{case_id}.png"
        remotion_command = [
            node,
            str(remotion_cli),
            "still",
            "src/index.ts",
            str(config["compositionId"]),
            str(still_path),
            f"--frame={render_frame}",
            "--gl=angle",
            f"--props={props_path.as_posix()}",
            f"--public-dir={public_root.as_posix()}",
        ]
        if browser_executable:
            remotion_command.append(f"--browser-executable={browser_executable}")
        run_checked(
            f"Remotion still {case_id}",
            remotion_command,
            cwd=TEMPLATE_ROOT,
        )
        size = still_path.stat().st_size
        if size < 4096:
            raise AssertionError(f"rendered still is unexpectedly small: {still_path} ({size} bytes)")
        dimensions = probe_dimensions(ffprobe, still_path)
        if dimensions != expected_dimensions:
            raise AssertionError(f"still dimensions mismatch for {case_id}: {dimensions} != {expected_dimensions}")
        digest = sha256(still_path)
        hashes.append(digest)
        case_results.append(
            {
                "id": case_id,
                "text": case["text"],
                "cueId": cue_id,
                "beatId": beat.get("id"),
                "eventId": event.get("id"),
                "expectedIntent": case["intent"],
                "actualIntent": beat.get("semanticIntent"),
                "expectedEventType": adapter["eventType"],
                "actualEventType": event.get("type"),
                "eventStatus": event.get("status"),
                "renderFrame": render_frame,
                "checks": checks,
                "stillPath": str(still_path.relative_to(SKILL_ROOT)).replace("\\", "/"),
                "dimensions": dimensions,
                "bytes": size,
                "sha256": digest,
            }
        )

    if len(set(hashes)) != len(hashes):
        raise AssertionError("semantic render stills are not unique; renderer may have ignored generated input props")

    concat_path = output_root / "contact_sheet_inputs.txt"
    concat_path.write_text(
        "\n".join(f"file '{item.as_posix()}'" for item in sorted(still_root.glob("*.png"))) + "\n",
        encoding="ascii",
    )
    contact_sheet = output_root / "contact_sheet.png"
    run_checked(
        "semantic render contact sheet",
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-vf",
            "scale=480:-1,tile=3x2:padding=8:margin=8:color=0x101010",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(contact_sheet),
        ],
        cwd=SKILL_ROOT,
    )
    if contact_sheet.stat().st_size < 4096:
        raise AssertionError("semantic render contact sheet is unexpectedly small")

    report = {
        "schemaVersion": "ngg-v4-semantic-render-regression-v1",
        "format": FORMAT,
        "ok": True,
        "composition": data["composition"],
        "runtime": {"node": node, "browserExecutable": browser_executable or "remotion-managed"},
        "selectedCaseIds": SELECTED_CASE_IDS,
        "pipeline": [
            "shared-semantic-contract",
            "caption-cues",
            "semantic-router-cli",
            "visual-event-builder-cli",
            "schema-validation",
            "qa-lint",
            "typescript-serialization",
            "remotion-still-with-generated-props",
        ],
        "cases": case_results,
        "uniqueStillHashes": len(set(hashes)),
        "contactSheet": str(contact_sheet.relative_to(SKILL_ROOT)).replace("\\", "/"),
    }
    report_path = output_root / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(report, output_root / "report.md")
    for item in case_results:
        print(f"PASS {item['id']}: {item['actualIntent']} -> {item['actualEventType']} @ frame {item['renderFrame']}")
    print(f"semantic-to-render regression: {len(case_results)} / {len(cases)}")
    print(f"report: {report_path}")
    print(f"contact sheet: {contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
