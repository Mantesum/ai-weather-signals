from datetime import UTC, datetime
from math import inf

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from . import __version__
from .config import get_settings
from .db import get_session
from .metrics import metrics
from .models import ModelVersion, ProcessingError, RawMessage, Source, WeatherEvent, WeatherSignal
from .pipeline.geocode import haversine_km
from .pipeline.normalize import safe_excerpt

app = FastAPI(
    title="AI Weather Signals API",
    version=__version__,
    description="Read-only, anonymized weather observation events for ProjectEOL.",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url=None,
)


def _event_dict(event: WeatherEvent) -> dict[str, object]:
    return {
        "id": event.id,
        "phenomenon": event.phenomenon,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "city_id": event.city_id,
        "starts_at": event.starts_at,
        "last_seen_at": event.last_seen_at,
        "status": event.status,
        "confidence": event.confidence,
        "independent_authors": event.independent_authors,
        "platform_count": event.platform_count,
        "official_confirmation": event.official_confirmation,
        "updated_at": event.updated_at,
    }


@app.get("/api/v1/health")
def health() -> dict[str, object]:
    return {"status": "ok", "version": __version__, "metrics": metrics.snapshot()}


@app.get("/api/v1/readiness")
def readiness(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(503, "database unavailable") from error
    return {"status": "ready"}


@app.get("/api/v1/version")
def version(session: Session = Depends(get_session)) -> dict[str, object]:
    settings = get_settings()
    model = session.scalar(select(ModelVersion).order_by(ModelVersion.created_at.desc()).limit(1))
    return {
        "application": __version__,
        "schema": settings.schema_version,
        "model": model.model_name if model else settings.llm_model,
        "prompt_version": model.prompt_version if model else None,
    }


@app.get("/api/v1/events")
def events(
    city_id: str | None = None,
    phenomenon: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    radius_km: float = Query(default=50, gt=0, le=500),
    active_only: bool = True,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    query = select(WeatherEvent)
    if city_id:
        query = query.where(WeatherEvent.city_id == city_id)
    if phenomenon:
        query = query.where(WeatherEvent.phenomenon == phenomenon)
    if start:
        query = query.where(WeatherEvent.last_seen_at >= start)
    if end:
        query = query.where(WeatherEvent.starts_at <= end)
    if active_only:
        query = query.where(WeatherEvent.status != "expired")
    rows = session.scalars(query.order_by(WeatherEvent.last_seen_at.desc()).limit(1000)).all()
    if (lat is None) != (lon is None):
        raise HTTPException(422, "lat and lon must be supplied together")
    selected: list[tuple[float, WeatherEvent]] = []
    for event in rows:
        distance = (
            haversine_km(lat, lon, event.latitude, event.longitude)
            if lat is not None and lon is not None
            else inf
        )
        if lat is None or distance <= radius_km:
            selected.append((distance, event))
    selected.sort(key=lambda item: (item[0], -item[1].last_seen_at.timestamp()))
    return {
        "items": [_event_dict(item) for _, item in selected[:limit]],
        "count": min(len(selected), limit),
        "updated_at": datetime.now(UTC),
    }


@app.get("/api/v1/events/{event_id}")
def event_detail(event_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    event = session.get(WeatherEvent, event_id)
    if not event:
        raise HTTPException(404, "event not found")
    evidence = []
    for link in event.links:
        message = link.signal.message
        evidence.append(
            {
                "observed_at": link.signal.observed_at,
                "assertion_type": link.signal.assertion_type,
                "evidence_type": link.signal.evidence_type,
                "excerpt": safe_excerpt(message.text),
                "permalink": message.permalink,
                "source": message.source.name,
            }
        )
    return {**_event_dict(event), "evidence": evidence}


@app.get("/api/v1/summary")
def summary(city_id: str | None = None, session: Session = Depends(get_session)) -> dict[str, object]:
    query = select(WeatherEvent.phenomenon, func.count(), func.max(WeatherEvent.confidence)).where(
        WeatherEvent.status != "expired"
    )
    if city_id:
        query = query.where(WeatherEvent.city_id == city_id)
    rows = session.execute(query.group_by(WeatherEvent.phenomenon)).all()
    return {"items": [{"phenomenon": row[0], "events": row[1], "max_confidence": row[2]} for row in rows]}


@app.get("/api/v1/sources/status")
def source_status(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        {
            "name": item.name,
            "adapter": item.adapter,
            "enabled": item.enabled,
            "last_success_at": item.last_success_at,
            "last_error": item.last_error,
            "cursor": item.cursor,
        }
        for item in session.scalars(select(Source).order_by(Source.name))
    ]


@app.get("/api/v1/metrics")
def metric_snapshot(session: Session = Depends(get_session)) -> dict[str, object]:
    database_counts = {
        "raw_messages": session.scalar(select(func.count()).select_from(RawMessage)) or 0,
        "signals": session.scalar(select(func.count()).select_from(WeatherSignal)) or 0,
        "active_events": session.scalar(
            select(func.count()).select_from(WeatherEvent).where(WeatherEvent.status != "expired")
        )
        or 0,
        "processing_errors": session.scalar(select(func.count()).select_from(ProcessingError)) or 0,
        "queue_size": session.scalar(
            select(func.count()).select_from(RawMessage).where(RawMessage.candidate_score.is_(None))
        )
        or 0,
    }
    return {"process": metrics.snapshot(), "database": database_counts}
