# Windows 11 operations

`scripts/setup.ps1` supports the default Docker Desktop installation. This deployment instead uses the PostgreSQL server configured by `DATABASE_URL` in `.env`; TLS can be required with `sslmode=require`. Local inference uses Ollama on loopback with `qwen3.5:9b`; the OpenAI-compatible llama.cpp provider remains optional.

Use `scripts/start-api.ps1`, `scripts/start-worker.ps1`, and `scripts/status.ps1`. The scripted API listens on `http://127.0.0.1:8010` to avoid conflicts with other local services. `scripts/register-tasks.ps1` creates current-user, at-logon scheduled tasks; review paths and `.env` permissions first. Manage both processes with `scripts/enable-services.ps1`, `scripts/disable-services.ps1`, and `scripts/restart-services.ps1`. Logs are written under the ignored `logs/` directory. Remove tasks with `Unregister-ScheduledTask` only when intended.

PowerShell execution policy may require `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Do not apply machine-wide policy changes for this project.
