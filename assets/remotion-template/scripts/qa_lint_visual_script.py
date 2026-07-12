#!/usr/bin/env python3
"""Pre-render QA lint for NGG Koubo Remotion V4 visual scripts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()

VALIDATOR_PATH = SCRIPT_DIR / "validate_visual_script.py"
SMALL_ICON_REQUIRED_EVENT_TYPES = {"infoCard", "iconPulse"}
CARD_LIKE_MAIN_EVENT_TYPES = {
    "infoCard",
    "captionHighlight",
    "flowPath",
    "statusStack",
    "platformFanout",
    "transitionPushZoom",
    "workflowDashboard",
    "evidenceWindow",
    "ctaRecommend",
    "capabilityShare",
    "sceneLockGrid",
    "transformationStack",
    "automationHandoff",
}
RENDERED_AUDIO_TYPES = {"sfx", "bgm"}
PENDING_AUDIO_STATUSES = {"pending-selection", "pending-generation", "disabled", "muted"}
SFX_VISUAL_SYNC_WINDOW_FRAMES = 8
NUMERIC_VALUE_RE = re.compile(r"[+\-]?\d+(?:\.\d+)?\s*(?:%|万|亿|倍|[KkMmGg]|x|X)?")
NUMERIC_UNIT_RE = re.compile(r"[+\-]?\d+(?:\.\d+)?\s*(?:%|万|亿|倍|[KkMmGg]|x|X)")
FLOW_TEXT_RE = re.compile(r"(第一|第二|第三|第1|第2|第3|步骤|流程|结论|行动|最后|step|Step|01|02|03)")
NUMERIC_FULFILLMENT_TYPES = {"dataPunch", "metricSpotlight", "capabilityShare", "transformationStack"}
FLOW_FULFILLMENT_TYPES = {"flowPath", "statusStack", "platformFanout", "transitionPushZoom", "automationHandoff", "captionHighlight", "sceneLockGrid", "transformationStack"}
MAIN_HUD_DURATION_BUDGET_TYPES = {
    "kineticTitle",
    "highlightBox",
    "flowPath",
    "statusStack",
    "dataPunch",
    "metricSpotlight",
    "transitionPushZoom",
    "captionHighlight",
    "ctaTitle",
    "ctaRecommend",
    "workflowDashboard",
    "evidenceWindow",
    "capabilityShare",
    "sceneLockGrid",
    "transformationStack",
    "semanticProblemMap",
    "automationHandoff",
    "topicKeyword",
    "claimStrip",
    "ratioGallery",
}

HUD_COPY_LIMITS = {
    "highlightBox": {"text": 16, "subtext": 16},
    "semanticProblemMap": {"text": 16, "subtext": 16},
    "captionHighlight": {"text": 10, "subtext": 16},
    "automationHandoff": {"text": 10, "subtext": 16},
    "flowPath": {"title": 14, "text": 8},
    "statusStack": {"title": 14, "text": 8},
    "kineticTitle": {"text": 16, "subtext": 12},
    "ctaTitle": {"text": 14, "subtext": 14},
    "topicKeyword": {"text": 8, "subtext": 8},
    "claimStrip": {"text": 18},
}

VISUAL_FAMILY_BY_TYPE = {
    "infoCard": "card",
    "captionHighlight": "automation-panel",
    "flowPath": "flow-list-panel",
    "statusStack": "flow-list-panel",
    "platformFanout": "platform-fanout",
    "transitionPushZoom": "platform-fanout",
    "dataPunch": "data-punch",
    "metricSpotlight": "data-punch",
    "kineticTitle": "big-title",
    "bigJudgement": "big-title",
    "highlightBox": "contrast-map",
    "materialMain": "material-proof",
    "materialZoom": "material-proof",
    "evidenceWindow": "material-proof",
    "ctaTitle": "cta-title",
    "ctaRecommend": "cta-recommend",
    "workflowDashboard": "dashboard-panel",
    "capabilityShare": "capability-share",
    "sceneLockGrid": "scene-lock-grid",
    "transformationStack": "transformation-stack",
    "semanticProblemMap": "contrast-map",
    "automationHandoff": "automation-panel",
    "topicKeyword": "topic-keyword",
    "claimStrip": "claim-strip",
    "ratioGallery": "ratio-gallery",
    "depthKeyword": "depth-keyword",
}

SEMANTIC_ALLOWED_EVENT_TYPES = {
    "negative-friction": {"semanticProblemMap", "highlightBox", "kineticTitle", "statusSticker"},
    "negative-to-positive": {"semanticProblemMap", "highlightBox"},
    "result-promise": {"kineticTitle", "bigJudgement"},
    "positive-confirm": {"captionHighlight", "statusSticker"},
    "automation-handoff": {"automationHandoff", "captionHighlight", "flowPath", "statusStack"},
    "numeric-metric": {"dataPunch", "metricSpotlight"},
    "enumeration": {"flowPath", "statusStack"},
    "workflow-fields": {"flowPath", "statusStack", "captionHighlight"},
    "manual-field": {"infoCard"},
    "capability-share": {"capabilityShare"},
    "scene-lock": {"sceneLockGrid"},
    "transformation-stack": {"transformationStack"},
    "asset-variants": {"ratioGallery", "flowPath", "materialMain"},
    "platform-fanout": {"transitionPushZoom", "platformFanout"},
    "proof-material": {"materialMain", "statusSticker"},
    "cta-resolve": {"ctaTitle", "ctaRecommend"},
    "workflow-step": {"flowPath", "statusStack", "captionHighlight"},
    "topic-intro": {"topicKeyword"},
    "explanation-claim": {"claimStrip", "quoteSource", "statusSticker"},
}


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_visual_script", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"failed to load validator: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_static_file(remotion_root: Path, path_value: str) -> Path:
    normalized = path_value.replace("\\", "/").lstrip("/")
    return remotion_root / "public" / normalized


def media_checks(data: dict[str, Any], remotion_root: Path | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if remotion_root is None:
        return errors, warnings

    for idx, scene in enumerate(data.get("scenes", [])):
        if not isinstance(scene, dict):
            continue
        source_video = scene.get("sourceVideo")
        if isinstance(source_video, str) and source_video:
            candidate = resolve_static_file(remotion_root, source_video)
            if not candidate.exists():
                errors.append(f"scenes[{idx}].sourceVideo missing under public/: {source_video}")

    presenter_audio = data.get("presenterAudio")
    if isinstance(presenter_audio, dict) and presenter_audio.get("mode") == "normalized-wav":
        audio_path = presenter_audio.get("path")
        if not isinstance(audio_path, str) or not audio_path:
            errors.append("presenterAudio normalized-wav mode has no path")
        elif not resolve_static_file(remotion_root, audio_path).is_file():
            errors.append(f"presenterAudio.path missing under public/: {audio_path}")

    for idx, event in enumerate(data.get("visualEvents", [])):
        if not isinstance(event, dict):
            continue
        for field in ["assetPath", "assetStack", "foregroundAssetPath"]:
            value = event.get(field)
            values = value if isinstance(value, list) else [value]
            for item in values:
                if isinstance(item, str) and item:
                    candidate = resolve_static_file(remotion_root, item)
                    if not candidate.exists():
                        errors.append(f"visualEvents[{idx}].{field} missing under public/: {item}")

    for idx, cue in enumerate(data.get("audioCues", [])):
        if not isinstance(cue, dict):
            continue
        cue_type = str(cue.get("type") or "")
        path = cue.get("path")
        status = str(cue.get("status") or "")
        if cue_type in RENDERED_AUDIO_TYPES and isinstance(path, str) and path:
            candidate = resolve_static_file(remotion_root, path)
            if not candidate.exists():
                errors.append(f"audioCues[{idx}].path missing under public/: {path}")
        elif cue_type in RENDERED_AUDIO_TYPES and status not in PENDING_AUDIO_STATUSES:
            warnings.append(
                f"audioCues[{idx}] has no renderable path; set status to pending/disabled or provide a public audio path"
            )

    return errors, warnings


def fps_contract_checks(data: dict[str, Any], remotion_root: Path | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if remotion_root is None:
        return errors, warnings
    report_path = remotion_root / "qa" / "media" / "presenter_normalization.json"
    if not report_path.is_file():
        warnings.append("fps-contract: presenter normalization report is missing; source/composition FPS cannot be cross-checked")
        return errors, warnings
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"fps-contract: cannot read presenter normalization report: {exc}")
        return errors, warnings
    frame_rate = report.get("frameRate", {}) if isinstance(report.get("frameRate"), dict) else {}
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    composition_fps = int(composition.get("fps") or 0)
    recorded_fps = int(frame_rate.get("compositionFps") or report.get("fps") or 0)
    if recorded_fps and composition_fps != recorded_fps:
        errors.append(
            f"fps-contract: visual_script composition.fps={composition_fps} differs from presenter report fps={recorded_fps}"
        )
    if frame_rate.get("mixedPresenterFps") is True and report.get("normalizationApplied") is not True:
        errors.append("fps-contract: mixed presenter FPS requires normalizationApplied=true")
    if frame_rate.get("requiresCfrNormalization") is True and report.get("normalizationApplied") is not True:
        errors.append("fps-contract: fractional/VFR/override mismatch requires CFR normalization before rendering")
    verification = report.get("verification", {}) if isinstance(report.get("verification"), dict) else {}
    if verification.get("passed") is not True:
        errors.append("fps-contract: presenter normalization verification did not pass")
    return errors, warnings


def audio_policy_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    fps = int(data.get("composition", {}).get("fps") or 25)
    visual_events = [event for event in data.get("visualEvents", []) if isinstance(event, dict)]
    sfx_cues: list[dict[str, Any]] = []

    for idx, cue in enumerate(data.get("audioCues", [])):
        if not isinstance(cue, dict):
            continue
        cue_type = str(cue.get("type") or "")
        cue_id = str(cue.get("id") or f"audioCues[{idx}]")
        status = str(cue.get("status") or "")
        start = int(cue.get("startFrame", 0) or 0)
        end = int(cue.get("endFrame", 0) or 0)
        duration = int(cue.get("durationFrames", 0) or 0)
        if end > start:
            duration = end - start

        if cue_type == "sfx":
            sfx_cues.append(cue)
            if cue.get("volumeDb") is not None and float(cue.get("volumeDb")) > -14:
                errors.append(
                    f"audio-sfx-volume failed: {cue_id} volumeDb={cue.get('volumeDb')} is too loud for voice-first V4; keep prominent SFX <= -14 dB"
                )
            if duration and duration > round(fps * 1.2):
                warnings.append(
                    f"audio-sfx-duration warning: {cue_id} lasts {duration / fps:.2f}s; V4 SFX should usually be short"
                )
            if status not in PENDING_AUDIO_STATUSES:
                nearby_visual = any(
                    abs(start - int(event.get("startFrame", 0) or 0)) <= SFX_VISUAL_SYNC_WINDOW_FRAMES
                    or abs(start - int(event.get("endFrame", 0) or 0)) <= SFX_VISUAL_SYNC_WINDOW_FRAMES
                    for event in visual_events
                )
                if not nearby_visual:
                    warnings.append(
                        f"audio-sfx-sync warning: {cue_id} is not within {SFX_VISUAL_SYNC_WINDOW_FRAMES}f of a visual event boundary"
                    )
        elif cue_type == "bgm":
            if cue.get("volumeDb") is not None and float(cue.get("volumeDb")) > -20:
                errors.append(
                    f"audio-bgm-volume failed: {cue_id} volumeDb={cue.get('volumeDb')} is too loud; BGM must stay under narration"
                )
            if cue.get("duckUnderVoice") is False and status not in {"disabled", "muted"}:
                warnings.append(f"audio-bgm-ducking warning: {cue_id} should duck under voice")

    sfx_cues.sort(key=lambda cue: int(cue.get("startFrame", 0) or 0))
    for current, nxt in zip(sfx_cues, sfx_cues[1:]):
        current_status = str(current.get("status") or "")
        next_status = str(nxt.get("status") or "")
        if current_status in PENDING_AUDIO_STATUSES or next_status in PENDING_AUDIO_STATUSES:
            continue
        gap = int(nxt.get("startFrame", 0) or 0) - int(current.get("startFrame", 0) or 0)
        if gap < round(fps * 0.5):
            warnings.append(
                "audio-sfx-density warning: "
                f"{current.get('id', '?')} and {nxt.get('id', '?')} are only {gap}f apart; avoid SFX on every visual change"
            )

    return errors, warnings


def event_shade_side(event: dict[str, Any], scene: dict[str, Any] | None = None) -> str | None:
    event_type = str(event.get("type") or "")
    if event_type in {"cornerChapterLabel", "ctaTitle", "ctaRecommend", "materialMain", "materialZoom", "evidenceWindow", "depthKeyword"}:
        return None

    placement = f"{event.get('safeArea', '')} {event.get('style', '')} {event.get('motionType', '')}".lower()
    explicit_side = "right" if "right" in placement else "left" if "left" in placement else None
    semantic_role = str(event.get("semanticRole") or "")

    if event_type in {"kineticTitle", "bigJudgement", "dataPunch", "quoteSource", "topicKeyword"}:
        return explicit_side or "left"
    if event_type == "claimStrip":
        return explicit_side or "right"
    if event_type in {"flowPath", "statusStack", "platformFanout", "ratioGallery"}:
        return explicit_side or "right"
    if event_type in {"capabilityShare", "sceneLockGrid", "transformationStack"}:
        return explicit_side or "left"
    if event_type == "semanticProblemMap" or (event_type == "highlightBox" and semantic_role == "semantic-problem-map"):
        return "left"
    if event_type == "metricSpotlight":
        return explicit_side or "left"
    if event_type == "workflowDashboard":
        return explicit_side or "right"
    if event_type == "transitionPushZoom" and semantic_role == "platform-fanout":
        return "right"
    if event_type == "automationHandoff" or (event_type == "captionHighlight" and semantic_role == "automation-handoff"):
        return "left"

    if event_type == "infoCard":
        if semantic_role == "manual-field":
            return "right"
        if explicit_side:
            return explicit_side
        presenter_layout = str((scene or {}).get("presenterLayout") or "")
        return None if presenter_layout == "pip" else "left"

    if event_type == "statusSticker":
        if semantic_role == "chapter-label" or "top-left" in placement or "corner" in placement:
            return None
        return explicit_side

    return None


def main_hud_lane(event: dict[str, Any], scene: dict[str, Any] | None = None) -> str | None:
    event_type = str(event.get("type") or "")
    if event_type in {"cornerChapterLabel", "statusSticker", "iconPulse", "presenterReposition", "depthKeyword"}:
        return None
    if event_type in {"ctaTitle", "ctaRecommend"}:
        return "center"
    if event_type in {"materialMain", "materialZoom", "evidenceWindow"}:
        return "proof"
    return event_shade_side(event, scene)


def hud_overlap_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    buffer_frames = 10

    scenes = [scene for scene in data.get("scenes", []) if isinstance(scene, dict)]
    scene_by_id = {str(scene.get("id") or ""): scene for scene in scenes}
    main_events: list[dict[str, Any]] = []

    for event in data.get("visualEvents", []):
        if not isinstance(event, dict):
            continue
        scene = scene_by_id.get(str(event.get("sceneId") or ""))
        lane = main_hud_lane(event, scene)
        if not lane:
            continue
        main_events.append(
            {
                "id": str(event.get("id") or "?"),
                "type": str(event.get("type") or "?"),
                "semanticRole": str(event.get("semanticRole") or ""),
                "copy": " ".join(
                    str(event.get(key) or "").strip()
                    for key in ("title", "text", "subtext", "status")
                    if str(event.get(key) or "").strip()
                ),
                "lane": lane,
                "start": int(event.get("startFrame", 0) or 0),
                "end": int(event.get("endFrame", 0) or 0),
            }
        )

    by_lane: dict[str, list[dict[str, Any]]] = {}
    for event in main_events:
        by_lane.setdefault(event["lane"], []).append(event)

    for lane, lane_events in by_lane.items():
        lane_events.sort(key=lambda item: (item["start"], item["end"]))
        for current, nxt in zip(lane_events, lane_events[1:]):
            if nxt["start"] < current["end"]:
                overlap = current["end"] - nxt["start"]
                errors.append(
                    "no-main-hud-same-lane-overlap failed: "
                    f"{overlap}f overlap on {lane} lane between "
                    f"{current['id']} ({current['type']} {current['start']}-{current['end']}) and "
                    f"{nxt['id']} ({nxt['type']} {nxt['start']}-{nxt['end']})"
                )
                continue
            gap = nxt["start"] - current["end"]
            if gap < buffer_frames:
                warnings.append(
                    "main HUD handoff buffer is short: "
                    f"{gap}f gap on {lane} lane between {current['id']} and {nxt['id']}; "
                    f"prefer at least {buffer_frames}f"
                )
            if (
                gap <= 90
                and current["type"] == nxt["type"]
                and current["semanticRole"] == nxt["semanticRole"]
                and current["copy"]
                and current["copy"] == nxt["copy"]
            ):
                errors.append(
                    "duplicate-main-hud-nearby failed: "
                    f"{current['id']} and {nxt['id']} repeat the same {current['type']} HUD copy "
                    f"within {gap}f on the {lane} lane; merge them or change the second beat into a semantic progression"
                )

    return errors, warnings


def hud_duration_budget_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    fps = int(data.get("composition", {}).get("fps") or 25)
    hard_min = round(fps * 3.2)
    preferred_min = round(fps * 4.5)

    for idx, event in enumerate(data.get("visualEvents", [])):
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "")
        if event_type not in MAIN_HUD_DURATION_BUDGET_TYPES:
            continue
        event_id = str(event.get("id") or f"visualEvents[{idx}]")
        start = int(event.get("startFrame", 0) or 0)
        end = int(event.get("endFrame", 0) or 0)
        duration = end - start
        if str(event.get("timingClass") or "") == "short-lightweight":
            short_min = round(fps * 1.8)
            if duration < short_min:
                errors.append(
                    "short-lightweight-hud-duration failed: "
                    f"{event_id} ({event_type}) lasts {duration}f; needs at least {short_min}f "
                    "so the lightweight entry and readable hold can complete"
                )
            continue
        if duration < hard_min:
            errors.append(
                "main-hud-duration-budget failed: "
                f"{event_id} ({event_type}) lasts {duration}f; needs at least {hard_min}f "
                "so entry, internal motion, hold, and exit can complete"
            )
        elif duration < preferred_min:
            warnings.append(
                "main HUD duration is below preferred hold: "
                f"{event_id} ({event_type}) lasts {duration}f; prefer {preferred_min}f or more"
            )

    return errors, warnings


def layered_hud_step_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for idx, event in enumerate(data.get("visualEvents", [])):
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "")
        if event_type not in {"capabilityShare", "sceneLockGrid", "transformationStack"}:
            continue
        event_id = str(event.get("id") or f"visualEvents[{idx}]")
        steps = event.get("internalSteps")
        if not isinstance(steps, list) or len(steps) < 2:
            errors.append(
                "layered-hud-internal-steps failed: "
                f"{event_id} ({event_type}) must define at least 2 internalSteps so header, tiles, and rows can appear by semantic phase"
            )
            continue
        if event_type == "capabilityShare" and len(steps) < 3:
            warnings.append(
                "capabilityShare is sparse: "
                f"{event_id} has {len(steps)} internalSteps; use 3-4 rows/objects when comparing shares or capabilities"
            )
        if event_type == "transformationStack" and len(steps) < 4:
            errors.append(
                "layered-hud-internal-steps failed: "
                f"{event_id} (transformationStack) needs source, target, at least one driver, and result metric steps"
            )

    return errors, warnings


def icon_and_card_strategy_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    scenes = [scene for scene in data.get("scenes", []) if isinstance(scene, dict)]
    scene_by_id = {str(scene.get("id") or ""): scene for scene in scenes}
    events = [event for event in data.get("visualEvents", []) if isinstance(event, dict)]
    icon_groups: dict[str, dict[str, list[str]]] = {}
    main_events: list[dict[str, Any]] = []

    for idx, event in enumerate(events):
        event_type = str(event.get("type") or "")
        semantic_role = str(event.get("semanticRole") or "")
        event_id = str(event.get("id") or f"visualEvents[{idx}]")
        requires_icon = event_type in SMALL_ICON_REQUIRED_EVENT_TYPES or (
            event_type == "statusSticker" and semantic_role != "chapter-label"
        )

        if requires_icon:
            icon_name = str(event.get("iconName") or "")
            if not icon_name:
                errors.append(f"small-card-has-icon failed: {event_id} ({event_type}) is missing iconName")
            else:
                group_id = str(event.get("beatGroupId") or event.get("sceneId") or "global")
                icon_groups.setdefault(group_id, {}).setdefault(icon_name, []).append(event_id)

        internal_steps = event.get("internalSteps")
        if isinstance(internal_steps, list):
            step_icons: dict[str, list[str]] = {}
            for step_idx, step in enumerate(internal_steps):
                if not isinstance(step, dict):
                    continue
                step_id = str(step.get("id") or f"{event_id}.internalSteps[{step_idx}]")
                icon_name = str(step.get("iconName") or "")
                if not icon_name:
                    errors.append(f"small-card-has-icon failed: {step_id} is missing iconName")
                    continue
                step_icons.setdefault(icon_name, []).append(step_id)
            for icon_name, step_ids in step_icons.items():
                if len(step_ids) > 1:
                    errors.append(
                        "no-repeated-icons-in-card-group failed: "
                        f"{event_id}.internalSteps repeats {icon_name} on {', '.join(step_ids)}"
                    )

        scene = scene_by_id.get(str(event.get("sceneId") or ""))
        if main_hud_lane(event, scene):
            main_events.append(event)

    for group_id, by_icon in icon_groups.items():
        for icon_name, event_ids in by_icon.items():
            if len(event_ids) > 1:
                errors.append(
                    "no-repeated-icons-in-card-group failed: "
                    f"{group_id} repeats {icon_name} on {', '.join(event_ids)}"
                )

    main_events.sort(key=lambda event: int(event.get("startFrame", 0) or 0))
    card_like_count = 0
    run: list[str] = []
    family_run: list[tuple[str, str]] = []
    for event in main_events:
        event_type = str(event.get("type") or "")
        event_id = str(event.get("id") or "?")
        is_card_like = event_type in CARD_LIKE_MAIN_EVENT_TYPES
        if is_card_like:
            card_like_count += 1
            run.append(event_id)
            if len(run) == 3:
                warnings.append(
                    "card-heavy-sequence-warning: "
                    f"3 consecutive main visual events are card/panel-like ({', '.join(run)})"
                )
        else:
            run = []

        family = VISUAL_FAMILY_BY_TYPE.get(event_type, event_type)
        if family_run and family_run[-1][1] == family:
            family_run.append((event_id, family))
        else:
            family_run = [(event_id, family)]
        if len(family_run) == 3:
            errors.append(
                "component-family-repetition failed: "
                f"3 consecutive main visual events use {family} ({', '.join(item[0] for item in family_run)}); "
                "change one beat into a different semantic visual form"
            )

    if main_events:
        ratio = card_like_count / len(main_events)
        if ratio > 0.35:
            warnings.append(
                "main-card-ratio-warning: "
                f"{card_like_count}/{len(main_events)} main visual events are card/panel-like ({ratio:.0%}); target <= 35%"
            )

    return errors, warnings


def visible_event_text(event: dict[str, Any]) -> str:
    return " ".join(str(event.get(key) or "") for key in ("title", "text", "subtext", "status"))


def is_clear_numeric_text(text: str) -> bool:
    if NUMERIC_UNIT_RE.search(text):
        return True
    if NUMERIC_VALUE_RE.search(text) and any(
        word in text for word in ["转化率", "提升", "增长", "比例", "百分", "指标", "数据", "规模"]
    ):
        return True
    return False


def hud_copy_quality_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for idx, event in enumerate(data.get("visualEvents", [])):
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "")
        event_id = str(event.get("id") or f"visualEvents[{idx}]")
        limits = HUD_COPY_LIMITS.get(event_type, {})

        for field, limit in limits.items():
            value = str(event.get(field) or "")
            if len(value) <= limit:
                continue
            message = (
                "hud-copy-too-long failed: "
                f"{event_id}.{field} has {len(value)} chars; limit is {limit}. "
                "HUD copy must be key-message copy, not full transcript text"
            )
            if event_type in {"highlightBox", "semanticProblemMap", "captionHighlight", "automationHandoff"}:
                errors.append(message)
            else:
                warnings.append(message.replace(" failed: ", " warning: "))

        emphasis_words = [
            str(item)
            for item in (event.get("emphasisWords") if isinstance(event.get("emphasisWords"), list) else [])
            if str(item)
        ]
        combined = f"{event.get('title', '')}{event.get('text', '')}{event.get('subtext', '')}"

        if event_type in {"highlightBox", "semanticProblemMap"}:
            if not emphasis_words:
                errors.append(
                    f"hud-emphasis-missing failed: {event_id} is a warning/contrast HUD but has no emphasisWords"
                )
            elif not any(word in combined for word in emphasis_words):
                errors.append(
                    f"hud-emphasis-missing failed: {event_id} emphasisWords do not appear in visible HUD copy"
                )

        if event_type in {"captionHighlight", "automationHandoff"} and str(event.get("semanticRole") or "") == "automation-handoff":
            if not emphasis_words:
                warnings.append(
                    f"hud-emphasis-missing warning: {event_id} confirm/handoff HUD should mark the green emphasis phrase"
                )
            elif not any(word in combined for word in emphasis_words):
                warnings.append(
                    f"hud-emphasis-missing warning: {event_id} emphasisWords do not appear in visible HUD copy"
                )

    return errors, warnings


def cta_provenance_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    beats = {
        str(beat.get("id") or ""): beat
        for beat in data.get("semanticBeats", [])
        if isinstance(beat, dict)
    }
    action_terms = ["评论区", "关注", "点赞", "收藏", "私信", "领取", "自提", "告诉我"]

    for event in data.get("visualEvents", []):
        if not isinstance(event, dict) or str(event.get("type") or "") not in {"ctaTitle", "ctaRecommend"}:
            continue
        event_id = str(event.get("id") or "?")
        source_beat_id = str(event.get("sourceBeatId") or "")
        source_beat = beats.get(source_beat_id, {})
        provenance = event.get("ctaProvenance")
        if source_beat_id and not isinstance(provenance, dict):
            errors.append(f"cta-provenance failed: {event_id} is generated from {source_beat_id} but has no ctaProvenance")
            continue

        source_text = str((provenance or {}).get("sourceText") or source_beat.get("text") or "")
        visible = visible_event_text(event)
        if not source_text:
            warnings.append(f"cta-provenance warning: {event_id} has no sourceText to audit")
            continue

        for term in action_terms:
            if term in visible and term not in source_text:
                errors.append(f"cta-provenance failed: {event_id} invented action {term!r} not present in sourceText")
        if "关键词：" in visible and not any(term in source_text for term in ["关键词", "扣", "回复", "发送"]):
            errors.append(f"cta-provenance failed: {event_id} invented a keyword CTA not supported by sourceText")

        action = str((provenance or {}).get("action") or "")
        keyword = str((provenance or {}).get("keyword") or "")
        if action and action not in source_text:
            errors.append(f"cta-provenance failed: {event_id}.ctaProvenance.action is not present in sourceText")
        if keyword and keyword not in source_text:
            errors.append(f"cta-provenance failed: {event_id}.ctaProvenance.keyword is not present in sourceText")

    return errors, warnings


def semantic_fulfillment_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    scenes = [scene for scene in data.get("scenes", []) if isinstance(scene, dict)]
    events = [event for event in data.get("visualEvents", []) if isinstance(event, dict)]
    events_by_scene: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        events_by_scene.setdefault(str(event.get("sceneId") or ""), []).append(event)

        event_id = str(event.get("id") or "?")
        event_type = str(event.get("type") or "")
        semantic_role = str(event.get("semanticRole") or "")
        text = visible_event_text(event)

        if is_clear_numeric_text(text) and event_type not in NUMERIC_FULFILLMENT_TYPES:
            errors.append(
                "semantic-fulfillment-numeric failed: "
                f"{event_id} contains a clear numeric metric but uses {event_type}; use dataPunch/metricSpotlight with count-up or chart motion"
            )

        if semantic_role == "workflow-step" and event_type == "infoCard":
            errors.append(
                "semantic-fulfillment-flow failed: "
                f"{event_id} is a workflow/enumeration beat rendered as infoCard; use flowPath/statusStack with internalSteps"
            )

    for scene in scenes:
        scene_id = str(scene.get("id") or "")
        narration = str(scene.get("narrationText") or "")
        scene_events = events_by_scene.get(scene_id, [])
        if is_clear_numeric_text(narration) and not any(str(event.get("type") or "") in NUMERIC_FULFILLMENT_TYPES for event in scene_events):
            errors.append(
                "semantic-fulfillment-numeric failed: "
                f"{scene_id} narration contains a clear numeric metric but no dataPunch/metricSpotlight event is scheduled"
            )
        if FLOW_TEXT_RE.search(narration) and not any(
            str(event.get("type") or "") in FLOW_FULFILLMENT_TYPES for event in scene_events
        ):
            warnings.append(
                "semantic-fulfillment-flow warning: "
                f"{scene_id} narration appears to describe a process/enumeration but no flowPath/statusStack event is scheduled"
            )

    return errors, warnings


def semantic_beat_fulfillment_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    beats = [beat for beat in data.get("semanticBeats", []) if isinstance(beat, dict)]
    events = [event for event in data.get("visualEvents", []) if isinstance(event, dict)]
    if not beats:
        errors.append("semantic-beats-present failed: visual_script.json has no semanticBeats")
        return errors, warnings

    events_by_beat: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        source_beat_id = str(event.get("sourceBeatId") or "")
        if source_beat_id:
            events_by_beat.setdefault(source_beat_id, []).append(event)

    for beat in beats:
        beat_id = str(beat.get("id") or "?")
        intent = str(beat.get("semanticIntent") or "")
        visual_form = str(beat.get("visualForm") or "")
        required_checks = beat.get("requiredChecks")
        matched_events = events_by_beat.get(beat_id, [])
        intentional_clean = intent == "explanation-claim" and visual_form == "intentionalCleanHold"
        if not matched_events:
            if intentional_clean:
                checks = [str(item) for item in required_checks or [] if str(item)]
                confidence = float(beat.get("confidence", 0.0) or 0.0)
                if "intentional-clean-hold" not in checks:
                    errors.append(
                        "intentional-clean-hold failed: "
                        f"{beat_id} has visualForm=intentionalCleanHold without the required audit check"
                    )
                elif confidence > 0.65:
                    errors.append(
                        "intentional-clean-hold failed: "
                        f"{beat_id} confidence={confidence:.2f}; do not suppress a high-confidence semantic beat"
                    )
                continue
            errors.append(
                "semantic-intent-fulfilled failed: "
                f"{beat_id} ({intent}/{visual_form}) has no visualEvent with sourceBeatId={beat_id}"
            )
            continue

        event_types = {str(event.get("type") or "") for event in matched_events}
        allowed_types = SEMANTIC_ALLOWED_EVENT_TYPES.get(intent)
        if allowed_types and not event_types.intersection(allowed_types):
            errors.append(
                "semantic-intent-fulfilled failed: "
                f"{beat_id} ({intent}/{visual_form}) rendered as {sorted(event_types)}; expected one of {sorted(allowed_types)}"
            )

        source_cue_ids = [str(item) for item in beat.get("sourceCueIds", []) if str(item)]
        if len(source_cue_ids) > 1 and not any(str(event.get("timingAnchor") or "") == "captionCueKeyword" for event in matched_events):
            warnings.append(
                "hud-keyword-cue-anchor warning: "
                f"{beat_id} spans multiple caption cues; generated HUD should anchor to the cue containing its visible keyword"
            )

        if intent in {"negative-friction", "negative-to-positive"}:
            if not any(
                str(event.get("type") or "") in {"highlightBox", "semanticProblemMap"}
                and str(event.get("semanticRole") or "") == "semantic-problem-map"
                for event in matched_events
            ):
                errors.append(
                    "negative-red-treatment failed: "
                    f"{beat_id} must render a red warning/contrast component, not a neutral or generic card"
                )
            if intent == "negative-friction" and any(
                str(event.get("type") or "") in {"highlightBox", "semanticProblemMap"}
                and str(event.get("subtext") or "").strip()
                for event in matched_events
            ):
                errors.append(
                    "negative-only-no-invented-positive failed: "
                    f"{beat_id} is negative-only, so it must not invent a green resolution card"
                )
            if intent == "negative-to-positive" and not any(
                str(event.get("type") or "") in {"highlightBox", "semanticProblemMap"}
                and str(event.get("subtext") or "").strip()
                for event in matched_events
            ):
                errors.append(
                    "negative-to-positive-resolution-missing failed: "
                    f"{beat_id} needs an explicit positive resolution in subtext"
                )

        if intent == "positive-confirm":
            if not any(str(event.get("type") or "") in {"captionHighlight", "statusSticker"} for event in matched_events):
                errors.append(f"positive-confirm-treatment failed: {beat_id} needs a confirm/handoff visual")

        if intent == "numeric-metric":
            if not any(
                str(event.get("type") or "") in NUMERIC_FULFILLMENT_TYPES
                and isinstance(event.get("numericValue"), (int, float))
                for event in matched_events
            ):
                errors.append(
                    "numeric-countup-required failed: "
                    f"{beat_id} must render dataPunch/metricSpotlight with numericValue"
                )

        if intent in {"workflow-fields", "enumeration", "asset-variants"}:
            if any(str(event.get("type") or "") == "infoCard" for event in matched_events):
                errors.append(
                    "workflow-not-generic-card failed: "
                    f"{beat_id} fell back to infoCard; use flowPath/statusStack/material visual grammar"
                )
            if not any(isinstance(event.get("internalSteps"), list) and event.get("internalSteps") for event in matched_events):
                warnings.append(
                    "workflow-not-generic-card warning: "
                    f"{beat_id} has no internalSteps; staged list/process animation may be weak"
                )

        if intent == "proof-material":
            material_events = [event for event in matched_events if str(event.get("type") or "") == "materialMain"]
            if material_events:
                for event in material_events:
                    asset_path = str(event.get("assetPath") or "")
                    if asset_path.lower().endswith((".mp4", ".mov", ".m4v", ".webm")) and str(event.get("style") or "") != "recording-proof":
                        errors.append(
                            "proof-video-must-play failed: "
                            f"{event.get('id', '?')} uses video asset {asset_path} without style=recording-proof"
                        )
            elif isinstance(required_checks, list) and "proof-video-must-play" in required_checks:
                warnings.append(
                    "proof-video-must-play warning: "
                    f"{beat_id} references proof/material language but no proof asset was available, so builder used a placeholder"
                )

    return errors, warnings


def rhythm_checks(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    composition = data.get("composition", {}) if isinstance(data.get("composition"), dict) else {}
    fps = int(composition.get("fps") or 25)
    visual_gap_warn = round(fps * 4.0)
    semantic_gap_error = round(fps * 7.0)
    main_min_frames = round(fps * 4.5)
    dense_event_types = {
        "kineticTitle",
        "highlightBox",
        "infoCard",
        "captionHighlight",
        "transitionPushZoom",
        "ctaTitle",
    }

    scenes = [scene for scene in data.get("scenes", []) if isinstance(scene, dict)]
    scene_by_id = {str(scene.get("id") or ""): scene for scene in scenes}
    events = [event for event in data.get("visualEvents", []) if isinstance(event, dict)]
    events_by_scene: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        scene_id = str(event.get("sceneId") or "")
        if scene_id:
            events_by_scene.setdefault(scene_id, []).append(event)

        event_type = str(event.get("type") or "")
        event_start = int(event.get("startFrame", 0) or 0)
        event_end = int(event.get("endFrame", 0) or 0)
        duration = event_end - event_start
        scene = scene_by_id.get(scene_id, {})
        scene_end = int(scene.get("endFrame", 0) or 0)
        scene_duration = int(scene.get("endFrame", 0) or 0) - int(scene.get("startFrame", 0) or 0)
        available_from_start = max(1, scene_end - event_start) if scene_end else main_min_frames
        required_duration = min(
            main_min_frames,
            available_from_start,
            max(18, scene_duration - round(fps * 0.4)),
        )
        if event_type in dense_event_types and scene_duration >= round(fps * 5.0) and duration < required_duration:
            warnings.append(
                f"visualEvents[{event.get('id', '?')}] lasts {duration / fps:.2f}s; dense V4 main HUD should hold 4.5-6s when scene length allows"
            )

    for scene in scenes:
        scene_id = str(scene.get("id") or "")
        scene_start = int(scene.get("startFrame", 0) or 0)
        scene_end = int(scene.get("endFrame", scene_start) or scene_start)
        scene_duration = max(0, scene_end - scene_start)
        if scene_duration <= 0:
            continue

        scene_events = sorted(
            events_by_scene.get(scene_id, []),
            key=lambda event: int(event.get("startFrame", 0) or 0),
        )
        if not scene_events:
            if scene_duration > semantic_gap_error:
                errors.append(f"{scene_id} has no visualEvents for {scene_duration / fps:.2f}s")
            elif scene_duration > visual_gap_warn:
                warnings.append(f"{scene_id} has no visualEvents for {scene_duration / fps:.2f}s")
            continue

        cursor = scene_start
        for event in scene_events:
            event_start = int(event.get("startFrame", scene_start) or scene_start)
            event_end = int(event.get("endFrame", event_start) or event_start)
            gap = max(0, event_start - cursor)
            if gap > semantic_gap_error:
                errors.append(
                    f"{scene_id} has {gap / fps:.2f}s without a semantic visual event before {event.get('id', '?')}"
                )
            elif gap > visual_gap_warn:
                warnings.append(
                    f"{scene_id} has {gap / fps:.2f}s without visual change before {event.get('id', '?')}"
                )
            cursor = max(cursor, event_end)

        tail_gap = max(0, scene_end - cursor)
        if tail_gap > semantic_gap_error:
            errors.append(f"{scene_id} has {tail_gap / fps:.2f}s tail gap after the last visual event")
        elif tail_gap > visual_gap_warn:
            warnings.append(f"{scene_id} has {tail_gap / fps:.2f}s tail gap after the last visual event")

    return errors, warnings


def format_report(errors: list[str], warnings: list[str]) -> str:
    lines = ["# V4 Pre-render QA Lint", ""]
    lines.append("## Status")
    lines.append("")
    lines.append("FAIL" if errors else "PASS")
    lines.append("")
    lines.append("## Errors")
    lines.append("")
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual-script", required=True, type=Path)
    parser.add_argument("--remotion-root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    validator = load_validator()
    errors, warnings = validator.validate(args.visual_script)
    data = load_json(args.visual_script)
    media_errors, media_warnings = media_checks(data, args.remotion_root)
    errors.extend(media_errors)
    warnings.extend(media_warnings)
    fps_errors, fps_warnings = fps_contract_checks(data, args.remotion_root)
    errors.extend(fps_errors)
    warnings.extend(fps_warnings)
    audio_errors, audio_warnings = audio_policy_checks(data)
    errors.extend(audio_errors)
    warnings.extend(audio_warnings)
    rhythm_errors, rhythm_warnings = rhythm_checks(data)
    errors.extend(rhythm_errors)
    warnings.extend(rhythm_warnings)
    hud_errors, hud_warnings = hud_overlap_checks(data)
    errors.extend(hud_errors)
    warnings.extend(hud_warnings)
    duration_errors, duration_warnings = hud_duration_budget_checks(data)
    errors.extend(duration_errors)
    warnings.extend(duration_warnings)
    layered_errors, layered_warnings = layered_hud_step_checks(data)
    errors.extend(layered_errors)
    warnings.extend(layered_warnings)
    icon_errors, icon_warnings = icon_and_card_strategy_checks(data)
    errors.extend(icon_errors)
    warnings.extend(icon_warnings)
    fulfillment_errors, fulfillment_warnings = semantic_fulfillment_checks(data)
    errors.extend(fulfillment_errors)
    warnings.extend(fulfillment_warnings)
    copy_errors, copy_warnings = hud_copy_quality_checks(data)
    errors.extend(copy_errors)
    warnings.extend(copy_warnings)
    cta_errors, cta_warnings = cta_provenance_checks(data)
    errors.extend(cta_errors)
    warnings.extend(cta_warnings)
    beat_errors, beat_warnings = semantic_beat_fulfillment_checks(data)
    errors.extend(beat_errors)
    warnings.extend(beat_warnings)

    report = format_report(errors, warnings)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"qa lint report written to {args.out}")
    else:
        print(report)

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
