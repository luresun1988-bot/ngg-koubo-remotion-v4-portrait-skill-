#!/usr/bin/env python3
"""Render and inspect a 25 fps presenter/PiP/audio continuity fixture."""

from __future__ import annotations

from array import array
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import wave
from typing import Any

from PIL import Image, ImageChops, ImageStat

from semantic_render_regression import (
    mirror_template_public_assets,
    resolve_browser_executable,
    resolve_node_executable,
    run_checked,
)


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "remotion-template"
FORMAT = "portrait" if "portrait" in SKILL_ROOT.name.lower() else "landscape"
FPS = 25
DURATION_FRAMES = 300
DURATION_SECONDS = DURATION_FRAMES / FPS
SCENE_BOUNDARIES = (0, 75, 150, 225, DURATION_FRAMES)
PUNCH_START = 155
PUNCH_END = 215


def format_config() -> dict[str, Any]:
    portrait = FORMAT == "portrait"
    return {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait" if portrait else "ngg-koubo-remotion-v4",
        "format": "9:16" if portrait else "16:9",
        "width": 1080 if portrait else 1920,
        "height": 1920 if portrait else 1080,
        "compositionId": "NGGKouboV4Portrait" if portrait else "NGGKouboV4",
        "peakScale": 1.08 if portrait else 1.10,
    }


