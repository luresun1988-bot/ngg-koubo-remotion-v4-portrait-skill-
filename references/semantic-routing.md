# V4 Semantic Routing

Use this reference when creating or rebuilding `semanticBeats` and `visualEvents`.

Treat the first source-bound theme thesis separately from the absolute opening. Mark one eligible beat with `themeThesisCandidate=true`, `suggestedDepthKeyword`, and `requiresApproval=true`; never create `depthKeyword` automatically. The first strong presenter-led question, problem framing, core judgement, contrast, transformation, or result promise may become a candidate. If the opening first shows result/proof material, preserve the proof and defer the candidate until the first eligible fullscreen/large presenter thesis. Greetings, setup filler, ordinary workflow steps, and tool names do not qualify.

V4 chooses HUD by spoken meaning first, then by component type. The required pipeline is:

```text
real transcript/timecodes
  -> captionCues
  -> semanticBeats
  -> visualEvents
  -> Remotion render
```

Run the semantic pipeline in this order:

```text
python scripts/semantic_router.py --visual-script 06_remotion/visual_script.json
python scripts/visual_event_builder.py --visual-script 06_remotion/visual_script.json
python scripts/validate_visual_script.py 06_remotion/visual_script.json
python scripts/qa_lint_visual_script.py --visual-script 06_remotion/visual_script.json --remotion-root 06_remotion --out 06_remotion/qa/pre_render_lint.md
```

For Skill/template changes to routing logic, also run:

```text
python scripts/semantic_router_regression.py
python scripts/sfx_semantic_routing_regression.py
```

## Confirmed V1 Routes

| semanticIntent | Typical spoken meaning | visualForm | Preferred event |
|---|---|---|---|
| `negative-friction` | still manual, repeated, inefficient, risky, too slow | `redWarningCard` | `semanticProblemMap` |
| `negative-to-positive` | not A but B; pain then spoken resolution | `redWarningToGreenConfirm` | `semanticProblemMap` |
| `manual-field` | repeated title, intro, tag, cover, field filling, local directory/field checks | `infoCard` | right-side status timeline plus `FIELDS` file-tree rows |
| `automation-handoff` | Codex/system takes over the task | `automationHandoff` | `automationHandoff` |
| `platform-fanout` | distribute one package to named or abstract channels | `platformFanout` | `platformFanout` |
| `asset-variants` | horizontal/vertical/square posters, multi-size covers | `ratioGallery` | `ratioGallery` |
| `numeric-metric` | percentages, counts, ratios, scale, minutes, seconds | `dataPunch` | `dataPunch` |
| `capability-share` | capability, market share, ranking, leader comparison | `capabilityShare` | `capabilityShare` |
| `scene-lock` | scenario, industry, local usage, where it lands | `sceneLockGrid` | `sceneLockGrid` |
| `transformation-stack` | sourced A to B, sourced driver, explicit sourced result | `transformationStack` | `transformationStack`; explicit `captionHighlight` fallback when incomplete |
| `proof-material` | screen recording, screenshot, backend, generated result | `materialMain` or proof sticker | `materialMain` / `statusSticker` |
| `cta-resolve` | comment keyword, claim, self-pickup, follow-up action | `ctaTitle` | `ctaTitle` |
| `enumeration` | first/second/third, steps, directions, numbered actions | `numberedList` | `statusStack` / `flowPath` |
| `workflow-step` | sourced input, setting, conditional next action, or generation process | `flowPath` | `flowPath` |
| `positive-confirm` | finished, completed, automated, solved | `greenConfirmCard` | `captionHighlight` |
| `result-promise` | opening promise, contrarian hook, result claim | `bigJudgement` | `kineticTitle` |
| `topic-intro` | this episode discusses/introduces one subject | `topicKeyword` | `topicKeyword` |
| `explanation-claim` | ordinary explanation, definition, or low-confidence claim | `claimStrip`, `sourceBoundSticker`, or `intentionalCleanHold` | strongest readable claim uses `claimStrip`; short claims use `statusSticker`; lower-priority repeats stay clean |

## Presenter-impact semantic binding

