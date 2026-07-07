# V4 Visual System

Use this reference for visual design and layout.

## Style

V4 Portrait uses high-energy short-video packaging for 9:16 Chinese vertical talking-head edits.

- Primary colors: white `#F0F0F0`, electric blue `#067EF6`, and black `#181818` / `#05070B`.
- Semantic colors: green `#20E0B0` for positive/result/completion, red `#D83C30` for wrong-path/risk/negative, gold `#C08A30` for proof/source/recommendation, and sparse auxiliary purple `#663684` only for model/category/adaptation modules.
- Do not use bright highlight green `#46FF7A`.
- Mood: fast, sharp, modern, technology-oriented, readable.
- Avoid one-note decoration. Every visual element must help the spoken idea.

## Style Branch: dark-fullscreen-semantic-hud

Use this branch for fullscreen presenter edits with semantic HUD packaging.

- Presenter is fullscreen by default.
- In 9:16 fullscreen presenter scenes, face safety beats component completeness. Do not place large panels, dashboards, network graphs, or wide card groups across the center face band. Use compact HUD rails, top timelines, right-side field lists, and short caption-safe strips instead.
- Complex full panels are allowed by default only in proof/material-main/PiP scenes where the presenter has already yielded the center screen to readable material.
- Do not add artificial colored room lights.
- Do not place a default fullscreen black/dark vignette or mask over presenter footage.
- Use readable HUD overlays with local support only where the HUD appears.
- Left/top chapter labels indicate section context. Use `cornerChapterLabel` for the top-left chapter marker style: an electric-blue rail, readable blue primary label, and short white Chinese subtitle. In 1080x1920, keep it compact and farther from the top-left edge than horizontal V4; primary and subtitle labels should usually sit around 22-26 px.
- Side HUD panels, flow diagrams, cards, and proof boards appear only when they explain the current spoken idea.
- In portrait fullscreen presenter scenes, `flowPath`, `automationHandoff`, `platformFanout`, `capabilityShare`, `sceneLockGrid`, `transformationStack`, and CTA summaries default to compact forms. Use full-size panels only for proof/material/PiP beats or explicit full-panel review samples.
- Large proof material, screenshots, screen recordings, or readable assets become the main screen; only then does the presenter become PiP.
- In portrait projects, presenter PiP is a vertical 9:16 rounded window by default. Do not use a 16:9 landscape speaker PiP unless the source speaker footage is actually landscape and the user explicitly chooses that crop.
- Avoid decorative dashboards. HUD density must come from semantic need, not empty-space filling.

## HUB Local Shade Rules

HUB includes packaging elements: big titles, information cards, icons, status stickers, process panels, pain/contrast boards, platform fan-out panels, automation handoff panels, proof labels, and corner chapter labels.

HUB does not include bottom captions, caption keyword highlights, or the caption rounded strip.

- No-HUB presenter talk keeps the source-video brightness. Do not add a fullscreen dark overlay just to create mood.
- HUD edge gradient masks are disabled by default. Do not add a black edge gradient just because a HUD appears.
- Keep HUD readability through the component's own uniform backing, neutral shadow, typography, icon contrast, and placement.
- The template keeps `HudEdgeShade` as optional code for future use. If explicitly re-enabled later, HUD position and edge shade direction must be coupled: right-side HUD can only use right edge shade, and left-side HUD can only use left edge shade.
- Centered HUB, including CTA titles, should rely on the element's own backing, text shadow, local plate, or glow. Do not add a fullscreen mask.
- `cornerChapterLabel` is a lightweight marker and must not trigger edge shade. It should rely on neutral text shadow and the blue rail, not a backing panel.
- If edge shades are re-enabled later, they must not cover the face, mouth, eyes, or main hand gestures.
- If edge shades are re-enabled later, they should stay narrow enough for 1080x1920 and must not darken the face; peak near 0.68-0.78 opacity only when the user wants stronger HUD backing.

## Typography