def build_visual_script() -> dict[str, Any]:
    config = format_config()
    scene_specs = [
        ("scene-01-hook", "Hook", 0, 75, "theme-thesis", "fullscreen", "none", "主题观点"),
        ("scene-02-proof", "Proof", 75, 150, "proof-focus", "pip", "main", "证明素材播放"),
        ("scene-03-return", "Explanation", 150, 225, "positive-confirm", "fullscreen", "none", "音画连续"),
        ("scene-04-cta", "CTA", 225, 300, "cta-resolve", "fullscreen", "none", "评论区回复数字人领取模板"),
    ]
    scenes: list[dict[str, Any]] = []
    cues: list[dict[str, Any]] = []
    beats: list[dict[str, Any]] = []
    for index, (scene_id, scene_type, start, end, role, presenter, material, text) in enumerate(scene_specs, 1):
        cue_id = f"cap-{index:02d}"
        beat_id = f"beat-{index:02d}"
        scenes.append(
            {
                "id": scene_id,
                "type": scene_type,
                "segmentId": f"dynamic-continuity-{index:02d}",
                "startFrame": start,
                "endFrame": end,
                "semanticRole": role,
                "presenterLayout": presenter,
                "materialLayout": material,
                "intent": f"Dynamic continuity regression: {role}",
                "sourceVideo": "input/dynamic_presenter_video_only.mp4",
                "narrationText": text,
            }
        )
        cues.append(
            {
                "id": cue_id,
                "sceneId": scene_id,
                "startFrame": start,
                "endFrame": end,
                "text": text,
                "highlightWords": [],
            }
        )
        beats.append(
            {
                "id": beat_id,
                "sceneId": scene_id,
                "startFrame": start,
                "endFrame": end,
                "text": text,
                "semanticIntent": role,
                "visualForm": "runtime-regression",
                "confidence": 1.0,
                "sourceCueIds": [cue_id],
                "requiredChecks": ["runtime-continuity"],
            }
        )

    cta_provenance: dict[str, Any]
    if FORMAT == "portrait":
        cta_provenance = {
            "kind": "keyword",
            "sourceText": "评论区回复数字人领取模板",
            "action": "评论区回复",
            "keyword": "数字人",
        }
    else:
        cta_provenance = {
            "actions": [{"kind": "reply", "sourceText": "评论区回复"}],
            "keyword": "数字人",
        }
    beats[-1]["ctaProvenance"] = copy.deepcopy(cta_provenance)

    visual_events: list[dict[str, Any]] = [
        {
            "id": "corner-hook",
            "sceneId": "scene-01-hook",
            "type": "cornerChapterLabel",
            "startFrame": 5,
            "endFrame": 70,
            "text": "主题观点",
            "subtext": "动态回归",
            "sourceBeatId": "beat-01",
            "semanticRole": "chapter-label",
            "motionType": "corner-slide-fade",
        },
        {
            "id": "corner-proof-must-hide",
            "sceneId": "scene-02-proof",
            "type": "cornerChapterLabel",
            "startFrame": 75,
            "endFrame": 150,
            "text": "不应出现",
            "subtext": "PiP证明场景",
            "sourceBeatId": "beat-02",
            "semanticRole": "chapter-label",
            "motionType": "corner-slide-fade",
        },
        {
            "id": "material-proof",
            "sceneId": "scene-02-proof",
            "type": "materialMain",
            "startFrame": 75,
            "endFrame": 150,
            "text": "证明素材",
            "assetPath": "input/dynamic_proof.mp4",
            "sourceBeatId": "beat-02",
            "semanticRole": "proof-focus",
            "motionType": "screen-recording-proof",
            "style": "recording-proof",
            "densityMode": "proof-focus",
        },
        {
            "id": "corner-return",
            "sceneId": "scene-03-return",
            "type": "cornerChapterLabel",
            "startFrame": 150,
            "endFrame": 225,
            "text": "重点强调",
            "subtext": "音画连续",
            "sourceBeatId": "beat-03",
            "semanticRole": "chapter-label",
            "motionType": "corner-slide-fade",
        },
        {
            "id": "impact-short-fast",
            "sceneId": "scene-03-return",
            "type": "presenterReposition",
            "startFrame": PUNCH_START,
            "endFrame": PUNCH_END,
            "text": "短促重点",
            "sourceBeatId": "beat-03",
            "semanticRole": "positive-confirm",
            "motionType": "presenter-impact-punch",
            "presenterPeakScale": config["peakScale"],
        },
        {
            "id": "confirm-continuity",
            "sceneId": "scene-03-return",
            "type": "statusSticker",
            "startFrame": 155,
            "endFrame": 215,
            "text": "音画连续",
            "subtext": "已验证",
            "status": "complete",
            "emphasisWords": ["连续"],
            "iconName": "check-circle",
            "sourceBeatId": "beat-03",
            "semanticRole": "positive-confirm",
            "motionType": "confirm-pop",
            "safeArea": "left-safe",
        },
        {
            "id": "corner-cta",
            "sceneId": "scene-04-cta",
            "type": "cornerChapterLabel",
            "startFrame": 225,
            "endFrame": 300,
            "text": "收束行动",
            "subtext": "回归通过",
            "sourceBeatId": "beat-04",
            "semanticRole": "chapter-label",
            "motionType": "corner-slide-fade",
        },
        {
            "id": "cta-final",
            "sceneId": "scene-04-cta",
            "type": "ctaTitle",
            "startFrame": 230,
            "endFrame": 295,
            "text": "评论区回复",
            "subtext": "领取模板",
            "status": "关键词：数字人",
            "sourceBeatId": "beat-04",
            "semanticRole": "cta-resolve",
            "motionType": "cta-result-keyword",
            "timingClass": "short-lightweight",
            "ctaProvenance": cta_provenance,
        },
    ]

    return {
        "schemaVersion": config["schemaVersion"],
        "sourceVideoMode": "segmented-presenter",
        "projectConfigPath": "dynamic-continuity-regression",
        "metadata": {"purpose": "25fps rendered presenter continuity regression", "version": 1},
        "composition": {
            "format": config["format"],
            "width": config["width"],
            "height": config["height"],
            "fps": FPS,
            "durationFrames": DURATION_FRAMES,
        },
        "captionRenderMode": "none",
        "captionTimeline": {
            "sourceType": "provided",
            "sourcePath": "dynamic-continuity-regression",
            "method": "fixed-runtime-regression-timecodes",
            "generatedBy": "dynamic_continuity_regression.py",
            "notes": "Authoritative cues are retained while captionRenderMode=none suppresses the visual layer.",
        },
        "presenterAudio": {
            "mode": "normalized-wav",
            "path": "input/dynamic_presenter_narration_48k.wav",
            "sampleRate": 48000,
            "syncOffsetFrames": 0,
            "syncEvidence": "Synthetic four-frequency continuity fixture aligned at frame 0.",
            "normalizationReportPath": "qa/dynamic_continuity_regression.json",
        },
        "researchNotes": [
            {
                "id": "runtime-continuity",
                "topic": "presenter continuity",
                "summary": "Synthetic deterministic regression fixture.",
                "visualUse": "Test evidence only.",
            }
        ],
        "media": [
            {
                "id": "dynamic-presenter",
                "type": "video",
                "path": "input/dynamic_presenter_video_only.mp4",
                "role": "presenter",
                "hasAudio": False,
            },
            {
                "id": "dynamic-proof",
                "type": "video",
                "path": "input/dynamic_proof.mp4",
                "role": "proof",
                "hasAudio": False,
            },
        ],
        "scenes": scenes,
        "captionCues": cues,
        "semanticBeats": beats,
        "visualEvents": visual_events,
        "audioCues": [],
        "qaFrames": [
            {"frame": 40, "reason": "Hook presenter fullscreen and corner label sample.", "checks": ["presenter", "corner-label", "caption-none"]},
            {"frame": 105, "reason": "Material proof and presenter PiP sample.", "checks": ["material", "presenter-pip", "corner-label-hidden"]},
            {"frame": 180, "reason": "Presenter impact peak sample.", "checks": ["presenter", "short-impact"]},
            {"frame": 250, "reason": "CTA presenter fullscreen and corner label sample.", "checks": ["CTA", "presenter", "corner-label"]},
        ],
    }


