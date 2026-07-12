param(
  [Parameter(Mandatory = $true)]
  [string]$RemotionRoot,
  [string]$VisualScript = "visual_script.json",
  [string]$Output = "out/final.mp4",
  [string]$CompositionId = "NGGKouboV4Portrait",
  [int]$Concurrency = 1,
  [string]$RawInput = "",
  [switch]$PostprocessOnly,
  [switch]$KeepRaw,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $RemotionRoot).Path

function Resolve-ProjectPath([string]$Value) {
  if ([System.IO.Path]::IsPathRooted($Value)) {
    return [System.IO.Path]::GetFullPath($Value)
  }
  return [System.IO.Path]::GetFullPath((Join-Path $root $Value))
}

function Invoke-Step([string]$Label, [scriptblock]$Command) {
  Write-Host "[$Label]"
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE"
  }
}

$visualScriptPath = Resolve-ProjectPath $VisualScript
$outputPath = Resolve-ProjectPath $Output
if (-not (Test-Path -LiteralPath $visualScriptPath -PathType Leaf)) {
  throw "Missing visual script: $visualScriptPath"
}
if ((Test-Path -LiteralPath $outputPath) -and -not $Force) {
  throw "Output exists; pass -Force to replace: $outputPath"
}
if ((Test-Path -LiteralPath $outputPath) -and $Force) {
  Remove-Item -LiteralPath $outputPath -Force
}
$outputDir = Split-Path -Parent $outputPath
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$generatedRaw = -not $PostprocessOnly
if ($PostprocessOnly) {
  if (-not $RawInput) {
    throw "-PostprocessOnly requires -RawInput"
  }
  $rawPath = Resolve-ProjectPath $RawInput
} else {
  $rawPath = [System.IO.Path]::Combine(
    $outputDir,
    ([System.IO.Path]::GetFileNameWithoutExtension($outputPath) + ".remotion-raw.mp4")
  )
}
if (-not $generatedRaw -and -not (Test-Path -LiteralPath $rawPath -PathType Leaf)) {
  throw "Missing raw input: $rawPath"
}
if ($generatedRaw -and (Test-Path -LiteralPath $rawPath)) {
  Remove-Item -LiteralPath $rawPath -Force
}

$python = (Get-Command python -ErrorAction Stop).Source
$npxCommand = Get-Command npx.cmd -ErrorAction SilentlyContinue
if (-not $npxCommand) {
  $npxCommand = Get-Command npx -ErrorAction Stop
}
$npx = $npxCommand.Source

Push-Location $root
try {
  if (-not $PostprocessOnly) {
    Invoke-Step "validate visual script" {
      & $python "scripts/validate_visual_script.py" $visualScriptPath
    }
    Invoke-Step "pre-render QA" {
      & $python "scripts/qa_lint_visual_script.py" --visual-script $visualScriptPath --remotion-root $root --out "qa/pre_render_lint.md"
    }
    Invoke-Step "generate Remotion data" {
      & $python "scripts/write_generated_visual_script.py" --visual-script $visualScriptPath --out "src/generatedVisualScript.ts"
    }
    Invoke-Step "TypeScript" {
      & npm run typecheck --silent
    }
    Invoke-Step "Remotion render" {
      & $npx remotion render src/index.ts $CompositionId $rawPath --codec=h264 --audio-codec=aac --pixel-format=yuv420p --concurrency=$Concurrency --gl=angle
    }
  }

  Invoke-Step "BT.709 postprocess" {
    & $npx remotion ffmpeg -hide_banner -loglevel error -y -i $rawPath `
      -map 0:v:0 -map 0:a:0 `
      -vf "scale=out_range=tv:out_color_matrix=bt709,format=yuv420p" `
      -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p `
      -color_range tv -colorspace bt709 -color_trc bt709 -color_primaries bt709 `
      -x264-params "colorprim=bt709:transfer=bt709:colormatrix=bt709" `
      -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart $outputPath
  }

  Invoke-Step "final media QA" {
    & $python "scripts/final_media_qa.py" --video $outputPath --visual-script $visualScriptPath --out "qa/final_media_qa.md" --json-out "qa/final_media_qa.json"
  }
} catch {
  if (Test-Path -LiteralPath $outputPath) {
    $failedPath = Join-Path `
      (Split-Path -Parent $outputPath) `
      (([System.IO.Path]::GetFileNameWithoutExtension($outputPath)) + ".failed" + ([System.IO.Path]::GetExtension($outputPath)))
    if (Test-Path -LiteralPath $failedPath) {
      Remove-Item -LiteralPath $failedPath -Force
    }
    Move-Item -LiteralPath $outputPath -Destination $failedPath
    Write-Warning "Failed output retained for diagnosis: $failedPath"
  }
  throw
} finally {
  Pop-Location
}

if ($generatedRaw -and -not $KeepRaw -and (Test-Path -LiteralPath $rawPath)) {
  Remove-Item -LiteralPath $rawPath -Force
}
Write-Host "Final delivery passed: $outputPath"