- Use bold Chinese sans-serif typography for titles and captions.
- Use Source Han Sans SC / 思源黑体 as the global Chinese render font. Bundle it in `public/fonts` and register it with `@font-face`.
- Use monospace only for code, paths, terminal, or technical file cues.
- Do not use thin Chinese text for core information.
- Do not use hard black text outlines over every title; prefer strong fill, contrast, shadow, and localized backing.
- In Remotion headless renders, verify Chinese glyph rendering.
- The V4 template registers bundled `SourceHanSansSC-Regular.otf`, `SourceHanSansSC-Bold.otf`, and `SourceHanSansSC-Heavy.otf`; if the skill is moved to a machine without these assets, replace them with valid Source Han Sans SC files before rendering.
- Keep Chinese output style consistent. For mainland Chinese talking-head videos, normalize captions, titles, and HUD text to Simplified Chinese unless the user requests Traditional Chinese.
- Template-generated HUD/UI labels default to Simplified Chinese, including card fields, panel headers, platform nodes, process labels, proof tags, and placeholders. Keep English only for real brand/product names, code/API names, terminal commands, or source-material text that is genuinely English.
- All non-caption text needs a highlight treatment: strong neutral black shadow, subtle white edge, local backing, or semantic text color.
- Do not use colored glow or colored projection shadows. Blue, green, red, and amber may appear as text, icon, status fill, line, or content mark colors only.

## Hook And Big Text

Big text is the primary packaging element.

- Hook layout should feel like a designed title block, not a subtitle enlarged at the top edge. Long Chinese hooks must split into 2-3 stacked lines with strong hierarchy, usually left or center-left, leaving the face and captions safe. Use a large semantic keyword in electric blue, semantic green, or red depending on meaning.
- Avoid one-line squeezed hooks such as "别再手动做主图 这一步，该自动化了" across the top. Split into a main judgement and a smaller supporting line, similar to a reference-style title block.
- The template should auto-stack Hook title text as a safety net. Even if the event text is one line, brand/keyword titles such as "Codex 离谱用法" must render as separate lines.
- Pain/question hooks: word-by-word pop synced to the spoken question.
- Result, contrast, and numeric promise hooks: crash-in, rebound settle, then keyword second-pop.
- Main text is black/white bold type. Keywords use semantic green `#20E0B0` or electric blue `#067EF6`.
- Emphasized HUD keywords may use semantic color plus a single secondary enlarge/rebound. This applies to big titles and HUD text, not bottom captions.
- Negative or friction words such as "还在手动", "手动", "麻烦", "别再", "不是", "低效", "重复", "卡住", and "风险" require visible red negative treatment before the positive resolution. Default treatment is a dark red warning card/sticker with a red icon, red rail/border, and white text with the negative keyword in red. A negative hook must not appear as a neutral white/green title only.
- Red warning copy must be compressed into the key objection or wrong-path phrase. Do not place the whole spoken sentence in the warning card. Use white base text with the one decisive negative phrase in red.
- Hook intensity may be strong only for a short burst.
- Do not keep screen-shaking or glow effects active for long holds.
- Big text must not cover the face, mouth, eyes, key hand gestures, or bottom caption strip.

## Captions

Captions are mandatory by default.

- Position: bottom center safe area.
- Shape: adaptive dark translucent rounded strip.
- Layer count: one caption layer only.
- Line count: one or two lines only. Captions must show the complete spoken cue text from the transcript/ASR timeline; do not summarize, omit words, rewrite it as a shorter HUD phrase, wrap to three lines, or truncate with ellipsis. Reduce caption size first, then split the timing cue only if the full cue still cannot fit within two lines.
- Sync: caption cue start/end frames must follow the transcript/timecode source. When one narration segment is split into multiple caption cues, the concatenated cue text for that scene must still equal the full spoken line after punctuation/space normalization.
- Highlight: bottom captions use all-white text. Do not color individual caption words; reserve semantic colors for HUD, icons, charts, and proof highlights.
- Avoid duplicating the exact same sentence in a big title and bottom caption at the same moment unless it is an intentional Hook beat.
- Other UI must avoid caption area. If there is a conflict, move or simplify the UI, not the caption.

## Cards

Cards explain one point each.

