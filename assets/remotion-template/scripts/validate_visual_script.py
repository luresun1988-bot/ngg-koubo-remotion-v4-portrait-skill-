#!/usr/bin/env python3
"""Validate an NGG Koubo Remotion V4 visual_script.json file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from v4_utf8 import configure_utf8  # noqa: E402

configure_utf8()

REQUIRED_TOP_LEVEL = [
    "schemaVersion",
    "composition",
    "captionTimeline",
    "researchNotes",
    "media",
    "scenes",
    "semanticBeats",
    "captionCues",
    "visualEvents",
    "audioCues",
    "qaFrames",
]

ALLOWED_SCENE_TYPES = {
    "Hook",
    "Explanation",
    "Proof",
    "Process",
    "Contrast",
    "CleanMaterial",
    "CTA",
}

ALLOWED_AUDIO_TYPES = {"sfx", "bgm", "source", "silence"}
PENDING_AUDIO_STATUSES = {"pending-selection", "pending-generation", "disabled", "muted", "suggested"}
FORBIDDEN_CAPTION_TIMING_METHODS = {
    "proportional-scene-split",
    "scene-proportional",
    "estimated",
    "character-ratio-scene-fill",
    "text-length-scene-fill",
}

VISIBLE_TEXT_FIELDS = {
    "text",
    "subtext",
    "title",
    "status",
    "intent",
    "narrationText",
    "highlightWords",
    "emphasisWords",
    "summary",
    "reason",
    "checks",
    "visualUse",
    "topic",
    "semanticIntent",
    "visualForm",
    "keywords",
    "requiredChecks",
}

CORRUPTION_RE = re.compile(
    "|".join(
        [
            r"\ufffd",
            r"\?{2,}",
            r"[ÃÂÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]{2,}",
            r"鍙戝",
            r"涓€",
            r"鐨",
            r"鏄",
            r"鎴",
            r"閿",
            r"璇",
            r"绱犳",
            r"骞冲",
            r"鍔ㄥ",
            r"瑙備",
            r"杈戯",
            r"灏侀",
            r"瀛楁",
            r"浠嬨",
            r"垪",
        ]
    )
)

CAPTION_WARN_CHARS = 56
CAPTION_ERROR_CHARS = 86
FOCUS_ALLOWED_ROLES = {"proof-focus", "proof-material", "material-main"}
FOCUS_FORBIDDEN_TYPES = {
    "kineticTitle",
    "captionHighlight",
    "infoCard",
    "flowPath",
    "statusStack",
    "platformFanout",
    "dataPunch",
    "metricSpotlight",
    "workflowDashboard",
    "capabilityShare",
    "sceneLockGrid",
    "transformationStack",
    "transitionPushZoom",
    "ctaTitle",
    "ctaRecommend",
    "evidenceWindow",
    "semanticProblemMap",
    "automationHandoff",
    "topicKeyword",
    "claimStrip",
    "ratioGallery",
    "depthKeyword",
    "pairedInputRail",
    "factorTrinity",
    "causalDriver",
    "factorPriority",
    "compactPipeline",
    "limitationWarning",
    "priorityConclusion",
    "historicalGreenConclusion",
}
RENDERABLE_EVENT_TYPES = {
    "kineticTitle", "captionHighlight", "cornerChapterLabel", "infoCard", "statusSticker", "iconPulse",
    "materialMain", "materialZoom", "highlightBox", "presenterReposition", "transitionPushZoom", "ctaTitle",
    "bigJudgement", "dataPunch", "quoteSource", "flowPath", "statusStack", "platformFanout", "evidenceWindow",
    "ctaRecommend", "metricSpotlight", "workflowDashboard", "capabilityShare", "sceneLockGrid", "transformationStack",
    "semanticProblemMap", "automationHandoff", "topicKeyword", "claimStrip", "ratioGallery", "depthKeyword",
    "pairedInputRail", "factorTrinity", "causalDriver", "factorPriority", "compactPipeline",
    "limitationWarning", "priorityConclusion", "historicalGreenConclusion",
}
FOCUS_FORBIDDEN_ROLES = {
    "semantic-problem-map",
    "manual-field",
    "platform-fanout",
    "automation-handoff",
    "workflow-step",
    "capability-share",
    "scene-lock",
    "transformation-stack",
    "metric-growth",
    "result-promise",
    "cta-resolve",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"failed to read JSON: {path}: {exc}") from exc


def ensure_list(data: dict[str, Any], key: str, errors: list[str]) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        errors.append(f"{key} must be an array")
        return []
    return value


def frame_value(obj: dict[str, Any], key: str) -> int | None:
    value = obj.get(key)
    return value if isinstance(value, int) and value >= 0 else None


def visible_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def normalize_spoken_text(text: str) -> str:
    """Normalize spoken text for comparing split captions to scene narration."""
    return re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE).lower()


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def collect_text_corruption(value: object, path: str, errors: list[str]) -> None:
    """Fail fast when generated visible copy was already mojibake-corrupted."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key in VISIBLE_TEXT_FIELDS:
                collect_text_corruption(child, child_path, errors)
            elif isinstance(child, (dict, list)):
                collect_text_corruption(child, child_path, errors)
        return

    if isinstance(value, list):
        for idx, child in enumerate(value):
            collect_text_corruption(child, f"{path}[{idx}]", errors)
        return

    if isinstance(value, str) and CORRUPTION_RE.search(value):
        errors.append(
            f"{path} contains likely text encoding corruption: {value!r}; "
            "regenerate visual_script.json from UTF-8 input or Unicode-safe strings before rendering"
        )


