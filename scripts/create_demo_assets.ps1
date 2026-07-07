param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$InputDir = Join-Path $RepoRoot "public\input"
New-Item -ItemType Directory -Force -Path $InputDir | Out-Null

$MainVideo = Join-Path $InputDir "main.mp4"
$ProofImage = Join-Path $InputDir "proof.png"

if ($Force -or -not (Test-Path -LiteralPath $MainVideo)) {
  ffmpeg -hide_banner -loglevel error -y `
    -f lavfi -i "color=c=0x111418:s=1080x1920:r=25:d=36" `
    -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=48000" `
    -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac $MainVideo | Out-Null
}

if ($Force -or -not (Test-Path -LiteralPath $ProofImage)) {
  ffmpeg -hide_banner -loglevel error -y `
    -f lavfi -i "testsrc2=size=1280x720:rate=25:duration=1" `
    -frames:v 1 $ProofImage | Out-Null
}

Write-Host "Demo assets ready:"
Write-Host "  $MainVideo"
Write-Host "  $ProofImage"