- Maximum same-screen card count: three.
- Card content: short title, one primary semantic icon, optional status label.
- Cards are not the default packaging layer. Prefer big judgement text, data/chart forms, line annotations, flow paths, platform fan-out lines, source material, or CTA typography when those forms fit the semantic meaning.
- Large cards are reserved for complex information containers: automation handoff, workflow overview, proof material, and recommendation/CTA entry blocks.
- Small cards are allowed for short fields, steps, status items, platform nodes, and material items, but they must be mixed with non-card visual forms across the edit.
- Main card/panel-like events should stay near or below 35% of all main visual events. Three consecutive main visual events should not all be cards or panels.
- Three consecutive main visual events must not use the same rendered component family. If several adjacent beats are all process language, rotate the form instead of repeating one flow-list panel: use a flow path, then a data punch, timeline/filmstrip, status stickers, platform fan-out, proof material, or CTA typography.
- Use translucent high-contrast dark cards for explanation and workflow.
- Confirmed V4 card surface: one clean, uniform dark translucent backing, defaulting near `rgba(5,7,11,0.62)`.
- Card surfaces are borderless by default: no white outline, no grey ring, no pale second edge layer, and no colored border.
- Do not use directional gradients inside cards. The card must not fade from left to right or toward an arrow/action block; the whole card should stay as deep and clean as the left side of the confirmed reference.
- Internal rows, small cards, process nodes, and automation fields follow the same card-surface rule: uniform dark backing, neutral black shadow, and readable text/icon contrast.
- Use sticker-like labels for status, warning, numbers, OK, and step states.
- Use big text flow for Hook, contrast, conclusion, and CTA.
- Do not create large empty proof cards or placeholder material frames.
- If text does not fit, shorten the message or split the scene. Do not shrink Chinese text into unreadable blocks.
- HUD card text is key-message copy, not transcript copy. Keep warning/confirm cards to one short line when possible; use white text plus one semantic-color phrase, matching the reference style of white statement + red/green emphasized keyword.
- Warning/contrast card copy should stay near 16 Chinese characters per visible line. Confirm/handoff cards should use a short label plus one short result phrase. Do not carry complete narration into a card just because the transcript line is available.
- `emphasisWords` is required for generated red warning cards and should be present for green confirm cards. The emphasized words must be present in the visible HUD copy and should be the semantic point, such as `手动`, `不够分`, `工作流`, `自动化`, or `Codex`.

## Ring Shadows

Apply a visible outer ring shadow to all packaging surfaces except bottom captions:

- HUD panels, cards, process boards, contrast boards, status stickers, and flow panels.
- Presenter PiP windows and side presenter windows.
- Material windows, proof boards, gallery cards, and screenshot/recording frames.
- Non-caption large text should use neutral text shadow as its highlight.
- Default HUD surface shadow should be visibly separated, using `0 30px 72px rgba(0,0,0,0.68), 0 10px 24px rgba(0,0,0,0.54)` or a stronger equivalent.
- Default non-caption text shadow should be visibly readable on footage, using `0 3px 0 rgba(0,0,0,0.82), 0 8px 12px rgba(0,0,0,0.88), 0 18px 38px rgba(0,0,0,0.72), 0 0 2px rgba(255,255,255,0.16)` or a stronger neutral equivalent.
- Cards, HUD panels, presenter PiP windows, and material windows are borderless by default. Use clean uniform dark translucent backing and neutral black shadow for depth; add a neutral frame only when a proof material needs a readable edge.
- Cards and HUD panels should not use directional fade gradients that make their own content disappear. Their default backing is uniform `rgba(5,7,11,0.62)`.
- All card-like HUD surfaces should use a single uniform dark translucent panel. Do not use left-to-right fade, grey ring outlines, or a second pale edge layer.
- The old edge-to-face darkening belongs only to the separate optional `HudEdgeShade` layer. It is disabled by default; do not recreate it inside cards, panels, or fullscreen masks.

Bottom captions keep their own dark rounded strip and do not need the ring shadow.

## Semantic HUD Patterns

Choose HUD patterns by semantic role:

