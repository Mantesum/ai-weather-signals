from pathlib import Path

from ai_weather_signals.schemas import SourceDefinition
from ai_weather_signals.source_config import load_sources, set_source_enabled, upsert_source


def test_source_yaml_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "sources.yaml"
    source = SourceDefinition(name="local-feed", adapter="rss", target="https://example.test/rss")
    upsert_source(path, source)
    assert load_sources(path)[0] == source
    set_source_enabled(path, "local-feed", False)
    assert not load_sources(path)[0].enabled


def test_deployment_has_balanced_worldwide_google_coverage() -> None:
    sources = load_sources(Path("config/sources.yaml"))
    google = [source for source in sources if source.adapter == "google_news" and source.enabled]
    names = {source.name for source in google}
    assert {
        "google-news-africa",
        "google-news-north-america",
        "google-news-latin-america-caribbean",
        "google-news-europe",
        "google-news-middle-east-north-africa",
        "google-news-south-asia",
        "google-news-east-asia",
        "google-news-central-asia-caucasus",
        "google-news-oceania-pacific",
        "google-news-sea-regional",
    } <= names
    assert sum(len(source.options.get("queries", [])) for source in google) == 108
    assert all(source.poll_interval_seconds == 3600 for source in google)
    assert all("priority" not in source.tags for source in google)


def test_deployment_has_china_and_additional_aggregators() -> None:
    sources = {source.name: source for source in load_sources(Path("config/sources.yaml"))}
    expected = {
        "google-news-china-local-media",
        "cgtn-china-world-rss",
        "yahoo-news-rss",
        "bing-news-weather",
        "msn-weather-discovery",
        "reuters-climate-disaster",
    }
    assert expected <= sources.keys()
    assert all(sources[name].enabled for name in expected)
    assert sources["reuters-climate-disaster"].adapter == "google_news"
    assert "feeds.reuters.com" not in sources["reuters-climate-disaster"].target
    assert sources["msn-weather-discovery"].adapter == "multi_rss"