- Add `presenter-impact-punch` only as a sparse camera companion to a selected high-priority visible semantic event: `pain-question`, `theme-thesis`, `negative-friction`, `negative-to-positive`, `result-promise`, or asserted `positive-confirm`.
- Numeric data alone, workflow/enumeration, automation handoff, ordinary explanation, proof/material focus, topic/tool naming, and `cta-resolve` do not qualify. A numeric event may be the visible companion only when the same sourced beat independently carries an approved strong judgement/result role on the camera event.
- In the default lifecycle-synced form, copy the companion's `sceneId`, `sourceBeatId`, `startFrame`, and `endFrame` exactly onto the `presenterReposition` event. The semantic event is the master clock: camera entry starts with it, peak holds through its readable phase, and camera return uses its exit window.
- Do not add camera impact to every eligible beat. Preserve about eight seconds between impact starts and at most three in a rolling minute; choose the strongest beats after material/PiP and other camera conflicts are removed.

## Routing Priority

- Negative plus an asserted solution becomes `negative-to-positive`; pure negative and prospective completion stay red-only.
- Completion polarity is mandatory. Only asserted completion such as `已经完成`, `生成好了`, or `流程跑完` may route to green confirmation. `还没完成`, `如果完成设置`, `完成按钮`, future/planned completion, partial completion, and unresolved completion must not use `positive-confirm`.
- Strong proof words such as screenshot, recording, backend, or result proof beat generic completion words such as "跑通".
- Real-project opening guards: only the first strong hook sentence should use the Hook scene fallback as `result-promise`. Later setup lines in the same Hook scene must be routed by their own text, so an account-status warning can become `negative-friction` instead of a second or third big title.
- Proof routing requires strong proof language such as recording, screenshot, backend demonstration, proof, measured result, or page result. Do not route ordinary page-reading or webpage-handoff text to `proof-material` unless real proof material is available.
- Numeric metrics beat generic negative mood words. A sentence like "directly shocked: answer 100 questions" must stay `numeric-metric` instead of being swallowed by a neighboring negative beat.
- Multi-size asset signals require size/form words such as horizontal, vertical, square, multi-size, or three-size. A lone "cover" or "main image" is not enough.
- Numbered words such as "第一/第二/第三" beat broad transformation words unless the sentence also contains a clear transformation relation such as "从", "变成", "到", "团队", "杠杆", or "护城河".
- Capability, scene binding, and transformation routes must beat generic cards. Do not silently collapse them to `infoCard`; an evidence-incomplete transformation may use only the explicit audited `captionHighlight` fallback described above.
- CTA routing requires an explicit viewer-directed action such as `评论区回复…`, `评论区扣…`, `私信我`, `关注我/关注一下`, `收藏这一条`, or `直接领取`. Bare `评论区`, `关键词`, `关注`, or `自提` nouns are not enough; `页面展示了评论区互动数据`, `输入关键词生成标题`, and `门店支持到店自提` are not CTA.
- Future episode previews such as "下一期会介绍", "下期将拆解", or "下一条讲" are `explanation-claim` unless the same source text contains an explicit CTA action. Words such as "自动剪辑" inside a future preview do not mean completed automation or a present-tense handoff.
- Do not route a broad token alone. `从官网下载` is not transformation, `发布前检查` is not platform fan-out, and `模型文件` is not capability/share.
- Unknown or low-confidence spoken copy defaults to `explanation-claim`, never to a fabricated workflow diagram. Keep only the strongest readable claim in one scene as `claimStrip`; route a short claim to a source-bound `statusSticker`; mark lower-priority repeated claims as `intentionalCleanHold`.
- Treat clean holds as audited semantic decisions, not missing work. They are valid only for low-confidence `explanation-claim` beats with `requiredChecks` containing `intentional-clean-hold`; high-confidence numeric, process, contrast, proof, completion, or CTA beats must still render their matching semantic component.
- Do not use component roulette to break repetition. Keep at most two consecutive `claimStrip` main HUDs, then reduce/suppress lower-priority ordinary claims until a more specific semantic event resets the run.
- Record compound meaning in `semanticModifiers` and `entities`. For example, `10 张高清详情图已经自动生成好了` keeps `numeric-metric` as the primary intent plus `numeric`, `completed`, and `automated` modifiers.
- Numeric meaning remains primary across completion polarity. `10张详情图还没生成完` stays `numeric-metric`, adds `incomplete`, requires `negative-incomplete-treatment`, and renders `未完成` without green styling.
- A handoff is separate from completion. `把素材交给 Codex 自动完成` is `automation-handoff` with processing treatment; `Codex 还没有接管这一步` is `negative-friction`.
- The format-agnostic guards live in `scripts/semantic_guardrails.py` and are mirrored into every generated project. Landscape and portrait share polarity, future/topic, handoff, process, proof, explanation, and explicit-viewer-CTA predicates; only their component adapters differ.
- Component data must come from transcript entities, provided assets, or explicit user input. Do not invent platform names, brands, percentages, state labels, or transformation drivers.
- Generate `transformationStack` only when its source beat formally owns caption evidence for one source state, one target state, one or two drivers, and one explicit result. A target state is not a separate result.
- Every transformation step must carry `role`, a short `label`, exact source `text`, and non-empty `sourceCueIds`; all cited cues must belong to the same source beat and scene. `transformationSourceCueIds` must equal their ordered union.
- Do not scan uncited previous cues for drivers and do not synthesize copy such as `目标状态达成`. Missing relation, driver, result, or provenance must produce the audited `captionHighlight` fallback with a specific `fallbackReason`.
- Preserve complete numeric entities and suffixes. `2K`, `1k`, `30%`, and `3倍` must keep their suffix in `entities` and the generated numeric fields; normalize lowercase `k/m/g` to uppercase for display without dropping it.
- Build CTA title, subtext, status, action, and keyword only from the source beat. Generated CTA events must record `ctaProvenance.sourceText`; record `action` or `keyword` only when it appears in that source text.
- CTA has scheduling priority at the end of a scene. If an earlier left-lane HUD would push a sourced CTA below the readable minimum or remove it, trim/drop the earlier HUD and preserve the CTA with the lane buffer.

