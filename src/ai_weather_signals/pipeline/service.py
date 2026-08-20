import time
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..adapters.base import Adapter
from ..config import Settings
from ..enums import AssertionType
from ..metrics import metrics
from ..models import (
    Attachment,
    ClassificationDecision,
    EventSignal,
    GeocodeResult,
    IngestRun,
    ModelVersion,
    ProcessingError,
    RawMessage,
    Source,
    WeatherEvent,
    WeatherSignal,
)
from ..schemas import LLMExtraction, NormalizedMessage, SourceDefinition
from .cluster import ClusterCandidate, belongs_to_cluster
from .confidence import ConfidenceInputs, confidence_score, event_status
from .geocode import LocalGeocoder
from .normalize import author_hash, text_hash
from .prefilter import prefilter


class Classifier(Protocol):
    @property
    def prompt_hash(self) -> str: ...

    def classify(
        self,
        text: str,
        source_region: str | None,
        published_at: str,
        source_kind: str = "social",
        timeout_seconds: float | None = None,
    ) -> LLMExtraction: ...


def reconcile_source(session: Session, definition: SourceDefinition) -> Source:
    source = session.scalar(select(Source).where(Source.name == definition.name))
    if source is None:
        source = Source(name=definition.name, adapter=definition.adapter, target=definition.target)
        session.add(source)
    for key in (
        "adapter",
        "enabled",
        "target",
        "region",
        "language",
        "poll_interval_seconds",
        "trust",
        "tags",
        "store_text",
    ):
        setattr(source, key, getattr(definition, key))
    session.flush()
    return source


def _model_version(session: Session, settings: Settings, classifier: Classifier) -> ModelVersion:
    found = session.scalar(
        select(ModelVersion).where(
            ModelVersion.model_name == settings.llm_model,
            ModelVersion.prompt_sha256 == classifier.prompt_hash,
        )
    )
    if found:
        return found
    found = ModelVersion(
        model_name=settings.llm_model,
        prompt_version=getattr(classifier, "prompt_version", "unknown"),
        schema_version=settings.schema_version,
        prompt_sha256=classifier.prompt_hash,
    )
    session.add(found)
    session.flush()
    return found


def _persist_message(
    session: Session, source: Source, item: NormalizedMessage, settings: Settings
) -> tuple[RawMessage, bool]:
    existing = session.scalar(
        select(RawMessage).where(
            RawMessage.source_id == source.id, RawMessage.external_id == item.external_id
        )
    )
    if existing:
        return existing, False
    digest = text_hash(item.text)
    duplicate = (
        session.scalar(select(RawMessage.id).where(RawMessage.text_hash == digest).limit(1)) is not None
    )
    message = RawMessage(
        source_id=source.id,
        external_id=item.external_id,
        permalink=item.permalink,
        author_hash=author_hash(source.name, item.author_external_id, settings.author_hash_salt),
        text=item.text if source.store_text else None,
        text_hash=digest,
        language=item.language,
        published_at=item.published_at,
    )
    session.add(message)
    session.flush()
    for url in item.media_urls:
        session.add(Attachment(message_id=message.id, remote_url=url, media_type="unknown"))
    return message, duplicate


