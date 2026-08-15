param([Parameter(Mandatory = $true)][ValidatePattern('^v\d+\.\d+\.\d+$')][string]$Version)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
New-Item -ItemType Directory -Force -Path 'logs' | Out-Null
Start-Transcript -Path 'logs/update.log' -Append
try {
    if (git status --porcelain) { throw 'Working tree is not clean; commit or stash your changes before updating.' }
    git fetch origin --tags
    git rev-parse --verify "refs/tags/$Version" | Out-Null
    & "$root\scripts\backup.ps1"
    git switch --detach $Version
    uv sync --frozen --extra dev
    uv run alembic upgrade head
    uv run pytest
    uv run weather-signals sources check
    Write-Host "Update to $Version passed. Restart scheduled tasks or processes now."
} finally { Stop-Transcript }
