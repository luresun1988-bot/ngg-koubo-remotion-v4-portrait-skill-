#!/usr/bin/env python3
"""Programmatic approval gate for modifying the NGG V4 Skill repository.

The gate protects the repository state, records the pre-change snapshot, binds
visual/semantic changes to approved preview artifacts, and refuses regression
or release checks when the current tree is not the approved sealed result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "ngg-v4-skill-change-approval-v1"
BASELINE_NAME = ".skill-change-gate.json"
ACTIVE_RELATIVE = Path("qa") / "skill-change-approval" / "active.json"
EXCLUDED_PARTS = {
    ".git",
    "qa",
    "node_modules",
    "__pycache__",
    ".cache",
    ".remotion",
    "dist",
    "out",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}
CHANGE_CLASSES = {"visual-semantic", "structural-nonvisual"}


class GateError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent, suffix=".tmp"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GateError(f"missing approval gate file: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise GateError(f"approval gate JSON must be an object: {path}")
    return data


def normalize_relative(value: str) -> str:
    candidate = value.replace("\\", "/").strip().strip("/")
    if not candidate or candidate == ".":
        raise GateError("approval scope must name a file or directory inside the Skill")
    path = Path(candidate)
    if path.is_absolute() or ".." in path.parts:
        raise GateError(f"unsafe approval scope: {value}")
    return candidate


def protected_snapshot(root: Path) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.as_posix() == BASELINE_NAME:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        key = relative.as_posix()
        files[key] = {"sha256": sha256_file(path), "size": path.stat().st_size}
    return files


def snapshot_fingerprint(files: dict[str, dict[str, Any]]) -> str:
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def snapshot(root: Path) -> tuple[dict[str, dict[str, Any]], str]:
    files = protected_snapshot(root)
    return files, snapshot_fingerprint(files)


def baseline_path(root: Path) -> Path:
    return root / BASELINE_NAME


def active_path(root: Path) -> Path:
    return root / ACTIVE_RELATIVE


def load_baseline(root: Path) -> dict[str, Any]:
    data = read_json(baseline_path(root))
    if data.get("schemaVersion") != SCHEMA_VERSION:
        raise GateError("unsupported Skill change gate baseline schema")
    return data


def load_active(root: Path) -> dict[str, Any]:
    data = read_json(active_path(root))
    if data.get("schemaVersion") != SCHEMA_VERSION:
        raise GateError("unsupported active approval schema")
    return data


def changed_files(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for path in sorted(set(before) | set(after)):
        if path not in before:
            changes.append({"path": path, "change": "added", **after[path]})
        elif path not in after:
            changes.append({"path": path, "change": "deleted"})
        elif before[path] != after[path]:
            changes.append({"path": path, "change": "modified", **after[path]})
    return changes


def path_in_scope(path: str, scopes: list[str]) -> bool:
    return any(path == scope or path.startswith(scope.rstrip("/") + "/") for scope in scopes)


def verify_samples(request: dict[str, Any]) -> None:
    approval = request.get("approval")
    if not isinstance(approval, dict) or not str(approval.get("userConfirmation") or "").strip():
        raise GateError("approval is missing the explicit user confirmation text")
    samples = approval.get("samples")
    if request.get("changeClass") == "visual-semantic" and not samples:
        raise GateError("visual-semantic changes require at least one approved still or motion preview")
    for sample in samples or []:
        path = Path(str(sample.get("path") or ""))
        if not path.is_file():
            raise GateError(f"approved sample is missing: {path}")
        if sha256_file(path) != sample.get("sha256"):
            raise GateError(f"approved sample changed after confirmation: {path}")


def bootstrap(root: Path, repository: str, confirmation: str) -> None:
    path = baseline_path(root)
    if path.exists():
        raise GateError(f"approval gate already initialized: {path}")
    if not confirmation.strip():
        raise GateError("bootstrap requires the user's explicit confirmation text")
    files, fingerprint = snapshot(root)
    atomic_write_json(
        path,
        {
            "schemaVersion": SCHEMA_VERSION,
            "repository": repository,
            "protectedTreeFingerprint": fingerprint,
            "protectedFileCount": len(files),
            "establishedAt": utc_now(),
            "establishedByUserConfirmation": confirmation.strip(),
            "policy": {
                "visualSemanticRequiresApprovedSample": True,
                "structuralNonvisualRequiresExplicitConfirmation": True,
                "officialSkillEditsBeforeApproval": "forbidden",
                "githubCommitOrPush": "separate-explicit-authorization-required",
            },
        },
    )


def create_request(
    root: Path, change_id: str, change_class: str, summary: str, scopes: list[str]
) -> None:
    if change_class not in CHANGE_CLASSES:
        raise GateError(f"change class must be one of: {', '.join(sorted(CHANGE_CLASSES))}")
    if not change_id.strip() or not summary.strip():
        raise GateError("change id and summary are required")
    if active_path(root).exists():
        raise GateError(f"an active change request already exists: {active_path(root)}")
    baseline = load_baseline(root)
    files, fingerprint = snapshot(root)
    if fingerprint != baseline.get("protectedTreeFingerprint"):
        raise GateError(
            "current Skill tree differs from the sealed baseline; resolve the previous approval before creating another request"
        )
    normalized_scopes = sorted(set(normalize_relative(scope) for scope in scopes))
    if not normalized_scopes:
        raise GateError("at least one approved scope path is required")
    atomic_write_json(
        active_path(root),
        {
            "schemaVersion": SCHEMA_VERSION,
            "repository": baseline.get("repository"),
            "changeId": change_id.strip(),
            "changeClass": change_class,
            "summary": summary.strip(),
            "approvedScope": normalized_scopes,
            "createdAt": utc_now(),
            "baselineFingerprint": fingerprint,
            "baselineFiles": files,
            "status": "pending-user-approval",
        },
    )


def approve_request(root: Path, confirmation: str, sample_paths: list[str]) -> None:
    request = load_active(root)
    if request.get("status") != "pending-user-approval":
        raise GateError("only a pending request can be approved")
    if not confirmation.strip():
        raise GateError("approval requires the user's explicit confirmation text")
    if request.get("changeClass") == "visual-semantic" and not sample_paths:
        raise GateError("visual-semantic approval requires at least one still or motion preview")
    samples = []
    for value in sample_paths:
        path = Path(value).resolve()
        if not path.is_file():
            raise GateError(f"sample does not exist: {path}")
        samples.append({"path": str(path), "sha256": sha256_file(path), "size": path.stat().st_size})
    request["approval"] = {
        "approvedAt": utc_now(),
        "userConfirmation": confirmation.strip(),
        "samples": samples,
    }
    request["status"] = "approved-not-implemented"
    atomic_write_json(active_path(root), request)


def seal_request(root: Path) -> None:
    request = load_active(root)
    if request.get("status") != "approved-not-implemented":
        raise GateError("seal requires an approved, not-yet-implemented request")
    verify_samples(request)
    before = request.get("baselineFiles")
    if not isinstance(before, dict):
        raise GateError("active request is missing its baseline snapshot")
    files, fingerprint = snapshot(root)
    changes = changed_files(before, files)
    if not changes:
        raise GateError("no Skill implementation changes were found")
    scopes = [str(item) for item in request.get("approvedScope") or []]
    outside = [item["path"] for item in changes if not path_in_scope(item["path"], scopes)]
    if outside:
        raise GateError("implementation changed files outside approved scope: " + ", ".join(outside))
    request["implementation"] = {
        "sealedAt": utc_now(),
        "protectedTreeFingerprint": fingerprint,
        "changedFiles": changes,
    }
    request["status"] = "approved-and-sealed"
    atomic_write_json(active_path(root), request)


def verify(root: Path) -> str:
    baseline = load_baseline(root)
    files, fingerprint = snapshot(root)
    if fingerprint == baseline.get("protectedTreeFingerprint"):
        return "PASS: Skill tree matches the sealed approval baseline"
    if not active_path(root).is_file():
        raise GateError("Skill tree changed without an approved and sealed change request")
    request = load_active(root)
    if request.get("status") != "approved-and-sealed":
        raise GateError("Skill tree changed without an approved and sealed change request")
    if request.get("baselineFingerprint") != baseline.get("protectedTreeFingerprint"):
        raise GateError("active request was created against a stale Skill baseline")
    verify_samples(request)
    implementation = request.get("implementation")
    if not isinstance(implementation, dict):
        raise GateError("sealed request is missing implementation evidence")
    if fingerprint != implementation.get("protectedTreeFingerprint"):
        raise GateError("Skill tree changed after the approved implementation was sealed")
    return f"PASS: approved Skill change {request.get('changeId')} is sealed"


def finalize(root: Path) -> None:
    message = verify(root)
    request = load_active(root)
    files, fingerprint = snapshot(root)
    baseline = load_baseline(root)
    baseline.update(
        {
            "protectedTreeFingerprint": fingerprint,
            "protectedFileCount": len(files),
            "lastApprovedChangeId": request.get("changeId"),
            "lastApprovedAt": request.get("approval", {}).get("approvedAt"),
            "lastFinalizedAt": utc_now(),
        }
    )
    atomic_write_json(baseline_path(root), baseline)
    archive = active_path(root).parent / "archive" / f"{request.get('changeId')}.json"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise GateError(f"approval archive already exists: {archive}")
    shutil.move(str(active_path(root)), str(archive))
    print(message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Guard official NGG V4 Skill changes with explicit approval evidence.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    commands = parser.add_subparsers(dest="command", required=True)

    boot = commands.add_parser("bootstrap")
    boot.add_argument("--repository", required=True)
    boot.add_argument("--confirmation", required=True)

    create = commands.add_parser("create")
    create.add_argument("--change-id", required=True)
    create.add_argument("--change-class", choices=sorted(CHANGE_CLASSES), required=True)
    create.add_argument("--summary", required=True)
    create.add_argument("--scope", action="append", required=True)

    approve = commands.add_parser("approve")
    approve.add_argument("--confirmation", required=True)
    approve.add_argument("--sample", action="append", default=[])

    commands.add_parser("seal")
    commands.add_parser("verify")
    commands.add_parser("finalize")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.repo_root).resolve()
    try:
        if args.command == "bootstrap":
            bootstrap(root, args.repository, args.confirmation)
            print(f"PASS: approval gate initialized for {args.repository}")
        elif args.command == "create":
            create_request(root, args.change_id, args.change_class, args.summary, args.scope)
            print(f"PASS: pending change request created at {active_path(root)}")
        elif args.command == "approve":
            approve_request(root, args.confirmation, args.sample)
            print("PASS: explicit user approval recorded")
        elif args.command == "seal":
            seal_request(root)
            print("PASS: approved implementation sealed")
        elif args.command == "verify":
            print(verify(root))
        elif args.command == "finalize":
            finalize(root)
            print("PASS: approved implementation finalized as the new baseline")
    except (GateError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
