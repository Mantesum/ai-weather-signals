import json

import httpx

from ai_weather_signals.config import Settings
from ai_weather_signals.pipeline.llm import LLMClassifier


def test_llm_retries_invalid_json_and_sends_schema() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]})
        content = {
            "is_weather_candidate": True,
            "assertion_type": "personal_current_observation",
            "phenomenon": "rain",
            "intensity": 0.5,
            "place_name": "London",
            "observed_at": "2026-08-15T10:00:00Z",
            "time_precision": 0.9,
            "evidence_type": "text",
            "has_photo": False,
            "has_video": False,
            "confidence": 0.8,
            "is_repost_or_copy": False,
            "rationale_code": "current_personal",
        }
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(content)}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    classifier = LLMClassifier(
        Settings(llm_base_url="http://llm.test/v1", author_hash_salt="safe-test-salt"), client
    )
    result = classifier.classify("Rain in London now", "London", "2026-08-15T10:00:00Z")
    payload = json.loads(requests[0].content)
    assert result.phenomenon == "rain"
    assert len(requests) == 2
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["temperature"] == 0.1
