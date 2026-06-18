# Force UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Define the source directory
$sourceDir = ".\skills\bb-huge"

# Define the target skill directories
$targetDirs = @(
    "$HOME\.gemini\skills\bb-huge",
    "$HOME\.codex\skills\bb-huge",
    "$HOME\.claude\skills\bb-huge",
    "$HOME\.skillz\skills\bb-huge",
    "$HOME\.opencode\skills\bb-huge",
    "$HOME\.antigravity\skills\bb-huge"
    "$HOME\.agents\skills\"
    "$HOME\.skills\"
    "$HOME\.skillz\"
)

Write-Host "$([char]0x2705) Syncing bb-huge skill to all agents..." -ForegroundColor Cyan

foreach ($target in $targetDirs) {

    $parentDir = Split-Path -Parent $target

    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
    }

    robocopy $sourceDir $target /MIR /NJH /NJS /NDL /NFL | Out-Null

    Write-Host "$([char]0x2705) Updated: $target" -ForegroundColor Green
}

Write-Host "$([char]0x2714) All agent directories are up to date!" -ForegroundColor Magenta