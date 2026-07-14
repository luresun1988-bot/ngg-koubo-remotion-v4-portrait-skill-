#!/usr/bin/env python3
"""Validate repository-owned portrait real acceptance example fixtures."""

from __future__ import annotations

import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
FIXTURE_PATH = SKILL_ROOT / "references" / "examples" / "real_acceptance_examples.json"
COMPONENT_REGISTRY_PATH = SKILL_ROOT / "references" / "registries" / "component_registry.json"
SFX_MANIFEST_PATH = SKILL_ROOT / "assets" / "remotion-template" / "public" / "input" / "audio" / "sfx_manifest.json"

REQUIRED_PORTRAIT_CATEGORIES = {
    "topic keyword",
    "problem/limitation map",
    "dataPunch/numeric result",
    "CTA",
}
REQUIRED_LIBRARY_INTENTS = {
    "title_impact",
    "confirm",
    "negative_warning",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def component_event_types(registry: dict) -> set[str]:
    result: set[str] = set()
    for component in registry.get("components", []):
        result.update(str(item) for item in component.get("eventTypes", []))
    return result


def component_visual_forms(registry: dict) -> set[str]:
    return {str(component.get("visualForm")) for component in registry.get("components", []) if component.get("visualForm")}


def sfx_by_intent(manifest: dict) -> dict[str, dict]:
    return {str(item.get("intent")): item for item in manifest.get("items", []) if item.get("intent")}


def main() -> int:
    fixture = load_json(FIXTURE_PATH)
    component_registry = load_json(COMPONENT_REGISTRY_PATH)
    sfx_manifest = load_json(SFX_MANIFEST_PATH)

    if fixture.get("format") != "portrait":
        raise AssertionError(f"unexpected fixture format: {fixture.get('format')}")
    if component_registry.get("format") != "portrait":
        raise AssertionError(f"unexpected component registry format: {component_registry.get('format')}")

    event_types = component_event_types(component_registry)
    visual_forms = component_visual_forms(component_registry)
    examples = fixture.get("examples", [])
    categories = {str(item.get("category")) for item in examples}
    missing_categories = REQUIRED_PORTRAIT_CATEGORIES - categories
    if missing_categories:
        raise AssertionError(f"missing portrait example categories: {sorted(missing_categories)}")

    for item in examples:
        event_type = str(item.get("eventType"))
        visual_form = str(item.get("visualForm", ""))
        if event_type not in event_types:
            raise AssertionError(f"example {item.get('id')} uses unregistered event type: {event_type}")
        if visual_form and visual_form not in visual_forms:
            raise AssertionError(f"example {item.get('id')} uses unregistered visual form: {visual_form}")

    manifest_by_intent = sfx_by_intent(sfx_manifest)
    fixture_sfx = fixture.get("sfxExamples", [])
    fixture_intents = {str(item.get("intent")) for item in fixture_sfx}
    missing_intents = REQUIRED_LIBRARY_INTENTS - fixture_intents
    if missing_intents:
        raise AssertionError(f"missing portrait SFX library examples: {sorted(missing_intents)}")

    for item in fixture_sfx:
        intent = str(item.get("intent"))
        manifest_item = manifest_by_intent.get(intent)
        if not manifest_item:
            raise AssertionError(f"SFX intent not found in manifest: {intent}")
        if item.get("path") != manifest_item.get("path"):
            raise AssertionError(
                f"SFX path mismatch for {intent}: fixture={item.get('path')} manifest={manifest_item.get('path')}"
            )
        audio_file = SKILL_ROOT / "assets" / "remotion-template" / "public" / manifest_item["path"]
        if not audio_file.is_file():
            raise AssertionError(f"SFX file is missing: {audio_file}")
        if int(manifest_item.get("defaultVolumeDb", 0)) > -5:
            raise AssertionError(f"SFX default volume is above approved maximum: {intent}")

    project_ids = {str(item.get("id")) for item in fixture.get("projects", [])}
    if "portrait_0712" not in project_ids:
        raise AssertionError(f"missing portrait source project record: {project_ids}")

    print(
        "portrait example asset regression: "
        f"{len(examples)} examples, {len(fixture_sfx)} SFX library checks, {len(project_ids)} source projects"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
