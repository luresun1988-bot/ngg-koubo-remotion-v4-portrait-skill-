param(
  [switch]$SkipVideo,
  [switch]$SkipStills,
  [switch]$Clean,
  [switch]$Smoke
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
  param(
    [scriptblock]$Command,
    [string]$Label
  )
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE"
  }
}

$GalleryRoot = $PSScriptRoot
$AssetsRoot = Split-Path -Parent $GalleryRoot
$SkillRoot = Split-Path -Parent $AssetsRoot
$TemplateRoot = Join-Path $AssetsRoot "remotion-template"
$WorkRoot = Join-Path $GalleryRoot "_work"
$RemotionRoot = Join-Path $WorkRoot "remotion"
$RenderRoot = Join-Path $GalleryRoot "renders"
$KeyframeRoot = Join-Path $RenderRoot "keyframes"
$VisualScript = Join-Path $GalleryRoot "visual_script.gallery.json"
$GallerySpec = Get-Content -LiteralPath $VisualScript -Raw -Encoding utf8 | ConvertFrom-Json

if (-not (Test-Path -LiteralPath $VisualScript)) {
  throw "Missing gallery visual script: $VisualScript"
}

if ((Test-Path -LiteralPath $WorkRoot) -and $Clean) {
  Remove-Item -LiteralPath $WorkRoot -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $RemotionRoot, $RenderRoot, $KeyframeRoot | Out-Null

Get-ChildItem -LiteralPath $TemplateRoot -Force |
  Where-Object { $_.Name -in @("config", "public", "src", "package-lock.json", "package.json", "tsconfig.json") } |
  ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $RemotionRoot -Recurse -Force
  }

Copy-Item -LiteralPath $VisualScript -Destination (Join-Path $RemotionRoot "visual_script.json") -Force

$InputDir = Join-Path $RemotionRoot "public\input"
$MaterialDir = Join-Path $RemotionRoot "public\materials"
New-Item -ItemType Directory -Force -Path $InputDir, $MaterialDir | Out-Null

$PresenterVideo = Join-Path $InputDir "gallery_presenter.mp4"
$ProofVideo = Join-Path $MaterialDir "gallery_proof.mp4"

if ($Clean -or -not (Test-Path -LiteralPath $PresenterVideo)) {
  & ffmpeg -hide_banner -loglevel error -y `
    -f lavfi -i "color=c=0x111418:s=1080x1920:r=25:d=72" `
    -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=48000" `
    -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac $PresenterVideo | Out-Null
}

if ($Clean -or -not (Test-Path -LiteralPath $ProofVideo)) {
  & ffmpeg -hide_banner -loglevel error -y `
    -f lavfi -i "testsrc2=size=1280x720:rate=25:duration=6" `
    -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=48000" `
    -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac $ProofVideo | Out-Null
}

Push-Location $RemotionRoot
try {
  if (-not (Test-Path -LiteralPath (Join-Path $RemotionRoot "node_modules"))) {
    Invoke-Checked { npm install } "npm install"
  }

  Invoke-Checked { python (Join-Path $SkillRoot "scripts\validate_visual_script.py") (Join-Path $RemotionRoot "visual_script.json") } "validate_visual_script"
  Invoke-Checked { python (Join-Path $SkillRoot "scripts\qa_lint_visual_script.py") --visual-script (Join-Path $RemotionRoot "visual_script.json") --remotion-root $RemotionRoot } "qa_lint_visual_script"
  Invoke-Checked { python (Join-Path $SkillRoot "scripts\write_generated_visual_script.py") --visual-script (Join-Path $RemotionRoot "visual_script.json") --out (Join-Path $RemotionRoot "src\generatedVisualScript.ts") } "write_generated_visual_script"
  Invoke-Checked { npm run typecheck } "npm run typecheck"

  $Frames = @(
    @{Name="001_hook_hold.png"; Frame=75},
    @{Name="002_negative_hold.png"; Frame=225},
    @{Name="003_data_punch_hold.png"; Frame=375},
    @{Name="004_flow_path_hold.png"; Frame=525},
    @{Name="005_info_card_hold.png"; Frame=675},
    @{Name="006_capability_share_hold.png"; Frame=860},
    @{Name="007_scene_lock_hold.png"; Frame=975},
    @{Name="008_transformation_stack_hold.png"; Frame=1160},
    @{Name="009_platform_fanout_hold.png"; Frame=1315},
    @{Name="010_automation_handoff_hold.png"; Frame=1460},
    @{Name="011_material_pip_hold.png"; Frame=1575},
    @{Name="012_cta_hold.png"; Frame=1725},
    @{Name="013_topic_keyword_hold.png"; Frame=1875},
    @{Name="014_claim_strip_hold.png"; Frame=2025},
    @{Name="015_ratio_gallery_hold.png"; Frame=2175}
  )

  if ($Smoke) {
    $SmokeNames = @(
      "002_negative_hold.png",
      "003_data_punch_hold.png",
      "010_automation_handoff_hold.png",
      "011_material_pip_hold.png",
      "012_cta_hold.png",
      "014_claim_strip_hold.png"
    )
    $Frames = @($Frames | Where-Object { $_.Name -in $SmokeNames })
  }

  if (-not $SkipStills) {
    foreach ($FrameSpec in $Frames) {
      $OutPath = Join-Path $KeyframeRoot $FrameSpec.Name
      Invoke-Checked { npx remotion still src/index.ts NGGKouboV4Portrait $OutPath --frame=$($FrameSpec.Frame) --gl=angle } "remotion still $($FrameSpec.Name)"
      $RenderedFile = Get-Item -LiteralPath $OutPath
      if ($RenderedFile.Length -lt 4096) { throw "Still render is unexpectedly small: $OutPath" }
      $Dimensions = (& ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 $OutPath).Trim()
      $ExpectedDimensions = "$($GallerySpec.composition.width)x$($GallerySpec.composition.height)"
      if ($Dimensions -ne $ExpectedDimensions) { throw "Still dimensions mismatch for $($FrameSpec.Name): $Dimensions != $ExpectedDimensions" }
    }
  }

  $ConcatList = Join-Path $RenderRoot "contact_sheet_inputs.txt"
  if (-not $SkipStills) {
    $Frames |
      ForEach-Object {
        $Path = (Join-Path $KeyframeRoot $_.Name).Replace("\", "/")
        "file '$Path'"
      } |
      Set-Content -LiteralPath $ConcatList -Encoding ascii

    $Columns = 3
    $Rows = [math]::Ceiling($Frames.Count / [double]$Columns)
    $TileFilter = "scale=480:-1,tile=${Columns}x${Rows}:padding=8:margin=8:color=0x101010"
    & ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i $ConcatList -vf $TileFilter -frames:v 1 -update 1 (Join-Path $RenderRoot "contact_sheet.png") | Out-Null
  }

  if (-not $SkipVideo) {
    Invoke-Checked { npx remotion render src/index.ts NGGKouboV4Portrait (Join-Path $RenderRoot "component_gallery.mp4") --gl=angle } "remotion render component_gallery"
  }
}
finally {
  Pop-Location
}

Write-Host "Component gallery rendered:"
Write-Host "  Keyframes: $KeyframeRoot"
Write-Host "  Contact sheet: $(Join-Path $RenderRoot "contact_sheet.png")"
if (-not $SkipVideo) {
  Write-Host "  Video: $(Join-Path $RenderRoot "component_gallery.mp4")"
}
