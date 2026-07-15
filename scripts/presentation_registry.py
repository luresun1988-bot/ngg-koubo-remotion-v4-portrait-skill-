#!/usr/bin/env python3
"""Read-only runtime access to the V4 semantic and presentation registries.

The loader is deliberately format-agnostic so the same file can be mirrored in
the landscape and portrait Skills.  It does not mutate routed output; it makes
the machine-readable contracts available to the router, planner, validator and
QA tools through one validated interface.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_FILENAMES = (
    "semantic_contract.json",
    "presentation_rules.json",
    "component_registry.json",
    "icon_registry.json",
)


def _registry_dir() -> Path:
    candidates = (
        SCRIPT_DIR.parent / "references" / "registries",
        SCRIPT_DIR.parent.parent / "references" / "registries",
    )
    for directory in candidates:
        if all((directory / name).is_file() for name in REGISTRY_FILENAMES):
            return directory
    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"missing V4 registry bundle; searched: {searched}")


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"registry root must be an object: {path}")
    return data


def _index(items: Any, key: str, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise ValueError(f"{label} must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"{label} items must be objects")
        item_id = str(item.get(key) or "")
        if not item_id:
            raise ValueError(f"{label} item missing {key}")
        if item_id in indexed:
            raise ValueError(f"duplicate {label} {key}: {item_id}")
        indexed[item_id] = item
    return indexed


class PresentationRegistry:
    """Validated in-memory view of the four V4 registries."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.semantic_contract = _load_json(directory / "semantic_contract.json")
        self.presentation_rules = _load_json(directory / "presentation_rules.json")
        self.component_registry = _load_json(directory / "component_registry.json")
        self.icon_registry = _load_json(directory / "icon_registry.json")

        formats = {
            str(data.get("format") or "")
            for data in (
                self.semantic_contract,
                self.presentation_rules,
                self.component_registry,
                self.icon_registry,
            )
        }
        if len(formats) != 1 or "" in formats:
            raise ValueError(f"registry format mismatch: {sorted(formats)}")
        self.format = next(iter(formats))

        self.roles = _index(self.semantic_contract.get("roles"), "semanticIntent", "semantic roles")
        self.presentations = _index(
            self.presentation_rules.get("semanticToPresentation"),
            "semanticIntent",
            "presentation rules",
        )
        self.components = _index(
            self.component_registry.get("components"),
            "visualForm",
            "components",
        )
        self.icons = _index(self.icon_registry.get("icons"), "id", "icons")
        self.default_icon = str(self.icon_registry.get("defaultFallback") or "Sparkles")
        if self.default_icon not in self.icons:
            raise ValueError(f"icon defaultFallback is not registered: {self.default_icon}")

        for intent, role in self.roles.items():
            visual_form = str(role.get("visualForm") or "")
            fallback = str(role.get("fallbackVisualForm") or "")
            if visual_form not in self.components:
                raise ValueError(f"{intent} references unknown visualForm: {visual_form}")
            if fallback and fallback not in self.components:
                raise ValueError(f"{intent} references unknown fallbackVisualForm: {fallback}")

    def role(self, semantic_intent: str) -> dict[str, Any]:
        try:
            return self.roles[semantic_intent]
        except KeyError as exc:
            raise KeyError(f"unknown semanticIntent: {semantic_intent}") from exc

    def default_visual_form(self, semantic_intent: str) -> str:
        return str(self.role(semantic_intent).get("visualForm") or "")

    def fallback_visual_form(self, semantic_intent: str) -> str:
        role = self.role(semantic_intent)
        return str(role.get("fallbackVisualForm") or self.components[self.default_visual_form(semantic_intent)].get("fallback") or "")

    def component(self, visual_form: str) -> dict[str, Any]:
        try:
            return self.components[visual_form]
        except KeyError as exc:
            raise KeyError(f"unknown visualForm: {visual_form}") from exc

    def event_types(self, semantic_intent: str) -> tuple[str, ...]:
        rule = self.presentations.get(semantic_intent, {})
        values = rule.get("eventTypes", [])
        if not isinstance(values, list):
            raise ValueError(f"{semantic_intent} presentation eventTypes must be a list")
        return tuple(str(value) for value in values if str(value))

    def semantic_allowed_event_types(self) -> dict[str, set[str]]:
        return {
            intent: set(self.event_types(intent))
            for intent, rule in self.presentations.items()
            if rule.get("qaEnforce", True) is not False and self.event_types(intent)
        }

    def primary_sfx_intent(self, semantic_intent: str) -> str | None:
        value = self.presentations.get(semantic_intent, {}).get("primarySfxIntent")
        return str(value) if value else None

    def presentation_sfx_intents(self) -> dict[str, str]:
        return {
            intent: sfx
            for intent in self.presentations
            if (sfx := self.primary_sfx_intent(intent)) is not None
        }

    def icon_id(self, requested: str | None) -> str:
        return requested if requested in self.icons else self.default_icon


@lru_cache(maxsize=1)
def get_registry() -> PresentationRegistry:
    return PresentationRegistry(_registry_dir())


def semantic_default_visual_form(semantic_intent: str) -> str:
    return get_registry().default_visual_form(semantic_intent)


def semantic_fallback_visual_form(semantic_intent: str) -> str:
    return get_registry().fallback_visual_form(semantic_intent)


def presentation_sfx_intents() -> dict[str, str]:
    return get_registry().presentation_sfx_intents()


def semantic_allowed_event_types() -> dict[str, set[str]]:
    return get_registry().semantic_allowed_event_types()
