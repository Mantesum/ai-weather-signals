$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'service-processes.ps1')
foreach ($name in @('AIWeatherSignals-API', 'AIWeatherSignals-Worker')) {
    Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    Disable-ScheduledTask -TaskName $name | Out-Null
}
Stop-AIWeatherSignalsProcesses
Write-Host 'AI Weather Signals API and worker are stopped and disabled.'
