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
from presentation_registry import get_registry  # noqa: E402

EXPECTED_COLOR_TOKENS = {
    "background": "#05070b",
    "primary": "#067ef6",
    "completion": "#20e0b0",
    "warning": "#d83c30",
    "prompt": "#c08a30",
    "auxiliary": "#663684",
    "textPrimary": "#f0f0f0",
    "textMuted": "#cccccc",
}

STYLE_COLOR_KEYS = {
    "background": "black",
    "primary": "blue",
    "completion": "green",
    "warning": "red",
    "prompt": "amber",
    "auxiliary": "purple",
    "textPrimary": "white",
    "textMuted": "muted",
}


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

def assert_color_policy(presentation_rules: dict[str, Any]) -> None:
    policy = presentation_rules.get("colorPolicy")
    if not isinstance(policy, dict):
        fail("presentation_rules.colorPolicy must be an object")
    if policy.get("tokens") != EXPECTED_COLOR_TOKENS:
        fail(f"colorPolicy.tokens must match approved V4 palette: {EXPECTED_COLOR_TOKENS}")
    rules = policy.get("rules")
    if not isinstance(rules, dict):
        fail("colorPolicy.rules must be an object")
    expected_rules = {
        "baseHudText": "textPrimary",
        "maxSemanticHighlightPhrases": 1,
        "captionColor": "textPrimary",
        "completionRequiresAssertedState": True,
        "depthTitleColor": "textPrimary",
        "coloredGlowAllowed": False,
        "coloredProjectionShadowAllowed": False,
        "fullscreenColorMaskAllowed": False,
    }
    for key, expected in expected_rules.items():
        if rules.get(key) != expected:
            fail(f"colorPolicy.rules.{key} must be {expected!r}")

    style_path = SKILL_ROOT / "assets" / "remotion-template" / "src" / "v4Styles.ts"
    style_source = style_path.read_text(encoding="utf-8")
    for semantic_name, value in EXPECTED_COLOR_TOKENS.items():
        style_key = STYLE_COLOR_KEYS[semantic_name]
        if f"{style_key}: '{value}'" not in style_source:
            fail(f"v4Styles colors.{style_key} must be {value}")
        if f"{semantic_name}: colors.{style_key}" not in style_source:
            fail(f"v4Styles semanticColors.{semantic_name} must alias colors.{style_key}")
    if "#46ff7a" in style_source.lower():
        fail("forbidden bright green #46FF7A found in v4Styles")


def main() -> int:
    semantic_contract = load_json(REGISTRY_DIR / "semantic_contract.json")
    presentation_rules = load_json(REGISTRY_DIR / "presentation_rules.json")
    component_registry = load_json(REGISTRY_DIR / "component_registry.json")
    icon_registry = load_json(REGISTRY_DIR / "icon_registry.json")

    roles = role_map(semantic_contract)
    components = component_map(component_registry)
    icons = icon_ids(icon_registry)
    manifest_by_intent = sfx_manifest_items()
    runtime_registry = get_registry()
    assert_template_registry_mirrors()
    assert_color_policy(presentation_rules)

    if runtime_registry.format != "portrait":
        fail(f"runtime registry loaded wrong format: {runtime_registry.format}")

    for intent, rule in semantic_router.RULES.items():
        if intent not in roles:
            fail(f"router RULES intent missing from semantic_contract: {intent}")
        if roles[intent].get("visualForm") != rule.get("visualForm"):
            fail(f"{intent} visualForm registry={roles[intent].get('visualForm')} runtime={rule.get('visualForm')}")
        if runtime_registry.default_visual_form(intent) != roles[intent].get("visualForm"):
            fail(f"{intent} runtime registry default does not match semantic contract")

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
    layout_policy = presentation_rules.get("presenterLayoutPolicy")
    if not isinstance(layout_policy, dict):
        fail("presentation_rules.presenterLayoutPolicy must be an object")
    if layout_policy.get("automaticAllowed") != ["fullscreen", "large", "pip", "none"]:
        fail("portrait automatic presenter layouts changed unexpectedly")
    if layout_policy.get("manualOnly") != ["side"]:
        fail("portrait side layout must remain manual-only")
    if set(layout_policy.get("manualSources") or []) != {"manual-approved", "legacy-project"}:
        fail("portrait manual presenter layout sources are incomplete")
    if layout_policy.get("sideHudMovesPresenter") is not False:
        fail("portrait side HUDs must not move the presenter")
    if layout_policy.get("impactEventChangesPosition") is not False:
        fail("portrait presenter impact must remain scale-only")
    for rule in rules:
        if not isinstance(rule, dict):
            fail("presentation rule must be an object")
        intent = str(rule.get("semanticIntent") or "")
        if intent and intent not in roles:
            fail(f"presentation rule unknown semanticIntent: {intent}")
        sfx_intent = rule.get("primarySfxIntent")
        if sfx_intent is not None and str(sfx_intent) not in visual_event_builder.SFX_SUGGESTIONS:
            fail(f"presentation rule unknown SFX intent: {sfx_intent}")
        if runtime_registry.primary_sfx_intent(intent) != (str(sfx_intent) if sfx_intent else None):
            fail(f"presentation runtime SFX mismatch for {intent}")

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
