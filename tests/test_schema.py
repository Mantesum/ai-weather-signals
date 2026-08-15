from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ai_weather_signals.schemas import LLMExtraction


def valid_payload() -> dict[str, object]:
    return {
        "is_weather_candidate": True,
        "assertion_type": "personal_current_observation",
        "phenomenon": "heavy_rain",
        "intensity": 0.8,
        "place_name": "Moscow",
        "observed_at": datetime.now(UTC).isoformat(),
        "time_precision": 0.9,
        "evidence_type": "text",
        "has_photo": False,
        "has_video": False,
        "confidence": 0.85,
        "is_repost_or_copy": False,
        "rationale_code": "current_personal",
    }


def test_strict_schema_accepts_valid_json() -> None:
    assert LLMExtraction.model_validate(valid_payload()).phenomenon == "heavy_rain"


def test_schema_rejects_forecast_candidate_and_extra_fields() -> None:
    payload = valid_payload()
    payload["assertion_type"] = "forecast"
    with pytest.raises(ValidationError):
        LLMExtraction.model_validate(payload)
    payload = valid_payload()
    payload["personal_name"] = "must not be accepted"
    with pytest.raises(ValidationError):
        LLMExtraction.model_validate(payload)