def validate(path: Path) -> tuple[list[str], list[str]]:
    data = load_json(path)
    errors: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    collect_text_corruption(data, "", errors)

    if data.get("schemaVersion") != "ngg-koubo-remotion-v4-portrait":
        warnings.append("schemaVersion should be ngg-koubo-remotion-v4-portrait")

    composition = data.get("composition", {})
    if not isinstance(composition, dict):
        errors.append("composition must be an object")
        composition = {}

    if composition.get("format") != "9:16":
        errors.append("composition.format must be 9:16 for V4 Portrait")
    if composition.get("width") != 1080 or composition.get("height") != 1920:
        warnings.append("recommended V4 Portrait composition size is 1080x1920")
    if not isinstance(composition.get("fps"), int) or composition.get("fps", 0) <= 0:
        errors.append("composition.fps must be a positive integer")
    if not isinstance(composition.get("durationFrames"), int) or composition.get("durationFrames", 0) <= 0:
        errors.append("composition.durationFrames must be a positive integer")

    caption_render_mode = data.get("captionRenderMode", "embedded")
    if caption_render_mode not in {"embedded", "none"}:
        errors.append("captionRenderMode must be embedded or none")
    presenter_audio = data.get("presenterAudio")
    if presenter_audio is not None:
        if not isinstance(presenter_audio, dict):
            errors.append("presenterAudio must be an object when provided")
        elif presenter_audio.get("mode") not in {"embedded", "normalized-wav", "none"}:
            errors.append("presenterAudio.mode must be embedded, normalized-wav, or none")
        elif presenter_audio.get("mode") == "normalized-wav":
            if not presenter_audio.get("path"):
                errors.append("presenterAudio.path is required for normalized-wav mode")
            if presenter_audio.get("sampleRate") != 48000:
                errors.append("presenterAudio.sampleRate must be 48000 for normalized-wav mode")
            sync_offset = presenter_audio.get("syncOffsetFrames", 0)
            if not isinstance(sync_offset, int):
                errors.append("presenterAudio.syncOffsetFrames must be an integer")
            elif sync_offset and not str(presenter_audio.get("syncEvidence") or "").strip():
                errors.append("non-zero presenterAudio.syncOffsetFrames requires syncEvidence")
            report_path = str(presenter_audio.get("normalizationReportPath") or "")
            if not report_path:
                errors.append("normalized-wav presenterAudio requires normalizationReportPath")
            else:
                remotion_root = path.parent.resolve()
                report_file = (remotion_root / report_path).resolve()
                try:
                    report_file.relative_to(remotion_root)
                except ValueError:
                    errors.append("presenterAudio.normalizationReportPath must stay inside Remotion root")
                else:
                    if not report_file.is_file():
                        errors.append(f"presenterAudio normalization report is missing: {report_path}")
                    else:
                        try:
                            report = json.loads(report_file.read_text(encoding="utf-8-sig"))
                        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                            errors.append(f"presenterAudio normalization report is invalid: {exc}")
                        else:
                            verification = report.get("verification") if isinstance(report, dict) else None
                            if not isinstance(verification, dict) or verification.get("passed") is not True:
                                errors.append("presenterAudio normalization report must record verification.passed=true")

    scenes = ensure_list(data, "scenes", errors)
    semantic_beats = ensure_list(data, "semanticBeats", errors)
    caption_cues = ensure_list(data, "captionCues", errors)
    visual_events = ensure_list(data, "visualEvents", errors)
    audio_cues = ensure_list(data, "audioCues", errors)
    qa_frames = ensure_list(data, "qaFrames", errors)

    if not scenes:
        errors.append("scenes must contain at least one scene")
    if not caption_cues:
        errors.append("captionCues must contain timed captions")
    if not semantic_beats:
        warnings.append("semanticBeats is empty; V4 should route caption semantics before generating visualEvents")
    if not qa_frames:
        errors.append("qaFrames must contain layered QA samples")

    caption_timeline = data.get("captionTimeline")
    if not isinstance(caption_timeline, dict):
        warnings.append(
            "captionTimeline is missing or invalid; record whether captions came from SRT/VTT, alignment JSON, ASR, or source segment durations"
        )
    else:
        method = str(caption_timeline.get("method") or "").strip()
        source_type = str(caption_timeline.get("sourceType") or "").strip()
        source_path = str(caption_timeline.get("sourcePath") or "").strip()
        if not method:
            warnings.append("captionTimeline.method is missing; caption timing source should be explicit")
        if not source_type:
            warnings.append("captionTimeline.sourceType is missing; expected srt/vtt/alignment-json/asr/segment-video-duration")
        if not source_path and source_type not in {"segment-video-duration", "provided"}:
            warnings.append("captionTimeline.sourcePath is missing; record the SRT/VTT/alignment/ASR file used for caption timing")
        normalized_method = method.lower().replace("_", "-")
        if normalized_method in FORBIDDEN_CAPTION_TIMING_METHODS or "proportional" in normalized_method:
            errors.append(
                f"captionTimeline.method={method!r} is forbidden; caption timing must use real SRT/VTT/alignment/ASR timecodes, not scene text distribution"
            )
        source_video_mode = str(data.get("sourceVideoMode") or "").strip()
        if source_video_mode == "precomposed-video" and normalized_method == "source-segment-duration":
            errors.append(
                "precomposed-video cannot use source-segment-duration captions; provide SRT/VTT/alignment/ASR timing"
            )
        if normalized_method == "source-segment-duration" and len(scenes) == 1:
            only_caption = caption_cues[0] if len(caption_cues) == 1 and isinstance(caption_cues[0], dict) else {}
            only_text = str(only_caption.get("text") or "")
            if re.fullmatch(r"Segment\s+1", only_text, flags=re.IGNORECASE):
                errors.append(
                    "single-video placeholder caption 'Segment 1' is not a real timeline; run ASR or provide subtitles before V4 precision editing"
                )

    scene_ids: set[str] = set()
    scene_by_id: dict[str, dict[str, Any]] = {}
    focus_scenes: set[str] = set()
    last_end = -1
    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            errors.append(f"scenes[{idx}] must be an object")
            continue
        scene_id = str(scene.get("id") or "")
        if not scene_id:
            errors.append(f"scenes[{idx}] missing id")
        else:
            scene_ids.add(scene_id)
            scene_by_id[scene_id] = scene
        if scene.get("type") not in ALLOWED_SCENE_TYPES:
            errors.append(f"scenes[{idx}] has invalid type: {scene.get('type')}")
        presenter_layout = scene.get("presenterLayout")
        material_layout = scene.get("materialLayout")
        if presenter_layout == "pip" and material_layout not in {"main", "clean"}:
            warnings.append(
                f"scenes[{idx}] uses presenterLayout=pip without materialLayout=main/clean; "
                "V4 defaults to fullscreen presenter and PiP only for material-main beats"
            )
        if material_layout == "main" and presenter_layout not in {"pip", "none"}:
            warnings.append(
                f"scenes[{idx}] uses materialLayout=main without presenterLayout=pip/none; "
                "check whether proof material is readable"
            )
        if presenter_layout == "pip" and material_layout in {"main", "clean"}:
            focus_scenes.add(scene_id)
        start = frame_value(scene, "startFrame")
        end = frame_value(scene, "endFrame")
        if start is None or end is None or end <= start:
            errors.append(f"scenes[{idx}] must have valid startFrame/endFrame")
        else:
            if last_end > start:
                warnings.append(f"scenes[{idx}] starts before the previous scene ends")
            last_end = max(last_end, end)

    caption_text_by_scene: dict[str, list[str]] = {}
    caption_cue_ids: set[str] = set()
    for idx, cue in enumerate(caption_cues):
        if not isinstance(cue, dict):
            errors.append(f"captionCues[{idx}] must be an object")
            continue
        cue_id = str(cue.get("id") or "").strip()
        if not cue_id:
            errors.append(f"captionCues[{idx}] missing id")
        elif cue_id in caption_cue_ids:
            errors.append(f"captionCues[{idx}] duplicates id: {cue_id}")
        else:
            caption_cue_ids.add(cue_id)
        text = cue.get("text")
        scene_id = str(cue.get("sceneId") or "")
        if not isinstance(text, str) or not text:
            errors.append(f"captionCues[{idx}] missing text")
        else:
            if scene_id:
                caption_text_by_scene.setdefault(scene_id, []).append(text)
            length = visible_len(text)
            if length > CAPTION_ERROR_CHARS:
                errors.append(
                    f"captionCues[{idx}] is too long ({length} visible chars); "
                    f"split captions before rendering"
                )
            elif length > CAPTION_WARN_CHARS:
                warnings.append(
                    f"captionCues[{idx}] is long ({length} visible chars); consider splitting"
                )
        highlights = cue.get("highlightWords", [])
        if not isinstance(highlights, list):
            errors.append(f"captionCues[{idx}].highlightWords must be an array")
        elif len(highlights) > 3:
            errors.append(f"captionCues[{idx}] has more than 3 highlighted terms")
        start = frame_value(cue, "startFrame")
        end = frame_value(cue, "endFrame")
        if start is None or end is None or end <= start:
            errors.append(f"captionCues[{idx}] must have valid startFrame/endFrame")
        if scene_id and scene_id not in scene_ids:
            errors.append(f"captionCues[{idx}] references unknown sceneId: {scene_id}")
        elif scene_id and start is not None and end is not None:
            scene = scene_by_id.get(scene_id)
            if scene:
                scene_start = frame_value(scene, "startFrame")
                scene_end = frame_value(scene, "endFrame")
                if (
                    scene_start is not None
                    and scene_end is not None
                    and (start < scene_start - 2 or end > scene_end + 2)
                ):
                    errors.append(
                        f"captionCues[{idx}] timing falls outside {scene_id}; "
                        "caption timing must stay synchronized with the spoken scene"
                    )

    for scene_id, scene in scene_by_id.items():
        narration = str(scene.get("narrationText") or "").strip()
        if not narration:
            continue
        normalized_narration = normalize_spoken_text(narration)
        if not normalized_narration:
            continue
        normalized_captions = normalize_spoken_text("".join(caption_text_by_scene.get(scene_id, [])))
        if not normalized_captions:
            errors.append(f"{scene_id} has narrationText but no captionCues")
        elif normalized_captions != normalized_narration:
            errors.append(
                f"{scene_id} caption text does not match full narrationText; "
                "captions must use complete transcript/ASR copy, not summaries or omitted text"
            )

    semantic_beat_ids = {
        str(beat.get("id") or "").strip()
        for beat in semantic_beats
        if isinstance(beat, dict) and str(beat.get("id") or "").strip()
    }
    theme_thesis_candidates = 0
    for idx, beat in enumerate(semantic_beats):
        if not isinstance(beat, dict):
            errors.append(f"semanticBeats[{idx}] must be an object")
            continue
        scene_id = str(beat.get("sceneId") or "")
        if scene_id and scene_id not in scene_ids:
            errors.append(f"semanticBeats[{idx}] references unknown sceneId: {scene_id}")
        if not beat.get("semanticIntent"):
            errors.append(f"semanticBeats[{idx}] missing semanticIntent")
        if not beat.get("visualForm"):
            errors.append(f"semanticBeats[{idx}] missing visualForm")
        source_cue_ids = beat.get("sourceCueIds", [])
        if not isinstance(source_cue_ids, list):
            errors.append(f"semanticBeats[{idx}].sourceCueIds must be an array")
        else:
            for cue_id in source_cue_ids:
                cue_ref = str(cue_id or "").strip()
                if cue_ref and cue_ref not in caption_cue_ids:
                    errors.append(
                        f"semanticBeats[{idx}] references unknown caption cue: {cue_ref}"
                    )
        checks = beat.get("requiredChecks")
        if not isinstance(checks, list) or not checks:
            errors.append(f"semanticBeats[{idx}] must define requiredChecks")
        start = frame_value(beat, "startFrame")
        end = frame_value(beat, "endFrame")
        if start is None or end is None or end <= start:
            errors.append(f"semanticBeats[{idx}] must have valid startFrame/endFrame")
        if beat.get("themeThesisCandidate") is True:
            theme_thesis_candidates += 1
            keyword = str(beat.get("suggestedDepthKeyword") or "").strip()
            if not 1 <= len(keyword) <= 6:
                errors.append(f"semanticBeats[{idx}] theme thesis suggestedDepthKeyword must contain 1-6 characters")
            if beat.get("requiresApproval") is not True:
                errors.append(f"semanticBeats[{idx}] theme thesis candidate must set requiresApproval=true")
            scene = scene_by_id.get(scene_id, {})
            if str(scene.get("presenterLayout") or "") not in {"fullscreen", "large"}:
                errors.append(f"semanticBeats[{idx}] theme thesis candidate requires fullscreen/large presenter")

    if theme_thesis_candidates > 1:
        errors.append(f"semanticBeats has {theme_thesis_candidates} theme thesis candidates; allow at most one")

    card_events_by_scene: dict[str, list[dict[str, Any]]] = {}
    independent_icon_flyins: dict[str, int] = {}
    material_events_by_scene: dict[str, int] = {}
    for idx, event in enumerate(visual_events):
        if not isinstance(event, dict):
            errors.append(f"visualEvents[{idx}] must be an object")
            continue
        scene_id = str(event.get("sceneId", ""))
        if scene_id and scene_id not in scene_ids:
            errors.append(f"visualEvents[{idx}] references unknown sceneId: {scene_id}")
        event_type = event.get("type")
        role = str(event.get("semanticRole") or "")
        if event_type not in RENDERABLE_EVENT_TYPES:
            errors.append(f"visualEvents[{idx}] uses unsupported/unrendered type: {event_type!r}")
        if not role:
            warnings.append(f"visualEvents[{idx}] missing semanticRole")
        anchor_cue_id = str(event.get("anchorCueId") or "").strip()
        if anchor_cue_id and anchor_cue_id not in caption_cue_ids:
            errors.append(
                f"visualEvents[{idx}] references unknown anchorCueId: {anchor_cue_id}"
            )
        event_source_cue_ids = event.get("sourceCueIds")
        if event_source_cue_ids is not None:
            if not isinstance(event_source_cue_ids, list):
                errors.append(f"visualEvents[{idx}].sourceCueIds must be an array")
            else:
                for cue_id in event_source_cue_ids:
                    cue_ref = str(cue_id or "").strip()
                    if cue_ref and cue_ref not in caption_cue_ids:
                        errors.append(
                            f"visualEvents[{idx}] references unknown caption cue: {cue_ref}"
                        )
        source_beat_id = str(event.get("sourceBeatId") or "").strip()
        if source_beat_id and source_beat_id not in semantic_beat_ids:
            errors.append(
                f"visualEvents[{idx}] references unknown sourceBeatId: {source_beat_id}"
            )
        if not event.get("motionType"):
            warnings.append(f"visualEvents[{idx}] missing motionType")
        if role == "platform-fanout" and event_type not in {"platformFanout", "transitionPushZoom"}:
            warnings.append(f"visualEvents[{idx}] platform-fanout should use type=platformFanout")
        if role == "automation-handoff" and event_type not in {"automationHandoff", "captionHighlight"}:
            warnings.append(f"visualEvents[{idx}] automation-handoff should use type=automationHandoff")
        if role == "semantic-problem-map" and event_type not in {"semanticProblemMap", "highlightBox"}:
            warnings.append(f"visualEvents[{idx}] semantic-problem-map should use type=semanticProblemMap")
        if event_type == "transitionPushZoom" and role != "platform-fanout":
            errors.append(f"visualEvents[{idx}] transitionPushZoom is a legacy platform-fanout alias and requires semanticRole=platform-fanout")
        if event_type == "highlightBox" and role != "semantic-problem-map":
            errors.append(f"visualEvents[{idx}] highlightBox is a legacy semantic-problem-map alias")
        if event_type == "captionHighlight" and role not in {"automation-handoff", "positive-confirm", "explanation-claim"}:
            errors.append(
                f"visualEvents[{idx}] captionHighlight requires automation-handoff, positive-confirm, "
                "or an audited explanation-claim fallback"
            )
        if event_type == "presenterReposition" and event.get("motionType") != "presenter-impact-punch":
            errors.append(f"visualEvents[{idx}] presenterReposition only supports motionType=presenter-impact-punch")
        if event_type == "depthKeyword":
            text = str(event.get("text") or "").strip()
            if not 1 <= len(text) <= 6:
                errors.append(f"visualEvents[{idx}] depthKeyword text must contain 1-6 characters")
            if event.get("approvalStatus") != "approved":
                errors.append(f"visualEvents[{idx}] depthKeyword requires approvalStatus=approved")
            if not event.get("foregroundAssetPath"):
                errors.append(f"visualEvents[{idx}] depthKeyword requires a transparent foregroundAssetPath")
            scene = scene_by_id.get(scene_id, {})
            if str(scene.get("presenterLayout") or "") not in {"fullscreen", "large"}:
                errors.append(f"visualEvents[{idx}] depthKeyword requires fullscreen/large presenter")
        if event_type == "historicalGreenConclusion" and event.get("presentationVariant") != "manual-approved":
            errors.append(
                f"visualEvents[{idx}] historicalGreenConclusion is manual-only and requires "
                "presentationVariant=manual-approved"
            )
        if event_type == "infoCard":
            card_events_by_scene.setdefault(scene_id, []).append(event)
        if event_type == "materialMain":
            material_events_by_scene[scene_id] = material_events_by_scene.get(scene_id, 0) + 1
        if event.get("motionType") == "icon-fly-in":
            independent_icon_flyins[scene_id] = independent_icon_flyins.get(scene_id, 0) + 1

        scene = scene_by_id.get(scene_id)
        if scene_id in focus_scenes and scene:
            event_start = frame_value(event, "startFrame")
            event_end = frame_value(event, "endFrame")
            scene_start = frame_value(scene, "startFrame")
            scene_end = frame_value(scene, "endFrame")
            if None not in {event_start, event_end, scene_start, scene_end} and overlaps(
                int(event_start),
                int(event_end),
                int(scene_start),
                int(scene_end),
            ):
                allowed = role in FOCUS_ALLOWED_ROLES or event_type in {"materialMain", "materialZoom", "highlightBox", "statusSticker"}
                forbidden = event_type in FOCUS_FORBIDDEN_TYPES or role in FOCUS_FORBIDDEN_ROLES
                if forbidden and not allowed:
                    errors.append(
                        f"visualEvents[{idx}] crowds material focus scene {scene_id}: "
                        f"type={event_type!r}, semanticRole={role!r}; split this HUD/process beat into another scene"
                    )

    for scene_id in focus_scenes:
        if material_events_by_scene.get(scene_id, 0) == 0:
            warnings.append(f"material focus scene {scene_id} has no materialMain event")

    presenter_impacts = sorted(
        (
            event
            for event in visual_events
            if isinstance(event, dict)
            and event.get("type") == "presenterReposition"
            and event.get("motionType") == "presenter-impact-punch"
        ),
        key=lambda event: int(event.get("startFrame", 0) or 0),
    )
    if presenter_impacts:
        fps = int(composition.get("fps") or 25)
        min_duration = max(1, round(18 * fps / 30))
        max_standalone_duration = max(min_duration, round(28 * fps / 30))
        max_synced_duration = round(6 * fps)
        min_gap = round(8 * fps)
        allowed_roles = {
            "result-promise",
            "negative-friction",
            "negative-to-positive",
            "semantic-problem-map",
            "positive-confirm",
            "pain-question",
            "theme-thesis",
        }
        non_sync_types = {"presenterReposition", "cornerChapterLabel", "iconPulse"}
        forbidden_overlap_types = {
            "materialMain",
            "materialZoom",
            "transitionPushZoom",
        }
        for impact in presenter_impacts:
            impact_id = str(impact.get("id") or "?")
            start = int(impact.get("startFrame", 0) or 0)
            end = int(impact.get("endFrame", start) or start)
            duration = end - start
            source_beat_id = str(impact.get("sourceBeatId") or "")
            sync_events = [
                other
                for other in visual_events
                if other is not impact
                and isinstance(other, dict)
                and str(other.get("type") or "") not in non_sync_types
                and str(other.get("sceneId") or "") == str(impact.get("sceneId") or "")
                and str(other.get("sourceBeatId") or "") == source_beat_id
                and int(other.get("startFrame", 0) or 0) == start
                and int(other.get("endFrame", 0) or 0) == end
            ]
            is_lifecycle_synced = bool(source_beat_id and sync_events)
            if duration < min_duration or (
                is_lifecycle_synced and duration > max_synced_duration
            ) or (
                not is_lifecycle_synced and duration > max_standalone_duration
            ):
                errors.append(
                    f"presenter impact {impact_id} lasts {duration}f; standalone requires "
                    f"{min_duration}-{max_standalone_duration}f, while lifecycle sync requires an exact "
                    f"same-scene/sourceBeatId/range semantic companion and at most {max_synced_duration}f"
                )
            if str(impact.get("semanticRole") or "") not in allowed_roles:
                errors.append(
                    f"presenter impact {impact_id} must bind to a strong question/judgement/reversal/warning/result role"
                )
            if not impact.get("sourceBeatId"):
                errors.append(f"presenter impact {impact_id} requires sourceBeatId")
            peak = impact.get("presenterPeakScale", 1.08)
            if not isinstance(peak, (int, float)) or not 1.06 <= float(peak) <= 1.10:
                errors.append(f"presenter impact {impact_id} peak scale must be 1.06-1.10 in portrait")
            scene = scene_by_id.get(str(impact.get("sceneId") or ""), {})
            if str(scene.get("presenterLayout") or "") not in {"fullscreen", "large"}:
                errors.append(f"presenter impact {impact_id} requires fullscreen/large presenter")
            for other in visual_events:
                if other is impact or not isinstance(other, dict):
                    continue
                if str(other.get("type") or "") not in forbidden_overlap_types:
                    continue
                if overlaps(
                    start,
                    end,
                    int(other.get("startFrame", 0) or 0),
                    int(other.get("endFrame", 0) or 0),
                ):
                    errors.append(
                        f"presenter impact {impact_id} overlaps forbidden {other.get('type')} event {other.get('id')}"
                    )
        for previous, current in zip(presenter_impacts, presenter_impacts[1:]):
            gap = int(current.get("startFrame", 0) or 0) - int(previous.get("startFrame", 0) or 0)
            if gap < min_gap:
                errors.append(
                    f"presenter impact starts {previous.get('id')} and {current.get('id')} are only {gap}f apart; require {min_gap}f"
                )
        for index, current in enumerate(presenter_impacts):
            window_start = int(current.get("startFrame", 0) or 0) - 60 * fps
            rolling_count = sum(
                1
                for prior in presenter_impacts[: index + 1]
                if int(prior.get("startFrame", 0) or 0) >= window_start
            )
            if rolling_count > 3:
                errors.append("presenter-impact-punch frequency exceeds three events in a rolling minute")
                break

    for scene_id, card_events in card_events_by_scene.items():
        max_simultaneous = 0
        for card in card_events:
            card_start = frame_value(card, "startFrame")
            card_end = frame_value(card, "endFrame")
            if card_start is None or card_end is None:
                continue
            simultaneous = 0
            for other in card_events:
                other_start = frame_value(other, "startFrame")
                other_end = frame_value(other, "endFrame")
                if other_start is None or other_end is None:
                    continue
                if overlaps(int(card_start), int(card_end), int(other_start), int(other_end)):
                    simultaneous += 1
            max_simultaneous = max(max_simultaneous, simultaneous)
        if max_simultaneous > 3:
            errors.append(f"scene {scene_id} has {max_simultaneous} simultaneous infoCard events; V4 max is 3 same-screen cards")
    for scene_id, count in independent_icon_flyins.items():
        if count > 1:
            warnings.append(f"scene {scene_id} has {count} independent icon fly-ins; V4 allows one per chapter")

    for idx, cue in enumerate(audio_cues):
        if not isinstance(cue, dict):
            errors.append(f"audioCues[{idx}] must be an object")
            continue
        cue_type = cue.get("type")
        if cue_type not in ALLOWED_AUDIO_TYPES:
            errors.append(f"audioCues[{idx}] has invalid type: {cue_type}")
        start = frame_value(cue, "startFrame")
        end = frame_value(cue, "endFrame")
        duration = frame_value(cue, "durationFrames")
        if cue_type in {"sfx", "bgm"} and start is None:
            errors.append(f"audioCues[{idx}] {cue_type} cue must have startFrame")
        if end is not None and start is not None and end <= start:
            errors.append(f"audioCues[{idx}] endFrame must be greater than startFrame")
        if duration is not None and duration <= 0:
            errors.append(f"audioCues[{idx}] durationFrames must be positive when provided")
        volume = cue.get("volumeDb")
        if volume is not None and not isinstance(volume, (int, float)):
            errors.append(f"audioCues[{idx}].volumeDb must be numeric when provided")
        if cue_type == "sfx" and not cue.get("sfxIntent"):
            errors.append(f"audioCues[{idx}] SFX cue missing sfxIntent")
        if cue_type == "sfx" and not cue.get("path") and not cue.get("sfxId") and cue.get("status") not in PENDING_AUDIO_STATUSES:
            warnings.append(
                f"audioCues[{idx}] SFX has no path/sfxId; set status=pending-selection or choose from manifest"
            )
        if cue_type == "bgm" and cue.get("enabled") and not cue.get("path"):
            warnings.append(f"audioCues[{idx}] BGM enabled but path is empty")
        if cue_type == "bgm" and not cue.get("path") and cue.get("status") not in PENDING_AUDIO_STATUSES:
            warnings.append(f"audioCues[{idx}] BGM has no path; set status=pending-generation/disabled or provide bgmPath")

    reasons = [q.get("reason") for q in qa_frames if isinstance(q, dict)]
    qa_required = ["Hook", "presenter", "CTA"]
    has_material = any(
        isinstance(scene, dict) and scene.get("materialLayout") in {"main", "clean"}
        for scene in scenes
    ) or any(
        isinstance(event, dict) and event.get("type") in {"materialMain", "materialZoom"}
        for event in visual_events
    )
    if has_material:
        qa_required.append("material")
    for required in qa_required:
        if not any(required.lower() in str(reason).lower() for reason in reasons):
            warnings.append(f"qaFrames should include a {required} sample when applicable")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("visual_script", type=Path)
    args = parser.parse_args()

    errors, warnings = validate(args.visual_script)
    for warning in warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("visual_script.json passed V4 validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
