# V4 Motion System

Use this reference before designing or implementing animation.

## Core Motion Principles

- Motion must follow narration meaning and timecodes.
- HUD events should start from the caption cue that contains their visible keyword when a semantic beat spans multiple cues. Cue-level anchoring is the default; word-level anchoring is used only when word timestamps exist.
- Plan semantic role before choosing the visual effect. `semanticRole` routes the effect family; `motionType` describes its timing.
- Use high rhythm, but avoid constant noise.
- Use frame-driven Remotion APIs only: `useCurrentFrame()`, `interpolate()`, `spring()`, `Sequence`, and `TransitionSeries`.
- Use `OffthreadVideo` for rendered source-video layers so frame extraction stays deterministic with H.264/B-frame footage.
- Do not use CSS transitions, CSS animations, timers, random values, or runtime-only motion.
- If a motion does not help the spoken idea, remove it.

## Rhythm

Default rhythm is strong-packaging dense motion, but still readable.

- Visual event builders must apply the V1 density scheduler before render data is written. Each generated main HUD may carry `densityMode` and `densityReason` metadata so QA can explain whether it came from default dense packaging, Hook/CTA/contrast emphasis, precomposed/light packaging, or proof-material focus.
- Density modes:
  - `dense`: default talking-head explanation/process rhythm.
  - `dense-strong`: Hook, CTA, and contrast scenes get slightly stronger/longer main HUD holds.
  - `light`: `sourceVideoMode=precomposed-video` or `packagingDensity=light`; keep generated HUD conservative and do not insert density refresh stickers.
  - `proof-focus`: material-main or presenter-PiP proof scenes; protect material readability and do not insert unrelated density refresh stickers.
- In dense scenes longer than about 7 seconds, if scheduled semantic HUD leaves a long empty span, the builder may insert a lightweight `statusSticker` with `semanticRole=density-refresh`. This is a rhythm marker, not a replacement for fulfilling a semantic beat.
- Density refresh stickers must stay small, top-left safe, iconed, and neutral. They should not compete with bottom captions or become a second main HUD panel.
- Main semantic HUD events should hold about 4.5-6 seconds when the scene length allows it.
- Main HUD events must have enough duration for entry, internal motion, readable hold, and exit. Below about 3.2 seconds is a QA failure; 3.2-4.5 seconds is a warning unless the beat is deliberately simple.
- Components with internal steps must budget enough frames for every step to appear and hold briefly. If an item is still entering, counting, drawing, or fading in when the component exits, the timing is invalid and must be extended or simplified.
- Every 2-3 seconds should contain a visible semantic change: field completion, node fan-out, state highlight, label swap, status change, or a new sub-event.
- Every scene longer than about 7 seconds must be split into multiple semantic sub-events. Do not rely on one short card at the beginning of a long talking-head segment.
- More than 4 seconds without a visual change is a QA warning in dense mode.
- More than 7 seconds without a semantic visual event is a QA failure unless the scene is deliberately clean proof-material playback.
- Hook, contrast, proof, and CTA may be denser.
- Dense does not mean crowded. If a frame becomes hard to read, split the beat.
- Prefer "main HUD persists + internal step animation + secondary semantic update" over flashing unrelated decorative elements.
- Main HUD events are scheduled into lanes: `left`, `right`, `center`, and `proof`. A `cornerChapterLabel` is exempt because it is a lightweight marker, not a main HUD.
- Do not overlap two main HUD effects in the same lane. Leave about 10 frames between same-lane handoffs so the first effect can exit before the next enters.
- Visual event builders should schedule main HUD lanes on absolute timeline frames, not only within scene-local boundaries. If a same-lane component needs to finish its exit, the next same-lane component should move later instead of stacking, including across adjacent scene boundaries.
- Preserve sourced CTA events when lane pressure occurs. If a previous left-lane HUD would push the CTA out of its scene or below the minimum readable duration, trim or drop the earlier HUD and keep the CTA plus the normal lane buffer.
- The lane must drive the rendered HUD position. `HudEdgeShade` is kept as optional code but is disabled by default; if it is re-enabled later, the same lane must drive both the rendered HUD and the shade side.
- If one idea needs several changes in the same area, implement them as internal steps inside one component instead of stacking separate HUD events.
- Do not solve every adjacent process beat with the same flow-list/status panel. After one flow-list panel, the next process beat should usually switch to another visual form such as a timeline/filmstrip, data punch, status stickers, platform fan-out, or proof material.
- For layered reference-style HUDs, the internal sequence is mandatory. Do not make the label, top icon/logo row, and data/grid body visible at the same time on the first frame; the reveal must follow the spoken semantic order.

