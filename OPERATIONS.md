# Operations

## Backup and restore

`scripts/backup.ps1` writes a timestamped custom-format PostgreSQL dump under ignored `backups/`. Run it before every migration and test restores regularly. Restore only into an empty or explicitly disposable database:

```powershell
./scripts/restore.ps1 -DumpPath ./backups/weather-signals-YYYYMMDD-HHMMSS.dump
```

## Tagged update

`scripts/update.ps1 -Version v0.3.0` refuses a dirty tree, fetches tags, verifies the tag exists, backs up PostgreSQL, switches to that tag without resetting files, syncs locked dependencies, migrates, tests and runs readiness. If it fails, keep services stopped, check `logs/update.log`, switch back to the previous tag/branch, sync, migrate if compatible, and restore the saved dump when a migration is not backward compatible.

Never auto-deploy arbitrary `main`. Sign releases and publish migration compatibility notes in future releases.

## Linux/VM

Install Python 3.12/uv, Git, Docker Engine and NVIDIA Container Toolkit if containerizing inference. Use `docker compose up -d postgres`, `uv sync --frozen`, `uv run alembic upgrade head`; supervise `weather-signals serve --host 127.0.0.1` and `weather-signals worker` with separate systemd units. Put TLS/authentication at a reverse proxy and back up to an encrypted off-host destination.
