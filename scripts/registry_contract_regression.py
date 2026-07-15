#!/usr/bin/env python3
"""Validate machine-readable V4 registry files against current runtime constants."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REGISTRY_DIR = SKILL_ROOT / "references" / "registries"
sys.path.insert(0, str(SCRIPT_DIR))

import semantic_router  # noqa: E402
import visual_event_builder  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> None:
    raise SystemExit(f"registry contract failed: {message}")


def role_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    roles = data.get("roles")
    if not isinstance(roles, list):
        fail("semantic_contract.roles must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in roles:
        if not isinstance(item, dict):
            fail("semantic_contract.roles items must be objects")
        intent = str(item.get("semanticIntent") or "")
        if not intent:
            fail("semantic_contract role missing semanticIntent")
        if intent in result:
            fail(f"duplicate semanticIntent {intent}")
        result[intent] = item
    return result


def component_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components = data.get("components")
    if not isinstance(components, list):
        fail("component_registry.components must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in components:
        if not isinstance(item, dict):
            fail("component_registry components must be objects")
        form = str(item.get("visualForm") or "")
        if not form:
            fail("component missing visualForm")
        if form in result:
            fail(f"duplicate component visualForm {form}")
        event_types = item.get("eventTypes")
        if not isinstance(event_types, list):
            fail(f"{form} eventTypes must be a list")
        result[form] = item
    return result


def icon_ids(data: dict[str, Any]) -> set[str]:
    icons = data.get("icons")
    if not isinstance(icons, list):
        fail("icon_registry.icons must be a list")
    result: set[str] = set()
    for item in icons:
        if not isinstance(item, dict):
            fail("icon_registry icons must be objects")
        icon_id = str(item.get("id") or "")
        if not icon_id:
            fail("icon missing id")
        result.add(icon_id)
    return result


def sfx_manifest_items() -> dict[str, dict[str, Any]]:
    manifest_path = SKILL_ROOT / "assets" / "remotion-template" / "public" / "input" / "audio" / "sfx_manifest.json"
    items = load_json(manifest_path).get("items")
    if not isinstance(items, list):
        fail("sfx_manifest.items must be a list")
    return {str(item.get("intent") or ""): item for item in items if isinstance(item, dict)}


def assert_template_registry_mirrors() -> None:
    template_dir = SKILL_ROOT / "assets" / "remotion-template" / "references" / "registries"
    if not template_dir.is_dir():
        fail("missing template registry mirror directory")
    for source in sorted(REGISTRY_DIR.glob("*.json")):
        target = template_dir / source.name
        if not target.is_file():
            fail(f"missing template registry mirror: {target.relative_to(SKILL_ROOT).as_posix()}")
        if source.read_bytes().replace(b"\r\n", b"\n") != target.read_bytes().replace(b"\r\n", b"\n"):
            fail(f"stale template registry mirror: {target.relative_to(SKILL_ROOT).as_posix()}")


def main() -> int:
    semantic_contract = load_json(REGISTRY_DIR / "semantic_contract.json")
    presentation_rules = load_json(REGISTRY_DIR / "presentation_rules.json")
    component_registry = load_json(REGISTRY_DIR / "component_registry.json")
    icon_registry = load_json(REGISTRY_DIR / "icon_registry.json")

    roles = role_map(semantic_contract)
    components = component_map(component_registry)
    icons = icon_ids(icon_registry)
    manifest_by_intent = sfx_manifest_items()
    assert_template_registry_mirrors()

    for intent, rule in semantic_router.RULES.items():
        if intent not in roles:
            fail(f"router RULES intent missing from semantic_contract: {intent}")
        if roles[intent].get("visualForm") != rule.get("visualForm"):
            fail(f"{intent} visualForm registry={roles[intent].get('visualForm')} runtime={rule.get('visualForm')}")

    for role in roles.values():
        form = str(role.get("visualForm") or "")
        fallback = str(role.get("fallbackVisualForm") or "")
        if form not in components:
            fail(f"visualForm missing from component_registry: {form}")
        if fallback and fallback not in components:
            fail(f"fallback visualForm missing from component_registry: {fallback}")

    rules = presentation_rules.get("semanticToPresentation")
    if not isinstance(rules, list):
        fail("presentation_rules.semanticToPresentation must be a list")
    for rule in rules:
        if not isinstance(rule, dict):
            fail("presentation rule must be an object")
        intent = str(rule.get("semanticIntent") or "")
        if intent and intent not in roles:
            fail(f"presentation rule unknown semanticIntent: {intent}")
        sfx_intent = rule.get("primarySfxIntent")
        if sfx_intent is not None and str(sfx_intent) not in visual_event_builder.SFX_SUGGESTIONS:
            fail(f"presentation rule unknown SFX intent: {sfx_intent}")

    for intent, suggestion in visual_event_builder.SFX_SUGGESTIONS.items():
        item = manifest_by_intent.get(intent)
        if not item:
            fail(f"SFX suggestion missing manifest item for intent {intent}")
        for field in ("sfxId", "path", "durationFrames", "durationSec"):
            if suggestion.get(field) != item.get(field):
                fail(f"SFX {intent}.{field} registry mismatch suggestion={suggestion.get(field)} manifest={item.get(field)}")
        if suggestion.get("volumeDb") != item.get("defaultVolumeDb"):
            fail(f"SFX {intent}.volumeDb does not match manifest defaultVolumeDb")

    required_icons = {"AlertTriangle", "BadgeCheck", "Bot", "ClipboardList", "FileText", "Info", "ListChecks", "Network", "Package", "ShieldCheck", "Sparkles", "TrendingUp", "User", "Users", "Workflow"}
    missing_icons = sorted(required_icons - icons)
    if missing_icons:
        fail(f"icon_registry missing required defaults: {', '.join(missing_icons)}")

    print("registry contract regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
