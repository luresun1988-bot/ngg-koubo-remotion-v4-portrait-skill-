---
name: ngg-koubo-remotion-v4-portrait
description: "Full-process 9:16 Chinese vertical talking-head Remotion editing skill. Use when Codex needs to plan, build, render, or QA high-energy koubo/digital-human videos with semantic research, transcript/timecode gating, visual_script.json, V4 Remotion template implementation, bold kinetic titles, captions, cards, icons, presenter repositioning, proof materials, SFX/BGM planning, thumbnails, and layered QA."
---

# NGG Koubo Remotion V4 Portrait

Produce or modify 9:16 Chinese vertical talking-head Remotion edits in the NGG V4 high-energy packaging system. Treat V4 Portrait as a production workflow, data contract, format-specific template, and QA gate—not only a visual style.

## Required Workflow

1. Inspect the request, project root, source media, script, timeline files, proof assets, posters, audio, and existing Remotion work. Preserve existing artifacts unless replacement is explicitly requested.
2. Read `references/workflow.md`, then load or create `project_config.json`. Initialize new work from the project root with `scripts/init_v4_project.py`; initialization must never guess presenter roles, overwrite an unmarked directory, or create nested `06_remotion/06_remotion`.
3. Declare `sourceVideoMode` as `raw-presenter`, `segmented-presenter`, or `precomposed-video`. Resolve presenter sources before timeline work, probe the primary presenter, use its nominal FPS as composition FPS, normalize fractional/VFR or mixed inputs to that fixed timebase, and use 25 fps only when probing is unavailable. Never infer precomposition merely from subtitles or ASR.
4. Require authoritative timecodes before frame-specific planning. Prefer SRT/VTT/alignment JSON/ASR word or sentence timestamps; segmented clip durations are valid only for real multi-clip presenter inputs. A single finished MP4 plus script is not a precision timeline—run ASR or stop.
5. Do light semantic research unless the user disables it. Research informs meaning and metaphors; online media is not final material without source and rights review.
6. Treat cover/poster work as conditional scope. Only when the user requests a cover, poster, thumbnail, or publish package, derive one short `posterTopicKeyword` and call `ngg-koubo-poster` if designed assets are missing. Keep covers outside the video body unless the narration discusses them or the user requests them on screen.
7. Build `06_remotion/visual_script.json` in this order:
   - create real timecoded `captionCues`;
   - run `scripts/split_caption_cues.py` before any beat/event references exist;
   - run `scripts/semantic_router.py` to create `semanticBeats`;
   - run `scripts/visual_event_builder.py` to create `visualEvents` and suggested semantic SFX;
   - run `scripts/validate_visual_script.py` immediately and stop on errors.
8. Read `references/semantic-routing.md` before generating or reviewing beats/events and `references/visual-script-schema.md` before changing the JSON contract. Preserve cue/beat references, scene ownership, half-open frame ranges, and source-authored provenance.
9. Run `scripts/qa_lint_visual_script.py --remotion-root 06_remotion` before rendering. Fix every hard failure; record any accepted limitation in the QA report.
10. Copy `assets/remotion-template/` for new portrait projects unless a V4 Portrait template already exists. Do not migrate finished legacy projects unless the user asks.
11. Implement motion only with deterministic Remotion frame APIs (`useCurrentFrame`, `interpolate`, `spring`, `Sequence`, `TransitionSeries`). No CSS animation, timers, or runtime randomness.
12. Read `references/visual-system.md` and `references/motion-system.md` before component or motion work. Use `assets/component-gallery/` for nontrivial style changes and run motion previews for presenter punches, depth typography, and fullscreen/PiP boundaries.
13. Read `references/audio-policy.md` before activating SFX/BGM or changing presenter audio. Suggested cues do not render until explicitly activated with an existing file.
14. Read `references/qa-checklist.md` and `references/forbidden-rules.md`, then render serial Chinese-font acceptance stills/contact sheets and required motion previews before the final MP4.
15. Prefer `scripts/render_final_and_qa.ps1` for delivery. Require native command success, matching FPS/resolution/frame count, full audio coverage, H.264/AAC, yuv420p/tv/BT.709 metadata, and a successful full-file decode.

## Non-Negotiable Contracts

### Shared Core and Format Isolation

- Keep format-agnostic semantic guards, semantic contract cases, and shared QA behavior synchronized with landscape V4.
- Keep portrait layout, canvas, safe areas, presenter geometry, motion values, and Remotion template changes inside the portrait Skill unless the user explicitly approves a corresponding landscape change.
- Refresh mirrored portrait runtime files with `scripts/sync_template_mirrors.py --write` after changing a mirrored source and require the dry check to pass before committing.
- Upgrade an existing `06_remotion` only with `scripts/upgrade_existing_project.py --remotion-root <path> --write`; preserve its automatic backups and project-specific data, source, packages, and assets.

### Timeline and Presenter Continuity

