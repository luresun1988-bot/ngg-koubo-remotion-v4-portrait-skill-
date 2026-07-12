# visual_script.json Schema Guide

Use this guide to create `06_remotion/visual_script.json`.

The schema is intentionally practical rather than exhaustive. Add fields only when they help implementation or QA. After creating the file, run `scripts/validate_visual_script.py` before generating Remotion TypeScript data.

## Required Top-Level Shape

```json
{
  "schemaVersion": "ngg-koubo-remotion-v4-portrait",
  "projectConfigPath": "../project_config.json",
  "sourceVideoMode": "raw-presenter",
  "captionRenderMode": "embedded",
  "packagingDensity": "dense",
  "composition": {
    "format": "9:16",
    "width": 1080,
    "height": 1920,
    "fps": 25,
    "durationFrames": 0
  },
  "captionTimeline": {
    "sourceType": "asr",
    "sourcePath": "qa/asr/asr_segments.json",
    "method": "sentence-timecodes",
    "generatedBy": "faster-whisper"
  },
  "researchNotes": [],
  "media": [],
  "scenes": [],
  "captionCues": [],
  "semanticBeats": [],
  "visualEvents": [],
  "audioCues": [],
  "qaFrames": []
}
```

## Text Safety

- Write JSON as UTF-8.
- Do not write hand-authored Chinese through PowerShell here-strings.
- Prefer reading Chinese from existing UTF-8 transcript files.
- For hand-authored Chinese labels, generate JSON through Python/Node with explicit UTF-8 or use JSON Unicode escapes.
- Visible copy must not contain question-mark placeholders, Unicode replacement characters, or mojibake caused by encoding mismatch.
- If corruption appears, regenerate `visual_script.json`; do not fix it later in QA.

## researchNotes

Record semantic research, not random browsing.

```json
{
  "id": "research-001",
  "topic": "viewer pain point",
  "source": "local brief or query",
  "summary": "The viewer cares whether repeated publishing work can be automated.",
  "visualUse": "Use contrast, platform fan-out, and automation handoff effects."
}
```

## media

Record all source assets used or considered.

```json
{
  "id": "talking-head-main",
  "type": "video",
  "path": "input/main.mp4",
  "role": "presenter",
  "durationSec": 0,
  "hasAudio": true
}
```

Types may include `video`, `audio`, `image`, `poster`, `platform-cover`, `screenshot`, `recording`, `logo`, `caption`, `transcript`, and `bgm`.

For publishing covers, prefer standalone designed posters:

```json
{
  "id": "poster-3x4",
  "type": "poster",
  "path": "input/assets/posters/poster_3x4.png",
  "role": "platform-cover",
  "aspectRatio": "3:4"
}
```

Use extracted video frame covers only if the project explicitly requests frame-based covers or no designed poster exists.
If `input/assets/posters/poster_*.png` files are missing, generate or copy them from `<projectRoot>/publish_package_skill_demo/.publish_assets/posters/final/` before rendering.

Do not add poster media to `visual_script.json` just because poster assets exist in the publish package. Add poster media only when the video body needs to show covers/posters on screen.

## scenes

Scene types:

- `Hook`
- `Explanation`
- `Proof`
- `Process`
- `Contrast`
- `CleanMaterial`
- `CTA`

```json
{
  "id": "scene-001",
  "type": "Hook",
  "segmentId": "001",
  "startFrame": 0,
  "endFrame": 125,
  "semanticRole": "pain-question",
  "presenterLayout": "large",
  "materialLayout": "none",
  "intent": "Open with the viewer pain.",
  "sourceVideo": "input/main.mp4",
  "narrationText": "Load this text from the UTF-8 transcript."
}
```

Presenter layout guidance:

- Use `large` for default fullscreen digital-human scenes.
- Use `pip` only when `materialLayout` is `main` or `clean` and the material is the primary screen.
- Use `side` sparingly; prefer fullscreen presenter plus side HUD overlays for the `dark-fullscreen-semantic-hud` branch.
- When `presenterLayout` is `pip` and `materialLayout` is `main` or `clean`, treat the scene as material focus mode. Avoid unrelated `infoCard`, `platform-fanout`, `automation-handoff`, `semantic-problem-map`, and generic `kineticTitle` events in that same frame range.

