# V4 Audio Policy

Use this reference before adding or changing audio.

## Priority

Voice is always primary.

Audio priority:

1. Narration or presenter voice.
2. Necessary original source sound.
3. Semantic SFX.
4. Default BGM bed or optional AI-generated BGM.

If an audio layer competes with voice clarity, reduce it or remove it.

## Presenter continuity

- Keep one continuous presenter playback source for the full composition.
- For one source video, `presenterAudio.mode=embedded` may keep its original audio.
- For segmented presenters, normalize every segment to the composition FPS, concatenate one video-only H.264 MP4, create one exact 48 kHz stereo PCM16 WAV, and mount that WAV once with the video muted.
- Do not stream-copy multiple MP4 containers with independent AAC tracks. AAC encoder delay and padding can accumulate at segment boundaries and cause lip-sync drift.
- Use a non-zero `syncOffsetFrames` only for a measured constant offset, only with `normalized-wav`, and record `syncEvidence`. Never use it to hide cumulative drift.
- Require `qa/media/presenter_normalization.json` with exact decoded video-frame and WAV-sample evidence before rendering segmented presenters.

## SFX

SFX is optional and semantic.

Allowed default cue types:

- Big title impact.
- Keyword second-pop.
- Step completion.
- Proof material appearing.
- Platform fan-out.
- Automation handoff.
- CTA resolution.

SFX tone:

- Short.
- Technology-oriented.
- Clean click, tap, soft hit, short whoosh, or confirmation.

Rules:

- Maximum one prominent SFX per spoken phrase.
- Keep SFX short and below narration.
- Do not add SFX to every visual change.
- Do not add SFX to hide weak motion design.
- If a manifest exists, reference by `sfxId`, not ad hoc file path.
- If no manifest is configured, write `sfxIntent` and leave selection pending.
- If no audio `path` is present, set `status` to `pending-selection`, `pending-generation`, `disabled`, or `muted`; the Remotion template will not render that cue.
- Align active SFX near a visual event boundary, usually within 8 frames of the event start or internal step impact.
- The six manifest-backed mastered library SFX default to `-5 dB`, matching the user-approved audition. Unregistered or ad hoc SFX must stay at or below `-14 dB` until separately auditioned and approved.
- Keep most SFX under 1.2 seconds. Longer risers or whooshes need an explicit reason in `notes`.

Recommended `sfxIntent` values:

- `title_impact`
- `keyword_pop`
- `step_complete`
- `proof_reveal`
- `platform_fanout`
- `automation_handoff`
- `cta_resolve`
- `soft_whoosh`
- `ui_tick`
- `confirm`

Example manifest shape:

```json
{
  "version": 1,
  "items": [
    {
      "sfxId": "ui_tick_01",
      "intent": "ui_tick",
      "path": "input/audio/sfx/ui_tick_01.wav",
      "durationFrames": 8,
      "defaultVolumeDb": -24
    }
  ]
}
```

When a manifest is configured, project scripts may map `sfxIntent` to `sfxId` and `path`, then keep the original `sfxIntent` for QA readability. Semantic routing defaults to `status: "suggested"` for generated SFX cues; suggested cues are review records and must not render audio until a human changes the cue to `status: "active"`.

Confirmed default SFX:

| sfxId | Intent | Default volume | Use |
| --- | --- | --- | --- |
| `automation_handoff_01` | `automation_handoff` | `-5 dB` | Manual task handed to Codex/AI/system, workflow takeover, or automation start. |
| `confirm_ding_01` | `confirm` | `-5 dB` | Positive completion, correct result, green check, workflow completed, or recommendation confirmed. |
| `data_count_01` | `data_count` | `-5 dB` | Numeric count-up, percentage growth, 5x, question count, or data punch HUD. |
| `negative_warning_01` | `negative_warning` | `-5 dB` | Red warning card, failed status, account problem, risk, wrong path, or blocked workflow. |
| `proof_reveal_01` | `proof_reveal` | `-5 dB` | Screenshot, recording, evidence window, result board, or Before/Now comparison reveal. |
| `title_impact_whoosh_01` | `title_impact` | `-5 dB` | Opening big-opinion title, major judgement, or keyword scale-up landing. Trigger slightly before the keyword/title visual landing. |

`automation_handoff_01` is a user-confirmed AI-generated WAV. Use it for handoff/takeover semantics, not final completion, title impact, or generic transition sweeps.
`data_count_01` is a user-confirmed AI-generated WAV. Use it for numeric/data semantics, not generic card entrances.
`proof_reveal_01` is a user-confirmed AI-generated WAV. Use it only when real proof material appears.
`title_impact_whoosh_01` is a user-confirmed AI-generated WAV. It is longer than most SFX at about 2 seconds, so use it sparingly and only for major opening or chapter-level beats.
`confirm_ding_01` is a user-confirmed AI-generated WAV. Use it for success/completion semantics, not for title impact, warning, or ordinary list ticks.
`negative_warning_01` is a user-confirmed AI-generated WAV. Use it only once per spoken warning/error beat.

All six library WAVs are mastered with `+18 dB` pre-gain and a `-1 dBFS` peak limiter before the `-5 dB` cue gain is applied. This asset-plus-cue combination is the approved contract; replacing a WAV requires a new loudness test and audition.

## BGM

BGM uses the shared V4 default music bed unless a project disables it or selects a project-specific track.

`project_config.json` controls:

- `bgmEnabled`
- `bgmPath`
- target style
- target BPM
- ducking rule

Default template path:

```text
input/audio/bgm/default_bgm.mp3
```

Do not invent other BGM paths. If a project disables default BGM or needs a different track but no file exists, record it as pending in the visual script and QA report.

The Remotion template renders BGM/SFX only when an `audioCues` item has a real `path` and is not suggested/pending/disabled/muted.

Default BGM cue:

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

## Ducking

Default mix policy:

- Voice remains clear at all times.
- SFX under dense speech should be reduced further.
- BGM, when present, must duck under speech.
- Clean material source audio should be intentionally retained, muted, or mixed; do not leave it accidental.

Current template support:

- SFX and BGM cues with real `path` values render through Remotion `Audio`.
- `volumeDb` is converted to linear volume.
- `fadeInFrames` and `fadeOutFrames` are frame-driven.
- `pending-selection`, `pending-generation`, `disabled`, `muted`, `source`, and `silence` cues are documentation/QA records and do not render added audio.
- The template does not yet do automatic voice-reactive ducking; use conservative `volumeDb` values and record any required manual mix notes.

## Audio QA

Check:

- Final render has an audio stream when expected.
- Audio duration covers the full video.
- Voice is not masked by SFX/BGM.
- Source sound is preserved only where intended.
- SFX and BGM paths exist if enabled.
- Every non-original SFX or BGM has a source or generation record when used in final output.
- `audio-sfx-volume`: the six registered mastered SFX are not louder than `-5 dB`; unregistered SFX are not louder than `-14 dB`.
- `audio-bgm-volume`: BGM is not louder than `-20 dB`.
- `audio-sfx-sync`: active SFX is close to a semantic visual event boundary.
- `audio-sfx-density`: SFX are not stacked on every small motion beat.
- `presenter-continuity`: the presenter video is mounted once and remains frame-continuous across scene/layout boundaries.
- `presenter-normalized-wav`: segmented presenter audio is 48 kHz stereo PCM16 with the reported exact sample count, while the combined presenter MP4 is video-only.