def write_tone_fixture(path: Path) -> None:
    sample_rate = 48000
    frequencies = (310.0, 530.0, 790.0, 1130.0)
    phase = 0.0
    chunk = array("h")
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample_index in range(round(DURATION_SECONDS * sample_rate)):
            segment = min(3, int(sample_index / (sample_rate * 3)))
            phase += 2 * math.pi * frequencies[segment] / sample_rate
            value = int(round(math.sin(phase) * 9000))
            chunk.extend((value, value))
            if len(chunk) >= 16384:
                wav_file.writeframes(chunk.tobytes())
                chunk = array("h")
        if chunk:
            wav_file.writeframes(chunk.tobytes())


def create_media_fixtures(ffmpeg: str, public_root: Path, config: dict[str, Any]) -> None:
    input_root = public_root / "input"
    input_root.mkdir(parents=True, exist_ok=True)
    presenter = input_root / "dynamic_presenter_video_only.mp4"
    proof = input_root / "dynamic_proof.mp4"
    narration = input_root / "dynamic_presenter_narration_48k.wav"
    presenter_filter = (
        "drawbox=x=iw*0.42:y=ih*0.28:w=iw*0.16:h=ih*0.18:color=0x20E0B0:t=fill,"
        "drawbox=x=iw*0.08:y=ih*0.72:w=iw*0.12:h=ih*0.08:color=0xE7C84B:t=fill"
    )
    run_checked(
        "dynamic presenter fixture",
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x7A1736:s={config['width']}x{config['height']}:r={FPS}:d={DURATION_SECONDS}",
            "-vf",
            presenter_filter,
            "-frames:v",
            str(DURATION_FRAMES),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(presenter),
        ],
    )
    run_checked(
        "dynamic proof fixture",
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={config['width']}x{config['height']}:rate={FPS}:duration=3",
            "-vf",
            "format=gray,format=yuv420p",
            "-frames:v",
            "75",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(proof),
        ],
    )
    write_tone_fixture(narration)


