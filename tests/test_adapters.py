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
