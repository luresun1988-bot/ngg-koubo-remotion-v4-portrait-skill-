param(
  [string]$RemotionRoot = ".",
  [string]$VisualScript = "visual_script.json",
  [string]$CompositionId = "NGGKouboV4Portrait",
  [int]$MaxPreviews = 12
)

$ErrorActionPreference = "Stop"
$ScriptRoot = $PSScriptRoot
$RemotionRoot = [System.IO.Path]::GetFullPath($RemotionRoot)
$VisualScriptPath = if ([System.IO.Path]::IsPathRooted($VisualScript)) {
  [System.IO.Path]::GetFullPath($VisualScript)
} else {
  Join-Path $RemotionRoot $VisualScript
}
$PlanPath = Join-Path $RemotionRoot "qa\motion_previews\plan.json"

python (Join-Path $ScriptRoot "build_motion_preview_plan.py") `
  --visual-script $VisualScriptPath `
  --out $PlanPath `
  --max-previews $MaxPreviews
if ($LASTEXITCODE -ne 0) { throw "motion preview planning failed" }

$Plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
Push-Location $RemotionRoot
try {
  foreach ($Preview in $Plan.previews) {
    $OutputPath = Join-Path $RemotionRoot ([string]$Preview.outputPath)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
    $LastFrame = [Math]::Max([int]$Preview.startFrame, [int]$Preview.endFrame - 1)
    npx remotion render src/index.ts $CompositionId $OutputPath `
      --frames="$($Preview.startFrame)-$LastFrame" `
      --codec=h264 `
      --audio-codec=aac `
      --crf=28 `
      --concurrency=1 `
      --gl=angle
    if ($LASTEXITCODE -ne 0) { throw "motion preview render failed: $($Preview.id)" }
  }
}
finally {
  Pop-Location
}

Write-Host "Motion previews rendered: $PlanPath"
