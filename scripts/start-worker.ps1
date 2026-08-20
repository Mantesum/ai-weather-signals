$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$logDirectory = Join-Path $root 'logs'
$errorLogPath = Join-Path $logDirectory 'worker-error.log'
$outputLogPath = Join-Path $logDirectory 'worker.log'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

try {
    $databaseHost = '192.168.1.205'
    $databasePort = 5432
    $ollamaUrl = 'http://127.0.0.1:11434/api/version'
    $dependenciesReady = $false
    foreach ($attempt in 1..120) {
        $databaseReady = Test-NetConnection -ComputerName $databaseHost -Port $databasePort `
            -InformationLevel Quiet -WarningAction SilentlyContinue
        try {
            Invoke-RestMethod -Uri $ollamaUrl -TimeoutSec 5 | Out-Null
            $ollamaReady = $true
        }
        catch {
            $ollamaReady = $false
        }
        if ($databaseReady -and $ollamaReady) {
            $dependenciesReady = $true
            break
        }
        Start-Sleep -Seconds 15
    }
    if (-not $dependenciesReady) {
        throw "PostgreSQL or Ollama did not become ready within 30 minutes."
    }

    $entryPoint = Join-Path $root '.venv\Scripts\weather-signals.exe'
    if (-not (Test-Path -LiteralPath $entryPoint)) { throw "Missing entry point: $entryPoint. Run scripts\setup.ps1 first." }
    $process = Start-Process -FilePath $entryPoint `
        -ArgumentList @('worker', '--interval', '300') `
        -RedirectStandardOutput $outputLogPath `
        -RedirectStandardError $errorLogPath `
        -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "Worker exited with code $($process.ExitCode)." }
}
catch {
    "$(Get-Date -Format o) $($_ | Out-String)" | Add-Content -LiteralPath $errorLogPath
    throw
}
