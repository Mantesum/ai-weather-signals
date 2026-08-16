$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$logDirectory = Join-Path $root 'logs'
$errorLogPath = Join-Path $logDirectory 'api.log'
$outputLogPath = Join-Path $logDirectory 'api-output.log'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

try {
    $entryPoint = Join-Path $root '.venv\Scripts\weather-signals.exe'
    if (-not (Test-Path -LiteralPath $entryPoint)) { throw "Missing entry point: $entryPoint. Run scripts\setup.ps1 first." }
    $process = Start-Process -FilePath $entryPoint `
        -ArgumentList @('serve', '--host', '127.0.0.1', '--port', '8010') `
        -RedirectStandardOutput $outputLogPath `
        -RedirectStandardError $errorLogPath `
        -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "API exited with code $($process.ExitCode)." }
}
catch {
    "$(Get-Date -Format o) $($_ | Out-String)" | Add-Content -LiteralPath $errorLogPath
    throw
}