def remotion_command_base(
    node: str,
    remotion_cli: Path,
    config: dict[str, Any],
    props_path: Path,
    public_root: Path,
    browser_executable: str,
) -> list[str]:
    command = [
        node,
        str(remotion_cli),
        "src/index.ts",
        str(config["compositionId"]),
    ]
    return command


def render_still(
    label: str,
    output: Path,
    frame: int,
    node: str,
    remotion_cli: Path,
    config: dict[str, Any],
    props_path: Path,
    public_root: Path,
    browser_executable: str,
) -> None:
    command = remotion_command_base(node, remotion_cli, config, props_path, public_root, browser_executable)
    command[2:2] = ["still"]
    command.extend(
        [
            str(output),
            f"--frame={frame}",
            "--gl=angle",
            f"--props={props_path.as_posix()}",
            f"--public-dir={public_root.as_posix()}",
        ]
    )
    if browser_executable:
        command.append(f"--browser-executable={browser_executable}")
    run_checked(label, command, cwd=TEMPLATE_ROOT)


def render_final(
    raw_path: Path,
    final_path: Path,
    node: str,
    remotion_cli: Path,
    config: dict[str, Any],
    props_path: Path,
    public_root: Path,
    browser_executable: str,
    ffmpeg: str,
) -> None:
    command = remotion_command_base(node, remotion_cli, config, props_path, public_root, browser_executable)
    command[2:2] = ["render"]
    command.extend(
        [
            str(raw_path),
            f"--frames=0-{DURATION_FRAMES - 1}",
            "--codec=h264",
            "--audio-codec=aac",
            "--pixel-format=yuv420p",
            "--concurrency=1",
            "--crf=18",
            "--gl=angle",
            f"--props={props_path.as_posix()}",
            f"--public-dir={public_root.as_posix()}",
        ]
    )
    if browser_executable:
        command.append(f"--browser-executable={browser_executable}")
    run_checked("dynamic Remotion render", command, cwd=TEMPLATE_ROOT)
    run_checked(
        "BT.709 postprocess",
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(raw_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-vf",
            "scale=out_range=tv:out_color_matrix=bt709,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-color_range",
            "tv",
            "-colorspace",
            "bt709",
            "-color_trc",
            "bt709",
            "-color_primaries",
            "bt709",
            "-x264-params",
            "colorprim=bt709:transfer=bt709:colormatrix=bt709",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(final_path),
        ],
    )


def extract_frames(ffmpeg: str, video: Path, frame_numbers: list[int], output_root: Path) -> dict[int, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    expression = "select=" + "+".join(f"eq(n\\,{frame})" for frame in frame_numbers)
    pattern = output_root / "raw_%03d.png"
    run_checked(
        "extract dynamic QA frames",
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video),
            "-vf",
            expression,
            "-vsync",
            "0",
            "-start_number",
            "0",
            str(pattern),
        ],
    )
    raw_paths = sorted(output_root.glob("raw_*.png"))
    if len(raw_paths) != len(frame_numbers):
        raise AssertionError(f"expected {len(frame_numbers)} extracted frames, found {len(raw_paths)}")
    result: dict[int, Path] = {}
    for frame, raw in zip(frame_numbers, raw_paths):
        target = output_root / f"frame_{frame:04d}.png"
        raw.replace(target)
        result[frame] = target
    return result


def blue_rail_pixels(path: Path) -> int:
    image = Image.open(path).convert("RGB")
    if FORMAT == "portrait":
        crop = image.crop((30, 54, 43, 120))
    else:
        crop = image.crop((42, 38, 56, 112))
    return sum(
        1
        for red, green, blue in crop.get_flattened_data()
        if blue > 100 and blue > red + 20 and blue > green + 15
    )


