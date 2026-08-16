# AI Weather Signals

An open, privacy-aware service that turns permitted public posts into corroborated reports of **observed** weather. It is a separate ProjectEOL component: it does not modify forecasts or the existing Weather site. The MVP uses FastAPI, SQLAlchemy/Alembic, PostgreSQL and a local OpenAI-compatible LLM.

## What it does

`source adapter → normalization → cheap multilingual filter → local LLM + strict JSON Schema → local geocoder → exact deduplication → spatiotemporal clustering → explainable confidence → /api/v1`

One post never becomes a confirmed event by itself. Full text is optional per source; authors are HMAC-hashed; tokens, sessions, dumps and model weights are ignored by Git. All sample sources are disabled until the operator explicitly selects and reviews them.

## Windows 11 quick start

Prerequisites: Git, `uv`, Docker Desktop and (for GPU inference) an NVIDIA driver. Run PowerShell from the repository:

```powershell
./scripts/setup.ps1
Copy-Item .env.example .env
# Set POSTGRES_PASSWORD for Compose and the matching DATABASE_URL password in .env.
docker compose up -d postgres
uv run alembic upgrade head
uv run weather-signals sources check
```

On Windows, use an existing local Ollama installation and a multilingual model such as `qwen3.5:9b`:

```powershell
ollama run qwen3.5:9b
```

Set `LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://127.0.0.1:11434`, and `LLM_MODEL=qwen3.5:9b`. The native integration disables thinking and constrains output with the extraction JSON schema. The OpenAI-compatible llama.cpp path remains available; see [LLM.md](LLM.md).

Add and enable only a source whose API terms and retention rules you have reviewed:

```powershell
uv run weather-signals sources add city-feed rss https://authority.example/feed.atom --region Moscow --language ru --trust 0.85
uv run weather-signals sources list
uv run weather-signals collect --force
uv run weather-signals aggregate
```

For a bounded pilot, add `--max-runtime-seconds 840`. If the budget expires, the run is recorded as partial and its source cursor is not advanced.

Run API and worker in separate terminals:

```powershell
uv run weather-signals serve
uv run weather-signals worker --interval 300
```

Open `http://127.0.0.1:8000/api/v1/docs`. Try `/api/v1/events?city_id=moscow`, `/api/v1/events?lat=55.75&lon=37.62&radius_km=50`, `/health`, `/readiness`, and `/version`.

For a no-network/no-model smoke check, all tests and fixtures use the deterministic offline classifier:

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
```

## Source configuration

Versioned definitions live in `config/sources.yaml`; mutable cursor, last success and last error live in PostgreSQL. Secrets are named by `env_token` and read only from the environment. See [SOURCES.md](SOURCES.md). The 70 pilot city anchors in `config/cities.yaml` filter a shared stream and provide fallback geocoding; they do not cause 70 separate requests.

## Operations

Use `scripts/start-api.ps1` and `scripts/start-worker.ps1` interactively. `scripts/register-tasks.ps1` installs two Task Scheduler jobs for the current user; manage them with `scripts/enable-services.ps1`, `scripts/disable-services.ps1`, and `scripts/restart-services.ps1`. Schedule `uv run weather-signals purge-retention` daily. Back up and restore with `scripts/backup.ps1` and `scripts/restore.ps1`; the latter requires an explicit dump path. Updates use tagged releases and refuse a dirty working tree; see [OPERATIONS.md](OPERATIONS.md) before production-like use.

Linux/VM uses the same `.env`, Compose PostgreSQL, migrations, CLI and API. Run the two long-lived commands under systemd or another supervisor; see [OPERATIONS.md](OPERATIONS.md).

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md), [DATA_MODEL.md](DATA_MODEL.md), [ADR/0001-mvp-boundaries.md](docs/adr/0001-mvp-boundaries.md)
- [LLM.md](LLM.md), [SOURCES.md](SOURCES.md), [INTEGRATION.md](INTEGRATION.md)
- [WINDOWS.md](WINDOWS.md), [OPERATIONS.md](OPERATIONS.md)
- [SECURITY.md](SECURITY.md), [PRIVACY.md](PRIVACY.md), [NOTICE](NOTICE)

Licensed under Apache-2.0. Data obtained through configured sources retains its own terms; this license does not grant rights to third-party content.
