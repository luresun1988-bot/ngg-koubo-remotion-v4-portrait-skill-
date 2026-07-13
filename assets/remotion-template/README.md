# NGG Koubo Remotion V4 Template

完整 V4 Remotion 工程模板。目标是新电脑 clone 后，可以恢复并运行当前 V4 口播剪辑效果：语义 HUD、红/绿对比卡、数据动效、流程节点、素材主屏/PiP、单行字幕、思源黑体、QA lint 和组件样式库。

## Requirements

- Windows / macOS / Linux
- Node.js 20+
- Python 3.10+
- FFmpeg in `PATH`

## Quick Start

```powershell
git clone <your-github-url> ngg-koubo-remotion-v4-portrait-template
cd ngg-koubo-remotion-v4-portrait-template
npm install
npm run demo:assets
npm run data:example
npm run validate
npm run qa:example
npm run typecheck
npm run still
```

The default still output is:

```text
out/still.png
```

Render the sample video:

```powershell
npm run render
```

## Repository Contents

- `src/`: Remotion V4 composition and component system.
- `config/visual_script.example.json`: runnable example visual script.
- `config/project_config.example.json`: project config shape.
- `public/fonts/`: bundled Chinese fonts, including Source Han Sans SC.
- `public/input/`: local demo/source media folder. Generated media is ignored by Git.
- `scripts/`: V4 generation, validation, QA, caption splitting, and media utilities.
- `references/`: V4 workflow, visual system, motion system, semantic routing, QA, forbidden rules, and audio policy.
- `component-gallery/`: fixed component sample gallery for reviewing V4 visual styles.

## Standard Workflow

For a real project:

1. Copy or clone this repository into the project Remotion workspace.
2. Put source media under `public/input/` and proof media under `public/materials/`.
3. Create or update `visual_script.json`.
4. Run:

```powershell
python scripts/semantic_router.py --visual-script visual_script.json
python scripts/visual_event_builder.py --visual-script visual_script.json
python scripts/split_caption_cues.py --visual-script visual_script.json
python scripts/validate_visual_script.py visual_script.json
python scripts/qa_lint_visual_script.py --visual-script visual_script.json --remotion-root .
python scripts/write_generated_visual_script.py --visual-script visual_script.json --out src/generatedVisualScript.ts
npm run typecheck
npm run render
```

## Component Gallery

Render stills for the component style library:

```powershell
npm run gallery
```

Render a gallery MP4:

```powershell
npm run gallery:video
```

Outputs are generated under `component-gallery/renders/` and are ignored by Git.

## What Is Committed

Committed:

- Remotion source code
- V4 scripts
- V4 references/docs
- bundled fonts
- example configs/scripts
- component gallery definitions

Ignored:

- `node_modules/`
- render outputs
- generated demo assets
- large source media
- per-project previews/QA frames
- `.env` files

## GitHub Setup

This machine does not currently have GitHub CLI installed. After creating an empty GitHub repository, push with:

```powershell
git remote add origin https://github.com/<owner>/ngg-koubo-remotion-v4-portrait-template.git
git branch -M main
git push -u origin main
```