def red_presenter_pixels(path: Path) -> int:
    image = Image.open(path).convert("RGB")
    small = image.resize((max(1, image.width // 4), max(1, image.height // 4)), Image.Resampling.NEAREST)
    return sum(
        1
        for red, green, blue in small.get_flattened_data()
        if red > 72 and green < 85 and red > green * 1.7 and red > blue * 1.25
    )


def green_box_width(path: Path) -> int:
    image = Image.open(path).convert("RGB")
    crop_left = round(image.width * 0.32)
    crop_top = round(image.height * 0.14)
    crop = image.crop((crop_left, crop_top, round(image.width * 0.68), round(image.height * 0.60)))
    coordinates: list[tuple[int, int]] = []
    for y in range(crop.height):
        for x in range(crop.width):
            red, green, blue = crop.getpixel((x, y))
            if green > 135 and red < 105 and blue < 215 and green > red * 1.45:
                coordinates.append((x, y))
    if not coordinates:
        raise AssertionError(f"green impact marker missing: {path}")
    xs = [point[0] for point in coordinates]
    return max(xs) - min(xs) + 1


def image_difference(left: Path, right: Path, crop_box: tuple[int, int, int, int] | None = None) -> float:
    first = Image.open(left).convert("RGB")
    second = Image.open(right).convert("RGB")
    if crop_box:
        first = first.crop(crop_box)
        second = second.crop(crop_box)
    difference = ImageChops.difference(first, second)
    return sum(ImageStat.Stat(difference).mean) / 3


def analyze_audio(ffmpeg: str, final_path: Path, output_root: Path) -> dict[str, Any]:
    decoded = output_root / "decoded_audio.wav"
    run_checked(
        "decode continuity audio",
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(final_path),
            "-vn",
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(decoded),
        ],
    )
    with wave.open(str(decoded), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        raw = array("h")
        raw.frombytes(wav_file.readframes(wav_file.getnframes()))
    samples = raw[0::channels]

    def window(center_seconds: float, duration_seconds: float) -> array:
        half = round(duration_seconds * sample_rate / 2)
        center = round(center_seconds * sample_rate)
        return samples[max(0, center - half) : min(len(samples), center + half)]

    def zero_cross_frequency(values: array) -> float:
        if len(values) < 2:
            return 0.0
        crossings = 0
        previous = values[0]
        for current in values[1:]:
            if (previous < 0 <= current) or (previous >= 0 > current):
                crossings += 1
            previous = current
        seconds = (len(values) - 1) / sample_rate
        return crossings / (2 * seconds) if seconds > 0 else 0.0

    def rms(values: array) -> float:
        if not values:
            return 0.0
        return math.sqrt(sum(float(value) * float(value) for value in values) / len(values))

    expected = [(1.5, 310.0), (3.8, 530.0), (6.8, 790.0), (9.8, 1130.0)]
    measured = []
    for center, target in expected:
        actual = zero_cross_frequency(window(center, 0.5))
        if abs(actual - target) > max(12.0, target * 0.035):
            raise AssertionError(f"audio continuity frequency mismatch at {center:.1f}s: {actual:.1f}Hz != {target:.1f}Hz")
        measured.append({"centerSeconds": center, "expectedHz": target, "measuredHz": round(actual, 2)})

    boundary_rms = []
    for boundary in (3.0, 6.0, 9.0):
        before = rms(window(boundary - 0.035, 0.05))
        after = rms(window(boundary + 0.035, 0.05))
        if min(before, after) < 900:
            raise AssertionError(f"audio dropout near {boundary:.1f}s: before={before:.1f}, after={after:.1f}")
        boundary_rms.append({"boundarySeconds": boundary, "beforeRms": round(before, 1), "afterRms": round(after, 1)})
    return {
        "decodedPath": str(decoded.relative_to(SKILL_ROOT)).replace("\\", "/"),
        "sampleRate": sample_rate,
        "channels": channels,
        "decodedSamplesPerChannel": len(samples),
        "frequencies": measured,
        "boundaryRms": boundary_rms,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_contact_sheet(ffmpeg: str, stills: dict[int, Path], output: Path) -> None:
    concat = output.with_suffix(".inputs.txt")
    concat.write_text("\n".join(f"file '{stills[frame].as_posix()}'" for frame in sorted(stills)) + "\n", encoding="ascii")
    run_checked(
        "dynamic contact sheet",
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
            str(concat),
            "-vf",
            "scale=320:-1,tile=5x5:padding=6:margin=8:color=0x101010",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(output),
        ],
    )


def main() -> int:
    config = format_config()
    output_root = SKILL_ROOT / "qa" / "dynamic_continuity_regression" / FORMAT
    public_root = output_root / "public"
    still_root = output_root / "stills"
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    still_root.mkdir(parents=True, exist_ok=True)
    mirror_template_public_assets(public_root)

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    npm = shutil.which("npm")
    if not ffmpeg or not ffprobe or not npm:
        raise RuntimeError("ffmpeg, ffprobe, and npm are required for dynamic continuity regression")
    create_media_fixtures(ffmpeg, public_root, config)

    normalization_report = {
        "schemaVersion": "ngg-v4-presenter-normalization-v1",
        "resolvedAudioMode": "normalized-wav",
        "compositionFps": FPS,
        "normalizationApplied": True,
        "frameRate": {
            "compositionFps": FPS,
            "mixedPresenterFps": False,
            "requiresCfrNormalization": False,
        },
        "output": {
            "totalFrames": DURATION_FRAMES,
            "totalSamples": round(DURATION_SECONDS * 48000),
        },
        "verification": {"passed": True},
    }
    declared_report = output_root / "qa" / "dynamic_continuity_regression.json"
    standard_report = output_root / "qa" / "media" / "presenter_normalization.json"
    declared_report.parent.mkdir(parents=True, exist_ok=True)
    standard_report.parent.mkdir(parents=True, exist_ok=True)
    report_text = json.dumps(normalization_report, ensure_ascii=False, indent=2)
    declared_report.write_text(report_text, encoding="utf-8")
    standard_report.write_text(report_text, encoding="utf-8")

    data = build_visual_script()
    visual_script_path = output_root / "visual_script.json"
    visual_script_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    props_path = output_root / "remotion.props.json"
    props_path.write_text(json.dumps({"visualScript": data}, ensure_ascii=False), encoding="utf-8")

    run_checked("dynamic visual script validation", [sys.executable, str(SCRIPT_DIR / "validate_visual_script.py"), str(visual_script_path)], cwd=SKILL_ROOT)
    run_checked(
        "dynamic visual script lint",
        [
            sys.executable,
            str(SCRIPT_DIR / "qa_lint_visual_script.py"),
            "--visual-script",
            str(visual_script_path),
            "--remotion-root",
            str(output_root),
            "--out",
            str(output_root / "pre_render_lint.md"),
        ],
        cwd=SKILL_ROOT,
    )

    if not (TEMPLATE_ROOT / "node_modules" / "@remotion" / "cli").is_dir():
        run_checked("npm install", [npm, "install"], cwd=TEMPLATE_ROOT)
    node = resolve_node_executable()
    remotion_cli = TEMPLATE_ROOT / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
    browser_executable = resolve_browser_executable()
    if not remotion_cli.is_file():
        raise RuntimeError(f"missing Remotion CLI: {remotion_cli}")

    composition_source = (TEMPLATE_ROOT / "src" / "V4Composition.tsx").read_text(encoding="utf-8")
    if composition_source.count("<OffthreadVideo") != 1:
        raise AssertionError("primary presenter must have exactly one OffthreadVideo mount in V4Composition.tsx")
    if composition_source.count("<PresenterAudioLayer") != 1:
        raise AssertionError("normalized presenter audio must be mounted exactly once")

    no_caption_still = output_root / "caption_none.png"
    embedded_caption_still = output_root / "caption_embedded_control.png"
    render_still("caption-none still", no_caption_still, 40, node, remotion_cli, config, props_path, public_root, browser_executable)
    caption_control = copy.deepcopy(data)
    caption_control["captionRenderMode"] = "embedded"
    caption_control_props = output_root / "caption_control.props.json"
    caption_control_props.write_text(json.dumps({"visualScript": caption_control}, ensure_ascii=False), encoding="utf-8")
    render_still("caption control still", embedded_caption_still, 40, node, remotion_cli, config, caption_control_props, public_root, browser_executable)
    caption_crop = (0, round(config["height"] * 0.70), config["width"], config["height"])
    caption_difference = image_difference(no_caption_still, embedded_caption_still, caption_crop)
    if caption_difference < 0.8:
        raise AssertionError(f"captionRenderMode=none visual gate was not observable: mean difference={caption_difference:.3f}")

    raw_path = output_root / "dynamic_continuity.remotion-raw.mp4"
    final_path = output_root / "dynamic_continuity.bt709.mp4"
    render_final(raw_path, final_path, node, remotion_cli, config, props_path, public_root, browser_executable, ffmpeg)

    media_report_path = output_root / "final_media_qa.md"
    media_json_path = output_root / "final_media_qa.json"
    run_checked(
        "dynamic final media QA",
        [
            sys.executable,
            str(SCRIPT_DIR / "final_media_qa.py"),
            "--video",
            str(final_path),
            "--visual-script",
            str(visual_script_path),
            "--out",
            str(media_report_path),
            "--json-out",
            str(media_json_path),
        ],
        cwd=SKILL_ROOT,
    )
    media_report = json.loads(media_json_path.read_text(encoding="utf-8-sig"))
    if not media_report.get("passed"):
        raise AssertionError(media_report)

    requested_frames = sorted(
        {
            40,
            74,
            75,
            80,
            85,
            90,
            95,
            105,
            115,
            125,
            130,
            135,
            140,
            145,
            149,
            150,
            160,
            154,
            155,
            159,
            170,
            185,
            199,
            205,
            214,
            215,
            250,
        }
    )
    stills = extract_frames(ffmpeg, final_path, requested_frames, still_root)

    label_counts = {frame: blue_rail_pixels(stills[frame]) for frame in (40, 105, 160, 250)}
    for frame in (40, 160, 250):
        if label_counts[frame] < 30:
            raise AssertionError(f"fullscreen corner label missing at frame {frame}: {label_counts[frame]} blue rail pixels")
    if label_counts[105] > 18:
        raise AssertionError(f"proof/PiP corner label was not suppressed at frame 105: {label_counts[105]} blue rail pixels")

    transition_frames = (74, 75, 80, 85, 90, 95, 105, 130, 135, 140, 145, 149, 150)
    presenter_pixels = {frame: red_presenter_pixels(stills[frame]) for frame in transition_frames}
    if abs(presenter_pixels[74] - presenter_pixels[75]) / max(1, presenter_pixels[74]) > 0.05:
        raise AssertionError(f"fullscreen-to-PiP boundary starts with a hard jump: {presenter_pixels[74]} -> {presenter_pixels[75]}")
    entry = [presenter_pixels[frame] for frame in (75, 80, 85, 90, 95)]
    if any(next_value > value * 1.03 for value, next_value in zip(entry, entry[1:])):
        raise AssertionError(f"PiP entry is not monotonic: {entry}")
    if entry[-1] >= entry[0] * 0.16:
        raise AssertionError(f"PiP entry did not reach compact geometry: {entry}")
    exit_values = [presenter_pixels[frame] for frame in (130, 135, 140, 145, 149)]
    if any(next_value < value * 0.97 for value, next_value in zip(exit_values, exit_values[1:])):
        raise AssertionError(f"PiP return is not monotonic: {exit_values}")
    if exit_values[-1] <= exit_values[0] * 5:
        raise AssertionError(f"PiP return did not reach fullscreen geometry: {exit_values}")
    if abs(presenter_pixels[149] - presenter_pixels[150]) / max(1, presenter_pixels[150]) > 0.05:
        raise AssertionError(f"PiP return did not land on frame 150: {presenter_pixels[149]} -> {presenter_pixels[150]}")

    proof_crop = (
        round(config["width"] * 0.28),
        round(config["height"] * 0.22),
        round(config["width"] * 0.76),
        round(config["height"] * 0.62),
    )
    proof_differences = [
        image_difference(stills[105], stills[115], proof_crop),
        image_difference(stills[115], stills[125], proof_crop),
    ]
    if min(proof_differences) < 0.02:
        raise AssertionError(f"proof video appears static: {proof_differences}")

    impact_frames = (154, 155, 159, 170, 185, 199, 205, 214, 215)
    impact_widths = {frame: green_box_width(stills[frame]) for frame in impact_frames}
    baseline_width = impact_widths[154]
    minimum_peak_ratio = 1.055 if FORMAT == "portrait" else 1.07
    if impact_widths[159] < baseline_width * minimum_peak_ratio:
        raise AssertionError(f"presenter impact peak is too weak: {impact_widths}")
    held_widths = [impact_widths[frame] for frame in (159, 170, 185, 199)]
    if max(held_widths) - min(held_widths) > baseline_width * 0.02:
        raise AssertionError(f"presenter impact did not hold its peak scale: {impact_widths}")
    if not (baseline_width * 1.015 < impact_widths[205] < impact_widths[199]):
        raise AssertionError(f"presenter impact did not return during the semantic exit: {impact_widths}")
    if abs(impact_widths[214] - baseline_width) / baseline_width > 0.035:
        raise AssertionError(f"presenter impact did not return by its final frame: {impact_widths}")
    if abs(impact_widths[215] - baseline_width) / baseline_width > 0.035:
        raise AssertionError(f"presenter scale drifted after the impact event: {impact_widths}")

    audio_report = analyze_audio(ffmpeg, final_path, output_root)
    contact_sheet = output_root / "contact_sheet.png"
    write_contact_sheet(ffmpeg, stills, contact_sheet)

    report = {
        "schemaVersion": "ngg-v4-dynamic-continuity-regression-v1",
        "format": FORMAT,
        "passed": True,
        "composition": data["composition"],
        "checks": {
            "singlePresenterMount": True,
            "singleNormalizedAudioMount": True,
            "captionRenderModeNone": True,
            "captionControlMeanDifference": round(caption_difference, 3),
            "cornerLabelBluePixels": label_counts,
            "presenterTransitionPixels": presenter_pixels,
            "proofFrameMeanDifferences": [round(value, 3) for value in proof_differences],
            "impactMarkerWidths": impact_widths,
            "audioContinuity": audio_report,
            "finalMediaQa": media_report,
        },
        "artifacts": {
            "video": str(final_path.relative_to(SKILL_ROOT)).replace("\\", "/"),
            "videoSha256": sha256(final_path),
            "contactSheet": str(contact_sheet.relative_to(SKILL_ROOT)).replace("\\", "/"),
            "finalMediaQa": str(media_report_path.relative_to(SKILL_ROOT)).replace("\\", "/"),
        },
    }
    report_path = output_root / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = [
        f"# V4 {FORMAT.title()} Dynamic Continuity Regression",
        "",
        "- Result: **PASS**",
        f"- Composition: `{config['width']}x{config['height']} / {FPS}fps / {DURATION_FRAMES} frames`",
        "- Timeline: fullscreen presenter → proof material + PiP → fullscreen return → CTA",
        "- Audio: one 48 kHz stereo WAV with four unique frequency sections; no dropout at 3s/6s/9s boundaries",
        "- Motion: 60-frame presenter impact with a 4-frame push, peak hold, and return synchronized to the companion semantic exit",
        f"- Final video SHA-256: `{report['artifacts']['videoSha256']}`",
        "",
        f"Contact sheet: `{report['artifacts']['contactSheet']}`",
    ]
    (output_root / "report.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    raw_path.unlink(missing_ok=True)
    print(f"dynamic continuity regression ({FORMAT}): PASS")
    print(f"report: {report_path}")
    print(f"contact sheet: {contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
