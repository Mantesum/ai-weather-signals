import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

from ai_weather_signals.adapters.base import Adapter, AdapterResult
from ai_weather_signals.config import Settings
from ai_weather_signals.enums import AssertionType, EvidenceType, Phenomenon
from ai_weather_signals.models import (
    ClassificationDecision,
    IngestRun,
    RawMessage,
    Source,
    WeatherEvent,
    WeatherSignal,
)
from ai_weather_signals.pipeline.confidence import load_weights
from ai_weather_signals.pipeline.geocode import LocalGeocoder
from ai_weather_signals.pipeline.offline import OfflineClassifier
from ai_weather_signals.pipeline.service import aggregate, ingest_once
from ai_weather_signals.schemas import LLMExtraction, NormalizedMessage, SourceDefinition


class FixtureAdapter(Adapter):
    def fetch(self, cursor: str | None = None) -> AdapterResult:
        items = [
            NormalizedMessage(
                source_name=self.source.name,
                external_id="1",
                author_external_id="observer-1",
                permalink="https://example.test/1",
                text="В Москве прямо сейчас сильный дождь и ливень",
                language="ru",
                published_at=datetime.now(UTC),
            )
        ]
        return AdapterResult(items, "1")


class OfficialClassifier:
    prompt_hash = "official-test-v1"

    def classify(
        self,
        text: str,
        source_region: str | None,
        published_at: str,
        timeout_seconds: float | None = None,
    ) -> LLMExtraction:
        return LLMExtraction(
            is_weather_candidate=True,
            assertion_type=AssertionType.OFFICIAL,
            phenomenon=Phenomenon.HEAVY_RAIN,
            intensity=0.8,
            place_name="Moscow",
            observed_at=datetime.fromisoformat(published_at),
            time_precision=0.9,
            evidence_type=EvidenceType.TEXT,
            confidence=0.9,
            rationale_code="official_report",
        )


class RepeatedAuthorAdapter(Adapter):
    def fetch(self, cursor: str | None = None) -> AdapterResult:
        now = datetime.now(UTC)
        return AdapterResult(
            [
                NormalizedMessage(
                    source_name=self.source.name,
                    external_id=str(index),
                    author_external_id="same-observer",
                    text="Heavy rain in Moscow right now",
                    language="en",
                    published_at=now,
                )
                for index in (1, 2)
            ],
            "2",
        )


def test_full_pipeline_is_idempotent(session) -> None:
    definition = SourceDefinition(
        name="fixture", adapter="rss", target="https://example.test/rss", region="Moscow", trust=0.6
    )
    settings = Settings(database_url="sqlite://", llm_enabled=False, author_hash_salt="safe-test-salt")
    geocoder = LocalGeocoder.from_yaml(Path("config/cities.yaml"))
    adapter = FixtureAdapter(definition)
    ingest_once(session, definition, adapter, OfflineClassifier(), geocoder, settings)
    ingest_once(session, definition, adapter, OfflineClassifier(), geocoder, settings)
    assert session.scalar(select(func.count()).select_from(RawMessage)) == 1
    assert session.scalar(select(func.count()).select_from(WeatherSignal)) == 1
    assert session.scalar(select(func.count()).select_from(ClassificationDecision)) == 1
    aggregate(session, load_weights(Path("config/confidence.yaml")))
    assert session.scalar(select(func.count()).select_from(WeatherEvent)) == 1


def test_expired_time_budget_does_not_advance_cursor(session) -> None:
    definition = SourceDefinition(
        name="fixture", adapter="rss", target="https://example.test/rss", region="Moscow"
    )
    settings = Settings(database_url="sqlite://", llm_enabled=False, author_hash_salt="safe-test-salt")
    run = ingest_once(
        session,
        definition,
        FixtureAdapter(definition),
        OfflineClassifier(),
        LocalGeocoder.from_yaml(Path("config/cities.yaml")),
        settings,
        deadline_monotonic=time.monotonic() - 1,
    )
    source = session.scalar(select(Source).where(Source.name == "fixture"))
    assert isinstance(run, IngestRun)
    assert run.status == "partial"
    assert source is not None and source.cursor is None
    assert session.scalar(select(func.count()).select_from(RawMessage)) == 0


def test_untrusted_source_cannot_create_official_signal(session) -> None:
    definition = SourceDefinition(
        name="social-feed",
        adapter="rss",
        target="https://example.test/rss",
        region="Moscow",
        tags=["social"],
    )
    ingest_once(
        session,
        definition,
        FixtureAdapter(definition),
        OfficialClassifier(),
        LocalGeocoder.from_yaml(Path("config/cities.yaml")),
        Settings(database_url="sqlite://", author_hash_salt="safe-test-salt"),
    )
    decision = session.scalar(select(ClassificationDecision))
    assert decision is not None
    assert not decision.accepted
    assert decision.reason == "untrusted_official"
    assert session.scalar(select(func.count()).select_from(WeatherSignal)) == 0


def test_repeated_author_remains_unconfirmed(session) -> None:
    definition = SourceDefinition(
        name="repeated-feed",
        adapter="rss",
        target="https://example.test/rss",
        region="Moscow",
        trust=0.8,
    )
    ingest_once(
        session,
        definition,
        RepeatedAuthorAdapter(definition),
        OfflineClassifier(),
        LocalGeocoder.from_yaml(Path("config/cities.yaml")),
        Settings(database_url="sqlite://", author_hash_salt="safe-test-salt"),
    )
    aggregate(session, load_weights(Path("config/confidence.yaml")))
    event = session.scalar(select(WeatherEvent))
    assert event is not None
    assert event.independent_authors == 1
    assert event.status == "unconfirmed"
