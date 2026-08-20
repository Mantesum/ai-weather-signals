from pathlib import Path

from ai_weather_signals.pipeline.geocode import LocalGeocoder, haversine_km


def test_local_geocoder_alias_and_fallback() -> None:
    geocoder = LocalGeocoder.from_yaml(Path("config/cities.yaml"))
    assert geocoder.resolve("Москва").city.id == "moscow"  # type: ignore[union-attr]
    assert geocoder.resolve("Heavy rain in London right now").city.id == "london"  # type: ignore[union-attr]
    assert geocoder.resolve("ভারী বৃষ্টি ঢাকা").city.id == "dhaka"  # type: ignore[union-attr]
    assert geocoder.resolve("Flooding near Johannesburg").city.id == "johannesburg"  # type: ignore[union-attr]
    fallback = geocoder.resolve(None, "Chicago")
    assert fallback and fallback.precision == 0.65
    assert haversine_km(55.7558, 37.6173, 55.7558, 37.6173) == 0
