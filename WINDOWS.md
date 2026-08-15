# Windows 11 operations

`scripts/setup.ps1` checks Git, uv, Docker and NVIDIA, creates `.env` from the safe example, installs Python 3.12 dependencies and prints next steps. Docker Desktop hosts PostgreSQL on loopback. The native CUDA llama.cpp server avoids WSL/Docker GPU uncertainty on the audited V100 machine.

Use `scripts/start-api.ps1`, `scripts/start-worker.ps1`, and `scripts/status.ps1`. `scripts/register-tasks.ps1` creates current-user, at-logon scheduled tasks; review paths and `.env` permissions first. Stop tasks with `Stop-ScheduledTask -TaskName AIWeatherSignals-API` and `...-Worker`; remove them with `Unregister-ScheduledTask` only when intended.

PowerShell execution policy may require `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Do not apply machine-wide policy changes for this project.
