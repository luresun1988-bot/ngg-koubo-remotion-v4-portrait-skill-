# V4 Forbidden Rules

Use this reference before finalizing any V4 visual script, template change, or QA pass. It records known bad outputs that must not recur.

## Layout Prohibitions

- Do not squeeze a long Hook title into one top-edge line. Split long Chinese hooks into a designed 2-3 line title block with clear hierarchy.
- Do not place a main Hook title so high that it feels like a subtitle strip. Hook titles should occupy a deliberate left or center-left title area and stay clear of face, hands, and bottom captions.
- In 9:16 fullscreen talking-head scenes, do not place large HUD panels, dashboards, workflow boards, network fan-out diagrams, or CTA summary bars over the center face area. Use portrait compact layouts unless the scene is proof/material-main/PiP.
- Do not use horizontal platform fan-out diagrams in fullscreen portrait presenter scenes; use a vertical distribution chain or another compact rail form.
- Do not place automation handoff as a large lower-left card in fullscreen portrait presenter scenes; it must become a compact side rail unless the presenter is PiP.
- Do not truncate bottom captions with ellipsis or hide the tail text. Captions must stay complete, readable, and within the portrait two-line maximum.
- Do not make every explanatory beat look like the same compact card group. Rotate between title blocks, red warning cards, numbered rows, icon tiles, data panels, poster stacks, material proof, and transformation stacks.
- Do not use a compact generic card layout for reference-style process or list beats when a vertical numbered list, layered data panel, or source-driver-result layout better matches the meaning.

## Semantic Prohibitions

- Do not ignore negative or friction words. Words such as "è¿å¨æå¨", "æå¨", "éº»ç¦", "å«å", "ä¸æ¯", "ä½æ", "éå¤", "å¡ä½", and "é£é©" require a red warning, strike/delete, red rail, or contrast-swap treatment.
- Do not render a negative Hook as only a positive green result line. Show the wrong path first, then resolve to the positive action.
- Do not render numeric metrics as small static cards. Numeric claims need count-up, bars, progress, or chart motion.
- Do not collapse enumeration or workflow language into one ordinary information card. Use numbered rows, flow nodes, or internal-step sequences.

## Material Prohibitions

- Do not render mp4/mov/webm proof assets as still images. Video proof material must play as video through `OffthreadVideo`.
- Do not keep the presenter in PiP after the video proof or material-main beat ends unless the next beat is also material-main.
- Do not place large proof video inside a small panel when the user expects it to be read or watched. Large video proof should be full material-main with presenter PiP.
- Do not treat poster assets as generic decoration. Poster assets may enter the video only when the narration or project topic is about covers, thumbnails, posters, or publishing assets.
- For thumbnail/poster-focused videos with 2-3 provided poster exports, do not hide all poster proof until the middle if the opening claim depends on the poster result. Use a right-side staggered poster stack preview when it strengthens the Hook.
- Do not display poster, cover, or thumbnail exports inside mismatched fixed-size frames. Keep 16:9, 4:3, and 3:4 assets in matching native-ratio surfaces, with no extra border frame unless a framed gallery is explicitly requested.

## Motion Prohibitions

- Do not let a HUD disappear while its own animation is still entering, drawing, counting, or revealing internal steps.
- Do not reveal top, middle, and bottom layers of a reference-style HUD in the same frame. Layered HUDs must build in semantic order.
- Do not repeat the same component family three times in a row, even if the script has several adjacent process beats.
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
