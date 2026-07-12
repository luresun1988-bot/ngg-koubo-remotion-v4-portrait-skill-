#!/usr/bin/env python3
"""Regression test for frame/sample-exact portrait presenter normalization."""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path

from init_v4_project import ffprobe_json, prepare_presenter_media, run


def make_segment(path: Path, size: str, duration: float, frequency: int, codec: str) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={size}:rate=24:duration={duration}",
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

    print("portrait presenter media regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
