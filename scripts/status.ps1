$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
docker compose ps
try { Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 5 | ConvertTo-Json -Depth 5 }
catch { Write-Warning "API unavailable: $($_.Exception.Message)" }
try { Invoke-RestMethod -Uri 'http://127.0.0.1:8080/health' -TimeoutSec 5 | ConvertTo-Json }
catch { Write-Warning "LLM unavailable: $($_.Exception.Message)" }
Get-ScheduledTask -TaskName 'AIWeatherSignals-*' -ErrorAction SilentlyContinue | Get-ScheduledTaskInfo
