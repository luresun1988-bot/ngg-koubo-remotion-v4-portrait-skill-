# V4 Forbidden Rules

Use this reference before finalizing any V4 visual script, template change, or QA pass. It records known bad outputs that must not recur.

## Layout Prohibitions

- Do not squeeze a long Hook title into one top-edge line. Split long Chinese hooks into a designed 2-3 line title block with clear hierarchy.
- Do not place a main Hook title so high that it feels like a subtitle strip. Hook titles should occupy a deliberate left or center-left title area and stay clear of face, hands, and bottom captions.
- In 9:16 fullscreen talking-head scenes, do not place large HUD panels, dashboards, workflow boards, network fan-out diagrams, or CTA summary bars over the center face area. Use portrait compact layouts unless the scene is proof/material-main/PiP.
- Do not use horizontal platform fan-out diagrams in fullscreen portrait presenter scenes; use a vertical distribution chain or another compact rail form.
- Do not place automation handoff as a large lower-left card in fullscreen portrait presenter scenes; it must become a compact side rail unless the presenter is PiP.
- Do not place `claimStrip` in the portrait mid-right eye band. Keep it in the top-safe band or downgrade it to a top-right sourced sticker.
- Do not wrap portrait captions, truncate them with ellipsis, or hide the tail text. Render exactly one line; split an overlong timed cue at a real language boundary before semantic routing.
- Do not render terminal punctuation in portrait captions, remove internal punctuation, or modify authoritative `captionCues[].text` merely to change display copy.
- Do not place portrait captions at an arbitrary fixed bottom margin. Keep the caption-strip center in the lower-quarter anchor band around 75% of canvas height.
- Do not make every explanatory beat look like the same compact card group. Rotate between title blocks, red warning cards, numbered rows, icon tiles, data panels, poster stacks, material proof, and transformation stacks.
- Do not use a compact generic card layout for reference-style process or list beats when a vertical numbered list, layered data panel, or source-driver-result layout better matches the meaning.
- Do not move the portrait presenter sideways automatically to create HUD space. `presenterLayout=side` is allowed only for an explicitly `manual-approved` scene or marked `legacy-project` compatibility; ordinary side HUDs keep the presenter fullscreen.

## Semantic Prohibitions

- Do not ignore negative or friction words. Words such as "还在手动", "手动", "麻烦", "别再", "不是", "低效", "重复", "卡住", and "风险" require a red warning, strike/delete, red rail, or contrast-swap treatment.
- Do not render a negative Hook as only a positive green result line. Show the wrong path first, then resolve to the positive action.
- Do not render numeric metrics as small static cards. Numeric claims need count-up, bars, progress, or chart motion.
- Do not drop or truncate numeric suffixes. `2K` must not become `2`, and `1k` may normalize to `1K` but not to `1`.
- Do not collapse enumeration or workflow language into one ordinary information card. Use numbered rows, flow nodes, or internal-step sequences.
- Do not treat future episode previews as completed work or present-tense automation handoff merely because they contain "自动" or a tool name.
- Do not invent CTA actions or keywords. Generated CTA copy must be traceable to `ctaProvenance.sourceText`, and a sourced CTA must not be discarded by lane scheduling.
- Do not build a `transformationStack` from only an A→B phrase. Source, target, one or two drivers, and an explicit result must each cite caption cues owned by the same source beat and scene.
- Do not borrow an uncited previous cue to fill a transformation driver or result, and do not synthesize result copy such as `目标状态达成`. Use the explicit `captionHighlight` fallback when the evidence contract is incomplete.
- Do not route the portrait pair, trinity, causal, priority, compact-pipeline, limitation, or prerequisite templates from weak keyword matches. Enforce their registered cardinality, relation, polarity, and source-cue contracts.
- Do not force a two-step or incomplete ordered workflow into `compactPipeline`; it is reserved for exactly three explicit ordered source steps.
- Do not automatically render a prerequisite with `historicalGreenConclusion`. That green variant requires `presentationVariant=manual-approved`; otherwise use blue/gold `priorityConclusion` so green continues to mean asserted success, completion, or validation.

## Material Prohibitions

