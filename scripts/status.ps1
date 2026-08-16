$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
Get-ScheduledTask -TaskName 'AIWeatherSignals-*' -ErrorAction SilentlyContinue |
    Select-Object TaskName, State |
    Format-Table -AutoSize
try { Invoke-RestMethod -Uri 'http://127.0.0.1:8010/api/v1/health' -TimeoutSec 5 | ConvertTo-Json -Depth 5 }
catch { Write-Warning "API unavailable: $($_.Exception.Message)" }
try {
    $ollama = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
    $loaded = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/ps' -TimeoutSec 5
    @{
        status = 'ok'
        provider = 'ollama'
        models = @($ollama.models).Count
        loaded_models = @($loaded.models).Count
        models_in_vram = @($loaded.models | Where-Object { $_.size_vram -gt 0 }).Count
    } | ConvertTo-Json
}
catch { Write-Warning "Ollama unavailable: $($_.Exception.Message)" }