## Hook Title Motions

Choose by semantic role:

- Pain/question: word-by-word pop, synced to speech beats.
- Result/contrast/number promise: crash-in, rebound settle, keyword second-pop.
- Strong title effects must be short. Shakes, glow pulses, and impact lines should resolve quickly.
- Emphasized title keywords can do one secondary enlarge/rebound after the main entrance. Use it only for 1-3 semantic keywords, not every word.
- Hook titles render as stacked title blocks by default. Do not animate a long Hook as one horizontal strip across the top edge.

Failure conditions:

- Title covers face, mouth, eyes, hands, or caption.
- Title cannot be read within about one second.
- Same motion is repeated for every scene without semantic reason.

## Semantic Effect Routing

Use these defaults when creating `visualEvents`:

| Spoken meaning | `semanticRole` | Recommended event type | Motion preset |
| --- | --- | --- | --- |
| Result promise, one-click outcome, numeric promise | `result-promise` | `kineticTitle` + optional `materialZoom` | `crash-rebound-keyword-pop` |
| Clear numeric metric, growth, ratio, scale | `metric-growth` | `dataPunch` / `metricSpotlight` | `count-up-chart` |
| Capability/share/ranking comparison | `capability-share` | `capabilityShare` | `layered-capability-share` |
| Scenario binding, industry/category landing | `scene-lock` | `sceneLockGrid` | `scene-grid-stagger` |
| From A to B, leverage, moat/driver/result | `transformation-stack` | `transformationStack` | `state-driver-result-build` |
| "Not A, but B"; real bottleneck; pain contrast | `semantic-problem-map` | `semanticProblemMap` | `contrast-swap-scan` |
| Negative/friction hook such as "还在手动", "别再", "不是", wrong path, risk | `negative-friction` | `semanticProblemMap` / `statusSticker` | `red-warning-pop-strike` |
| Repeated upload/title/intro/tag/cover fields or local directory checks | `manual-field` | `infoCard` | `status-polling-field-tree` |
| One content package splits to several platforms/channels | `platform-fanout` | `platformFanout` | `hub-to-platform-flow` |
| Manual/repeated work becomes AI/system execution | `automation-handoff` | `automationHandoff` | `field-collapse-to-action` |
| Episode/topic introduction | `topic-intro` | `topicKeyword` | `word-by-word-topic-reveal` |
| Ordinary explanation or low-confidence claim | `explanation-claim` | `claimStrip` | `lightweight-claim-slide` |
| Readable screenshot, screen recording, proof asset | `proof-focus` or `proof-material` | `materialMain` / `materialZoom` | `material-push-in` / `material-zoom-highlight` |
| Thumbnail/poster subject with 2-3 provided poster exports | `poster-stack-preview` | `materialZoom` / `materialMain` | `right-poster-stack-pop` |
| CTA or final action | `cta-resolve` | `ctaTitle` | `cta-result-keyword` |
| Section context, cold open, process chapter, proof chapter | `chapter-label` | `cornerChapterLabel` | `corner-slide-fade` |

Do not use a generic card when a more specific semantic pattern exists. For example, multi-platform publishing should use `platform-fanout`, not five platform cards.
Do not use `infoCard` for clear numeric metrics or process/enumeration beats. Numeric beats need count-up/chart motion; process beats need numbered rows, nodes, or flow paths.
Do not render negative/friction language as a normal positive title. The negative part should enter with red warning motion or a strike/delete gesture, then resolve to the positive idea.
In fullscreen/large portrait presenter scenes, `semanticProblemMap` uses a compact top-safe horizontal layout. It must not animate across the center eye/face band.

