$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'service-processes.ps1')
foreach ($name in @('AIWeatherSignals-API', 'AIWeatherSignals-Worker')) {
    Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    Enable-ScheduledTask -TaskName $name | Out-Null
}
Stop-AIWeatherSignalsProcesses
foreach ($name in @('AIWeatherSignals-API', 'AIWeatherSignals-Worker')) { Start-ScheduledTask -TaskName $name }
Write-Host 'AI Weather Signals API and worker are enabled and starting.'
