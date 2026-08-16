$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$api = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$root\scripts\start-api.ps1`""
$worker = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$root\scripts\start-worker.ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 365) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'AIWeatherSignals-API' -Action $api -Trigger $trigger -Settings $settings -Description 'ProjectEOL observed weather API' -Force
Register-ScheduledTask -TaskName 'AIWeatherSignals-Worker' -Action $worker -Trigger $trigger -Settings $settings -Description 'ProjectEOL public weather signal worker' -Force
Write-Host 'Registered AIWeatherSignals-API and AIWeatherSignals-Worker. Run scripts\enable-services.ps1 to start them.'