- `result-promise`: big result title plus compact proof/package preview.
- `metric-growth` / numeric proof: `dataPunch` or `metricSpotlight`, with animated count-up, percent/unit reveal, and a mini bar/progress/chart cue.
- Strong short metrics such as `100 道题`, `52 道题`, or `< 1 分钟` should default to the current A-style left-side big-number punch: large white number, blue unit, minimal local support, and no heavy half-screen shadow plate. Use right-side or compact proof variants only when the left side is occupied by higher-priority face/material content.
- `capability-share`: `capabilityShare`, for capability, market/share, model/company ranking, global/local comparison, or "who is leading" beats. It uses a compact section label, 2-3 object/logo/icon tiles, and a lower data/share panel with animated bars.
- `scene-lock`: `sceneLockGrid`, for scenario binding, industry categories, local usage contexts, or "where this lands" beats. It uses a compact section label plus scenario tiles.
- `transformation-stack`: `transformationStack`, for "from A to B", individual-to-team, moat/leverage, driver-to-result, or productivity shift beats. It uses a top state transition, middle driver chips, and a bottom result metric strip.
- `semantic-problem-map`: contrast panel for "not A, but B" or "the real bottleneck is X".
- `manual-field`: repeated task or repeated field filling, local directory checks, or field availability checks. Prefer the right-safe-zone `STATUS POLLING` timeline above a `FIELDS` file-tree/field-list: a bare status line with spaced labels/nodes, then a slim blue rail plus 2-3 row backings with semantic icons, status dots, checks, or `生成中`. Do not use a large outer card, stacked task-card container, or circular `AI/FILES` badge for this pattern.
- `workflow-step`: `flowPath` or `statusStack`, with numbered rows/nodes and item-by-item reveal.
- `platform-fanout`: one source package fans out to several platforms or channels.
- `automation-handoff`: repeated/manual fields collapse into AI/system execution, on a uniform dark translucent panel with clean black shadow and no horizontal fade.
- `proof-focus`: readable proof material with highlight boxes, arrows, highlight cues, and simplified overlays.
- `cta-resolve`: final result-summary typography, not an ordinary card. Default structure is one large closing judgement, one short explanatory line, and one compact keyword/action strip such as `关键词：Codex 用法`. Use white base text plus semantic green emphasis for the decisive word. In fullscreen-presenter scenes, place CTA typography in the left/upper-left safe area by default and keep the center head/face area clear.
- `poster-stack-preview`: for cover/poster/thumbnail topics, show 2-3 poster exports as a right-side staggered stack during the Hook or early proof beat, while the left title carries the negative or result statement.

Semantic fulfillment rules:

- Numeric values like `+30%`, `3倍`, `885万`, `0.04%`, conversion rate, growth, scale, or ratio must not be rendered as plain `infoCard`. Use a number-first component where the value visibly grows from zero or from a baseline.
- Process and enumeration language such as first/second/third, five things, stages, steps, or workflow must not be collapsed into one ordinary card. Use `flowPath`, `statusStack`, or numbered rows.
- Negative language such as do not, wrong, not A, risk, or denial needs red warning, strike-through, contrast swap, or sticker treatment.
- Red negative treatment should be compact and intentional: a dark red translucent card/sticker with red border/rail, red icon, and short copy. Long negative claims use a horizontal warning card with white + red mixed text; very short claims can use a smaller red sticker with red text. It should read like a warning or objection, not like a normal information card recolored.
- Pure negative or denial copy stays red-only. If the line only says "不是 XXX" or describes a wrong path without a spoken fix, do not add a green confirm card, and do not fill in generic copy like "这一步，该自动化了".
- Confirmed/positive resolution cards may mirror the negative style with semantic green: green icon, green rail/border, white + green mixed text, and the same compact sticker/card language.
- The paired red-warning plus green-confirm layout is reserved for lines that explicitly contain both sides of the contrast, such as "不是 A，而是 B" or "交给 Codex 自动完成".
- Pain-point language needs a contrast/problem map rather than a neutral explanation card.
- Layered HUDs must not reveal every layer at once. For `capabilityShare`, show label/title first, then object tiles, then lower data rows and bar growth. For `sceneLockGrid`, show label/title first, then scene tiles one by one. For `transformationStack`, show source state, arrow, target state, driver chips, then result metric.

## Icons And Stickers

- Default icon style: lucide-style line icons.
- If the spoken or visible noun is a concrete existing brand, platform, product, or company such as 抖音, 英伟达, OpenAI, Google, or B站, use the real provided logo/icon asset when available and legally usable. If no real logo asset exists in the project or shared library, fall back to the closest semantic lucide icon.
- Implementation default: `lucide-react`.
- Every small information card, process node, status node, platform node, and field row must include one primary semantic icon.
- One primary icon per card or process node. A completion check may appear as a secondary state marker, but it must not replace the semantic icon.
- Repeated cards or nodes in the same `beatGroupId`, list, or grouped set must use different semantic icons.
- Do not fall back to a generic icon for every missing case. The initializer should infer `iconName` from `semanticRole` and visible text, then swap to a synonym if the group already used that icon.
- Semantic icon defaults:
  - Upload/publish: `UploadCloud`, `SendHorizontal`
  - Title/copy: `FileText`, `TextCursorInput`
  - Intro/description: `AlignLeft`, `ListChecks`
  - Tags/keywords: `Tags`, `Hash`
  - Cover/image: `Image`, `Images`
  - Video/material package: `Video`, `Package`
  - Multi-platform/distribution: `Route`, `Network`
  - Automation/execution: `Bot`, `Cpu`, `Workflow`
  - Check/completion: `CheckCircle2`, `BadgeCheck`
  - Risk/negative: `AlertTriangle`, `CircleX`
  - Data/growth: `BarChart3`, `TrendingUp`
  - Capability/share/ranking: `BarChart3`, `BrainCircuit`, `Network`
  - Scene binding/categories: `Link2`, `CreditCard`, `GraduationCap`, `Landmark`, `Building2`
  - Proof/source: `ShieldCheck`, `ExternalLink`
  - AI/model/category: `BrainCircuit`, `Layers`
