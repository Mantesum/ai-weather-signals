from ai_weather_signals.pipeline.normalize import author_hash, normalized_text, text_hash
from ai_weather_signals.pipeline.prefilter import prefilter


def test_normalization_and_stable_hash() -> None:
    assert normalized_text("  СИЛЬНЫЙ   дождь https://example.test/x ") == "сильный дождь"
    assert text_hash("Rain  now") == text_hash("RAIN now")
    assert author_hash("source", "42", "secret-salt") == author_hash("source", "42", "secret-salt")


def test_multilingual_prefilter() -> None:
    assert prefilter("У нас в Москве сильный дождь", {"москва"}).candidate
    assert prefilter("Heavy snow in Chicago right now", {"chicago"}).candidate
    assert not prefilter("Обычный рабочий день", {"москва"}).candidate
