param([string]$OutputDirectory = 'backups')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$resolved = Join-Path $root $OutputDirectory
New-Item -ItemType Directory -Force -Path $resolved | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$target = Join-Path $resolved "weather-signals-$stamp.dump"
$containerPath = "/tmp/weather-signals-$stamp.dump"
docker compose exec -T postgres pg_dump -U weather_signals -d weather_signals -Fc --file=$containerPath
docker compose cp "postgres:$containerPath" $target
docker compose exec -T postgres rm -f $containerPath
Write-Host "Backup written to $target"