- Use the probed primary-presenter FPS; 25 fps is only the missing-probe fallback. Convert all seconds onto the composition timebase and never reuse source-frame counts when FPS differs.
- Make scenes one contiguous half-open partition. Caption gaps must not create presenter gaps.
- Mount the primary presenter once from frame 0 through the end. Scene changes affect layout and overlays, not playback or embedded audio.
- For segmented presenters, normalize one frame-exact continuous video-only stream plus one 48 kHz stereo PCM WAV. Mount the WAV once and mute presenter-video audio. Never concatenate independent AAC tracks.
- Use `presenterAudio.syncOffsetFrames` only for a measured constant source offset with written evidence; never use it to hide cumulative drift.
- Use `OffthreadVideo` for H.264 presenter and proof-video layers. Preserve UTF-8 Chinese paths and store generated paths relative to the final Remotion root.

### Semantic Integrity

- Route every important event from spoken meaning. `semanticRole` chooses the visual grammar; `type` is only the component family.
- Apply shared completion, CTA, future/topic, handoff, ordered-workflow, numeric, proof, and explanation guards before portrait component selection. `交给…之前` remains a prerequisite workflow, while explicit `首先/然后/最后` source cues form one ordered source-bound workflow before portrait component selection.
- Treat completion and result evaluation as polarity-sensitive. Green `positive-confirm` and confirm SFX require either asserted completion or an asserted positive result such as `结果正确`, `验证通过`, `执行成功`, `没有错误`, or `失败项为0`; asserted failure/error routes negative. Questions, possibility, prevention, negation, future/conditional, partial, unresolved, noun/meta, and later-failed wording must not confirm.
- Keep numeric facts primary even when incomplete. Preserve Arabic and Chinese quantities such as `10张` and `十张`, suffixes, and source entities; add the incomplete modifier/check and render a sourced unfinished state without green styling.
- Preserve CTA action channel and keyword through matching `ctaProvenance`. Do not invent actions, channels, keywords, proof, positive resolutions, numbers, brands, platforms, states, or results.
- Keep automation-handoff steps ordered and source-bound. Numeric, process, enumeration, negative, proof, transformation, platform, and CTA beats must use their matching visual grammar.
- Structured components for workflow/enumeration, manual fields, capabilities, scenes, platforms, asset ratios, and automation must build every visible item from caption cues owned by the current source beat. Each `internalSteps[]` item carries a short exact-source `label`, exact-source `text`, and non-empty `sourceCueIds`; require at least two items except automation handoff, which may use one. If the source does not contain enough distinct items, emit an audited `captionHighlight` with `semanticFallbackFrom` and a specific `fallbackReason` instead of inventing rows, brands, platforms, fields, scenes, or ratios.
- A `transformationStack` requires a sourced A→B relation, one or two sourced drivers, and an explicit sourced result. Every step must carry `text` plus `sourceCueIds` owned by the source beat, and the event must record their ordered union in `transformationSourceCueIds`. If any layer is missing, use an explicit `captionHighlight` semantic fallback with a reason; never invent a result such as `目标状态达成` or borrow an uncited nearby cue.
- Treat real CTA, strong proof, and numeric-metric cues as hard semantic boundaries; progressive workflows must not absorb or bridge across them.
- For portrait structured explanations, use the approved source-bound presentation set: exactly two input assets -> `pairedInputRail`; exactly three equal factors -> `factorTrinity`; an asserted driver-to-target relation -> `causalDriver`; an explicitly decisive factor -> `factorPriority`; exactly three ordered workflow steps -> `compactPipeline`; an asserted capability boundary -> `limitationWarning`; and an explicit prerequisite -> `priorityConclusion`.
- The prerequisite route uses blue/gold `priorityConclusion` automatically. The green historical alternative `historicalGreenConclusion` is manual-only and requires `presentationVariant: "manual-approved"`; never infer it automatically because green remains reserved for asserted completion, success, or validation.
- Every item shown by these structured portrait components must be sourced from the owning caption beat through exact `text` and non-empty `sourceCueIds`. Missing cardinality, relation, polarity, or prerequisite evidence must use the registered audited fallback rather than fabricated labels.

### Portrait Visual and Material Integrity

- Default to fullscreen presenter. Use PiP only when readable proof material becomes the main screen; use a vertical 9:16 rounded presenter PiP by default and return to fullscreen after proof ends.
- Protect the center face/eye/mouth band, hand gestures, captions, and material readability. Use compact top-safe or side-rail HUD forms in fullscreen presenter scenes; reserve large complex panels for proof/material-main/PiP scenes.
- Keep one bottom caption layer. `embedded` renders complete authoritative cue text in one or two all-white lines with adaptive dark backing; `none` preserves the full timecoded caption data but renders no caption layer. Never truncate or fabricate timing.
- Keep source brightness by default. Use semantic colors, uniform dark translucent HUD backing, and neutral shadows; do not use colored glow, directional card gradients, generic edge masks, or more than three simultaneous information cards.
- Keep card/panel forms near or below 35% of main events, avoid three consecutive card/panel families, and use source-bound semantic refreshes rather than slow presenter zoom or component roulette. Clean proof playback is exempt.
- Play readable proof video as video through `materialMain` + `recording-proof` + `OffthreadVideo`; run `scripts/proof_motion_qa.py` before rendering so missing, undecodable, or frozen recording-proof video cannot pass as moving evidence. Suppress ordinary HUD during material focus and retain only sourced proof overlays/labels.