## captionCues

Record the timing source before the cues:

```json
{
  "captionTimeline": {
    "sourceType": "srt | vtt | alignment-json | asr | segment-video-duration",
    "sourcePath": "05_timing/captions.srt",
    "method": "sentence-timecodes | word-timecodes | source-segment-duration",
    "generatedBy": "faster-whisper | provided | project-alignment",
    "notes": "Optional timing notes."
  }
}
```

Rules:

- `composition.fps` defaults to the primary presenter's probed nominal FPS. Use 25 only when probing is unavailable; an explicit override must be documented in `project_config.json.frameRate.selectionSource`.
- Frame ranges are project-timebase values. Convert source timestamps through seconds before quantizing to `composition.fps`; never copy frame numbers from a different-FPS timeline.
- `captionTimeline` must describe where caption timing came from.
- `sourceVideoMode` records whether the source is raw presenter footage, segmented presenter clips, or an already precomposed video.
- `captionRenderMode` is `embedded` or `none`. `none` disables only the rendered caption layer; `captionCues` and `captionTimeline` remain mandatory and authoritative.
- `presenterAudio.mode` is `embedded`, `normalized-wav`, or `none`. `normalized-wav` requires `path`, `sampleRate=48000`, `normalizationReportPath`, and optional measured `syncOffsetFrames` with `syncEvidence` when non-zero. Segmented presenter output uses a video-only MP4 and mounts the WAV once.
- A presenter camera punch uses `type=presenterReposition`, `motionType=presenter-impact-punch`, a strong `semanticRole`, `sourceBeatId`, and optional `presenterPeakScale` / `presenterSettleScale`. Scale its half-open range from composition FPS: 18–28 frames at 30 fps or about 15–23 at 25 fps, peak scale 1.06–1.10, settle scale 1.03–1.05, at least about eight seconds from the next punch, and no more than three times in a rolling minute.
- `packagingDensity=light` is the default for `precomposed-video`, because the source may already contain subtitles, PiP, screen demos, or HUD overlays.
- Forbidden methods include `proportional-scene-split`, `scene-proportional`, `estimated`, and `character-ratio-scene-fill`.
- When a finished source video has no SRT/VTT/alignment, run ASR and use ASR cue start/end times.
- Scene boundaries should align to real speech breakpoints where possible. Do not split one spoken sentence at a scene boundary into tiny fragments just to satisfy a visual scene cut.

```json
{
  "id": "cap-001",
  "sceneId": "scene-001",
  "startFrame": 0,
  "endFrame": 70,
  "text": "Load this text from the UTF-8 transcript.",
  "highlightWords": ["keyword"]
}
```

Rules:

- One caption layer only.
- Caption text must come from the transcript/ASR word or sentence timeline. Do not replace it with a short summary, topic label, or HUD phrase.
- Caption cue start/end frames must come from the transcript/ASR/alignment timeline. Do not distribute a scene's full text across its duration by character count.
- `highlightWords` may remain in the cue for semantic analysis, but bottom captions render all text in white. Do not use caption keyword coloring; semantic colors belong to HUD, icons, charts, and proof highlights.
- Timing must come from transcript/timecode data, not guesses.
- If a scene has `narrationText`, all caption cues with the same `sceneId` must concatenate back to that full spoken text after punctuation/space normalization. Splitting a long line is allowed; deleting words is not.
- Keep cues short enough for the bottom strip. Run `scripts/split_caption_cues.py` before data generation when a cue exceeds the V4 caption limit.
- The validator warns above 32 visible characters and fails above 48 visible characters.

## semanticBeats

`semanticBeats` is the routing layer between transcript captions and visual HUD events. Build it from real `captionCues` before generating or rebuilding `visualEvents`.

```json
{
  "id": "beat-001",
  "sceneId": "scene-001",
  "startFrame": 0,
  "endFrame": 130,
  "beatGroupId": "scene-001-01",
  "text": "还在手动做主图？这一步，该自动化了",
  "semanticIntent": "negative-to-positive",
  "visualForm": "red-warning-to-green-confirm",
  "keywords": ["手动", "自动化"],
  "requiredChecks": ["negative-red-treatment", "positive-confirm-treatment"]
}
```

