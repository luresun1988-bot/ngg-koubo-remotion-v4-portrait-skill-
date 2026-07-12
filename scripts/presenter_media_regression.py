#!/usr/bin/env python3
"""Regression test for frame/sample-exact portrait presenter normalization."""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path

from init_v4_project import (
    decoded_video_frame_count,
    duration_frames_at_fps,
    ffprobe_json,
    prepare_presenter_media,
    resolve_composition_fps,
    run,
    select_presenter_videos,
    video_summary,
)


def make_segment(
    path: Path,
    size: str,
    duration: float,
    frequency: int,
    codec: str,
    rate: str = "24",
) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={size}:rate={rate}:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={frequency}:sample_rate=44100:duration={duration}",
        "-shortest",
        "-c:v",
        codec,
        "-c:a",
        "aac" if path.suffix.lower() == ".mp4" else "pcm_s16le",
        str(path),
    ]
    run(command)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        first = root / "segment-01.mp4"
        second = root / "segment-02.avi"
        make_segment(first, "720x1280", 1.0, 440, "libx264")
        make_segment(second, "640x480", 0.8, 660, "mpeg4")

        selection_root = root / "selection"
        selection_video_dir = selection_root / "04_video"
        selection_video_dir.mkdir(parents=True)
        ambiguous_presenter = selection_video_dir / "host.mp4"
        ambiguous_material = selection_video_dir / "details-recording.mp4"
        ambiguous_presenter.touch()
        ambiguous_material.touch()
        try:
            select_presenter_videos(selection_root, None, None)
        except SystemExit as exc:
            if "multiple ambiguous videos" not in str(exc):
                raise
        else:
            raise AssertionError("ambiguous auto-discovery must require explicit presenter roles")
        selected, selection_report = select_presenter_videos(
            selection_root,
            [ambiguous_presenter],
            None,
        )
        if selected != [ambiguous_presenter.resolve()] or selection_report.get("selectionSource") != "explicit-presenter-video":
            raise AssertionError(selection_report)

        probed_fps, probed_report = resolve_composition_fps(
            [{"fps": 25.0, "fpsText": "25/1"}],
            None,
        )
        if probed_fps != 25 or probed_report.get("selectionSource") != "primary-presenter-probe":
            raise AssertionError(probed_report)
        thirty_fps, _ = resolve_composition_fps(
            [{"fps": 30.0, "fpsText": "30/1"}],
            None,
        )
        if thirty_fps != 30:
            raise AssertionError(thirty_fps)
        fallback_fps, fallback_report = resolve_composition_fps([], None)
        if fallback_fps != 25 or fallback_report.get("selectionSource") != "default-fallback":
            raise AssertionError(fallback_report)
        override_fps, override_report = resolve_composition_fps(
            [{"fps": 30.0, "fpsText": "30/1"}],
            25,
        )
        if override_fps != 25 or override_report.get("selectionSource") != "explicit-override":
            raise AssertionError(override_report)
        if duration_frames_at_fps({"durationSec": 2.0, "durationFrames": 60}, 25) != 50:
            raise AssertionError("duration must be requantized onto the composition FPS")

        source, summaries, descriptor, report = prepare_presenter_media(
            [first, second],
            root / "remotion" / "public" / "input",
            30,
            "auto",
            0,
        )
        if source != "input/combined_presenter_video_only.mp4":
            raise AssertionError(source)
        if descriptor.get("mode") != "normalized-wav" or descriptor.get("sampleRate") != 48000:
            raise AssertionError(descriptor)
        if report.get("verification", {}).get("passed") is not True:
            raise AssertionError(report)
        if report.get("totalFrames") != sum(report.get("segmentFrames", [])):
            raise AssertionError(report)

        video = root / "remotion" / "public" / source
        streams = ffprobe_json(video).get("streams", [])
        if any(stream.get("codec_type") == "audio" for stream in streams):
            raise AssertionError("normalized presenter video must be video-only")
        wav_path = root / "remotion" / "public" / descriptor["path"]
        with wave.open(str(wav_path), "rb") as wav_file:
            if (wav_file.getframerate(), wav_file.getnchannels(), wav_file.getsampwidth()) != (48000, 2, 2):
                raise AssertionError("normalized narration must be 48 kHz stereo PCM16")
            if wav_file.getnframes() != report.get("totalSamples"):
                raise AssertionError("normalized narration sample count does not match report")
        if len(summaries) != 2:
            raise AssertionError("segment summaries were lost")

        fractional = root / "fractional-presenter.mp4"
        make_segment(fractional, "360x640", 1.0, 880, "libx264", rate="30000/1001")
        fractional_summary = video_summary(fractional)
        if fractional_summary.get("fractionalFps") is not True:
            raise AssertionError(fractional_summary)
        fractional_fps, fractional_report = resolve_composition_fps([fractional_summary], None)
        if fractional_fps != 30 or fractional_report.get("requiresCfrNormalization") is not True:
            raise AssertionError(fractional_report)
        fractional_source, _, fractional_descriptor, fractional_normalization = prepare_presenter_media(
            [fractional],
            root / "fractional-remotion" / "public" / "input",
            fractional_fps,
            "auto",
            0,
            [fractional_summary],
        )
        if fractional_source != "input/presenter_source_cfr.mp4":
            raise AssertionError(fractional_source)
        if fractional_descriptor.get("mode") != "embedded":
            raise AssertionError(fractional_descriptor)
        if fractional_normalization.get("normalizationApplied") is not True:
            raise AssertionError(fractional_normalization)
        fractional_output = root / "fractional-remotion" / "public" / fractional_source
        if decoded_video_frame_count(fractional_output) != round(float(fractional_summary["durationSec"]) * 30):
            raise AssertionError("fractional presenter was not normalized to the 30 fps composition timebase")
        if not any(stream.get("codec_type") == "audio" for stream in ffprobe_json(fractional_output).get("streams", [])):
            raise AssertionError("fractional CFR normalization must preserve embedded audio")

    print("portrait presenter media regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