## Deployed Motion Presets

The V4 template currently implements these concrete presets:

- `word-pop`: staged word entrance for pain/question hooks.
- `crash-rebound-keyword-pop`: title scale-in, rebound, and short keyword emphasis for results, routes, and CTA.
- `keyword-second-pop`: emphasized title words scale up briefly once after the primary entrance, then settle back; no continuous pulsing.
- `presenter-impact-punch`: reserve for a strong source-bound question, core judgement, reversal, warning, or asserted result. At 30 fps use 18–28 frames total: push to 1.06–1.10 in 4–6 frames, rebound to 1.03–1.05 in another 4–6 frames, hold briefly, and return in 6–10 frames. Keep a face-safe origin near `50% 37%`, at most three punches in a rolling minute, and about eight seconds between punches. Do not overlap proof/material focus, PiP transitions, or another major camera move.
- `contrast-swap-scan`: pain contrast board with state highlight and "not A / but B" layout.
- `hub-to-platform-flow`: center package fans out to platform nodes with staggered line reveal.
- `field-collapse-to-action`: repeated fields expand, check, and hand off into Codex/system execution.
- `red-warning-pop-strike`: compact red warning card/sticker enters with a short pop. The red treatment must be carried by the card/sticker itself: red icon, red rail/border, white + red mixed text, and optional strike/delete line only when it visibly crosses the negative text. The positive green resolution card appears after the negative beat, not at the same time.
- `right-poster-stack-pop`: 2-3 poster assets appear on the right one by one with scale/translate/rotation offsets, holding as a stacked preview while the Hook text occupies the left/center-left.
- `count-up-chart`: numeric value grows from zero/baseline to target; suffix such as `%` appears after the count; mini bars or progress cue grow with the number.
- `layered-capability-share`: section label/title enters first, capability/object tiles enter one by one, then the lower share panel enters and bars grow row by row.
- `scene-grid-stagger`: section label/title enters first, then scenario tiles appear one by one with distinct semantic icons and short active-state emphasis.
- `state-driver-result-build`: source state icon enters, arrow draws to target state, driver chips appear one by one, then the result metric strip appears or counts up.
- `flow-list-stagger`: numbered process rows enter one by one with unique semantic icons.
- `corner-slide-fade`: lightweight top-left chapter label slides in softly and does not trigger edge shade.
- `material-zoom-highlight`: material board push-in with state highlight and proof highlight.
- `screen-recording-proof`: material board styled as a screen-recording or backend proof surface.
- `cta-result-keyword`: CTA closes with a large result judgement, a delayed explanatory line, and a compact keyword/action strip. The strip enters after the judgement has settled, and the emphasized CTA word gets one secondary scale pop. In fullscreen-presenter scenes, the CTA is a left-lane HUD by default so it does not cover the presenter's face.

## Card Motion

Default card entrance:

- Primary card enters first.
- Secondary cards enter with 3-6 frame stagger.
- Use slight scale, opacity, and position movement.
- Use active state pulse only once per important step.
- Use 16-22 frame fade windows for smoother enter/exit when event duration allows it.
- Main cards should leave with a slight translate/opacity fade rather than snapping off.
- Long card beats should animate internal state, such as list items completing, node emphasis changing, or a state highlight crossing the panel.

Avoid:

- Five-card piles.
- Every card sliding from the same direction.
- Cards exiting while their backing gradient snaps off abruptly.

## Optional HUB Edge Shade Motion

HUB edge shades are disabled by default. Keep the `HudEdgeShade` implementation available for future tests, but do not render edge-gradient masks in normal V4 outputs unless the user explicitly asks to re-enable them.