Required fields:

- `id`: stable beat id.
- `sceneId`: valid scene id.
- `startFrame` / `endFrame`: real timing inherited from caption cues.
- `beatGroupId`: group id used for icon uniqueness, card ratio checks, and staged internal motion.
- `text`: original spoken text or a direct concatenation of caption cue text.
- `semanticIntent`: the primary meaning class, such as `result-promise`, `negative-friction`, `negative-to-positive`, `numeric-metric`, `workflow-fields`, `manual-field`, `capability-share`, `scene-lock`, `transformation-stack`, `asset-variants`, `platform-fanout`, `proof-material`, `positive-confirm`, `topic-intro`, `explanation-claim`, or `cta-resolve`.
- `visualForm`: the required visual grammar, such as `redWarningCard`, `dataPunch`, `flowPath`, `ratioGallery`, `platformFanout`, or `materialMain`. Low-confidence ordinary explanations may use `sourceBoundSticker` for a short sourced label or `intentionalCleanHold` for an audited no-main-HUD decision.
- `requiredChecks`: QA obligations that must be satisfied by the generated visual event.
- `routingDecision`: optional builder audit reason such as `short-claim-source-sticker`, `lower-priority-claim-in-same-scene`, `scene-tail-after-specific-event`, or `claim-strip-run-limit`.
- `semanticModifiers`: optional compound meanings such as `numeric`, `completed`, `automated`, `negative`, or `proof-bound`.
- `entities`: source-bound numbers, products, platforms, brands, assets, or topic nouns used to populate components.
- `themeThesisCandidate`, `suggestedDepthKeyword`, and `requiresApproval`: optional proposal metadata. These fields never create a behind-presenter effect without approval.

Rules:

- `semanticBeats` must be generated from transcript/caption semantics, not from a preferred component list.
- A beat may cover multiple short caption cues when they form one spoken idea.
- `visualEvents[].sourceBeatId` must point back to the source beat.
- If the builder cannot fulfill a beat, it must use the closest allowed form and QA must warn or fail. Do not silently fall back to `infoCard`.
- `cornerChapterLabel` may be added for scene context, but it does not satisfy a semantic beat by itself.

## visualEvents

```json
{
  "id": "ve-001",
  "sceneId": "scene-001",
  "type": "kineticTitle",
  "startFrame": 0,
  "endFrame": 80,
  "text": "Use UTF-8 or Unicode escapes for Chinese labels.",
  "emphasisWords": ["keyword"],
  "semanticRole": "pain-question",
  "motionType": "word-pop",
  "style": "dark-fullscreen-semantic-hud",
  "safeArea": "avoid-face-caption"
}
```

Common event types:

- `kineticTitle`
- `captionHighlight`
- `cornerChapterLabel`
- `infoCard`
- `statusSticker`
- `iconPulse`
- `materialMain`
- `materialZoom`
- `highlightBox`
- `presenterReposition`
- `transitionPushZoom`
- `ctaTitle`
- `bigJudgement`
- `dataPunch`
- `quoteSource`
- `flowPath`
- `statusStack`
- `platformFanout`
- `evidenceWindow`
- `ctaRecommend`
- `capabilityShare`
- `sceneLockGrid`
- `transformationStack`
- `semanticProblemMap`
- `automationHandoff`
- `topicKeyword`
- `claimStrip`
- `ratioGallery`
- `depthKeyword`

Each significant event should declare semantic role and motion type.

Keyword emphasis:

- Use `emphasisWords` for 1-3 HUD words that should receive a secondary enlarge/rebound after the main entrance.
- `emphasisWords` is for HUD/big-title emphasis. Bottom captions may carry `highlightWords` metadata, but the rendered caption text stays all white and should not scale, pulse, or color individual words.
- If omitted, the template may use a short `subtext` as a conservative emphasis target for `kineticTitle`.

Icon and grouped-card fields:

