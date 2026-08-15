param([Parameter(Mandatory = $true)][string]$DumpPath)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$resolved = (Resolve-Path -LiteralPath $DumpPath).Path
if ([IO.Path]::GetExtension($resolved) -ne '.dump') { throw 'Expected a .dump file.' }
Write-Warning 'Restore overwrites objects in the configured weather_signals database. Confirm the target is correct.'
$confirmation = Read-Host 'Type RESTORE to continue'
if ($confirmation -ne 'RESTORE') { throw 'Restore cancelled.' }
$containerPath = '/tmp/weather-signals-restore.dump'
docker compose cp $resolved "postgres:$containerPath"
try { docker compose exec -T postgres pg_restore -U weather_signals -d weather_signals --clean --if-exists --no-owner $containerPath }
finally { docker compose exec -T postgres rm -f $containerPath }
