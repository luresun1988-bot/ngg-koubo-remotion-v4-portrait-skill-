#!/usr/bin/env python3
"""Regression coverage for audio_cue_audibility_qa.py."""

from audio_cue_audibility_qa import cue_windows, evaluate_levels


def main() -> int:
    windows = cue_windows(1.0, 0.5)
    assert windows["before"] == (0.75, 0.25)
    assert windows["cue"] == (1.0, 0.5)
    assert windows["after"] == (1.5, 0.25)

    audible = evaluate_levels({"meanDb": -10.0, "maxDb": -1.0}, [{"meanDb": -20.0, "maxDb": -10.0}], 1.5)
    assert audible["status"] == "audible"
    review = evaluate_levels({"meanDb": -19.0, "maxDb": -9.5}, [{"meanDb": -20.0, "maxDb": -10.0}], 1.5)
    assert review["status"] == "review"
    assert evaluate_levels({"meanDb": -10.0, "maxDb": -1.0}, [], 1.5)["status"] == "undetermined"
    print("audio cue audibility QA regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