- `iconName` is required for small information cards, process nodes, status nodes, platform nodes, and field rows. Use a `lucide-react` icon name from the V4 semantic icon map.
- `beatGroupId` groups related small cards or nodes for linting and animation. Icons must not repeat within the same `beatGroupId`.
- `internalSteps` is for one longer component with internal item-by-item animation. Each internal step that renders as a small card/node should include its own `iconName`.
- Do not use `Zap` or another generic icon as a universal fallback. If a script cannot infer a good icon, pick the nearest semantic alternative.

Numeric fulfillment fields:

- Use `type: "dataPunch"` or `type: "metricSpotlight"` for clear numeric metrics such as `+30%`, `3倍`, `885万`, `0.04%`, growth, conversion rate, scale, or ratio.
- Set `numericValue`, `numericPrefix`, and `numericSuffix` when possible. Example: `numericValue: 30`, `numericPrefix: "+"`, `numericSuffix: "%"`. Preserve source suffixes such as `K/k`; normalize lowercase `k/m/g` to uppercase for display rather than dropping the suffix.
- The template animates the value from zero/baseline to `numericValue`; do not encode numeric metrics as a plain `infoCard`.

Process/enumeration fulfillment fields:

- Use `type: "flowPath"` or `type: "statusStack"` for first/second/third, numbered lists, steps, stages, and workflows.
- Put rows/nodes in `internalSteps`; each step needs `label` and `iconName`.
- Do not collapse a process or enumeration into one ordinary `infoCard`.

Negative/friction fulfillment fields:

- Use `semanticRole: "negative-friction"` when the visible phrase contains "还在手动", "手动", "麻烦", "别再", "不是", "低效", "重复", "卡住", or "风险" and the beat is framed as a wrong path or objection.
- Recommended types are `semanticProblemMap` for a red contrast block or `statusSticker` for a compact red warning sticker. `highlightBox` remains a legacy alias only.
- Recommended `motionType` is `red-warning-pop-strike`.
- The positive resolution should be a following internal step or subsequent event, not the only visible treatment.

Layered reference-style HUD fields:

- Use `type: "capabilityShare"` when the transcript compares capability, share, ranking, model/company positions, global/local strength, or "who leads". Use `internalSteps` for the object/logo/icon tiles and bar rows. Each step needs `label`, `iconName`, and preferably a percent/status such as `42%`.
- Use `type: "sceneLockGrid"` when the transcript lists practical scenarios, industries, local adoption categories, or "where this is used". Use `internalSteps` for the scenario tiles; each tile needs a distinct `iconName`.
- Use `type: "transformationStack"` when the transcript expresses "from A to B", individual-to-team, moat/leverage, driver-to-result, or productivity shifts. Use `internalSteps` in this order: source state, target state, one or two driver chips, result metric.
- These components are not one-shot panels. Their internal sections must appear in semantic phases: header/title, then top object/scenario tiles, then data rows/bar growth or remaining tiles.
- `internalSteps` must contain only source-bound content. Do not use gallery defaults as project facts when entities, percentages, platforms, or transformation states were not spoken or provided.

Manual depth typography fields:

- Use `type: "depthKeyword"` only after explicit approval.
- `text` is one white keyword line of 1-6 characters.
- Set `approvalStatus: "approved"` and provide `foregroundAssetPath` to a transparent, composition-aligned presenter cutout image/video.
- If the cutout is missing, use `topicKeyword` or `claimStrip`; do not pretend ordinary foreground text is behind the presenter.

Main HUD lane scheduling:

- Treat side/center/proof packaging as main HUD events unless they are `cornerChapterLabel`, bottom captions, `statusSticker` corner markers, or presenter reposition metadata.
- Assign each main HUD to a lane: `left`, `right`, `center`, or `proof`. The lane usually comes from `safeArea`, otherwise from semantic defaults such as Hook/contrast on the left, platform/process on the right, CTA centered, and material proof in `proof`.
- Same-lane main HUD events must not overlap. Prefer about 6 frames between the previous `endFrame` and next `startFrame`.
- The lane/side decision must be consistent with the rendered component position. HUD edge shades are disabled by default; if `HudEdgeShade` is explicitly re-enabled later, the same lane/side decision must drive both the component and the shade.
- If a component needs multiple beats in the same area, use `internalSteps` or one longer event with internal animation instead of several overlapping events.
- Do not schedule three consecutive main events with the same rendered component family. Adjacent process beats should vary between `flowPath`, `statusStack`, `dataPunch`, `platformFanout`, material proof, stickers, or CTA typography when the semantics allow it.
- Treat sourced `ctaTitle` / `ctaRecommend` as priority events. If an earlier same-lane HUD would make the CTA unreadably short or remove it, trim/drop the earlier HUD and keep the CTA with the lane buffer.

