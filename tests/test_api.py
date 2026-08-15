from datetime import UTC, datetime

from fastapi.testclient import TestClient

from ai_weather_signals.api import app
from ai_weather_signals.db import get_session
from ai_weather_signals.models import WeatherEvent


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
