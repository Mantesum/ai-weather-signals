from pathlib import Path

import httpx

from ai_weather_signals.adapters.eonet import EONETAdapter
from ai_weather_signals.adapters.gdelt import GDELTAdapter
from ai_weather_signals.adapters.google_news import GoogleNewsAdapter
from ai_weather_signals.adapters.mastodon import MastodonAdapter
from ai_weather_signals.adapters.multi_rss import MultiRSSAdapter
from ai_weather_signals.adapters.rss import RSSAdapter
from ai_weather_signals.adapters.x_recent import XRecentSearchAdapter
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


def test_x_recent_search_uses_bearer_token_and_since_id(monkeypatch) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "101",
                        "author_id": "7",
                        "created_at": "2026-08-16T10:00:00Z",
                        "lang": "ru",
                        "text": "Сильный дождь сейчас в Москве",
                    }
                ],
                "meta": {"newest_id": "101", "result_count": 1},
            },
        )

    monkeypatch.setenv("X_BEARER_TOKEN", "fixture-token")
    source = SourceDefinition(
        name="fixture-x",
        adapter="x_recent",
        target="https://api.x.test/2/tweets/search/recent",
        env_token="X_BEARER_TOKEN",
        options={"query": "(weather OR погода) -is:retweet", "max_results": 10},
    )
    result = XRecentSearchAdapter(
        source, httpx.Client(transport=httpx.MockTransport(handler))
    ).fetch("100")

    assert requests[0].headers["Authorization"] == "Bearer fixture-token"
    assert requests[0].url.params["since_id"] == "100"
    assert requests[0].url.params["max_results"] == "10"
    assert result.messages[0].permalink == "https://x.com/i/web/status/101"
    assert result.cursor == "101"


def test_x_recent_search_requires_token(monkeypatch) -> None:
    monkeypatch.delenv("FIXTURE_MISSING_X_TOKEN", raising=False)
    source = SourceDefinition(
        name="fixture-x",
        adapter="x_recent",
        target="https://api.x.test/2/tweets/search/recent",
        env_token="FIXTURE_MISSING_X_TOKEN",
    )
    try:
        XRecentSearchAdapter(source).fetch()
    except RuntimeError as error:
        assert "FIXTURE_MISSING_X_TOKEN" in str(error)
    else:
        raise AssertionError("missing X token must fail closed")


def test_google_news_combines_queries_and_deduplicates() -> None:
    requests: list[httpx.Request] = []
    rss = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
    <guid>story-1</guid><title>Flash flood in Manila</title>
    <link>https://news.test/story-1</link><pubDate>Sun, 16 Aug 2026 10:00:00 GMT</pubDate>
    </item></channel></rss>"""

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=rss)

    source = SourceDefinition(
        name="fixture-google",
        adapter="google_news",
        target="https://news.test/rss/search",
        options={"queries": ["flood Philippines", "bagyo Philippines"], "total_limit": 10},
    )
    result = GoogleNewsAdapter(
        source, httpx.Client(transport=httpx.MockTransport(handler))
    ).fetch()

    assert len(requests) == 2
    assert {request.url.params["q"] for request in requests} == {
        "flood Philippines",
        "bagyo Philippines",
    }
    assert len(result.messages) == 1
    assert result.messages[0].raw["provider"] == "google_news_rss"


def test_multi_rss_keeps_same_identifier_from_different_feeds() -> None:
    rss = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
    <guid>alert-1</guid><title>Severe rain warning</title>
    <link>https://alerts.test/1</link><pubDate>Sun, 16 Aug 2026 10:00:00 GMT</pubDate>
    </item></channel></rss>"""
    source = SourceDefinition(
        name="fixture-multi-rss",
        adapter="multi_rss",
        target="https://alerts.test",
        options={"feeds": ["https://alerts.test/a", "https://alerts.test/b"]},
    )
    adapter = MultiRSSAdapter(
        source,
        httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=rss))),
    )
    result = adapter.fetch()
    assert len(result.messages) == 2
    assert len({message.external_id for message in result.messages}) == 2


def test_gdelt_contract_maps_article() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["mode"] == "ArtList"
        return httpx.Response(
            200,
            json={
                "articles": [
                    {
                        "url": "https://news.test/flood",
                        "title": "Flood in Jakarta",
                        "seendate": "20260816T100000Z",
                        "language": "English",
                        "domain": "news.test",
                        "sourcecountry": "Indonesia",
                    }
                ]
            },
        )

    source = SourceDefinition(
        name="fixture-gdelt",
        adapter="gdelt",
        target="https://api.gdelt.test/doc",
        options={"query": "flood Indonesia"},
    )
    result = GDELTAdapter(
        source, httpx.Client(transport=httpx.MockTransport(handler))
    ).fetch()
    assert result.messages[0].text == "Flood in Jakarta"
    assert result.messages[0].raw["source_country"] == "Indonesia"


def test_eonet_contract_maps_open_event() -> None:
    payload = {
        "events": [
            {
                "id": "EONET_1",
                "title": "Tropical Cyclone Example",
                "description": "Near Manila",
                "link": "https://eonet.test/events/1",
                "categories": [{"id": "severeStorms", "title": "Severe Storms"}],
                "sources": [{"id": "JTWC", "url": "https://source.test/cyclone"}],
                "geometry": [
                    {"date": "2026-08-16T10:00:00Z", "type": "Point", "coordinates": [121, 15]}
                ],
            }
        ]
    }
    source = SourceDefinition(
        name="fixture-eonet",
        adapter="eonet",
        target="https://eonet.test/api/v3/events",
    )
    result = EONETAdapter(
        source,
        httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))),
    ).fetch()
    assert result.messages[0].external_id == "EONET_1"
    assert result.messages[0].permalink == "https://source.test/cyclone"