## Timing Anchor

Generated HUD events should start near the caption cue containing the visible HUD keyword, not always at the beginning of a multi-cue beat.

## SFX Suggestions

`visual_event_builder.py` also derives review-only SFX cues from confirmed semantic beats and their routed visual events. These cues use `status: "suggested"` and must not render audio until explicitly reviewed and changed to `active`.

Confirmed SFX suggestion routes:

| semanticIntent / event | suggested sfxIntent | suggested sfxId |
|---|---|---|
| `result-promise` + `kineticTitle` / `bigJudgement` | `title_impact` | `title_impact_whoosh_01` |
| `negative-friction` / `negative-to-positive` | `negative_warning` | `negative_warning_01` |
| `positive-confirm` | `confirm` | `confirm_ding_01` |
| `automation-handoff` | `automation_handoff` | `automation_handoff_01` |
| `numeric-metric` / `dataPunch` | `data_count` | `data_count_01` |
| `proof-material` / proof-focused material event | `proof_reveal` | `proof_reveal_01` |

When the builder shifts an event to the cue keyword, it records:

```json
{
  "timingAnchor": "captionCueKeyword",
  "anchorCueId": "cap-012"
}
```

## HUD Copy Rules

- HUD copy is not a subtitle. Compress it to the key idea and keep the full sentence in bottom captions.
- HUD copy compression must preserve semantic polarity. Negative phrases such as `不可能手动做` must not lose `不`, and account/status failure phrases such as `账号未转正` should compress to the decisive phrase instead of the whole spoken sentence.
- Negative and contrast beats use white base text plus red emphasis. Confirm/result beats use white base text plus green emphasis. Structural labels use blue.
- Use `emphasisWords` for 1-3 visible HUD keywords. These words must appear in the HUD copy.
- Bottom captions stay all-white and complete.

## QA Contract

Every generated `visualEvent` that fulfills a semantic beat must keep:

```json
{
  "sourceBeatId": "beat-001",
  "beatGroupId": "scene-001-beat-001"
}
```

The regression suite currently covers 123 positive, compound, adversarial, future-preview, numeric-suffix, real-project, short-tail, shared guard, and complete-evidence transformation examples. `semantic_component_contract_regression.py` additionally checks canonical event types, source-bound short-claim downgrade, same-scene claim selection, the two-claim run limit, no invented platforms/brands/states/ratios, CTA provenance and scheduling priority, approval-gated theme-thesis candidates, transformation provenance/fallback behavior, and schema/renderer type parity. The SFX regression suite covers the six confirmed semantic audio suggestions and requires `status: "suggested"`. A route change should update the tests and this document in the same commit.