def ingest_once(
    session: Session,
    definition: SourceDefinition,
    adapter: Adapter,
    classifier: Classifier,
    geocoder: LocalGeocoder,
    settings: Settings,
    deadline_monotonic: float | None = None,
) -> IngestRun:
    source = reconcile_source(session, definition)
    run = IngestRun(source_id=source.id)
    session.add(run)
    session.commit()
    started = time.monotonic()
    try:
        result = adapter.fetch(source.cursor)
        run.fetched_count = len(result.messages)
        model_version = _model_version(session, settings, classifier)
        time_budget_exhausted = False
        for item in result.messages:
            if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
                time_budget_exhausted = True
                break
            try:
                message, exact_duplicate = _persist_message(session, source, item, settings)
                if not message.text or session.scalar(
                    select(WeatherSignal.id).where(WeatherSignal.message_id == message.id)
                ):
                    continue
                filtered = prefilter(message.text, geocoder.names())
                message.candidate_score = filtered.score
                if not filtered.candidate:
                    continue
                run.candidate_count += 1
                existing_decision = session.scalar(
                    select(ClassificationDecision.id).where(
                        ClassificationDecision.message_id == message.id,
                        ClassificationDecision.model_version_id == model_version.id,
                    )
                )
                if existing_decision is not None:
                    continue
                remaining = (
                    max(0.0, deadline_monotonic - time.monotonic())
                    if deadline_monotonic is not None
                    else None
                )
                extraction = classifier.classify(
                    message.text,
                    source.region,
                    message.published_at.isoformat(),
                    source_kind=(
                        "official"
                        if "official" in source.tags
                        else "news"
                        if "news" in source.tags
                        else "social"
                    ),
                    timeout_seconds=remaining,
                )
                run.classified_count += 1
                decision = ClassificationDecision(
                    message_id=message.id,
                    model_version_id=model_version.id,
                    is_weather_candidate=extraction.is_weather_candidate,
                    accepted=False,
                    reason="llm_rejected",
                    extraction_json=extraction.model_dump(mode="json"),
                )
                session.add(decision)
                if not extraction.is_weather_candidate:
                    continue
                if extraction.assertion_type == AssertionType.OFFICIAL and "official" not in source.tags:
                    decision.reason = "untrusted_official"
                    continue
                match = geocoder.resolve(extraction.place_name, source.region)
                if match is None:
                    match = geocoder.resolve(message.text, source.region)
                if match is None:
                    decision.reason = "unresolved_place"
                    session.add(
                        ProcessingError(
                            stage="geocode",
                            entity_id=message.id,
                            error_type="unresolved_place",
                            message=extraction.place_name or "missing place",
                            retryable=False,
                        )
                    )
                    continue
                decision.accepted = True
                decision.reason = "accepted"
                signal = WeatherSignal(
                    message_id=message.id,
                    model_version_id=model_version.id,
                    assertion_type=extraction.assertion_type,
                    phenomenon=extraction.phenomenon,
                    intensity=extraction.intensity,
                    observed_at=extraction.observed_at or message.published_at,
                    time_precision=extraction.time_precision,
                    evidence_type=extraction.evidence_type,
                    has_photo=extraction.has_photo or bool(item.media_urls),
                    has_video=extraction.has_video,
                    llm_confidence=extraction.confidence,
                    is_copy=extraction.is_repost_or_copy or exact_duplicate,
                    place_name=extraction.place_name,
                )
                session.add(signal)
                session.flush()
                session.add(
                    GeocodeResult(
                        signal_id=signal.id,
                        city_id=match.city.id,
                        geonames_id=match.city.geonames_id,
                        display_name=match.city.name,
                        latitude=match.city.latitude,
                        longitude=match.city.longitude,
                        precision=match.precision,
                    )
                )
            except Exception as error:
                run.error_count += 1
                metrics.inc("processing_errors")
                session.add(
                    ProcessingError(
                        stage="message",
                        entity_id=item.external_id,
                        error_type=type(error).__name__,
                        message=str(error)[:2000],
                    )
                )
        if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
            time_budget_exhausted = True
        if time_budget_exhausted:
            run.status = "partial"
            source.last_error = "Time budget exhausted; source cursor was not advanced."
        else:
            source.cursor = result.cursor
            source.last_success_at = datetime.now(UTC)
            source.last_error = None
            run.status = "success"
        metrics.inc("messages_fetched", run.fetched_count)
        metrics.inc("messages_classified", run.classified_count)
    except Exception as error:
        session.rollback()
        failed_source = session.scalar(select(Source).where(Source.name == definition.name))
        failed_run = session.get(IngestRun, run.id)
        if failed_source:
            failed_source.last_error = str(error)[:2000]
        if failed_run:
            failed_run.status = "failed"
            failed_run.error_count += 1
            run = failed_run
        session.add(
            ProcessingError(
                stage="adapter",
                entity_id=definition.name,
                error_type=type(error).__name__,
                message=str(error)[:2000],
            )
        )
    run.finished_at = datetime.now(UTC)
    run.duration_ms = int((time.monotonic() - started) * 1000)
    session.commit()
    return run