### Theme Thesis, Depth Type, and Presenter Impact

- Bind behind-presenter keyword typography to the first eligible source-bound theme thesis, not mechanically to frame 0. Preserve a proof-first opening and defer the effect until a strong fullscreen/large-presenter question, judgement, contrast, transformation, or result promise states the topic.
- Create only an approval-required theme-thesis candidate automatically. Promote `depthKeyword` only after explicit user approval and approval of a transparent, composition-aligned presenter foreground cutout.
- Use one sourced white keyword of at most six Chinese characters on one line behind the presenter. Do not split it around the head or add semantic colors or a numeric subline.
- Keep the base camera stable. Reserve `presenter-impact-punch` for strong source-bound questions, judgements, reversals, warnings, or asserted results. Prefer lifecycle sync: match one visible semantic companion by scene, `sourceBeatId`, and exact half-open range; push to peak in 4–6 FPS-scaled frames, hold at peak with no rebound, then return during the companion's exit and finish on the same frame. Use the short standalone fallback only when no companion can be synchronized. Keep starts about eight seconds apart, at most three in a rolling minute, and separate from fullscreen/PiP geometry transitions, material focus, CTA, and ordinary explanation.

### Audio and Output

- Keep voice primary. Mount one reusable `V4AudioLayers`; normalized narration comes only from `presenterAudio`, and added audio comes only from active `audioCues`. Never maintain a second hard-coded audio list in a custom composition. Pending, suggested, disabled, muted, or pathless cues remain silent.
- Derive manifest-backed SFX cue length from `durationSec` and the actual composition FPS; never reuse a 25 fps catalog frame count on another timebase.
- Follow the portrait mix values and semantic cue policy in `references/audio-policy.md`; the six manifest-backed mastered SFX default to `-5 dB`, while unregistered or ad hoc SFX stay at or below `-14 dB`. Reduce any cue that masks narration, and do not activate SFX for every visual change.
- Require final output to decode completely with expected video frames and audio, requested codecs, yuv420p/tv/BT.709 metadata, no black gaps, no audio truncation, decoded mix levels below clipping, and an exact-frame contact sheet generated from the final encoded file.

## Reference Routing

- `references/workflow.md`: setup, input gating, conditional poster scope, research, production sequence, outputs.
- `references/semantic-routing.md`: route priority, shared guards, completion/CTA/proof semantics, timing anchors, HUD copy, SFX suggestions.
- `references/visual-script-schema.md`: full JSON shape, ranges, references, foreground contract.
- `references/visual-system.md`: portrait typography, captions, cards, semantic HUD, proof layouts, face-safe areas.
- `references/motion-system.md`: portrait timing, motion presets, progressive components, material and presenter motion.
- `references/audio-policy.md`: presenter continuity, SFX/BGM, mix values, ducking, audio QA.
- `references/qa-checklist.md`: lint, sampling, visual/motion/audio/color acceptance.
- `references/forbidden-rules.md`: known portrait failure patterns that must not recur.

## Default Deliverables

Unless the user requests less, produce `project_config.json`, `06_remotion/visual_script.json`, the portrait Remotion composition, pre-render lint for nontrivial work, serial acceptance stills/contact sheet, motion previews required by the edit, `qa_report.md`, final-media QA reports, and the final 9:16 MP4. Produce a poster manifest only when poster/publish-package work is actually in scope.

## Validation and Forward Testing

Run the maintained local suite before committing any nontrivial revision:

```powershell
python scripts/run_skill_regression.py
```

The default suite includes the 23-case shared semantic contract and 55-case shared guardrail suite, a six-case semantic-text → generated visual-script → real Remotion still regression with controlled warning assertions, a rendered 12-second/25fps fullscreen → proof/PiP → fullscreen → CTA continuity regression, and a six-keyframe component render smoke. The dynamic regression verifies corner-label visibility, caption suppression, proof playback, smooth portrait presenter geometry, a short impact punch, continuous normalized audio, frame count, audio coverage, BT.709 metadata, and full-file decode. Add `--audit` after dependency changes and `--gallery` after component style/motion changes. Run `scripts/render_motion_previews.ps1` when motion timing, presenter geometry, or lip sync needs review.

Forward-test substantial workflow changes on a realistic request equivalent to: use V4 Portrait to cut a 9:16 Chinese talking-head video from a source video, script, screenshots, and no prebuilt timeline. Confirm that the agent gates on real timecodes, keeps poster generation conditional, produces config/visual-script/Remotion/QA plans before rendering, preserves presenter continuity, protects the portrait face band, and does not fabricate semantic claims or proof.

When a local historical-project manifest is available, add `--real-corpus-manifest <path>` to the unified regression command. Gate cases must preserve declared format/FPS/duration/media contracts; audit cases expose legacy validator/lint debt without rewriting the original project.