- Icon color follows semantic purpose: structure/numbering uses electric blue `#067EF6`; completion/result uses green `#20E0B0`; risk/negative uses red `#D83C30`; proof/recommendation uses gold `#C08A30`; model/category may use sparse purple `#663684`.
- Stickers are for status, numbers, warning, step state, or CTA emphasis.
- Corner chapter labels are for current section context, not status proof. Keep them top-left, compact, and independent from bottom captions.
- Icons and stickers must not be used to fill empty space.

## Proof Materials

Real user-provided materials are preferred over abstract packaging.

- Clear screenshot or recording: show as main screen.
- Presenter becomes lower-left vertical rounded-rectangle PiP.
- Large video assets provided as proof or demo material must play as video. Do not treat mp4/mov/webm proof assets as static images or first-frame placeholders.
- Video proof material uses `recording-proof` and `OffthreadVideo`, muted by default, so the original narration stays primary.
- After the video proof beat ends, return the presenter to fullscreen unless the next beat is another material-main scene.
- Use zoom/crop, semantic-green `#20E0B0` highlight boxes, arrows, and highlight cues to guide attention.
- If material must be read, simplify overlays and keep it on screen long enough.
- Platform cover assets are standalone designed posters by default, not video frame screenshots.
- Platform cover assets are publish-package deliverables by default, not ordinary proof material inside the video.
- Do not show poster assets in the video body unless the spoken content explicitly discusses covers, thumbnails, poster design, publishing assets, or multi-platform cover outputs.
- Exception for thumbnail/poster-focused projects: if the entire topic is cover/poster generation and the user provides 2-3 poster exports, the opening may use a right-side poster stack preview with one-by-one pop-in. This is not considered decorative because posters are the subject of the video.
- For multi-platform cover proof, prefer designed poster exports such as `poster_16x9`, `poster_3x4`, and `poster_4x3`. Use video-frame screenshots only when the user explicitly asks for frame-based covers or no poster asset exists.
- Poster and cover exports must keep their native aspect ratio on screen. A 16:9 poster should use a wide 16:9 rectangle, a 4:3 poster should use a 4:3 rectangle, and a 3:4 poster should use a vertical 3:4 rectangle. Do not wrap them in one-size-fits-all frames, letterboxed placeholder boxes, or borders that are not the same ratio as the image.
- For poster stacks, the visible surface is the poster itself plus neutral shadow. Avoid extra frames unless the user asks for a framed gallery style.
- When designed posters are missing, derive a short `posterTopicKeyword` from the video theme and call `ngg-koubo-poster` to generate the poster set before using `cover-gallery`.
- Material-main scenes enter focus mode by default: suppress normal side HUD panels, process cards, automation panels, platform fan-outs, and generic big titles unless the event is explicitly `proof-focus`, `proof-material`, or `material-main`.
- During focus mode, keep only the readable material, presenter PiP, bottom caption, and proof-specific highlights or labels.
- The template supports three material-main layout branches:
  - `single-proof`: one clear screenshot/image fills the material board with clean highlight.
  - `cover-gallery`: 2-3 standalone poster or platform-cover exports appear as a staggered gallery; use `assetStack`; only use this when covers/posters are the current spoken topic.
  - `recording-proof`: a screen-recording or backend screenshot style with browser chrome, state highlight, and verification label.
- If no real material exists, downgrade to big text, process steps, icons, and captions.
- Do not invent fake screenshots, fake data, or fake proof.

## Presenter Safe Area

Protect face, mouth, eyes, and key hand gestures.

- Hook: presenter may be large if it supports emotion and presence.
- Proof: material may be main screen, presenter in lower-left PiP.
- Process: presenter may remain fullscreen unless a large material or diagram needs the main screen.
- CTA: presenter returns to a dominant or clear speaking layout.
- Presenter movement must be semantic by scene type, not arbitrary empty-space chasing.