- Do not render mp4/mov/webm proof assets as still images. Video proof material must play as video through `OffthreadVideo`.
- Do not keep the presenter in PiP after the video proof or material-main beat ends unless the next beat is also material-main.
- Do not place large proof video inside a small panel when the user expects it to be read or watched. Large video proof should be full material-main with presenter PiP.
- Do not render the portrait speaker PiP as a 16:9 landscape window. The default presenter PiP in 9:16 projects is a vertical rounded window.
- Do not remount or restart the primary presenter video/audio at scene boundaries. PiP and fullscreen are layouts of one continuous source, not separate playback instances.
- Do not stream-copy or concatenate segmented presenter MP4 containers that retain independent AAC tracks. Normalize to one video-only stream plus one 48 kHz PCM WAV and verify exact frame/sample counts.
- Do not use slow symmetric presenter zooms, rebound, continuous scale drift, or repeated breathing camera motion. Do not count presenter zoom as a semantic-density refresh. A lifecycle-synced `presenter-impact-punch` must exactly match a same-scene, same-`sourceBeatId` visible semantic companion and may last at most six seconds; otherwise scale the fallback from composition FPS: 18–28 frames at 30 fps or about 15–23 at 25 fps. Keep impact starts about eight seconds apart and at most three in any rolling minute. Never trigger it from CTA or ordinary explanation.
- Do not interpret the compatibility event name `presenterReposition` as horizontal movement. In portrait output it is scale-only impact metadata.
- Do not force behind-presenter text at frame 0 when the opening is result/proof material or before the presenter states the theme thesis.
- Do not auto-create `depthKeyword` from a theme-thesis candidate. Require explicit approval and a transparent, composition-aligned foreground cutout asset.
- Do not map unknown or low-confidence explanation copy to a fabricated workflow diagram. Keep the strongest scene claim as `claimStrip`, downgrade a short sourced claim to a lightweight sticker, or record an audited `intentionalCleanHold`.
- Do not infer a heavy semantic route from one broad token such as `从`, `发布`, `模型`, or `想要` without the required relation and entities.
- Do not ship component demo defaults as project facts. Never add unspoken platforms, brands, percentages, ratios, fields, transformation states, drivers, or results.
- Do not treat poster assets as generic decoration. Poster assets may enter the video only when the narration or project topic is about covers, thumbnails, posters, or publishing assets.
- For thumbnail/poster-focused videos with 2-3 provided poster exports, do not hide all poster proof until the middle if the opening claim depends on the poster result. Use a right-side staggered poster stack preview when it strengthens the Hook.
- Do not display poster, cover, or thumbnail exports inside mismatched fixed-size frames. Keep 16:9, 4:3, and 3:4 assets in matching native-ratio surfaces, with no extra border frame unless a framed gallery is explicitly requested.

## Motion Prohibitions

- Do not let a HUD disappear while its own animation is still entering, drawing, counting, or revealing internal steps.
- Do not reveal top, middle, and bottom layers of a reference-style HUD in the same frame. Layered HUDs must build in semantic order.
- Do not repeat the same component family three times in a row, even if the script has several adjacent process beats.
- Do not solve repeated `claimStrip` events by randomly cycling unrelated components. Reduce lower-priority ordinary claims or leave them intentionally clean after the second consecutive main claim.
- Do not stack main HUD effects in the same lane. Use internal steps or leave a handoff buffer.
- Do not use CSS animation, CSS transition, timers, runtime randomness, strong flash whites, face-covering transitions, or full-screen glitch noise.

## Visual Style Prohibitions

- Do not add colored glow or colored projection shadows. Semantic colors may appear in text, icons, fills, rails, and charts only.
- Do not add white/grey ring outlines around cards or panels by default.
- Do not use directional gradients inside cards or panels that make one side fade away. Use uniform dark translucent backing.
- Do not add a fullscreen dark mask over presenter footage.
- Do not add a HUD background edge-gradient mask in normal V4 renders. The retained `HudEdgeShade` code is optional and disabled by default.
- If optional side edge shade is explicitly re-enabled, do not let it appear on the opposite side from the HUD.

## QA Sampling Requirements

- For video proof, sample at least three frames across the proof beat to confirm it changes over time.
- For internal-step HUDs, sample early, middle, and late frames to confirm every step appears and holds before exit.
- For Hook, sample the title peak frame and verify the title block is intentionally composed, not squeezed or clipped.
- For negative language, sample the negative beat and verify a red/strike/contrast treatment is visible.
