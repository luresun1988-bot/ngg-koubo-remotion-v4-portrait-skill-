---
name: ngg-koubo-remotion-v4-portrait
description: "Full-process 9:16 Chinese vertical talking-head Remotion editing skill. Use when Codex needs to plan, build, render, or QA high-energy koubo/digital-human videos with semantic research, transcript/timecode gating, visual_script.json, V4 Remotion template implementation, bold kinetic titles, captions, cards, icons, presenter repositioning, proof materials, SFX/BGM planning, thumbnails, and layered QA."
---

# NGG Koubo Remotion V4 Portrait

Use this skill to produce or modify a 9:16 Chinese vertical talking-head Remotion edit in the NGG V4 high-energy packaging style.

V4 is a production workflow and visual system, not only a style note. Always plan the edit before implementing it.

## Required Workflow

1. Inspect the project request, project root, source media, script, captions, proof assets, screenshots, recordings, logos, and any existing Remotion files.
2. Load or create `project_config.json`. If it is missing, create it from the V4 shape in `references/workflow.md`.
3. Require a timeline before detailed editing. Prefer existing `srt`, `vtt`, JSON transcript, or caption files; otherwise generate ASR timecodes with available local tools before planning frame-specific captions or visual events.
4. Determine one short `posterTopicKeyword` from the video theme before cover/poster generation. This is the only theme text passed to `ngg-koubo-poster` and recorded in poster assets.
5. Do light semantic research for every project unless the user explicitly disables it. Use research to understand the topic and design relevant visual metaphors; do not treat online images or video as usable final assets without source and rights review.
6. If standalone poster assets are missing, call `ngg-koubo-poster` with `posterTopicKeyword` before treating platform covers as available publish-package assets. V4 expects the current Poster workflow to produce one chosen creative direction in three sizes, not three competing final directions.
7. Generate or update `06_remotion/visual_script.json` before writing Remotion code. It must describe scenes, caption cues, semantic beats, visual events, audio cues, QA frames, and research notes. Run `scripts/semantic_router.py` before `scripts/visual_event_builder.py` when creating or rebuilding visual events. Run `scripts/validate_visual_script.py` immediately after generation and stop on any schema or text-corruption error.
8. Run `scripts/split_caption_cues.py` before Remotion data generation when any caption cue is long. The default output uses ASCII JSON escapes to avoid Windows shell/codepage corruption.
9. Run `scripts/qa_lint_visual_script.py` before rendering. Stop on hard failures such as mojibake, overlong captions, invalid PiP usage, material focus conflicts, or missing public assets.
10. Use the unified V4 Portrait Remotion template for new 9:16 projects. Do not migrate old finished projects unless the user explicitly asks.
11. Implement all motion with Remotion frame-driven APIs such as `useCurrentFrame()`, `interpolate()`, `spring()`, `Sequence`, and `TransitionSeries`.
12. Render stills/contact sheets, then run `scripts/render_motion_previews.ps1` for presenter punches, depth typography, and fullscreen/PiP boundaries before the final MP4. Fix hard QA failures before calling the edit complete.

## Reference Routing

- Read `references/workflow.md` for project setup, semantic research, timecode gating, required outputs, and `project_config.json`.
- Read `references/visual-system.md` before designing captions, cards, typography, colors, icons, proof-material layouts, or presenter safe areas.
- Read `references/motion-system.md` before planning Hook titles, card motion, icon motion, material motion, presenter repositioning, and transitions.
- Read `references/semantic-routing.md` before creating, rebuilding, or reviewing semantic beats and generated HUD events.
- Read `references/audio-policy.md` before adding SFX, BGM placeholders, ducking, or audio QA.
- Read `references/visual-script-schema.md` before creating or changing `visual_script.json`.
- Read `references/qa-checklist.md` before rendering previews, contact sheets, or final outputs.
- Read `references/forbidden-rules.md` before finalizing any V4 visual script or template change. It records known bad outputs that must not recur.
- Copy `assets/remotion-template/` for new V4 Remotion projects unless a V4 template already exists in the project.
- Use `assets/component-gallery/` before or after nontrivial component-style changes. It renders fixed keyframes, a contact sheet, and an optional MP4 for V4 component review without depending on a real project.