CTA provenance fields:

```json
{
  "type": "ctaTitle",
  "text": "点个关注",
  "subtext": "我们下期见",
  "ctaProvenance": {
    "kind": "action",
    "sourceText": "点个关注，我们下期见",
    "action": "关注"
  }
}
```

- Generated CTA events must include `ctaProvenance.sourceText`.
- Add `action` or `keyword` only when the exact action or keyword appears in `sourceText`.
- Do not manufacture comment, reply, follow, private-message, pickup, or keyword copy from gallery defaults.

Material focus rule:

- In a scene where material is the main screen and the presenter is PiP, use `proof-focus`, `proof-material`, or `material-main` for allowed proof overlays.
- Do not stack process HUD, automation HUD, platform fan-out, and generic title events over the readable material.
- If the spoken meaning needs process/HUD explanation, create a separate fullscreen-presenter process scene before or after the proof scene.
- If a material asset path ends in `.mp4`, `.mov`, `.m4v`, or `.webm`, use `style: "recording-proof"` and render it as video. Do not use a screenshot or first frame unless the user explicitly asks for a still.
- After a video-proof scene, the next non-material scene should return `presenterLayout` to `large` or fullscreen-equivalent.

Recommended semantic roles:

- `result-promise`
- `chapter-label`
- `pain-question`
- `semantic-problem-map`
- `manual-field`
- `metric-growth`
- `platform-fanout`
- `automation-handoff`
- `workflow-step`
- `proof-focus`
- `proof-material`
- `material-main`
- `negative-friction`
- `poster-stack-preview`
- `cta-resolve`

The initializer should create first-pass `visualEvents` for these roles from transcript keywords instead of leaving only placeholder Hook/CTA events. Treat those events as editable starter decisions, then refine them manually when the spoken meaning requires a better beat.

Recommended motion types:

- `word-pop`
- `crash-rebound-keyword-pop`
- `keyword-second-pop`
- `contrast-swap-scan`
- `card-stagger-stack`
- `hub-to-platform-flow`
- `field-collapse-to-action`
- `material-push-in`
- `material-zoom-highlight`
- `screen-recording-proof`
- `red-warning-pop-strike`
- `right-poster-stack-pop`
- `hud-slide-fade`
- `count-up-chart`
- `flow-list-stagger`
- `layered-capability-share`
- `scene-grid-stagger`
- `state-driver-result-build`

`contrast-swap-scan` is a legacy motion name. In current V4 it means pain/contrast swap with red rail, keyword emphasis, or state highlight; it must not add a visible scanning sweep.

Material-main style hints:

- `style: "single-proof"` for one image or screenshot proof board.
- `style: "cover-gallery"` with `assetStack` for 2-3 standalone poster or platform-cover exports, only when the narration explicitly discusses covers, thumbnails, posters, publishing assets, or multi-platform cover outputs.
- `style: "recording-proof"` with `motionType: "screen-recording-proof"` for backend screenshots or screen recording proof.
- `style: "poster-stack-preview"` with `motionType: "right-poster-stack-pop"` for opening thumbnail/poster topic previews where 2-3 poster exports pop in on the right side.
- Poster, cover, and thumbnail assets in `assetStack` must keep their native visible aspect ratios. Do not use fixed placeholder frames that mismatch 16:9, 4:3, or 3:4 source assets.

Video proof example:

```json
{
  "type": "materialMain",
  "semanticRole": "proof-material",
  "motionType": "screen-recording-proof",
  "style": "recording-proof",
  "text": "自动调用主图 Skill",
  "assetPath": "input/materials/demo_recording_25fps.mp4"
}
```

Opening poster stack example for a thumbnail/poster-focused Hook:

```json
{
  "type": "materialMain",
  "semanticRole": "poster-stack-preview",
  "motionType": "right-poster-stack-pop",
  "style": "poster-stack-preview",
  "text": "三尺寸主图",
  "assetStack": [
    "input/posters/poster_3x4.png",
    "input/posters/poster_4x3.png",
    "input/posters/poster_16x9.png"
  ],
  "safeArea": "right avoid-face-caption"
}
```

Poster gallery example, only for a spoken poster/publishing-assets proof beat:

```json
{
  "type": "materialMain",
  "semanticRole": "proof-material",
  "motionType": "material-zoom-highlight",
  "style": "cover-gallery",
  "text": "Multi-size poster set",
  "assetStack": [
    "input/assets/posters/poster_3x4.png",
    "input/assets/posters/poster_4x3.png",
    "input/assets/posters/poster_16x9.png"
  ]
}
```

Do not generate this poster gallery merely because `ngg-koubo-poster` produced publish-package posters. The current Poster handoff is one selected creative direction in three sizes; those assets stay in the publish package unless the video script talks about covers/posters.

Semantic routing examples:

```json
{
  "type": "semanticProblemMap",
  "semanticRole": "semantic-problem-map",
  "motionType": "contrast-swap-scan",
  "text": "Not editing speed",
  "subtext": "Publishing workflow is the bottleneck"
}
```

```json
{
  "type": "platformFanout",
  "semanticRole": "platform-fanout",
  "motionType": "hub-to-platform-flow",
  "text": "One source video",
  "subtext": "Multiple publishing tasks"
}
```

```json
{
  "type": "automationHandoff",
  "semanticRole": "automation-handoff",
  "motionType": "field-collapse-to-action",
  "text": "Repeated fields",
  "subtext": "Handoff to system execution"
}
```

```json
{
  "type": "capabilityShare",
  "semanticRole": "capability-share",
  "motionType": "layered-capability-share",
  "status": "GLOBAL · CAPABILITY",
  "text": "国外 · 能力取胜",
  "title": "ENTERPRISE LLM SHARE · 2025",
  "internalSteps": [
    {"label": "Anthropic", "iconName": "BrainCircuit", "status": "42%"},
    {"label": "OpenAI", "iconName": "Bot", "status": "21%"},
    {"label": "Google", "iconName": "Network", "status": "10%"}
  ]
}
```

```json
{
  "type": "sceneLockGrid",
  "semanticRole": "scene-lock",
  "motionType": "scene-grid-stagger",
  "status": "CHINA · SCENE-LOCK",
  "text": "国内 · 场景绑定",
  "internalSteps": [
    {"label": "支付", "iconName": "CreditCard"},
    {"label": "高考", "iconName": "GraduationCap"},
    {"label": "政务", "iconName": "Landmark"}
  ]
}
```

```json
{
  "type": "transformationStack",
  "semanticRole": "transformation-stack",
  "motionType": "state-driver-result-build",
  "text": "一个人变成一个团队",
  "subtext": "AI 提效",
  "internalSteps": [
    {"label": "一个人", "iconName": "User"},
    {"label": "一个团队", "iconName": "Users"},
    {"label": "护城河", "iconName": "ShieldCheck", "status": "MOAT"},
    {"label": "杠杆", "iconName": "TrendingUp", "status": "LEVERAGE"},
    {"label": "55%-81%", "iconName": "FlaskConical", "status": "FASTER"}
  ]
}
```

## audioCues

`audioCues` records added audio layers. Source presenter/video audio usually stays inside `sourceVideo` and does not need a separate cue unless the project needs to document intentional muting or replacement.

```json
{
  "id": "aud-001",
  "type": "sfx",
  "startFrame": 48,
  "durationFrames": 10,
  "sfxIntent": "keyword_pop",
  "sfxId": "ui_tick_01",
  "path": "input/audio/sfx/ui_tick_01.wav",
  "volumeDb": -23,
  "duckUnderVoice": true,
  "fadeInFrames": 1,
  "fadeOutFrames": 3,
  "status": "active"
}
```

Semantic SFX routing may emit review-only cues:

```json
{
  "id": "aud-sfx-beat-003-data_count",
  "type": "sfx",
  "startFrame": 120,
  "durationFrames": 25,
  "sfxIntent": "data_count",
  "sfxId": "data_count_01",
  "path": "input/audio/sfx/data_count_01.wav",
  "volumeDb": -26,
  "duckUnderVoice": true,
  "status": "suggested",
  "sourceBeatId": "beat-003",
  "sourceEventId": "ve-beat-003",
  "suggestedBy": "semantic-sfx-router"
}
```

Allowed audio cue types:

- `sfx`: short semantic sound effect.
- `bgm`: optional music bed.
- `source`: documentation record for source audio handling; it does not render an added `Audio` layer.
- `silence`: documentation record for intentional silence/mute; it does not render an added `Audio` layer.

Rules:

- New V4 projects default to `sfxManifestPath: "input/audio/sfx_manifest.json"`.
- If the default manifest is available and the beat is handoff, Codex/AI takeover, manual-to-automation, or automation-start semantics, use `sfxId: "automation_handoff_01"` with `path: "input/audio/sfx/automation_handoff_01.wav"`.
- If the default manifest is available and the beat is success, completion, correct, or green-confirm semantics, use `sfxId: "confirm_ding_01"` with `path: "input/audio/sfx/confirm_ding_01.wav"`.
- If the default manifest is available and the beat is numeric count-up, percentage growth, 5x, question count, or data punch semantics, use `sfxId: "data_count_01"` with `path: "input/audio/sfx/data_count_01.wav"`.
- If the default manifest is available and the beat is warning, error, risk, blocked, or wrong-path semantics, use `sfxId: "negative_warning_01"` with `path: "input/audio/sfx/negative_warning_01.wav"`.
- If the default manifest is available and the beat is screenshot, recording, evidence window, result board, or Before/Now proof material reveal semantics, use `sfxId: "proof_reveal_01"` with `path: "input/audio/sfx/proof_reveal_01.wav"`.
- If the default manifest is available and the beat is an opening big judgement or keyword scale-up, use `sfxId: "title_impact_whoosh_01"` with `path: "input/audio/sfx/title_impact_whoosh_01.wav"`.
- If no SFX manifest is configured, leave `sfxId` empty, keep `sfxIntent`, and set `status: "pending-selection"`.
- If no BGM has been generated or chosen, set `status: "pending-generation"` or `disabled`; do not invent a path.
- `status: "suggested"` means the router recommends a confirmed library sound, but it must not render until reviewed and changed to `active`.
- The Remotion template renders only `sfx`/`bgm` cues that have a real `path` and are not `suggested`, `pending-selection`, `pending-generation`, `disabled`, or `muted`.
- `path` is relative to Remotion `public/`, for example `input/audio/sfx/ui_tick_01.wav`.
- Default SFX volume is about `-23 dB`; prominent SFX must stay at or below `-14 dB`.
- Default BGM volume is about `-30 dB`; BGM louder than `-20 dB` is a QA failure.
- Use `fadeInFrames` and `fadeOutFrames` for longer BGM or whoosh cues. Short tick/click SFX may use tiny fades or none.
- Active SFX should land near a visual event boundary and should not be added to every minor visual change.

Pending SFX example:

```json
{
  "id": "aud-hook-impact",
  "type": "sfx",
  "startFrame": 36,
  "durationFrames": 12,
  "sfxIntent": "title_impact",
  "sfxId": "",
  "path": "",
  "volumeDb": -23,
  "duckUnderVoice": true,
  "status": "pending-selection"
}
```

BGM placeholder example:

```json
{
  "id": "bgm-001",
  "type": "bgm",
  "startFrame": 0,
  "path": "input/audio/bgm/default_bgm.mp3",
  "volumeDb": -30,
  "duckUnderVoice": true,
  "loop": true,
  "fadeInFrames": 25,
  "fadeOutFrames": 50,
  "status": "active",
  "source": "default V4 BGM library"
}
```

## qaFrames

```json
{
  "frame": 48,
  "reason": "Hook keyword pop, check title readability and caption safety.",
  "checks": ["caption-safe", "face-safe", "title-readable"]
}
```

Include at least:

- One frame per scene.
- Hook keyframes.
- Material main screen frames.
- Presenter reposition frames.
- Transition frames.
- CTA frame.
