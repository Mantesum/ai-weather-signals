from datetime import UTC, datetime

from fastapi.testclient import TestClient

from ai_weather_signals.api import app
from ai_weather_signals.db import get_session
from ai_weather_signals.models import ClassificationDecision, ModelVersion, RawMessage, Source, WeatherEvent


def test_health_and_event_filters(session) -> None:
    event = WeatherEvent(
        phenomenon="rain",
        city_id="moscow",
        latitude=55.7558,
        longitude=37.6173,
        starts_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
        status="probable",
        confidence=0.7,
        independent_authors=2,
        platform_count=1,
    )
    session.add(event)
    session.commit()
    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        assert client.get("/api/v1/health").status_code == 200
        response = client.get("/api/v1/events", params={"city_id": "moscow"})
        assert response.status_code == 200
        assert response.json()["items"][0]["phenomenon"] == "rain"
        assert client.get("/api/v1/events", params={"lat": 55}).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_classification_audit_endpoint(session) -> None:
    source = Source(name="audit", adapter="rss", target="https://example.test/feed")
    session.add(source)
    session.flush()
    message = RawMessage(
        source_id=source.id,
        external_id="audit-1",
        text="Forecast rain tomorrow",
        text_hash="hash",
        language="en",
        published_at=datetime.now(UTC),
    )
    model = ModelVersion(
        model_name="test-model",
        prompt_version="test-v1",
        schema_version="1.0",
        prompt_sha256="prompt-hash",
    )
    session.add_all([message, model])
    session.flush()
    session.add(
        ClassificationDecision(
            message_id=message.id,
            model_version_id=model.id,
            is_weather_candidate=False,
            accepted=False,
            reason="llm_rejected",
            extraction_json={"assertion_type": "forecast"},
        )
    )
    session.commit()
    app.dependency_overrides[get_session] = lambda: session
    try:
        response = TestClient(app).get("/api/v1/classifications", params={"accepted": False})
        assert response.status_code == 200
        assert response.json()["items"][0]["reason"] == "llm_rejected"
    finally:
        app.dependency_overrides.clear()
