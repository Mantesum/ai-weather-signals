import time
from datetime import UTC, datetime, timedelta

import typer
import uvicorn
from sqlalchemy import select

from .adapters.factory import build_adapter
from .config import get_settings
from .db import Base, SessionLocal, engine
from .logging import configure_logging
from .models import RawMessage, Source
from .pipeline.confidence import load_weights
from .pipeline.geocode import LocalGeocoder
from .pipeline.llm import LLMClassifier
from .pipeline.offline import OfflineClassifier
from .pipeline.service import Classifier, aggregate, ingest_once, reconcile_source
from .schemas import SourceDefinition
from .source_config import load_sources, set_source_enabled, upsert_source

app = typer.Typer(help="Manage public weather sources and processing workers.")
sources_app = typer.Typer(help="Manage versioned source definitions.")
app.add_typer(sources_app, name="sources")


@app.command("init-db")
def init_db() -> None:
    """Development bootstrap; production uses Alembic migrations."""
    Base.metadata.create_all(engine)
    typer.echo("Database schema is ready.")


@sources_app.command("list")
def sources_list() -> None:
    for source in load_sources(get_settings().source_config_path):
        typer.echo(
            f"{source.name:24} {source.adapter:12} {'enabled' if source.enabled else 'disabled'} {source.target}"
        )


@sources_app.command("check")
def sources_check() -> None:
    sources = load_sources(get_settings().source_config_path)
    names = [item.name for item in sources]
    if len(names) != len(set(names)):
        typer.echo("Duplicate source names", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"OK: {len(sources)} valid source definitions")


@sources_app.command("status")
def sources_status() -> None:
    with SessionLocal() as session:
        rows = session.scalars(select(Source).order_by(Source.name)).all()
        for source in rows:
            typer.echo(
                f"{source.name:24} last={source.last_success_at or '-'} "
                f"cursor={source.cursor or '-'} error={source.last_error or '-'}"
            )
    if not rows:
        typer.echo("No source has run yet.")


@sources_app.command("add")
def sources_add(
    name: str,
    adapter: str,
    target: str,
    region: str | None = None,
    language: str = "und",
    interval: int = 600,
    trust: float = 0.5,
    disabled: bool = False,
) -> None:
    upsert_source(
        get_settings().source_config_path,
        SourceDefinition(
            name=name,
            adapter=adapter,
            target=target,
            region=region,
            language=language,
            poll_interval_seconds=interval,
            trust=trust,
            enabled=not disabled,
        ),
    )
    typer.echo(f"Saved source {name}")


@sources_app.command("enable")
def sources_enable(name: str) -> None:
    set_source_enabled(get_settings().source_config_path, name, True)
    typer.echo(f"Enabled {name}")


@sources_app.command("disable")
def sources_disable(name: str) -> None:
    set_source_enabled(get_settings().source_config_path, name, False)
    typer.echo(f"Disabled {name}")


@app.command("collect")
def collect(
    offline: bool = typer.Option(False, help="Use deterministic fixture classifier, not the LLM"),
    force: bool = typer.Option(False, help="Ignore the configured polling interval"),
    source: list[str] | None = typer.Option(
        None, "--source", help="Run only the named source; repeat the option for multiple sources"
    ),
    max_runtime_seconds: int | None = typer.Option(
        None, min=1, help="Stop safely after this many seconds without advancing a partial source cursor"
    ),
) -> None:
    settings = get_settings()
    definitions = load_sources(settings.source_config_path)
    if source:
        requested = set(source)
        known = {item.name for item in definitions}
        unknown = sorted(requested - known)
        if unknown:
            typer.echo(f"Unknown source(s): {', '.join(unknown)}", err=True)
            raise typer.Exit(code=2)
        definitions = [item for item in definitions if item.name in requested]
    if not offline and any(item.enabled for item in definitions) and not settings.llm_enabled:
        typer.echo("LLM_ENABLED is false; enable an LLM or use --offline.", err=True)
        raise typer.Exit(code=2)
    geocoder = LocalGeocoder.from_yaml(settings.city_config_path)
    classifier: Classifier = OfflineClassifier() if offline else LLMClassifier(settings)
    deadline = time.monotonic() + max_runtime_seconds if max_runtime_seconds is not None else None
    with SessionLocal() as session:
        for definition in definitions:
            if not definition.enabled:
                reconcile_source(session, definition)
                session.commit()
                continue
            if deadline is not None and time.monotonic() >= deadline:
                typer.echo("Collection time budget exhausted before the next source.")
                break
            current = session.scalar(select(Source).where(Source.name == definition.name))
            if (
                not force
                and current
                and current.last_success_at
                and current.last_success_at
                > datetime.now(UTC) - timedelta(seconds=definition.poll_interval_seconds)
            ):
                typer.echo(f"{definition.name}: not due")
                continue
            run = ingest_once(
                session,
                definition,
                build_adapter(definition),
                classifier,
                geocoder,
                settings,
                deadline_monotonic=deadline,
            )
            typer.echo(
                f"{definition.name}: {run.status}, fetched={run.fetched_count}, classified={run.classified_count}, errors={run.error_count}"
            )


@app.command("aggregate")
def aggregate_command() -> None:
    settings = get_settings()
    with SessionLocal() as session:
        count = aggregate(session, load_weights(settings.confidence_config_path))
    typer.echo(f"Updated {count} events")


@app.command("worker")
def worker(
    offline: bool = False,
    once: bool = False,
    interval: int = 300,
    max_runtime_seconds: int | None = None,
) -> None:
    while True:
        collect(offline=offline, force=False, source=None, max_runtime_seconds=max_runtime_seconds)
        aggregate_command()
        if once:
            return
        time.sleep(max(interval, 30))


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    configure_logging(get_settings().log_level)
    uvicorn.run("ai_weather_signals.api:app", host=host, port=port, reload=reload)


@app.command("purge-retention")
def purge_retention() -> None:
    """Remove retained text after the configured period; provenance and hashes remain."""
    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(days=settings.raw_text_retention_days)
    with SessionLocal() as session:
        rows = session.scalars(
            select(RawMessage).where(RawMessage.published_at < cutoff, RawMessage.text.is_not(None))
        ).all()
        for row in rows:
            row.text = None
            row.attachments.clear()
        session.commit()
    typer.echo(f"Anonymized {len(rows)} expired raw messages.")


@app.command("erase-message")
def erase_message(source_name: str, external_id: str) -> None:
    """Apply a provider tombstone/removal request without retaining author or text."""
    with SessionLocal() as session:
        row = session.scalar(
            select(RawMessage)
            .join(Source)
            .where(Source.name == source_name, RawMessage.external_id == external_id)
        )
        if row is None:
            typer.echo("Message not found", err=True)
            raise typer.Exit(code=1)
        row.text = None
        row.author_hash = None
        row.permalink = None
        row.deleted_at = datetime.now(UTC)
        row.attachments.clear()
        session.commit()
    typer.echo("Message content and author hash erased.")


if __name__ == "__main__":
    app()