## Hard Rules

- First version is 9:16 only and must not modify the horizontal V4 skill or template.
- New projects use the unified V4 template.
- Do not start detailed storyboard timing, caption timing, Remotion timeline implementation, or final animation until transcript/timecodes exist.
- Caption timing must come from real transcript timecodes: SRT/VTT, alignment JSON, ASR sentence/word timestamps, or one-source-clip-per-caption segment durations. Do not create complete captions by proportionally distributing text across a scene duration. If only a script exists for a finished talking-head video, run ASR first and record the source in `captionTimeline`.
- A single finished MP4 without SRT/VTT/alignment/ASR is not a valid precision-edit timeline. Initialization must run ASR when available or stop with a clear request for subtitles/timecodes; it must not create a fake `Segment 1` caption timeline.
- V4 scripts must run UTF-8-safe on Windows Chinese paths and filenames. Use explicit UTF-8 reads/writes and preserve Chinese paths through ffmpeg/ffprobe calls.
- Record `sourceVideoMode` as `raw-presenter`, `segmented-presenter`, or `precomposed-video`. For precomposed videos that already contain subtitles, PiP, browser demos, or other overlays, default `packagingDensity` to `light` and avoid re-packaging every line.
- Default presenter layout is fullscreen digital human. Use PiP only when clear proof material, screenshots, screen recordings, or large content assets become the main screen.
- Mount one continuous primary presenter source from composition frame 0 through the end. Scene changes may alter layout, PiP geometry, and overlays, but must not remount, restart, seek, or duplicate the presenter's embedded audio. Use one continuous normalized WAV when presenter audio is external.
- For segmented presenters, normalize every segment to composition FPS and 1080x1920, concatenate one video-only MP4, concatenate one exact 48 kHz stereo PCM WAV, and mount each once. Never stream-copy MP4 containers with independent AAC tracks.
- Every important visual event must be chosen from its spoken meaning first. `semanticRole` routes the effect; `type` only describes the broad event family.
- Visual events must come from `semanticBeats` whenever the project is generated or rebuilt. The required pipeline is: real transcript/timecoded `captionCues` -> `semanticBeats` -> `visualEvents`. Do not jump directly from script text to arbitrary cards.
- Each semantic beat must record `semanticIntent`, `visualForm`, `beatGroupId`, and `requiredChecks`. Each generated visual event must keep `sourceBeatId` so QA can prove the spoken meaning was fulfilled.
- Treat `semanticIntent` as the primary meaning and keep compound facts in `semanticModifiers` / `entities`. A numeric completed automation result remains numeric-first while retaining `completed` and `automated` modifiers.
- Route unknown or low-confidence ordinary explanation to `explanation-claim -> claimStrip`; never manufacture a workflow diagram merely to keep the screen busy. Route episode/topic introductions to `topic-intro -> topicKeyword`.
- Semantic choices must be visually fulfilled, not merely labeled. If transcript meaning is numeric, process, enumeration, negation, pain contrast, platform distribution, proof, or CTA, the rendered HUD must use the matching visual form instead of silently falling back to a generic card.
- Negative or friction words such as "还在手动", "手动", "麻烦", "别再", "不是", "低效", "重复", "卡住", or "风险" must trigger a visible negative treatment: red warning sticker/card, strike/delete line, red rail, or contrast swap before the positive resolution appears. Do not render negative hooks as neutral white/green titles only.
- If the spoken copy only states a negative or denial, such as "不是 XXX" without an explicit "而是 XXX", "该自动化", "交给 Codex", or other positive resolution, render the red warning card only. Do not invent a green confirm card or default line such as "这一步，该自动化了".
- Use the red warning + green confirm paired treatment only when the transcript itself contains both the wrong path and the positive resolution.
- HUD copy is not a subtitle. Warning cards, confirm cards, flow nodes, and status stickers must use short key-message copy, not full spoken sentences. If transcript text is long, extract the key negative/positive phrase and leave the complete wording to the bottom caption.
- HUD text should use white base text plus 1-2 semantic-color emphasis words. Negative cards use red emphasis, confirm/result cards use green emphasis, structural labels use blue, and proof/recommendation uses gold. Do not color the whole sentence when only one phrase is the point.
- Visual-event builders must compress HUD copy before rendering. Warning/contrast cards should keep `text` and `subtext` near 16 Chinese characters each; confirm/handoff cards should keep the main label near 10 characters and the supporting line near 16 characters. If the full spoken sentence is important, it belongs in the bottom caption, not the HUD.
- Generated negative and confirm HUD events must include `emphasisWords` that appear in the visible HUD copy, so the template can render white base text plus red/green key phrases instead of an all-white or all-colored sentence.
- Hook titles must use large stacked title composition, not one long squeezed line near the top edge. For long Chinese hooks, split into 2-3 lines, place the title block in a left/center-left safe area, and use one large semantic keyword in blue/green/red as appropriate.
- The Remotion template must enforce stacked Hook rendering even if `visualEvents[].text` is accidentally provided as one line. A Hook like "Codex 离谱用法" should render as separate title lines, not as a horizontal strip.
- Visual event timing must be anchored to transcript/caption meaning. When a semantic beat spans multiple caption cues, start the HUD near the cue that contains the visible HUD keyword, not automatically at the beginning of the whole beat or scene.
- Numeric metrics such as `+30%`, `3倍`, `885万`, `0.04%`, conversion rate, growth, scale, or ratio must use `dataPunch` / `metricSpotlight` with count-up, progress, bar, or chart motion. Do not render clear numeric metrics as ordinary `infoCard`.
- Preserve the complete source numeric entity, including suffixes such as `K/k`, `%`, `倍`, `万`, and `亿`. A spoken `2K` or `1K` must remain `2K` or `1K` in `entities`, `numericSuffix`, and visible number treatment; never truncate it to `2` or `1`.
- Capability, share, ranking, global/local comparison, or company/model share beats may use `capabilityShare`: a layered HUD with a top semantic label, object/logo/icon tiles, and a lower bar/share panel. These sections must appear by semantic phase, not all at once.
- Scene-binding, local usage scenarios, industry categories, or "where it is used" beats may use `sceneLockGrid`: a section label plus staged scenario tiles. Each tile needs a distinct semantic icon and should appear one by one.
- Transformation, leverage, "from individual to team", moat/driver/result, or capability shift beats may use `transformationStack`: top state transition, middle driver chips, and bottom result metric strip. It must reveal source, arrow, target, drivers, then result in semantic order.
- Workflow, enumeration, or step language such as first/second/third step must use `flowPath` / `statusStack` with numbered rows or nodes and `internalSteps`. Do not render process lists as one ordinary card.
- Completion language such as "流程跑完", "输出完成", "搞定", or "自动跑完" is positive completion unless the transcript explicitly says failure. It should use green/confirm/completion treatment, never a red failure sticker by default.
- Process handoff language such as "把网页丢给 Codex", "Codex 接管", or "交给 Codex" should route to automation handoff or workflow takeover, not a generic process card.
- Future episode language such as "下一期会介绍", "下期将拆解", or "下一条讲" describes planned content. Without an explicit action CTA in the same source text, route it to `explanation-claim`, never `positive-confirm` or `automation-handoff` merely because it contains "自动" or a tool name.
- Generated CTA copy must be source-bound and include `ctaProvenance.sourceText`. Do not invent "评论区", "关键词", "关注", reply actions, or keyword values. If a source CTA would collide with an earlier same-lane HUD, preserve the CTA and trim or drop the earlier HUD while keeping the lane buffer.
- V4 default rhythm is strong-packaging dense motion. Main semantic HUD events should hold about 4.5-6 seconds when the scene allows it, and long talking-head scenes need lightweight semantic visual changes every 2-3 seconds.
- Main HUD events need enough time for entry, internal motion, readable hold, and exit. In QA, any main HUD shorter than about 3.2 seconds is a failure; 3.2-4.5 seconds is only acceptable for simple beats and should be warned.
- Short 3-4 second spoken beats should be merged with neighboring beats when they form one idea. If they cannot be merged, use `timingClass=short-lightweight` and a lightweight HUD; do not force a full long panel into a short sentence.
- If a HUD component has internal steps, the event must not end before all visible steps finish and hold briefly. A partially completed animation disappearing is a hard QA failure, even if the event duration is above the generic minimum.
- Do not leave a dense-mode talking-head scene visually idle. More than 4 seconds without visible change is a QA warning; more than 7 seconds without a semantic visual event is a failure unless the scene is deliberately clean proof-material playback.
- Do not stack main HUD effects on the same side. Main HUD events are assigned to `left`, `right`, `center`, or `proof` lanes; the same lane must not overlap, and handoffs should leave about 10 frames of buffer unless the overlap is an intentional internal step inside one component.
- Layered HUD components such as `capabilityShare`, `sceneLockGrid`, and `transformationStack` must reveal internally in order. Do not reveal top, middle, and bottom sections in the same frame.
- Emphasized HUD keywords may use one secondary enlarge/rebound after the main entrance. Use `emphasisWords` for the 1-3 words that deserve the second pop. Do not apply repeated pulsing or continuous scaling.
- Treat semantic HUD refresh and presenter camera impact as separate systems. Use `presenterReposition` with `motionType=presenter-impact-punch` only for a strong source-bound question, core judgement, reversal, warning, or asserted result. At 30 fps keep it 18–28 frames total with a 4–6-frame push, 4–6-frame rebound, short hold, and 6–10-frame return; scale peaks at 1.06–1.10 in portrait. Keep at most three in a rolling minute and about eight seconds apart. Never use slow symmetric zoom, continuous drift, or camera movement to satisfy dense-motion quotas.
- Use behind-presenter keyword typography on the first source-bound theme thesis, not mechanically at frame 0. A theme thesis is the first strong presenter-led question, core judgement, contrast, or result promise that clearly states the video's subject. If the opening first shows result/proof material, keep the proof clean and defer the effect until the first eligible fullscreen/large presenter thesis. Greetings, setup filler, ordinary steps, and tool names are ineligible.
- Theme-thesis routing may only create an approval-required candidate. Create `depthKeyword` after explicit approval and only with a transparent, composition-aligned presenter foreground cutout; otherwise use ordinary foreground `topicKeyword`/`claimStrip` typography.
- HUD background gradient masks are disabled by default. The template keeps `HudEdgeShade` code as an optional future switch, but new renders should rely on each HUD component's own backing, shadow, and typography unless the user explicitly asks to re-enable edge shades.
- Use Source Han Sans SC / 思源黑体 as the global Chinese render font. Bundle the font with the Remotion template instead of relying on system fallback.
- Keep one bottom caption layer only. Captions sit in the bottom center safe area with an adaptive dark rounded background and complete all-white text and no colored keyword highlights. Captions must show the complete spoken cue text from the transcript/ASR timeline in one or two lines: do not summarize, omit, rewrite as HUD copy, wrap to three lines, truncate with ellipsis, or hide the tail. Shrink the caption font or split the timing cue before removing words.
- Respect `captionRenderMode`. `embedded` renders the single bottom caption layer. `none` keeps the authoritative `captionCues` and `captionTimeline` for semantic routing and QA but renders no bottom captions because the user will add them later. Never delete or fabricate timing data merely because caption rendering is disabled.
- Bottom captions may use at most two lines in portrait. Do not allow three lines; split cues or reduce caption font size before rendering.
- When rebuilding captions after style changes, preserve or regenerate real cue timecodes. It is forbidden to take a scene's full narration and split it by character count across the scene; this causes subtitle drift after scene boundaries and must be treated as a timing failure.
- Protect face, mouth, eyes, and key hand gestures. Protect captions. Protect material readability.
- In 9:16 fullscreen talking-head scenes, face safety is the first layout rule. Do not place large cards, dashboard panels, wide workflow maps, network diagrams, or large CTA blocks over the center face band. Use compact HUD forms by default: right rails, top timelines, small corner labels, numeric punches, field lists, and short caption-safe strips.
- In portrait fullscreen/large presenter scenes, render `semanticProblemMap` as a compact top-safe contrast strip above the face band. Use full-size stacked contrast panels only for proof/material-main/PiP or explicit full-panel review samples.
- Full-size complex panels are allowed only when the scene is proof/material-main/PiP, when the presenter is no longer the primary center subject, or when the user explicitly asks for a full-panel review sample.
- Do not use a default fullscreen black/dark mask over presenter footage. Presenter talking-head scenes keep source-video brightness by default.
- HUB means packaging elements such as big titles, cards, icons, status stickers, flow panels, contrast panels, automation panels, and proof labels. Bottom captions, caption highlights, and the caption rounded strip are not HUB.
- Use `cornerChapterLabel` for lightweight top-left chapter/topic labels. It is a small HUD marker, not a subtitle and not a card; it must not trigger `HudEdgeShade`.
- When HUB elements need contrast, first use the component's own uniform dark backing, neutral shadow, and text hierarchy. Do not add a HUD background gradient mask by default. If edge shade is explicitly re-enabled later, left HUB may only use a left edge shade, right HUB may only use a right edge shade, and centered HUB should still rely on its own backing/shadow instead of a fullscreen shade.
- Clear proof material beats packaging impact. If a screenshot or recording must be read, simplify the motion until it is readable.
- Large video proof material must play as video, not be converted to a static still. Use `materialMain` with `recording-proof` and render mp4/mov/webm assets through `OffthreadVideo`; presenter becomes PiP only while the video proof is the main screen, then returns to fullscreen after the proof beat ends.
- Platform covers are standalone designed poster assets by default, not video frame screenshots. Use extracted video frames only when the project explicitly requests frame-based covers or no designed poster exists.
- Platform covers are publish-package assets by default, not video-body material. Do not put posters into the Remotion timeline unless the narration explicitly discusses covers, thumbnails, posters, platform publishing assets, or the user asks to show them in the video.
- When the project topic is cover/poster/thumbnail generation and 2-3 poster assets are provided, opening Hook may use a right-side poster stack preview: posters pop in one by one with staggered scale/position, while the left side carries the negative hook or result promise. This is allowed because posters are the subject, not decorative filler.
- Poster, cover, and thumbnail assets must be displayed in their native aspect ratio such as 16:9, 4:3, or 3:4. Do not place them inside mismatched fixed-size frames, padded placeholder boxes, or decorative borders that do not match the asset dimensions.
- V4 only passes `posterTopicKeyword` to `ngg-koubo-poster`; do not ask Poster for three concept directions unless the user explicitly requests exploration.
- Use `OffthreadVideo` for rendered talking-head or source-video layers by default. Avoid browser `<Video>` for H.264 source clips with B-frames or sparse keyframes because frame seeking can create visible jitter in Remotion renders.
- Same screen maximum: three information cards. More than three information points must become a staged process, split scene, or material sequence.
- Each card or process node gets at most one primary semantic icon. Do not add icons as decoration.
- Every small information card, process node, status node, platform node, and field row must have a semantic `lucide-react` icon. Bottom captions, corner chapter labels, and big titles do not require icons.
- Icons in the same `beatGroupId`, list, or grouped set of small cards must not repeat. Use semantic alternatives instead of falling back to one generic icon.
- Populate component labels, nodes, brands, platforms, ratios, percentages, states, drivers, and results only from transcript entities, provided assets, or explicit user direction. Gallery/demo defaults are never project facts.
- Cards are not the default visual form. Use large cards only for complex containers such as automation handoff, workflow overview, proof material, and recommendation/CTA. Hook, contrast, numeric judgement, chapter labels, charts, platform lines, and real material should use non-card forms when possible.
- Reference-style list/process beats should use clean vertical or layered layouts: numbered rows, icon tiles, capability/data panels, or source/driver/result stacks. Do not make every explanation look like the same compact card group.
- Across main visual events, card/panel-like forms should stay near or below 35%, and three consecutive main events must not all be cards/panels.
- Do not render three consecutive main events with the same component family, even when the spoken content is all process language. Rotate the visual grammar: flow path, data punch, timeline/filmstrip, status stickers, platform fan-out, proof material, or CTA typography.
- All HUD elements, non-caption text, cards, presenter PiP windows, and material windows need a visible neutral black/white outer ring shadow. Bottom captions are excluded from this ring-shadow rule.
- Do not use colored glow or colored projection shadows. Text, icons, and status fills may keep semantic colors, but shadows must remain neutral black/white.
- Cards, HUD panels, presenter PiP windows, and material windows are borderless by default; use a clean uniform dark translucent backing and neutral black shadow for separation. Do not use white/grey ring outlines unless a specific material proof needs a readable frame.
- Do not put directional gradients on the cards or HUD panels themselves. Cards and panels use stable local backing. The old edge-to-face gradient code remains isolated in `HudEdgeShade`, but it is disabled by default.
- All card-like HUD surfaces use one clean, uniform dark translucent backing, not a left-to-right fade. Default backing is `rgba(5,7,11,0.62)` with a clearly visible neutral black shadow such as `0 30px 72px rgba(0,0,0,0.68), 0 10px 24px rgba(0,0,0,0.54)` and no grey ring outline. This includes info cards, automation handoff panels, platform fan-out panels, contrast/problem panels, status cards, and process nodes.
- Confirmed card style: one dark translucent rectangular group with consistent depth across the whole surface, borderless, no pale grey edge, no second backing layer, no left-to-right or arrow-direction fade. Internal small cards and rows use the same uniform backing logic.
- If `HudEdgeShade` is explicitly re-enabled later, it must extend from the screen edge toward the presenter-safe boundary, stopping before the face, mouth, eyes, and main hand gestures.
- All non-caption text should carry a neutral highlight treatment such as strong black shadow, subtle white edge, local backing, or semantic text color. Bottom captions keep their own caption style.
- Use SFX sparingly and semantically. Voice stays primary. BGM uses the shared V4 default music bed unless a project disables it or selects a project-specific track.
- Confirmed default SFX library currently includes `title_impact_whoosh_01` for opening big-opinion titles, major judgements, and keyword scale-up landings, `confirm_ding_01` for success, completion, correct result, and green-confirm beats, `negative_warning_01` for red warning, error, risk, wrong-path, failed-status, and blocked-workflow beats, `automation_handoff_01` for Codex/AI takeover, manual-to-automation handoff, and automation-start beats, `data_count_01` for numeric count-up/data-punch beats, and `proof_reveal_01` for screenshot/recording/evidence reveal beats.
- `audioCues` are the only source of added SFX/BGM in the Remotion template. A cue with `status=suggested`, `pending-selection`, `pending-generation`, `disabled`, `muted`, or no `path` must not render audio.
- The semantic SFX router may create `status=suggested` audio cues for confirmed library sounds. Treat them as review recommendations only; do not change them to `active` unless the user or project direction confirms the sound.
- SFX must be tied to semantic beats such as big-title impact, keyword second-pop, step completion, proof material appearing, platform fan-out, automation handoff, or CTA resolution. Do not add SFX to every minor animation.
- SFX should normally be short, near the visual event boundary, and below voice. Use `volumeDb` around `-23` by default; prominent SFX must stay at or below `-14 dB`.
- BGM defaults to `input/audio/bgm/default_bgm.mp3` at about `-30 dB`, loops under narration, and must duck under voice. If a project disables default BGM or needs a different track but no file exists, record it as pending or disabled instead of inventing a path.
- Strong flash whites, face-covering transitions, full-screen glitch noise, random animation, CSS transitions, CSS animation, timers, and runtime randomness are forbidden.
- Visible Chinese copy must not contain question-mark placeholders, Unicode replacement characters, or mojibake caused by encoding mismatch. This is an upstream generation failure and must be fixed before Remotion data generation or rendering.
- Visible HUD/UI copy defaults to Simplified Chinese. Do not use English labels for template-generated cards, panels, platform nodes, status chips, process fields, proof labels, or placeholders unless they are real brand names, product names, code/API terms, terminal commands, or text inside an authentic source screenshot.
- Long captions must be split before rendering. Do not rely on visual QA to discover subtitle overflow.

