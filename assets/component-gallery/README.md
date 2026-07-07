# V4 Component Gallery

This gallery is a small, repeatable style lab for `ngg-koubo-remotion-v4`.
Use it before changing a real project when a V4 component's look, layout, or motion needs review.

## Purpose

- Preview one component family at a time.
- Separate component style problems from full-video semantic planning problems.
- Produce stable keyframes, a contact sheet, and a short gallery MP4 for review.
- Keep rendered outputs out of Git; only the source gallery script and visual script are versioned.

## Components Covered

| Segment | Component | Purpose | Status |
| --- | --- | --- | --- |
| 01 | `kineticTitle` | Hook / result promise big title | Baseline |
| 02 | `highlightBox` | Negative / pain contrast | Baseline |
| 03 | `dataPunch` | Numeric count-up / metric | Baseline |
| 04 | `flowPath` | Numbered workflow / enumeration | Scale pass |
| 05 | `infoCard` | Small field card style | Scale pass |
| 06 | `capabilityShare` | Capability/share/ranking panel | Scale pass |
| 07 | `sceneLockGrid` | Scenario/category tiles | Scale pass |
| 08 | `transformationStack` | Source -> target -> drivers -> result | Scale pass |
| 09 | `transitionPushZoom` | Platform fan-out | Scale pass |
| 10 | `captionHighlight` | Automation handoff panel | Scale pass |
| 11 | `materialMain` | Proof video main screen + presenter PiP | Baseline |
| 12 | `ctaTitle` | CTA close | Baseline |

## Run

From this directory:

```powershell
.\render_gallery.ps1
```

Optional:

```powershell
.\render_gallery.ps1 -SkipVideo
.\render_gallery.ps1 -SkipStills
.\render_gallery.ps1 -Clean
```

- `-SkipVideo`: render keyframes and contact sheet only.
- `-SkipStills`: render MP4 only, reusing existing keyframes/contact sheet.
- `-Clean`: rebuild the temporary Remotion workspace from scratch.

## Outputs

Generated files are written to:

```text
renders/
  keyframes/
  contact_sheet.png
  component_gallery.mp4
```

Temporary Remotion files are written to:

```text
_work/remotion/
```

## Review Rules

- Review keyframes first, then the MP4.
- If a component is rejected, change the component implementation and rerun the gallery before testing a real project.
- Do not judge full-video pacing from this gallery; it is for component style and motion only.
- Card-ratio lint warnings are expected in this gallery because it intentionally shows every component family; they are still hard guidance for real project videos.
- Do judge readability, entrance/exit smoothness, internal-step sequencing, face/caption safety, color usage, and whether the component visually matches its semantic role.
