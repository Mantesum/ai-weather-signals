from pathlib import Path

import httpx

from ai_weather_signals.adapters.mastodon import MastodonAdapter
from ai_weather_signals.adapters.rss import RSSAdapter
from ai_weather_signals.schemas import SourceDefinition


def test_rss_contract_uses_anonymized_fixture() -> None:
    content = Path("tests/fixtures/rss.xml").read_bytes()
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content)))
    adapter = RSSAdapter(
        SourceDefinition(name="fixture-rss", adapter="rss", target="https://example.test/rss"), client
    )
    result = adapter.fetch()
    assert result.cursor == "fixture-1"
    assert "ливень" in result.messages[0].text


def test_mastodon_contract_strips_html_and_keeps_permalink() -> None:
    payload = [
        {
            "id": "42",
            "url": "https://social.test/@a/42",
            "created_at": "2025-08-15T10:00:00Z",
            "content": "<p>Heavy <b>rain</b> now</p>",
            "language": "en",
            "account": {"id": "7"},
            "media_attachments": [],
        }
    ]
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)))
    source = SourceDefinition(
        name="fixture-masto", adapter="mastodon", target="https://social.test", options={"hashtag": "weather"}
    )
    result = MastodonAdapter(source, client).fetch()
    assert result.messages[0].text == "Heavy rain now"
    assert result.cursor == "42"


def test_mastodon_combines_multiple_hashtags_without_duplicates() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        identifier = "43" if request.url.path.endswith("/rain") else "42"
        return httpx.Response(
            200,
            json=[
                {
                    "id": identifier,
                    "url": f"https://social.test/@weather/{identifier}",
                    "created_at": "2026-08-16T10:00:00Z",
                    "content": "<p>Rain now</p>",
                    "language": "en",
                    "account": {"id": "7"},
                    "media_attachments": [],
                }
            ],
        )

    source = SourceDefinition(
        name="fixture-masto",
        adapter="mastodon",
        target="https://social.test",
        options={"hashtags": ["weather", "rain"], "limit": 10},
    )
    result = MastodonAdapter(source, httpx.Client(transport=httpx.MockTransport(handler))).fetch("40")
    assert len(requests) == 2
    assert {request.url.params["min_id"] for request in requests} == {"40"}
    assert {message.external_id for message in result.messages} == {"42", "43"}
    assert result.cursor == "43"