## Default Deliverables

Produce these unless the user asks for a smaller scope:

- `project_config.json`
- `06_remotion/visual_script.json`
- `publish_package_skill_demo/.publish_assets/posters/poster_manifest.json` when poster assets are generated or included in the publish package
- `06_remotion/qa/pre_render_lint.md` for nontrivial projects
- V4 Portrait Remotion project or composition files
- `06_remotion/qa/contact_sheet.*` or sampled stills
- `06_remotion/qa/qa_report.md`
- final 9:16 MP4

## Implementation Defaults

- Style: high-energy short-video packaging. Preferred V4 branch: `dark-fullscreen-semantic-hud`.
- Palette: primary colors are white `#F0F0F0`, electric blue `#067EF6`, and black `#181818` / `#05070B`. Semantic colors are green `#20E0B0`, red `#D83C30`, gold `#C08A30`, and sparse auxiliary purple `#663684`. Do not use bright highlight green `#46FF7A`.
- Hook: choose motion by semantics. Pain/question hooks use word-by-word pop. Result, contrast, and numeric promise hooks use crash-in, rebound, and keyword second-pop.
- Emphasis: key HUD words can use a single secondary scale pop through `emphasisWords`; keep bottom captions stable and readable.
- Captions: `captionRenderMode=embedded` uses one bottom-center adaptive dark rounded strip with complete synchronized all-white text, at most two lines and no truncation. `captionRenderMode=none` renders nothing while preserving the full timecoded caption data for semantics.
- Materials: clear screenshots/recordings become main screen; presenter becomes rounded-rectangle PiP only for that material-main/proof beat.
- Portrait presenter PiP must be a vertical 9:16 rounded window by default, not a 16:9 landscape speaker window.
- Material layouts: use `single-proof` for one screenshot/image, `cover-gallery` only when the spoken content needs to show 2-3 standalone designed posters/platform covers, and `recording-proof` for backend screenshot or screen-recording proof.
- Semantic HUD effects: use pain contrast for "not A, but B"; platform fan-out for multi-platform/channel publishing; manual-field task-status stacks for repeated title/intro/tag/cover filling; automation handoff for repeated fields or manual tasks becoming AI/system execution; proof highlight for readable material; CTA rebound for final action.
- CTA default style is a result-summary plus keyword strip, not a plain top title. Prefer one large closing judgement, one short explanatory line, and one compact keyword/action strip such as "关键词：Codex 用法". Use white base text plus semantic emphasis for the decisive word. In portrait fullscreen-presenter scenes, place CTA as a top/right or right-rail narrow summary by default; do not place large CTA typography over the center head/face area unless the scene is proof material or the presenter is already PiP/side-positioned.
- Portrait compact HUD defaults: `flowPath` becomes a narrow side/bottom process list; `automationHandoff` becomes a right-rail handoff; `platformFanout` becomes a vertical distribution chain; `capabilityShare`, `transformationStack`, and `sceneLockGrid` shrink and stay near the edge; `manual-field` keeps the right-side timeline plus field-list direction. Use full panels only in proof/material-main/PiP scenes.
- Reference-style layered HUD effects: use `capabilityShare` for capability/share/ranking comparisons and `sceneLockGrid` for scenario binding/category tiles. Both must use staged internal animation instead of one-shot panel reveal.
- Transformation HUD effects: use `transformationStack` when the line means "from A to B because of driver X/Y, producing result Z"; this borrows the reference layout of state icons, arrow, driver chips, and metric strip.
- Semantic fulfillment QA is mandatory: numeric beats must show animated numbers/charts, process beats must show flow/list nodes, negative beats must show red warning/delete/contrast treatment, enumeration beats must show numbering, and pain beats must show contrast/problem mapping. If the template cannot fulfill the semantic form, record the fallback as a QA limitation before rendering.
- Corner chapter labels: use top-left `cornerChapterLabel` for section context such as `COLD OPEN`, `PAIN POINT`, `PROCESS`, `PROOF`, and `CTA`, with a short Chinese subtitle.
- Initialization should generate semantic visual events from transcript keywords when possible: `result-promise`, `semantic-problem-map`, `manual-field`, `platform-fanout`, `automation-handoff`, `workflow-step`, and `cta-resolve`.
- Initialization should discover real timelines in this order: SRT/VTT, alignment/timestamp JSON, ASR JSON/SRT, then segmented source durations. Segmented source durations are allowed only for multiple rendered segment clips, not as a fake timeline for a single finished MP4.
- Initialize from the project root by default. If `--output-dir` points directly to an existing or intended `06_remotion`, use that directory as the Remotion root and do not silently create `06_remotion/06_remotion`.
- Initialization should also run dense rhythm scheduling. If a scene is longer than about 7 seconds, add semantic sub-events such as package overview, manual-field progress, platform fan-out, automation handoff, or workflow-step updates so the scene does not rely on one short card at the beginning.
- Presenter movement: keep the base camera stable. Fullscreen/PiP layout changes use one continuous 0.8-second geometry interpolation and pre-exit PiP so the presenter lands at the scene boundary; semantic camera punches use the short `presenter-impact-punch` contract only.
- Transitions: cuts by default; push/zoom only for chapter, contrast, or proof-material shifts.

## Forward Testing

For nontrivial revisions to this skill, forward-test on at least one realistic prompt: "Use `$ngg-koubo-remotion-v4-portrait` to cut a 9:16 Chinese vertical talking-head video from a source video, script, screenshots, and no prebuilt timeline." Check whether the agent creates a timeline plan, `project_config.json`, `visual_script.json`, V4 template implementation plan, and QA plan before rendering.

For semantic routing revisions, run `python scripts/semantic_router_regression.py`, `python scripts/semantic_component_contract_regression.py`, and `python scripts/sfx_semantic_routing_regression.py`. Require positive, adversarial, compound-semantic, renderer-contract, and confirmed SFX examples to pass before committing.

For visual scheduling or density revisions, run `python scripts/visual_density_regression.py` and require dense, light/precomposed, proof-focus, and lane-buffer cases to pass before committing.

For component-level style or motion revisions, run `assets/component-gallery/render_gallery.ps1 -SkipVideo` first and inspect `assets/component-gallery/renders/contact_sheet.png` plus the component keyframes. Render `component_gallery.mp4` when motion timing needs review.