- If re-enabled, left-side HUD triggers only a left edge shade and right-side HUD triggers only a right edge shade.
- If re-enabled, bottom captions and `cornerChapterLabel` still never trigger edge shade.
- If re-enabled, centered HUD and CTA titles should not trigger an edge shade by default.
- If re-enabled, no-HUB presenter talk must have no edge shade and no fullscreen mask.
- If re-enabled, edge shades enter and exit with the HUD event using Remotion frame-driven opacity. Dense-mode fade windows should be about 16-22 frames when the event duration allows it.
- If re-enabled, the shade may ease a few pixels from the edge as it fades in, but it must not use CSS transitions, CSS animations, timers, random values, or runtime-only motion.
- If re-enabled, shade exit must be sampled during QA and should fade out naturally instead of snapping off.
- If re-enabled, edge shade duration must follow the active HUD lifecycle and must not disappear before the HUD finishes.
- If re-enabled, edge shade follows the actually visible HUD lane after main-HUD filtering. If a bad script overlaps same-lane HUD events, the template must not double-render shades or panels.

## Icon Motion

Default:

- Icon enters with its card.
- Icon may pulse once when its card becomes active.

Special:

- Independent icon fly-in is only for Hook, chapter switch, or process overview.
- Independent fly-in may happen at most once per chapter.
- Trails should be short and lightly glowing.

## Material Motion

Default material motion:

- Main screenshot or recording appears large.
- Camera/crop pushes to the key region.
- Semantic-green `#20E0B0` highlight box, arrow, or highlight cue points at the relevant area.

Use `cover-gallery` style only when the narration explicitly discusses covers, thumbnails, posters, publishing assets, or multi-platform cover outputs. Use `assetStack` with 2-3 assets.

Use clean full-screen playback when details must be read or source motion matters.
If the material is a video file (`mp4`, `mov`, `m4v`, or `webm`), it must play with `OffthreadVideo`. Do not use a first-frame still to represent a video proof. The proof beat duration should not exceed the video duration unless the design intentionally freezes on the final frame after playback.
After a video proof scene ends, presenter layout should return to fullscreen unless another material-main scene immediately follows.

Material readability beats motion impact. If motion blurs or hides the proof, simplify it.

When material is the main screen and the presenter is PiP, use material focus mode:

- Do not run side HUD panels, automation handoff panels, platform fan-out panels, or unrelated kinetic titles over the material.
- Allow only proof-specific highlight boxes, highlight cues, arrows, short labels, and bottom captions.
- If the narration needs both a process explanation and a readable proof material, split them into separate beats instead of stacking them on one frame.

## Presenter Repositioning

Presenter movement follows scene type:

- Hook: presenter should usually remain fullscreen.
- Explanation, Process, Contrast: presenter remains fullscreen unless a large material or diagram needs the main screen.
- Proof: source material main screen, presenter rounded PiP.
- CTA: presenter returns to a clear speaking layout.

Movement style:

- Scale and translate with easing.
- Keep the base camera stable. Do not use presenter scale to fill a semantic refresh quota; cards, icons, numbers, and labels provide ordinary refreshes.
- A slow symmetric `1 -> peak -> 1` zoom lasting longer than one second reads as drift and is forbidden for semantic emphasis.
- Fullscreen/PiP geometry transitions are not semantic camera punches. Interpolate left/top/width/height/radius for about 0.8 seconds while keeping one video instance mounted. Begin PiP-to-fullscreen return during the final 0.8 seconds of proof so it lands exactly at the next scene boundary.

## Dynamic Motion QA

Run `scripts/render_motion_previews.ps1` after still/contact-sheet approval. It renders short H.264 previews around every `presenter-impact-punch`, behind-presenter depth event/candidate, and presenter-layout boundary. Review these clips for speed, rebound, geometry continuity, lip sync, and accidental camera drift before the full render.
- No hard jumps.
- Sample frames before and after repositioning.
- Segment boundaries must not create face/body jumps.

## Transitions

Default transition is a direct cut.

Allowed semantic transitions:

- Push.
- Zoom.
- Scale handoff.

Use transitions only for chapter changes, contrast/reversal, or proof-material entry.

Forbidden:

- Strong flash white.
- Face-covering transition.
- Full-screen glitch noise.
- Random decorative wipes.
- Full-screen effects that obscure captions without reason.
