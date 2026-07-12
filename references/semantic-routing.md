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
| `transformation-stack` | from A to B, individual to team, driver to result | `transformationStack` | `transformationStack` |
| `proof-material` | screen recording, screenshot, backend, generated result | `materialMain` or proof sticker | `materialMain` / `statusSticker` |
| `cta-resolve` | comment keyword, claim, self-pickup, follow-up action | `ctaTitle` | `ctaTitle` |
| `enumeration` | first/second/third, steps, directions, numbered actions | `numberedList` | `statusStack` / `flowPath` |
| `positive-confirm` | finished, completed, automated, solved | `greenConfirmCard` | `captionHighlight` |
| `result-promise` | opening promise, contrarian hook, result claim | `bigJudgement` | `kineticTitle` |
| `topic-intro` | this episode discusses/introduces one subject | `topicKeyword` | `topicKeyword` |
| `explanation-claim` | ordinary explanation, definition, or low-confidence claim | `claimStrip` | `claimStrip` |

## Routing Priority

- Negative plus explicit automation/completion becomes `negative-to-positive`; pure negative stays red-only.
- Strong proof words such as screenshot, recording, backend, or result proof beat generic completion words such as "跑通".
- Real-project opening guards: only the first strong hook sentence should use the Hook scene fallback as `result-promise`. Later setup lines in the same Hook scene must be routed by their own text, so an account-status warning can become `negative-friction` instead of a second or third big title.
- Proof routing requires strong proof language such as recording, screenshot, backend demonstration, proof, measured result, or page result. Do not route ordinary page-reading or webpage-handoff text to `proof-material` unless real proof material is available.
- Numeric metrics beat generic negative mood words. A sentence like "directly shocked: answer 100 questions" must stay `numeric-metric` instead of being swallowed by a neighboring negative beat.
- Multi-size asset signals require size/form words such as horizontal, vertical, square, multi-size, or three-size. A lone "cover" or "main image" is not enough.
- Numbered words such as "第一/第二/第三" beat broad transformation words unless the sentence also contains a clear transformation relation such as "从", "变成", "到", "团队", "杠杆", or "护城河".
- Capability, scene binding, and transformation routes must beat generic cards. Do not silently collapse them to `infoCard`.
- CTA words must be action-specific: "评论区", "领取", "自提", "告诉我", "私信", "关键词", "关注", "点赞", or "收藏". Do not route every "需要" to CTA.
- Do not route a broad token alone. `从官网下载` is not transformation, `发布前检查` is not platform fan-out, and `模型文件` is not capability/share.
- Unknown or low-confidence spoken copy defaults to `explanation-claim -> claimStrip`, never to a fabricated workflow diagram.
- Record compound meaning in `semanticModifiers` and `entities`. For example, `10 张高清详情图已经自动生成好了` keeps `numeric-metric` as the primary intent plus `numeric`, `completed`, and `automated` modifiers.
- Component data must come from transcript entities, provided assets, or explicit user input. Do not invent platform names, brands, percentages, state labels, or transformation drivers.

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

The regression suite currently covers 104 positive, compound, adversarial, real-project, and short-tail intent-preservation examples. `semantic_component_contract_regression.py` additionally checks canonical event types, no invented platforms/brands/states/ratios, approval-gated theme-thesis candidates, and schema/renderer type parity. The SFX regression suite covers the six confirmed semantic audio suggestions and requires `status: "suggested"`. A route change should update the tests and this document in the same commit.
