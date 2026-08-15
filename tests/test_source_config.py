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
