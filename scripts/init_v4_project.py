#!/usr/bin/env python3
"""Initialize an NGG Koubo Remotion V4 workspace from a raw project folder."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SKILL_ROOT / "assets" / "remotion-template"
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
SUBTITLE_EXTS = {".srt", ".vtt"}
ALIGNMENT_NAMES = {"alignment_1_9.json", "alignment.json", "captions.json", "asr_segments.json"}
ASR_MODEL = os.environ.get("V4_ASR_MODEL", "small")
ASR_DEVICE = os.environ.get("V4_ASR_DEVICE", "auto")
ASR_COMPUTE_TYPE = os.environ.get("V4_ASR_COMPUTE_TYPE", "int8")
DENSE_MAIN_EVENT_SEC = 5.2
DENSE_SUPPLEMENT_EVENT_SEC = 5.0
DENSE_MAX_VISUAL_GAP_SEC = 3.0
DENSE_LONG_SCENE_SEC = 7.0
DEFAULT_BGM_PATH = "input/audio/bgm/default_bgm.mp3"
DEFAULT_BGM_VOLUME_DB = -30
DEFAULT_SFX_MANIFEST_PATH = "input/audio/sfx_manifest.json"
DEFAULT_COMPOSITION_FPS = 25
PRESENTER_AUDIO_MODES = {"auto", "embedded", "normalized-wav", "none"}
PRESENTER_SAMPLE_RATE = 48000
NUMERIC_UNIT_RE = re.compile(r"[+\-]?\d+(?:\.\d+)?\s*(?:%|万|亿|倍|x|X)")
FLOW_TEXT_RE = re.compile(r"(第一|第二|第三|第1|第2|第3|步骤|流程|结论|行动|最后|01|02|03)")
ICON_CANDIDATES: dict[str, list[str]] = {
    "manual-field": ["UploadCloud", "FileText", "AlignLeft", "Tags", "Image", "ClipboardList"],
    "platform-fanout": ["Route", "Network", "Package", "SendHorizontal", "PanelsTopLeft"],
    "automation-handoff": ["Bot", "Cpu", "Workflow", "CheckCircle2", "BadgeCheck"],
    "workflow-step": ["Workflow", "ListChecks", "Package", "Route", "FileCheck2"],
    "metric-growth": ["TrendingUp", "BarChart3", "Hash"],
    "semantic-problem-map": ["AlertTriangle", "CircleX", "Repeat2"],
    "result-promise": ["TrendingUp", "BadgeCheck", "BarChart3"],
    "proof-focus": ["ShieldCheck", "ExternalLink", "ScanSearch"],
    "proof-material": ["ShieldCheck", "ExternalLink", "Images"],
    "cta-resolve": ["BadgeCheck", "SendHorizontal", "FileCheck2"],
    "capability-share": ["BrainCircuit", "Bot", "Network", "BarChart3"],
    "scene-lock": ["CreditCard", "GraduationCap", "Landmark", "Link2"],
    "transformation-stack": ["User", "Users", "ShieldCheck", "TrendingUp", "FlaskConical"],
}
TEXT_ICON_HINTS: list[tuple[list[str], str]] = [
    (["\u4e0a\u4f20", "\u53d1\u5e03"], "UploadCloud"),
    (["\u6807\u9898", "\u6587\u6848"], "FileText"),
    (["\u7b80\u4ecb", "\u8bf4\u660e"], "AlignLeft"),
    (["\u6807\u7b7e", "\u5173\u952e\u8bcd"], "Tags"),
    (["\u5c01\u9762", "\u56fe\u7247", "\u4e3b\u56fe"], "Image"),
    (["\u89c6\u9891"], "Video"),
    (["\u7d20\u6750\u5305", "\u7d20\u6750"], "Package"),
    (["\u5e73\u53f0", "\u5206\u53d1"], "Network"),
    (["\u81ea\u52a8", "\u6267\u884c", "Codex"], "Bot"),
    (["\u68c0\u67e5", "\u5b8c\u6210"], "CheckCircle2"),
    (["\u98ce\u9669", "\u9519\u8bef", "\u4e0d\u662f"], "AlertTriangle"),
    (["\u6570\u636e", "\u6bd4\u4f8b"], "BarChart3"),
    (["\u589e\u957f"], "TrendingUp"),
    (["\u8bc1\u660e", "\u6765\u6e90"], "ShieldCheck"),
    (["AI", "\u6a21\u578b", "\u5206\u7c7b", "\u9002\u914d"], "BrainCircuit"),
]
ICON_REQUIRED_EVENT_TYPES = {"infoCard", "iconPulse"}
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402
from split_caption_cues import split_cues  # noqa: E402
from semantic_router import apply_semantic_beats  # noqa: E402
from visual_event_builder import apply_visual_events  # noqa: E402

configure_utf8()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, text=True, encoding="utf-8", errors="replace")


def ffprobe_json(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads(result.stdout)


def video_summary(path: Path) -> dict[str, Any]:
    raw = ffprobe_json(path)
    streams = raw.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    duration = float(raw.get("format", {}).get("duration", 0) or 0)
    fps_text = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or ""
    fps = ratio_to_float(fps_text) or 0.0
    return {
        "path": str(path),
        "durationSec": duration,
        "durationFrames": round(duration * fps),
        "fpsText": fps_text,
        "fps": fps,
        "width": int(video_stream.get("width", 0) or 0),
        "height": int(video_stream.get("height", 0) or 0),
        "hasAudio": bool(audio_streams),
        "videoCodec": video_stream.get("codec_name", ""),
        "audioCodecs": [item.get("codec_name", "") for item in audio_streams],
    }


def resolve_composition_fps(
    summaries: list[dict[str, Any]],
    requested_fps: int | None,
) -> tuple[int, dict[str, Any]]:
    """Use an explicit override, otherwise the primary presenter FPS, then the 25 fps fallback."""
    if requested_fps is not None and requested_fps <= 0:
        raise SystemExit("--fps must be a positive integer")

    measured = [float(item.get("fps") or 0) for item in summaries]
    valid_measured = [value for value in measured if value > 0]
    nominal = [max(1, round(value)) for value in valid_measured]

    if requested_fps is not None:
        selected = requested_fps
        source = "explicit-override"
    elif nominal:
        selected = nominal[0]
        source = "primary-presenter-probe"
    else:
        selected = DEFAULT_COMPOSITION_FPS
        source = "default-fallback"

    return selected, {
        "compositionFps": selected,
        "selectionSource": source,
        "defaultFallbackFps": DEFAULT_COMPOSITION_FPS,
        "sourceFps": measured,
        "sourceFpsText": [str(item.get("fpsText") or "") for item in summaries],
        "mixedPresenterFps": len(set(nominal)) > 1,
    }


def duration_frames_at_fps(summary: dict[str, Any], fps: int) -> int:
    """Quantize source wall-clock duration onto the selected composition timebase."""
    return max(1, round(float(summary.get("durationSec") or 0) * fps))


def ratio_to_float(text: str) -> float | None:
    try:
        if "/" in text:
            num, den = text.split("/", 1)
            den_value = float(den)
            return float(num) / den_value if den_value else None
        return float(text)
    except Exception:  # noqa: BLE001
        return None


def find_videos(project_root: Path) -> list[Path]:
    preferred = project_root / "04_video"
    search_root = preferred if preferred.exists() else project_root
    videos = [
        path
        for path in search_root.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTS
    ]
    return sorted(videos, key=lambda item: item.name.lower())


def load_text_segments(project_root: Path) -> list[str]:
    candidates = [
        project_root / "05_timing" / "tts_segments_utf8.json",
        project_root / "02_script" / "tts_segments.json",
        project_root / "05_timing" / "alignment_1_9.json",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            continue
        texts = extract_texts(data)
        if texts:
            return texts
    return []


def extract_texts(value: Any) -> list[str]:
    output: list[str] = []
    if isinstance(value, list):
        for item in value:
            output.extend(extract_texts(item))
    elif isinstance(value, dict):
        for key in ["text", "script", "sentence", "content", "narrationText"]:
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                output.append(item.strip())
                return output
        for key in ["segments", "items", "data"]:
            if key in value:
                output.extend(extract_texts(value[key]))
    return output


def parse_timestamp_seconds(value: str) -> float:
    clean = value.strip().replace(",", ".")
    parts = clean.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    return float(clean)


def parse_srt_or_vtt(path: Path, fps: int) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n"))
    cues: list[dict[str, Any]] = []
    index = 1
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if lines[0].upper().startswith("WEBVTT"):
            continue
        time_line_idx = next((idx for idx, line in enumerate(lines) if "-->" in line), -1)
        if time_line_idx < 0:
            continue
        start_text, end_text = [part.strip().split(" ")[0] for part in lines[time_line_idx].split("-->", 1)]
        cue_text = "".join(lines[time_line_idx + 1 :]).strip()
        if not cue_text:
            continue
        start_frame = round(parse_timestamp_seconds(start_text) * fps)
        end_frame = max(start_frame + 1, round(parse_timestamp_seconds(end_text) * fps))
        cues.append(
            {
                "id": f"cap-{index:03d}",
                "startFrame": start_frame,
                "endFrame": end_frame,
                "text": cue_text,
                "highlightWords": [],
            }
        )
        index += 1
    return cues


def cues_from_json_timeline(path: Path, fps: int) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    raw_items = data
    if isinstance(data, dict):
        for key in ("segments", "captionCues", "items", "data"):
            if isinstance(data.get(key), list):
                raw_items = data[key]
                break
    if not isinstance(raw_items, list):
        return []
    cues: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("sentence") or item.get("content") or item.get("script") or "").strip()
        if not text:
            continue
        start_seconds = item.get("startSeconds", item.get("start", item.get("start_time")))
        end_seconds = item.get("endSeconds", item.get("end", item.get("end_time")))
        if start_seconds is None and item.get("startFrame") is not None:
            start_frame = int(item.get("startFrame") or 0)
        else:
            start_frame = round(float(start_seconds or 0) * fps)
        if end_seconds is None and item.get("endFrame") is not None:
            end_frame = int(item.get("endFrame") or start_frame + 1)
        else:
            end_frame = round(float(end_seconds or 0) * fps)
        if end_frame <= start_frame:
            continue
        cues.append(
            {
                "id": f"cap-{idx + 1:03d}",
                "startFrame": start_frame,
                "endFrame": end_frame,
                "text": text,
                "highlightWords": [],
            }
        )
    return cues


def discover_timeline(project_root: Path, fps: int) -> tuple[list[dict[str, Any]], dict[str, str]] | None:
    search_roots = [project_root / "05_timing", project_root / "02_script", project_root]
    candidates: list[Path] = []
    for root in search_roots:
        if root.exists():
            candidates.extend(path for path in root.rglob("*") if path.is_file())
    for path in sorted(candidates, key=lambda item: (item.suffix.lower() not in SUBTITLE_EXTS, item.name.lower())):
        if path.suffix.lower() not in SUBTITLE_EXTS:
            continue
        cues = parse_srt_or_vtt(path, fps)
        if cues:
            return cues, {
                "sourceType": path.suffix.lower().lstrip("."),
                "sourcePath": str(path),
                "method": "sentence-timecodes",
                "generatedBy": "provided",
            }
    for path in sorted(candidates, key=lambda item: item.name.lower()):
        if path.suffix.lower() != ".json":
            continue
        if path.name not in ALIGNMENT_NAMES and "alignment" not in path.name.lower() and "asr" not in path.name.lower():
            continue
        try:
            cues = cues_from_json_timeline(path, fps)
        except Exception:  # noqa: BLE001
            continue
        if cues:
            source_type = "asr" if "asr" in path.name.lower() else "alignment-json"
            return cues, {
                "sourceType": source_type,
                "sourcePath": str(path),
                "method": "sentence-timecodes",
                "generatedBy": "provided" if source_type != "asr" else "asr",
            }
    return None


def write_srt(cues: list[dict[str, Any]], path: Path, fps: int) -> None:
    def ts(frame: int) -> str:
        total_ms = round(frame * 1000 / fps)
        hours, rest = divmod(total_ms, 3600_000)
        minutes, rest = divmod(rest, 60_000)
        seconds, millis = divmod(rest, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

    content = "\n\n".join(
        f"{idx}\n{ts(int(cue['startFrame']))} --> {ts(int(cue['endFrame']))}\n{cue['text']}"
        for idx, cue in enumerate(cues, start=1)
    )
    path.write_text(content + "\n", encoding="utf-8")


def run_asr_if_available(video: Path, remotion_root: Path, fps: int) -> tuple[list[dict[str, Any]], dict[str, str]] | None:
    if importlib.util.find_spec("faster_whisper") is None:
        return None
    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel(ASR_MODEL, device=ASR_DEVICE, compute_type=ASR_COMPUTE_TYPE)
        segments, _info = model.transcribe(str(video), language="zh", vad_filter=True)
        asr_dir = remotion_root / "qa" / "asr"
        asr_dir.mkdir(parents=True, exist_ok=True)
        raw_segments: list[dict[str, Any]] = []
        cues: list[dict[str, Any]] = []
        for idx, segment in enumerate(segments, start=1):
            text = str(segment.text or "").strip()
            if not text:
                continue
            start_frame = round(float(segment.start) * fps)
            end_frame = max(start_frame + 1, round(float(segment.end) * fps))
            item = {
                "id": f"cap-{idx:03d}",
                "startSeconds": float(segment.start),
                "endSeconds": float(segment.end),
                "startFrame": start_frame,
                "endFrame": end_frame,
                "text": text,
            }
            raw_segments.append(item)
            cues.append(
                {
                    "id": item["id"],
                    "startFrame": start_frame,
                    "endFrame": end_frame,
                    "text": text,
                    "highlightWords": [],
                }
            )
        if not cues:
            return None
        json_path = asr_dir / "asr_segments.json"
        srt_path = asr_dir / "asr_transcript.srt"
        json_path.write_text(json.dumps(raw_segments, ensure_ascii=True, indent=2), encoding="utf-8")
        write_srt(cues, srt_path, fps)
        return cues, {
            "sourceType": "asr",
            "sourcePath": str(json_path),
            "method": "sentence-timecodes",
            "generatedBy": "faster-whisper",
        }
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"ASR failed for {video}: {exc}") from exc


def copy_template(template_root: Path, remotion_root: Path) -> None:
    if remotion_root.exists():
        raise SystemExit(f"target Remotion directory already exists: {remotion_root}")
    shutil.copytree(template_root, remotion_root, ignore=shutil.ignore_patterns("node_modules", "out"))


def resolved_presenter_audio_mode(requested: str, videos: list[Path], summaries: list[dict[str, Any]]) -> str:
    if requested not in PRESENTER_AUDIO_MODES:
        raise SystemExit(f"invalid presenter audio mode: {requested}")
    if requested == "auto":
        return "embedded" if len(videos) == 1 else "normalized-wav"
    if requested == "embedded" and len(videos) > 1:
        raise SystemExit(
            "segmented presenter media cannot keep independent embedded AAC tracks; "
            "use auto, normalized-wav, or none"
        )
    if requested == "normalized-wav" and not any(bool(item.get("hasAudio")) for item in summaries):
        raise SystemExit("normalized-wav requires at least one presenter audio stream")
    return requested


def exact_wav_samples(path: Path, expected_samples: int) -> int:
    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        sample_width = source.getsampwidth()
        sample_rate = source.getframerate()
        frames = source.readframes(source.getnframes())
    if (channels, sample_width, sample_rate) != (2, 2, PRESENTER_SAMPLE_RATE):
        raise SystemExit(f"normalized presenter WAV has unexpected PCM format: {path}")
    frame_size = channels * sample_width
    current_samples = len(frames) // frame_size
    if current_samples < expected_samples:
        frames += b"\x00" * ((expected_samples - current_samples) * frame_size)
    elif current_samples > expected_samples:
        frames = frames[: expected_samples * frame_size]
    with wave.open(str(path), "wb") as target:
        target.setnchannels(channels)
        target.setsampwidth(sample_width)
        target.setframerate(sample_rate)
        target.writeframes(frames)
    return expected_samples


def normalize_presenter_segment(
    source: Path,
    video_out: Path,
    wav_out: Path | None,
    fps: int,
    expected_frames: int,
    has_audio: bool,
) -> int:
    duration_seconds = expected_frames / fps
    video_filter = (
        f"scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps={fps}"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-vf",
            video_filter,
            "-frames:v",
            str(expected_frames),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(video_out),
        ]
    )
    expected_samples = round(duration_seconds * PRESENTER_SAMPLE_RATE)
    if wav_out is None:
        return expected_samples
    if has_audio:
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(source),
                "-map",
                "0:a:0",
                "-af",
                f"aresample={PRESENTER_SAMPLE_RATE}:async=1:first_pts=0,apad,atrim=duration={duration_seconds:.9f}",
                "-ar",
                str(PRESENTER_SAMPLE_RATE),
                "-ac",
                "2",
                "-c:a",
                "pcm_s16le",
                str(wav_out),
            ]
        )
    else:
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=channel_layout=stereo:sample_rate={PRESENTER_SAMPLE_RATE}",
                "-t",
                f"{duration_seconds:.9f}",
                "-c:a",
                "pcm_s16le",
                str(wav_out),
            ]
        )
    return exact_wav_samples(wav_out, expected_samples)


def concat_pcm_wavs(paths: list[Path], output: Path) -> int:
    total_samples = 0
    with wave.open(str(output), "wb") as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(PRESENTER_SAMPLE_RATE)
        for path in paths:
            with wave.open(str(path), "rb") as source:
                if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (
                    2,
                    2,
                    PRESENTER_SAMPLE_RATE,
                ):
                    raise SystemExit(f"cannot concatenate unexpected WAV format: {path}")
                sample_count = source.getnframes()
                target.writeframes(source.readframes(sample_count))
                total_samples += sample_count
    return total_samples


def decoded_video_frame_count(path: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return int(result.stdout.strip())


def prepare_presenter_media(
    videos: list[Path],
    public_input: Path,
    fps: int,
    requested_audio_mode: str,
    sync_offset_frames: int,
    summaries: list[dict[str, Any]] | None = None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    public_input.mkdir(parents=True, exist_ok=True)
    summaries = summaries if summaries is not None else [video_summary(video) for video in videos]
    audio_mode = resolved_presenter_audio_mode(requested_audio_mode, videos, summaries)
    if sync_offset_frames and audio_mode != "normalized-wav":
        raise SystemExit("presenter sync offset is supported only with normalized-wav audio")

    if len(videos) == 1 and audio_mode in {"embedded", "none"}:
        out = public_input / "presenter_source.mp4"
        shutil.copy2(videos[0], out)
        report = {
            "schemaVersion": "ngg-v4-portrait-presenter-normalization-v1",
            "resolvedAudioMode": audio_mode,
            "normalizationApplied": False,
            "sourceCount": 1,
            "verification": {"passed": True, "mode": "single-source-pass-through"},
        }
        descriptor = {"mode": audio_mode, "syncOffsetFrames": 0}
        return "input/presenter_source.mp4", summaries, descriptor, report

    work_dir = public_input / ".normalized_segments"
    work_dir.mkdir(parents=True, exist_ok=True)
    normalized_videos: list[Path] = []
    normalized_wavs: list[Path] = []
    segment_frames: list[int] = []
    segment_samples: list[int] = []
    try:
        for index, (source, summary) in enumerate(zip(videos, summaries), start=1):
            expected_frames = duration_frames_at_fps(summary, fps)
            video_out = work_dir / f"segment-{index:04d}.mp4"
            wav_out = work_dir / f"segment-{index:04d}.wav" if audio_mode == "normalized-wav" else None
            expected_samples = normalize_presenter_segment(
                source,
                video_out,
                wav_out,
                fps,
                expected_frames,
                bool(summary.get("hasAudio")),
            )
            normalized_videos.append(video_out)
            segment_frames.append(expected_frames)
            if wav_out is not None:
                normalized_wavs.append(wav_out)
                segment_samples.append(expected_samples)

        concat_list = work_dir / "concat_list.txt"
        concat_list.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in normalized_videos),
            encoding="utf-8",
        )
        presenter_video = public_input / "combined_presenter_video_only.mp4"
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-map",
                "0:v:0",
                "-c",
                "copy",
                "-an",
                str(presenter_video),
            ]
        )
        total_frames = sum(segment_frames)
        decoded_frames = decoded_video_frame_count(presenter_video)
        if decoded_frames != total_frames:
            raise SystemExit(
                f"normalized presenter frame count mismatch: expected {total_frames}, got {decoded_frames}"
            )

        presenter_audio_path: str | None = None
        total_samples = 0
        if audio_mode == "normalized-wav":
            presenter_wav = public_input / "presenter_narration_48k.wav"
            total_samples = concat_pcm_wavs(normalized_wavs, presenter_wav)
            if total_samples != sum(segment_samples):
                raise SystemExit("normalized presenter WAV sample count mismatch")
            presenter_audio_path = "input/presenter_narration_48k.wav"

        descriptor: dict[str, Any] = {
            "mode": audio_mode,
            "syncOffsetFrames": sync_offset_frames,
            "normalizationReportPath": "qa/media/presenter_normalization.json",
        }
        if sync_offset_frames:
            descriptor["syncEvidence"] = "user-measured constant offset supplied at initialization"
        if presenter_audio_path:
            descriptor.update({"path": presenter_audio_path, "sampleRate": PRESENTER_SAMPLE_RATE})
        report = {
            "schemaVersion": "ngg-v4-portrait-presenter-normalization-v1",
            "resolvedAudioMode": audio_mode,
            "normalizationApplied": True,
            "sourceCount": len(videos),
            "fps": fps,
            "segmentFrames": segment_frames,
            "totalFrames": total_frames,
            "totalSamples": total_samples if audio_mode == "normalized-wav" else None,
            "verification": {
                "passed": True,
                "decodedVideoFrames": decoded_frames,
                "videoOnly": True,
                "wavSampleCount": total_samples if audio_mode == "normalized-wav" else None,
            },
        }
        return "input/combined_presenter_video_only.mp4", summaries, descriptor, report
    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir)


def infer_source_video_mode(videos: list[Path], timeline_meta: dict[str, str] | None) -> str:
    if len(videos) > 1:
        return "segmented-presenter"
    if timeline_meta and timeline_meta.get("sourceType") in {"srt", "vtt", "alignment-json", "asr"}:
        return "precomposed-video"
    return "raw-presenter"


def packaging_density_for_mode(source_video_mode: str) -> str:
    return "light" if source_video_mode == "precomposed-video" else "dense"


def project_config(
    project_root: Path,
    output_root: Path,
    videos: list[Path],
    source_video_mode: str,
    timeline_meta: dict[str, str] | None,
    caption_render_mode: str,
    presenter_audio: dict[str, Any],
    frame_rate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "projectRoot": str(project_root),
        "sourceMedia": {
            "talkingHeadVideos": [str(video) for video in videos],
            "scriptCandidates": [
                str(project_root / "02_script" / "tts_segments.json"),
                str(project_root / "05_timing" / "tts_segments_utf8.json"),
            ],
            "proofAssets": str(project_root / "publish_package_skill_demo" / ".publish_assets"),
            "posterAssets": str(project_root / "publish_package_skill_demo" / ".publish_assets" / "posters"),
            "platformCoverAssets": str(project_root / "publish_package_skill_demo" / ".publish_assets" / "covers"),
        },
        "outputFormat": "9:16",
        "template": "ngg-koubo-remotion-v4-portrait",
        "style": "high-energy-packaging",
        "sourceVideoMode": source_video_mode,
        "packagingDensity": packaging_density_for_mode(source_video_mode),
        "captionRenderMode": caption_render_mode,
        "presenterAudio": presenter_audio,
        "frameRate": frame_rate,
        "captionTimeline": timeline_meta or {},
        "posterTopicKeyword": "",
        "semanticSearch": True,
        "sfxEnabled": True,
        "bgmEnabled": True,
        "sfxManifestPath": DEFAULT_SFX_MANIFEST_PATH,
        "bgmPath": DEFAULT_BGM_PATH,
        "poster": {
            "generatorSkill": "ngg-koubo-poster",
            "generationMode": "single-direction-three-sizes",
            "videoBodyUsage": "publish_package_only",
            "manifestPath": str(
                project_root
                / "publish_package_skill_demo"
                / ".publish_assets"
                / "posters"
                / "poster_manifest.json"
            ),
            "finalPosterDir": str(
                project_root
                / "publish_package_skill_demo"
                / ".publish_assets"
                / "posters"
                / "final"
            ),
            "remotionPublicPosterDir": "",
        },
        "v4Workspace": str(output_root),
    }


def contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def has_clear_numeric_metric(text: str) -> bool:
    if NUMERIC_UNIT_RE.search(text):
        return True
    return bool(re.search(r"[+\-]?\d+(?:\.\d+)?", text)) and contains_any(
        text,
        ["\u8f6c\u5316\u7387", "\u63d0\u5347", "\u589e\u957f", "\u6bd4\u4f8b", "\u767e\u5206", "\u6307\u6807", "\u6570\u636e"],
    )


def has_capability_share_signal(text: str) -> bool:
    return contains_any(
        text,
        [
            "\u80fd\u529b",
            "\u5360\u6bd4",
            "\u4efd\u989d",
            "\u6392\u540d",
            "\u6392\u884c",
            "\u56fd\u5916",
            "\u56fd\u5185",
            "\u5168\u7403",
            "\u4e2d\u56fd",
            "\u516c\u53f8",
            "\u6a21\u578b",
            "Anthropic",
            "OpenAI",
            "Google",
        ],
    )


def has_scene_lock_signal(text: str) -> bool:
    return contains_any(
        text,
        [
            "\u573a\u666f",
            "\u7ed1\u5b9a",
            "\u884c\u4e1a",
            "\u54ea\u91cc\u7528",
            "\u843d\u5730",
            "\u5e94\u7528",
            "\u652f\u4ed8",
            "\u9ad8\u8003",
            "\u653f\u52a1",
            "\u529e\u516c",
        ],
    )


def has_transformation_signal(text: str) -> bool:
    return contains_any(
        text,
        [
            "\u4ece",
            "\u53d8\u6210",
            "\u8f6c\u5411",
            "\u4e00\u4e2a\u4eba",
            "\u56e2\u961f",
            "\u6760\u6746",
            "\u62a4\u57ce\u6cb3",
            "\u63a8\u52a8",
            "\u53d8\u5316",
            "\u63d0\u6548",
            "\u6548\u7387",
        ],
    )


def extract_numeric_metric(text: str) -> tuple[float, str, str] | None:
    match = re.search(r"([+\-]?)(\d+(?:\.\d+)?)\s*(%|万|亿|倍|x|X)?", text)
    if not match:
        return None
    prefix = "+" if match.group(1) == "+" else ""
    suffix = match.group(3) or ""
    return float(match.group(2)), prefix, suffix


def event_needs_icon(event: dict[str, Any]) -> bool:
    event_type = str(event.get("type") or "")
    semantic_role = str(event.get("semanticRole") or "")
    if event_type in ICON_REQUIRED_EVENT_TYPES:
        return True
    return event_type == "statusSticker" and semantic_role != "chapter-label"


def infer_icon_name(event: dict[str, Any], used_icons: set[str]) -> str:
    text = " ".join(str(event.get(key) or "") for key in ("title", "text", "subtext", "status"))
    for needles, icon_name in TEXT_ICON_HINTS:
        if contains_any(text, needles) and icon_name not in used_icons:
            return icon_name

    role = str(event.get("semanticRole") or "workflow-step")
    for icon_name in ICON_CANDIDATES.get(role, ICON_CANDIDATES["workflow-step"]):
        if icon_name not in used_icons:
            return icon_name

    return ICON_CANDIDATES.get(role, ICON_CANDIDATES["workflow-step"])[0]


def assign_icons_to_visual_events(events: list[dict[str, Any]]) -> None:
    used_by_group: dict[str, set[str]] = {}
    for event in events:
        if not event_needs_icon(event):
            continue
        group_id = str(event.get("beatGroupId") or event.get("sceneId") or "global")
        used_icons = used_by_group.setdefault(group_id, set())
        icon_name = str(event.get("iconName") or "")
        if not icon_name or icon_name in used_icons:
            icon_name = infer_icon_name(event, used_icons)
            event["iconName"] = icon_name
        used_icons.add(icon_name)


def derive_poster_topic_keyword(texts: list[str]) -> str:
    joined = "".join(texts[:3])
    if contains_any(joined, ["\u4e00\u952e", "\u5206\u53d1", "\u591a\u5e73\u53f0"]):
        return "\u4e00\u952e\u5206\u53d1\u591a\u5e73\u53f0"
    if texts:
        compact = "".join(texts[0].split())
        return compact[:10]
    return ""


def semantic_role_for_text(text: str, idx: int, scene_count: int) -> str:
    if idx == 0:
        if contains_any(text, ["\u8fd8\u5728\u624b\u52a8", "\u624b\u52a8", "\u522b\u518d", "\u4e0d\u662f", "\u9ebb\u70e6"]):
            return "semantic-problem-map"
        return "result-promise" if contains_any(text, ["\u4e00\u952e", "\u81ea\u52a8", "Skill", "Codex"]) else "pain-question"
    if idx == scene_count - 1:
        return "cta-resolve"
    if contains_any(text, ["\u4e0d\u662f", "\u800c\u662f", "\u6700\u9ebb\u70e6", "\u75db\u70b9", "\u74f6\u9888"]):
        return "semantic-problem-map"
    if has_clear_numeric_metric(text):
        return "metric-growth"
    if has_scene_lock_signal(text):
        return "scene-lock"
    if has_capability_share_signal(text):
        return "capability-share"
    if has_transformation_signal(text):
        return "transformation-stack"
    if contains_any(text, ["\u91cd\u590d", "\u586b\u5199", "\u6807\u9898", "\u7b80\u4ecb", "\u6807\u7b7e", "\u5c01\u9762"]):
        return "manual-field"
    if contains_any(text, ["\u6296\u97f3", "\u5c0f\u7ea2\u4e66", "B \u7ad9", "B\u7ad9", "\u5feb\u624b", "\u591a\u5e73\u53f0"]):
        return "platform-fanout"
    if contains_any(text, ["\u81ea\u52a8", "\u4ea4\u7ed9", "Codex", "AI", "\u7cfb\u7edf", "\u6267\u884c"]):
        return "automation-handoff"
    if contains_any(text, ["\u751f\u6210", "\u8c03\u7528", "\u4e0a\u4f20", "\u53d1\u5e03", "\u6d41\u7a0b"]) or FLOW_TEXT_RE.search(text):
        return "workflow-step"
    return "workflow-step"


def scene_type_for_role(role: str, idx: int, scene_count: int) -> str:
    if idx == 0:
        return "Hook"
    if idx == scene_count - 1:
        return "CTA"
    if role == "semantic-problem-map":
        return "Contrast"
    if role in {
        "manual-field",
        "platform-fanout",
        "automation-handoff",
        "workflow-step",
        "metric-growth",
        "capability-share",
        "scene-lock",
        "transformation-stack",
    }:
        return "Process"
    if role in {"proof-focus", "proof-material"}:
        return "Proof"
    return "Explanation"


def event_window(
    scene: dict[str, Any],
    fps: int,
    offset_sec: float = 0.2,
    duration_sec: float = DENSE_MAIN_EVENT_SEC,
) -> tuple[int, int]:
    scene_start = int(scene["startFrame"])
    scene_end = int(scene["endFrame"])
    start = min(scene_end - 1, scene_start + max(0, int(fps * offset_sec)))
    end = min(scene_end, start + max(12, int(fps * duration_sec)))
    if end <= start:
        end = min(scene_end, start + 1)
    return start, end


def add_event_for_scene(events: list[dict[str, Any]], scene: dict[str, Any], idx: int, fps: int) -> None:
    role = str(scene.get("semanticRole") or "")
    scene_id = str(scene["id"])
    start, end = event_window(scene, fps)
    base = {
        "sceneId": scene_id,
        "startFrame": start,
        "endFrame": end,
        "semanticRole": role,
        "beatGroupId": f"{scene_id}-{role}",
        "style": "dark-fullscreen-semantic-hud",
        "safeArea": "avoid-face-caption",
    }
    if role == "result-promise":
        events.append(
            {
                **base,
                "id": "ve-hook-title",
                "type": "kineticTitle",
                "text": "\u4e00\u952e\u5206\u53d1\u591a\u5e73\u53f0",
                "subtext": "\u53d1\u5e03\u6d41\u7a0b\u81ea\u52a8\u8dd1\u5b8c",
                "motionType": "crash-rebound-keyword-pop",
            }
        )
    elif role == "pain-question":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-pain-question",
                "type": "kineticTitle",
                "text": "\u53d1\u5e03\u5230\u5e95\u5361\u5728\u54ea",
                "subtext": "\u4e0d\u53ea\u662f\u526a\u8f91\u901f\u5ea6",
                "motionType": "word-pop",
            }
        )
    elif role == "semantic-problem-map":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-pain-contrast",
                "type": "highlightBox",
                "text": "\u4e0d\u662f\u526a\u8f91",
                "subtext": "\u800c\u662f\u91cd\u590d\u53d1\u5e03",
                "motionType": "contrast-swap-scan",
            }
        )
    elif role == "metric-growth":
        metric = extract_numeric_metric(str(scene.get("narrationText") or "")) or (30.0, "+", "%")
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-metric-growth",
                "type": "dataPunch",
                "text": "\u6570\u5b57\u6307\u6807",
                "subtext": "\u7528\u589e\u957f\u52a8\u753b\u8868\u8fbe",
                "status": "\u6307\u6807",
                "numericValue": metric[0],
                "numericPrefix": metric[1],
                "numericSuffix": metric[2],
                "iconName": "TrendingUp",
                "motionType": "count-up-chart",
            }
        )
    elif role == "capability-share":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-capability-share",
                "type": "capabilityShare",
                "text": "\u80fd\u529b\u5bf9\u6bd4",
                "subtext": "\u770b\u8c01\u5728\u9886\u5148",
                "status": "\u4efd\u989d / \u6392\u540d",
                "internalSteps": [
                    {"id": "cap-01", "label": "\u9886\u5148\u8005", "iconName": "BrainCircuit", "status": "42%"},
                    {"id": "cap-02", "label": "\u8ffd\u8d76\u8005", "iconName": "Bot", "status": "21%"},
                    {"id": "cap-03", "label": "\u53d8\u91cf", "iconName": "Network", "status": "10%"},
                ],
                "motionType": "layered-capability-share",
            }
        )
    elif role == "scene-lock":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-scene-lock",
                "type": "sceneLockGrid",
                "text": "\u573a\u666f\u7ed1\u5b9a",
                "subtext": "\u628a\u80fd\u529b\u843d\u5230\u5177\u4f53\u573a\u666f",
                "status": "\u5e94\u7528\u573a\u666f",
                "internalSteps": [
                    {"id": "scene-01", "label": "\u652f\u4ed8", "iconName": "CreditCard"},
                    {"id": "scene-02", "label": "\u6559\u80b2", "iconName": "GraduationCap"},
                    {"id": "scene-03", "label": "\u653f\u52a1", "iconName": "Landmark"},
                ],
                "motionType": "scene-grid-stagger",
            }
        )
    elif role == "transformation-stack":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-transformation-stack",
                "type": "transformationStack",
                "text": "\u80fd\u529b\u8f6c\u5316",
                "subtext": "\u4ece\u5355\u70b9\u52a8\u4f5c\u5230\u7cfb\u7edf\u6d41\u7a0b",
                "status": "\u6760\u6746",
                "internalSteps": [
                    {"id": "state-source", "label": "\u4e00\u4e2a\u4eba", "iconName": "User"},
                    {"id": "state-target", "label": "\u4e00\u4e2a\u56e2\u961f", "iconName": "Users"},
                    {"id": "driver-moat", "label": "\u62a4\u57ce\u6cb3", "iconName": "ShieldCheck", "status": "MOAT"},
                    {"id": "driver-leverage", "label": "\u6760\u6746", "iconName": "TrendingUp", "status": "LEVERAGE"},
                    {"id": "result-metric", "label": "55%-81%", "iconName": "FlaskConical", "status": "FASTER"},
                ],
                "motionType": "state-driver-result-build",
            }
        )
    elif role == "manual-field":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-manual-fields",
                "type": "infoCard",
                "text": "\u6807\u9898 / \u7b80\u4ecb / \u6807\u7b7e",
                "subtext": "\u6bcf\u4e2a\u5e73\u53f0\u91cd\u590d\u586b",
                "status": "\u91cd\u590d\u4efb\u52a1",
                "iconName": "FileText",
                "motionType": "card-stagger-stack",
            }
        )
    elif role == "platform-fanout":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-platform-fanout",
                "type": "transitionPushZoom",
                "text": "\u4e00\u4efd\u7d20\u6750\u5305",
                "subtext": "\u5206\u53d1\u591a\u4e2a\u5e73\u53f0",
                "motionType": "hub-to-platform-flow",
            }
        )
    elif role == "automation-handoff":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-automation-handoff",
                "type": "captionHighlight",
                "text": "\u91cd\u590d\u586b\u5199",
                "subtext": "\u4ea4\u7ed9 Codex \u6267\u884c",
                "motionType": "field-collapse-to-action",
            }
        )
    elif role == "workflow-step":
        events.append(
            {
                **base,
                "id": f"ve-{idx + 1:03d}-workflow-step",
                "type": "flowPath",
                "text": "\u6d41\u7a0b\u63a8\u8fdb",
                "title": "\u7ed3\u8bba / \u6570\u636e / \u884c\u52a8",
                "status": "\u6d41\u7a0b\u5217\u8868",
                "internalSteps": [
                    {"id": "step-01", "label": "\u7ed3\u8bba", "iconName": "BadgeCheck"},
                    {"id": "step-02", "label": "\u6570\u636e", "iconName": "BarChart3"},
                    {"id": "step-03", "label": "\u884c\u52a8", "iconName": "SendHorizontal"},
                ],
                "motionType": "flow-list-stagger",
            }
        )
    elif role == "cta-resolve":
        events.append(
            {
                **base,
                "id": "ve-cta-title",
                "type": "ctaTitle",
                "startFrame": max(int(scene["startFrame"]), int(scene["endFrame"]) - round(fps * 5.0)),
                "endFrame": int(scene["endFrame"]),
                "text": "\u60f3\u8981\u8fd9\u5957 Skill",
                "subtext": "\u8bc4\u8bba\u533a\u6263\uff1a\u5206\u53d1",
                "motionType": "crash-rebound",
            }
        )

    add_supplemental_events(events, scene, idx, fps)


def add_supplemental_events(events: list[dict[str, Any]], scene: dict[str, Any], idx: int, fps: int) -> None:
    text = str(scene.get("narrationText") or "")
    role = str(scene.get("semanticRole") or "")
    scene_id = str(scene["id"])
    scene_start = int(scene["startFrame"])
    scene_end = int(scene["endFrame"])
    scene_frames = scene_end - scene_start
    if scene_frames < fps * 5 or role == "cta-resolve":
        return

    def base_event(offset_sec: float, duration_sec: float, semantic_role: str) -> dict[str, Any]:
        start, end = event_window(scene, fps, offset_sec=offset_sec, duration_sec=duration_sec)
        return {
            "sceneId": scene_id,
            "startFrame": start,
            "endFrame": end,
            "semanticRole": semantic_role,
            "beatGroupId": f"{scene_id}-{semantic_role}",
            "style": "dark-fullscreen-semantic-hud",
            "safeArea": "avoid-face-caption",
        }

    if role != "platform-fanout" and contains_any(
        text,
        ["\u6296\u97f3", "\u5c0f\u7ea2\u4e66", "B \u7ad9", "B\u7ad9", "\u5feb\u624b", "\u591a\u5e73\u53f0"],
    ):
        events.append(
            {
                **base_event(3.0, DENSE_SUPPLEMENT_EVENT_SEC, "platform-fanout"),
                "id": f"ve-{idx + 1:03d}-platform-fanout-extra",
                "type": "transitionPushZoom",
                "text": "\u4e00\u6761\u89c6\u9891",
                "subtext": "\u5206\u53d1\u5230\u591a\u5e73\u53f0",
                "motionType": "hub-to-platform-flow",
            }
        )

    if role != "manual-field" and contains_any(
        text,
        ["\u91cd\u590d", "\u586b\u5199", "\u6807\u9898", "\u7b80\u4ecb", "\u6807\u7b7e", "\u5c01\u9762"],
    ):
        events.append(
            {
                **base_event(5.6, DENSE_SUPPLEMENT_EVENT_SEC, "manual-field"),
                "id": f"ve-{idx + 1:03d}-manual-fields-extra",
                "type": "infoCard",
                "text": "\u6807\u9898 / \u7b80\u4ecb / \u6807\u7b7e",
                "subtext": "\u5e73\u53f0\u95f4\u91cd\u590d\u5f55\u5165",
                "status": "\u5f85\u81ea\u52a8\u5316",
                "iconName": "ClipboardList",
                "motionType": "card-stagger-stack",
            }
        )


def chapter_label_for_scene(scene: dict[str, Any]) -> tuple[str, str]:
    scene_type = str(scene.get("type") or "")
    role = str(scene.get("semanticRole") or "")
    if scene_type == "Hook":
        return "COLD OPEN", "\u4e00\u4e2a\u53cd\u76f4\u89c9\u5f00\u573a"
    if scene_type == "CTA" or role == "cta-resolve":
        return "FINAL ACTION", "\u6700\u540e\u4e00\u6b65"
    if role == "semantic-problem-map":
        return "PAIN POINT", "\u771f\u6b63\u74f6\u9888"
    if role == "platform-fanout":
        return "DISTRIBUTION", "\u591a\u5e73\u53f0\u5206\u53d1"
    if role == "automation-handoff":
        return "AUTO HANDOFF", "\u4ea4\u7ed9\u7cfb\u7edf\u6267\u884c"
    if role == "manual-field":
        return "PUBLISH FIELDS", "\u91cd\u590d\u586b\u5199"
    if role in {"proof-focus", "proof-material", "material-main"}:
        return "PROOF", "\u771f\u5b9e\u7d20\u6750\u8bc1\u660e"
    return "PROCESS", "\u6d41\u7a0b\u63a8\u8fdb"


def add_corner_chapter_labels(events: list[dict[str, Any]], scenes: list[dict[str, Any]]) -> None:
    for scene in scenes:
        text, subtext = chapter_label_for_scene(scene)
        scene_id = str(scene["id"])
        events.append(
            {
                "id": f"ve-{scene_id}-corner-label",
                "sceneId": scene_id,
                "type": "cornerChapterLabel",
                "startFrame": int(scene["startFrame"]),
                "endFrame": int(scene["endFrame"]),
                "text": text,
                "subtext": subtext,
                "semanticRole": "chapter-label",
                "motionType": "corner-slide-fade",
                "style": "top-left-corner-label",
                "safeArea": "top-left-no-shade",
            }
        )


def dense_event_for_gap(
    scene: dict[str, Any],
    fps: int,
    start_frame: int,
    index: int,
) -> dict[str, Any]:
    scene_id = str(scene["id"])
    scene_end = int(scene["endFrame"])
    role = str(scene.get("semanticRole") or "workflow-step")
    start = min(scene_end - 1, start_frame)
    end = min(scene_end, start + max(18, round(fps * DENSE_SUPPLEMENT_EVENT_SEC)))
    if end <= start:
        end = min(scene_end, start + 1)

    base = {
        "sceneId": scene_id,
        "startFrame": start,
        "endFrame": end,
        "beatGroupId": f"{scene_id}-{role}",
        "style": "dark-fullscreen-semantic-hud",
        "safeArea": "avoid-face-caption",
    }

    if role == "manual-field":
        if index % 2 == 0:
            return {
                **base,
                "id": f"ve-{scene_id}-dense-platform-{index}",
                "type": "transitionPushZoom",
                "semanticRole": "platform-fanout",
                "text": "\u53d1\u5e03\u7d20\u6750\u5305",
                "subtext": "\u89c6\u9891 / \u4e3b\u56fe / \u6807\u9898 / \u7b80\u4ecb / \u6807\u7b7e",
                "motionType": "hub-to-platform-flow",
            }
        return {
            **base,
            "id": f"ve-{scene_id}-dense-handoff-{index}",
            "type": "captionHighlight",
            "semanticRole": "automation-handoff",
            "text": "\u53d1\u5e03\u914d\u7f6e",
            "subtext": "\u81ea\u52a8\u5f52\u6863\u5230\u5e73\u53f0\u8981\u6c42",
            "motionType": "field-collapse-to-action",
        }

    if role == "platform-fanout":
        return {
            **base,
            "id": f"ve-{scene_id}-dense-fanout-{index}",
            "type": "transitionPushZoom",
            "semanticRole": "platform-fanout",
            "text": "\u5e73\u53f0\u5206\u53d1\u6d41",
            "subtext": "\u540c\u4e00\u7d20\u6750\u6309\u5e73\u53f0\u62c6\u5206",
            "motionType": "hub-to-platform-flow",
        }

    if role == "automation-handoff":
        return {
            **base,
            "id": f"ve-{scene_id}-dense-automation-{index}",
            "type": "captionHighlight",
            "semanticRole": "automation-handoff",
            "text": "\u81ea\u52a8\u5316\u4ea4\u63a5",
            "subtext": "\u5b57\u6bb5\u9010\u9879\u5b8c\u6210",
            "motionType": "field-collapse-to-action",
        }

    if role == "cta-resolve":
        return {
            **base,
            "id": f"ve-{scene_id}-dense-cta-lead-{index}",
            "type": "infoCard",
            "semanticRole": "workflow-step",
            "text": "\u6700\u540e\u4e00\u6b65",
            "subtext": "\u628a\u8fd9\u5957\u5206\u53d1\u6d41\u7a0b\u8dd1\u901a",
            "status": "\u51c6\u5907 CTA",
            "iconName": "BadgeCheck",
            "motionType": "card-stagger-stack",
        }

    return {
        **base,
        "id": f"ve-{scene_id}-dense-step-{index}",
        "type": "flowPath",
        "semanticRole": "workflow-step",
        "text": "\u6d41\u7a0b\u5b50\u6b65\u9aa4",
        "title": "\u7ed3\u8bba / \u6570\u636e / \u884c\u52a8",
        "status": "\u6d41\u7a0b\u5217\u8868",
        "internalSteps": [
            {"id": "step-01", "label": "\u7ed3\u8bba", "iconName": "BadgeCheck"},
            {"id": "step-02", "label": "\u6570\u636e", "iconName": "BarChart3"},
            {"id": "step-03", "label": "\u884c\u52a8", "iconName": "SendHorizontal"},
        ],
        "motionType": "flow-list-stagger",
    }


def densify_visual_events(
    events: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
    fps: int,
) -> None:
    max_gap_frames = round(fps * DENSE_MAX_VISUAL_GAP_SEC)
    long_scene_frames = round(fps * DENSE_LONG_SCENE_SEC)
    step_frames = round(fps * 4.6)

    for scene in scenes:
        scene_start = int(scene["startFrame"])
        scene_end = int(scene["endFrame"])
        if scene_end - scene_start < long_scene_frames:
            continue

        scene_events = sorted(
            [event for event in events if event.get("sceneId") == scene.get("id")],
            key=lambda event: int(event.get("startFrame", 0)),
        )
        cursor = scene_start
        inserted = 0

        for event in scene_events:
            event_start = int(event.get("startFrame", scene_start))
            if event_start - cursor > max_gap_frames:
                insert_at = min(scene_end - 1, cursor + round(fps * 0.2))
                events.append(dense_event_for_gap(scene, fps, insert_at, inserted))
                inserted += 1
            cursor = max(cursor, int(event.get("endFrame", event_start)))

        while scene_end - cursor > max_gap_frames and inserted < 4:
            insert_at = min(scene_end - 1, cursor + round(fps * 0.2))
            dense_event = dense_event_for_gap(scene, fps, insert_at, inserted)
            events.append(dense_event)
            inserted += 1
            cursor = min(scene_end, int(dense_event["startFrame"]) + step_frames)


def starter_visual_script(
    project_config_path: str,
    source_video: str,
    summaries: list[dict[str, Any]],
    texts: list[str],
    fps: int,
    timeline_cues: list[dict[str, Any]] | None = None,
    timeline_meta: dict[str, str] | None = None,
    source_video_mode: str = "raw-presenter",
    caption_render_mode: str = "embedded",
    presenter_audio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    duration_frames = sum(duration_frames_at_fps(item, fps) for item in summaries)
    if not summaries:
        duration_frames = fps * 10
    if timeline_cues:
        duration_frames = max(duration_frames, max(int(cue["endFrame"]) for cue in timeline_cues))
    scene_count = max(1, len(timeline_cues) if timeline_cues else len(summaries))
    scenes: list[dict[str, Any]] = []
    captions: list[dict[str, Any]] = []
    qa_frames: list[dict[str, Any]] = []
    cursor = 0
    for idx in range(scene_count):
        if timeline_cues:
            cue = timeline_cues[idx]
            start = max(0, int(cue["startFrame"]))
            end = max(start + 1, min(duration_frames, int(cue["endFrame"])))
            text = str(cue.get("text") or "")
        else:
            frames = duration_frames_at_fps(summaries[idx], fps) if idx < len(summaries) else duration_frames
            start = cursor
            end = duration_frames if idx == scene_count - 1 else min(duration_frames, cursor + frames)
            text = texts[idx] if idx < len(texts) else f"Segment {idx + 1}"
        semantic_role = semantic_role_for_text(text, idx, scene_count)
        scene_type = scene_type_for_role(semantic_role, idx, scene_count)
        scene_id = f"scene-{idx + 1:03d}"
        scenes.append(
            {
                "id": scene_id,
                "type": scene_type,
                "segmentId": f"{idx + 1:03d}",
                "startFrame": start,
                "endFrame": end,
                "semanticRole": semantic_role,
                "presenterLayout": "large",
                "materialLayout": "none",
                "intent": "Semantic V4 scene generated from real caption timeline." if timeline_cues else "Semantic V4 scene generated from source segment timing.",
                "sourceVideo": source_video,
                "narrationText": text,
            }
        )
        caption_id = str(timeline_cues[idx].get("id") or f"cap-{idx + 1:03d}") if timeline_cues else f"cap-{idx + 1:03d}"
        captions.append(
            {
                "id": caption_id,
                "sceneId": scene_id,
                "startFrame": start if timeline_cues else start + min(8, max(0, end - start - 1)),
                "endFrame": end if timeline_cues else max(start + 1, end - 8),
                "text": text,
                "highlightWords": [],
            }
        )
        qa_frames.append(
            {
                "frame": start + max(1, (end - start) // 2),
                "reason": f"{scene_type} presenter layout sample.",
                "checks": ["caption-safe", "face-safe", "timing"],
            }
        )
        cursor = end

    poster_topic_keyword = derive_poster_topic_keyword(texts)
    caption_timeline = timeline_meta or {
        "sourceType": "segment-video-duration",
        "sourcePath": "sourceMedia.talkingHeadVideos",
        "method": "source-segment-duration",
        "generatedBy": "init_v4_project.py",
        "notes": "Starter captions use one source clip duration per text segment. Use SRT/VTT/alignment/ASR for finished single-video precision editing.",
    }

    visual_script = {
        "schemaVersion": "ngg-koubo-remotion-v4-portrait",
        "projectConfigPath": project_config_path,
        "composition": {
            "format": "9:16",
            "width": 1080,
            "height": 1920,
            "fps": fps,
            "durationFrames": duration_frames,
        },
        "sourceVideoMode": source_video_mode,
        "presenterAudio": presenter_audio or {"mode": "embedded", "syncOffsetFrames": 0},
        "captionRenderMode": caption_render_mode,
        "packagingDensity": packaging_density_for_mode(source_video_mode),
        "captionTimeline": caption_timeline,
        "researchNotes": [
            {
                "id": "research-local-001",
                "topic": poster_topic_keyword or "local transcript",
                "source": "local transcript semantic pass",
                "summary": "Starter visual events were routed from transcript keywords into V4 semantic roles.",
                "visualUse": "Use result title, pain contrast, manual-field cards, platform fan-out, automation handoff, and CTA where the narration supports them.",
            }
        ],
        "media": [
            {
                "id": "talking-head-main",
                "type": "video",
                "path": source_video,
                "role": "presenter",
                "durationSec": round(duration_frames / fps, 3),
                "hasAudio": any(bool(item.get("hasAudio")) for item in summaries),
            }
        ],
        "scenes": scenes,
        "semanticBeats": [],
        "captionCues": captions,
        "visualEvents": [],
        "audioCues": [
            {
                "id": "bgm-default",
                "type": "bgm",
                "startFrame": 0,
                "durationFrames": duration_frames,
                "path": DEFAULT_BGM_PATH,
                "volumeDb": DEFAULT_BGM_VOLUME_DB,
                "duckUnderVoice": True,
                "loop": True,
                "fadeInFrames": fps,
                "fadeOutFrames": fps * 2,
                "status": "active",
                "source": "default V4 BGM library",
            }
        ],
        "qaFrames": qa_frames,
    }
    apply_semantic_beats(visual_script)
    apply_visual_events(visual_script)
    assign_icons_to_visual_events(visual_script["visualEvents"])
    visual_script["visualEvents"].sort(
        key=lambda item: (str(item.get("sceneId", "")), int(item.get("startFrame", 0)))
    )
    return visual_script


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-dir", default="10_v4", type=Path)
    parser.add_argument("--template-root", default=DEFAULT_TEMPLATE, type=Path)
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        help="Explicit composition FPS override. By default use the probed primary presenter FPS, then fall back to 25.",
    )
    parser.add_argument("--source-video", action="append", type=Path)
    parser.add_argument(
        "--caption-render-mode",
        choices=("embedded", "none"),
        default="embedded",
        help="Render bottom captions or keep the authoritative timeline without rendering captions.",
    )
    parser.add_argument(
        "--presenter-audio-mode",
        choices=tuple(sorted(PRESENTER_AUDIO_MODES)),
        default="auto",
        help="auto keeps one source embedded but normalizes segmented presenter audio to one WAV.",
    )
    parser.add_argument(
        "--presenter-sync-offset-frames",
        type=int,
        default=0,
        help="Measured constant render-time offset for normalized presenter WAV audio.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    requested_output = args.output_dir if args.output_dir.is_absolute() else project_root / args.output_dir
    requested_output = requested_output.resolve()
    output_is_remotion_root = requested_output.name.lower() == "06_remotion"
    output_root = requested_output.parent if output_is_remotion_root else requested_output
    remotion_root = requested_output if output_is_remotion_root else output_root / "06_remotion"
    if remotion_root.parent.name.lower() == "06_remotion":
        raise SystemExit(
            f"refusing to create nested Remotion workspace: {remotion_root}. "
            "Run init from the project root or pass --output-dir to the project workspace root, not an existing 06_remotion child."
        )
    if output_is_remotion_root:
        if remotion_root.exists() and not args.force:
            raise SystemExit(f"Remotion directory already exists; pass --force to replace: {remotion_root}")
        if remotion_root.exists() and args.force:
            shutil.rmtree(remotion_root)
    else:
        if output_root.exists() and not args.force:
            raise SystemExit(f"output directory already exists; pass --force to replace: {output_root}")
        if output_root.exists() and args.force:
            shutil.rmtree(output_root)

    videos = [video.resolve() for video in args.source_video] if args.source_video else find_videos(project_root)
    if not videos:
        raise SystemExit(f"no source videos found under {project_root}")

    source_summaries = [video_summary(video) for video in videos]
    composition_fps, frame_rate_report = resolve_composition_fps(source_summaries, args.fps)
    print(
        f"composition fps: {composition_fps} "
        f"({frame_rate_report['selectionSource']}; source={frame_rate_report['sourceFpsText']})"
    )

    timeline = discover_timeline(project_root, composition_fps)
    needs_asr = timeline is None and len(videos) == 1
    if needs_asr and importlib.util.find_spec("faster_whisper") is None:
        raise SystemExit(
            "single finished MP4 input has no SRT/VTT/alignment/ASR timeline, and faster-whisper is not installed. "
            "Provide a real subtitle/timing file or install faster-whisper; V4 will not create a fake Segment 1 precision timeline."
        )

    output_root.mkdir(parents=True, exist_ok=True)
    copy_template(args.template_root.resolve(), remotion_root)
    source_video, summaries, presenter_audio, normalization_report = prepare_presenter_media(
        videos,
        remotion_root / "public" / "input",
        composition_fps,
        args.presenter_audio_mode,
        args.presenter_sync_offset_frames,
        source_summaries,
    )
    normalization_report["frameRate"] = frame_rate_report
    qa_media_dir = remotion_root / "qa" / "media"
    qa_media_dir.mkdir(parents=True, exist_ok=True)
    (qa_media_dir / "presenter_normalization.json").write_text(
        json.dumps(normalization_report, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    if needs_asr:
        timeline = run_asr_if_available(videos[0], remotion_root, composition_fps)
    timeline_cues = timeline[0] if timeline else None
    timeline_meta = timeline[1] if timeline else None
    texts = load_text_segments(project_root)
    if timeline_cues:
        texts = [str(cue.get("text") or "") for cue in timeline_cues]
    source_video_mode = infer_source_video_mode(videos, timeline_meta)
    config = project_config(
        project_root,
        output_root,
        videos,
        source_video_mode,
        timeline_meta,
        args.caption_render_mode,
        presenter_audio,
        frame_rate_report,
    )
    config["posterTopicKeyword"] = derive_poster_topic_keyword(texts)
    config_path = output_root / "project_config.json"
    config_path.write_text(
        json.dumps(config, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    visual_script_path = remotion_root / "visual_script.json"
    visual_script = starter_visual_script(
        "../project_config.json",
        source_video,
        summaries,
        texts,
        composition_fps,
        timeline_cues=timeline_cues,
        timeline_meta=timeline_meta,
        source_video_mode=source_video_mode,
        caption_render_mode=args.caption_render_mode,
        presenter_audio=presenter_audio,
    )
    visual_script, split_count = split_cues(visual_script, max_chars=30, min_frames=12)
    visual_script_path.write_text(json.dumps(visual_script, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"starter caption split count: {split_count}")

    run(["python", str(SKILL_ROOT / "scripts" / "validate_visual_script.py"), str(visual_script_path)])

    generated_ts = remotion_root / "src" / "generatedVisualScript.ts"
    run(
        [
            "python",
            str(SKILL_ROOT / "scripts" / "write_generated_visual_script.py"),
            "--visual-script",
            str(visual_script_path),
            "--out",
            str(generated_ts),
        ]
    )

    print(f"initialized V4 workspace: {output_root}")
    print(f"project config: {config_path}")
    print(f"visual script: {visual_script_path}")
    print(f"remotion root: {remotion_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
