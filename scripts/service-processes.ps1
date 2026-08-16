function Stop-AIWeatherSignalsProcesses {
    $root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
    $entryPoint = Join-Path $root '.venv\Scripts\weather-signals.exe'
    $owned = Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and $_.CommandLine -and
        $_.CommandLine.Contains($entryPoint, [StringComparison]::OrdinalIgnoreCase)
    }
    foreach ($process in ($owned | Sort-Object ProcessId -Descending)) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
    if ($owned) { Start-Sleep -Seconds 2 }
}
