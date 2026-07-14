#!/usr/bin/env python3
"""Regression checks for line-ending-safe template mirror comparison."""

from __future__ import annotations

from pathlib import Path
import tempfile

from sync_template_mirrors import mirror_bytes_equal


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ngg-v4-portrait-mirror-") as temp_dir:
        root = Path(temp_dir)
        source = root / "source.ps1"
        target = root / "target.ps1"
        source.write_bytes(b"line-1\nline-2\n")
        target.write_bytes(b"line-1\r\nline-2\r\n")
        if not mirror_bytes_equal(source, target):
            raise AssertionError("LF and CRLF text mirrors must compare equal")
        target.write_bytes(b"line-1\r\nchanged\r\n")
        if mirror_bytes_equal(source, target):
            raise AssertionError("different text content must not compare equal")
        binary_source = root / "source.bin"
        binary_target = root / "target.bin"
        binary_source.write_bytes(b"a\nb")
        binary_target.write_bytes(b"a\r\nb")
        if mirror_bytes_equal(binary_source, binary_target):
            raise AssertionError("binary mirrors must remain byte-exact")
    print("portrait template mirror line-ending regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