def aggregate(session: Session, weights: dict[str, float], now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    signals = session.scalars(
        select(WeatherSignal)
        .join(GeocodeResult)
        .where(WeatherSignal.observed_at >= now - timedelta(hours=12))
    ).all()
    changed: set[str] = set()
    for signal in signals:
        if session.scalar(select(EventSignal.signal_id).where(EventSignal.signal_id == signal.id)):
            continue
        geo = signal.geocode
        if geo is None:
            continue
        candidate = ClusterCandidate(signal.phenomenon, geo.latitude, geo.longitude, signal.observed_at)
        events = session.scalars(
            select(WeatherEvent).where(
                WeatherEvent.last_seen_at >= now - timedelta(hours=6),
                WeatherEvent.phenomenon == signal.phenomenon,
            )
        ).all()
        event = next(
            (
                item
                for item in events
                if belongs_to_cluster(
                    candidate, item.phenomenon, item.latitude, item.longitude, item.last_seen_at
                )
            ),
            None,
        )
        if event is None:
            event = WeatherEvent(
                phenomenon=signal.phenomenon,
                city_id=geo.city_id,
                latitude=geo.latitude,
                longitude=geo.longitude,
                starts_at=signal.observed_at,
                last_seen_at=signal.observed_at,
                status="unconfirmed",
                confidence=0,
            )
            session.add(event)
            session.flush()
        event.starts_at = min(event.starts_at, signal.observed_at)
        event.last_seen_at = max(event.last_seen_at, signal.observed_at)
        session.add(EventSignal(event_id=event.id, signal_id=signal.id, contribution=signal.llm_confidence))
        changed.add(event.id)
    session.flush()
    active_event_ids = set(
        session.scalars(
            select(WeatherEvent.id).where(WeatherEvent.last_seen_at >= now - timedelta(hours=12))
        )
    )
    for event_id in changed | active_event_ids:
        event = session.get(WeatherEvent, event_id)
        assert event is not None
        linked = [link.signal for link in event.links]
        by_author: dict[str, WeatherSignal] = {}
        for item in linked:
            author = item.message.author_hash or item.message.id
            current = by_author.get(author)
            if current is None or item.observed_at > current.observed_at:
                by_author[author] = item
        independent = list(by_author.values())
        platforms = {item.message.source.adapter for item in independent}
        official = any(
            item.assertion_type == AssertionType.OFFICIAL and "official" in item.message.source.tags
            for item in independent
        )
        copies = sum(item.is_copy for item in independent) / max(len(independent), 1)
        input_values = ConfidenceInputs(
            llm=sum(item.llm_confidence for item in independent) / len(independent),
            geography=sum(item.geocode.precision for item in independent if item.geocode)
            / len(independent),
            time=sum(item.time_precision for item in independent) / len(independent),
            source_trust=sum(item.message.source.trust for item in independent) / len(independent),
            personal_weight=sum(
                1.0 if item.assertion_type == AssertionType.PERSONAL_CURRENT else 0.75
                for item in independent
            )
            / len(independent),
            independent_authors=len(independent),
            platforms=len(platforms),
            media=any(item.has_photo or item.has_video for item in independent),
            official=official,
            copy_ratio=copies,
        )
        event.independent_authors = len(independent)
        event.platform_count = len(platforms)
        event.official_confirmation = official
        event.confidence = confidence_score(input_values, weights)
        event.status = event_status(event.confidence, len(independent), len(platforms), official)
    for event in session.scalars(
        select(WeatherEvent).where(
            WeatherEvent.last_seen_at < now - timedelta(hours=12), WeatherEvent.status != "expired"
        )
    ):
        event.status = "expired"
    opposites = {
        "heat": {"cold", "extreme_cold"},
        "extreme_heat": {"cold", "extreme_cold"},
        "cold": {"heat", "extreme_heat"},
        "extreme_cold": {"heat", "extreme_heat"},
    }
    active = session.scalars(
        select(WeatherEvent).where(WeatherEvent.last_seen_at >= now - timedelta(hours=3))
    ).all()
    for event in active:
        if any(
            other.id != event.id
            and other.city_id == event.city_id
            and other.phenomenon in opposites.get(event.phenomenon, set())
            for other in active
        ):
            event.status = "conflicting"
            event.confidence = max(0, round(event.confidence - weights["conflict_penalty"], 4))
    session.commit()
    metrics.inc("events_aggregated", len(changed))
    return len(changed)
