$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

foreach ($tool in @('git', 'uv', 'docker')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Required tool is missing: $tool" }
}
Write-Host (git --version)
Write-Host (uv --version)
Write-Host (docker --version)
uv python find 3.12
docker info --format 'Docker server {{.ServerVersion}}' | Write-Host
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) { nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader }
else { Write-Warning 'nvidia-smi is missing; offline mode remains available.' }

if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
    Write-Warning 'Created .env. Replace every CHANGE_ME before starting PostgreSQL.'
}
$env:UV_CACHE_DIR = Join-Path $root '.uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $root '.uv-python'
uv sync --extra dev
uv run weather-signals sources check
Write-Host 'Next: set secrets in .env, run docker compose up -d postgres, then uv run alembic upgrade head.'
