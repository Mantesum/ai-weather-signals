from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

from ai_weather_signals.adapters.base import Adapter, AdapterResult
from ai_weather_signals.config import Settings
from ai_weather_signals.models import RawMessage, WeatherEvent, WeatherSignal
from ai_weather_signals.pipeline.confidence import load_weights
from ai_weather_signals.pipeline.geocode import LocalGeocoder
from ai_weather_signals.pipeline.offline import OfflineClassifier
from ai_weather_signals.pipeline.service import aggregate, ingest_once
from ai_weather_signals.schemas import NormalizedMessage, SourceDefinition


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
    aggregate(session, load_weights(Path("config/confidence.yaml")))
    assert session.scalar(select(func.count()).select_from(WeatherEvent)) == 1
