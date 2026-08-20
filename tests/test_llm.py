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
        Settings(
            llm_provider="openai",
            llm_base_url="http://llm.test/v1",
            author_hash_salt="safe-test-salt",
        ),
        client,
    )
    result = classifier.classify("Rain in London now", "London", "2026-08-15T10:00:00Z")
    payload = json.loads(requests[0].content)
    assert result.phenomenon == "rain"
    assert len(requests) == 2
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["temperature"] == 0.1


def test_ollama_uses_native_schema_and_disables_thinking() -> None:
    requests: list[httpx.Request] = []
    content = {
        "is_weather_candidate": False,
        "assertion_type": "forecast",
        "phenomenon": "rain",
        "intensity": 0.4,
        "place_name": "Moscow",
        "observed_at": None,
        "time_precision": 0.3,
        "evidence_type": "text",
        "has_photo": False,
        "has_video": False,
        "confidence": 0.9,
        "is_repost_or_copy": False,
        "rationale_code": "future_forecast",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"message": {"content": json.dumps(content)}})

    classifier = LLMClassifier(
        Settings(
            llm_provider="ollama",
            llm_base_url="http://ollama.test:11434",
            llm_model="qwen3.5:9b",
            author_hash_salt="safe-test-salt",
        ),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = classifier.classify("Завтра в Москве дождь", "Moscow", "2026-08-16T10:00:00Z")
    payload = json.loads(requests[0].content)
    assert requests[0].url.path == "/api/chat"
    assert not result.is_weather_candidate
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["format"]["required"]
    assert payload["options"]["num_predict"] == 160
    assert payload["options"]["num_ctx"] == 4096
    assert json.loads(payload["messages"][1]["content"])["source_kind"] == "social"
    assert payload["keep_alive"] == "15m"


def test_timeout_is_not_retried() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise httpx.ReadTimeout("slow model", request=request)

    classifier = LLMClassifier(
        Settings(
            llm_provider="ollama",
            llm_base_url="http://ollama.test:11434",
            author_hash_salt="safe-test-salt",
        ),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )
    try:
        classifier.classify("Rain in London now", "London", "2026-08-16T10:00:00Z")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Timeout must fail classification")
    assert len(requests) == 1
