from datetime import datetime

from ..enums import AssertionType, EvidenceType, Phenomenon
from ..schemas import LLMExtraction
from .normalize import normalized_text

PHENOMENA = {
    Phenomenon.HEAVY_RAIN: ("ливень", "сильный дожд", "downpour", "heavy rain"),
    Phenomenon.RAIN: ("дожд", "rain"),
    Phenomenon.HEAVY_SNOW: ("сильный снег", "метель", "blizzard", "heavy snow"),
    Phenomenon.SNOW: ("снег", "snow"),
    Phenomenon.HAIL: ("град", "hail"),
    Phenomenon.THUNDERSTORM: ("гроз", "thunder"),
    Phenomenon.STRONG_WIND: ("сильный ветер", "strong wind"),
    Phenomenon.FOG: ("туман", "fog"),
    Phenomenon.FLOOD: ("затоп", "наводнен", "flood"),
    Phenomenon.EXTREME_HEAT: ("аномальная жара", "extreme heat"),
    Phenomenon.EXTREME_COLD: ("сильный мороз", "extreme cold"),
}


class OfflineClassifier:
    """Deterministic network-free fixture/smoke classifier, never the production default."""

    prompt_hash = "offline-rules-v1"
    prompt_version = "offline-rules-v1"

    def classify(
        self,
        text: str,
        source_region: str | None,
        published_at: str,
        source_kind: str = "social",
        timeout_seconds: float | None = None,
    ) -> LLMExtraction:
        value = normalized_text(text)
        assertion = AssertionType.PERSONAL_CURRENT
        if source_kind == "news":
            assertion = AssertionType.NEWS
        elif source_kind == "official":
            assertion = AssertionType.OFFICIAL
        candidate = True
        if any(word in value for word in ("прогноз", "ожидается", "tomorrow", "forecast")):
            assertion, candidate = AssertionType.FORECAST, False
        elif "?" in text:
            assertion, candidate = AssertionType.QUESTION, False
        elif any(word in value for word in ("нет дожд", "не идет", "no rain", "isn't raining")):
            assertion, candidate = AssertionType.NEGATION, False
        elif any(word in value for word in ("в душе", "метафор", "raining cats")):
            assertion, candidate = AssertionType.JOKE, False
        phenomenon = next(
            (kind for kind, terms in PHENOMENA.items() if any(term in value for term in terms)),
            Phenomenon.UNKNOWN,
        )
        return LLMExtraction(
            is_weather_candidate=candidate,
            assertion_type=assertion,
            phenomenon=phenomenon,
            intensity=0.75 if "сильн" in value or "heavy" in value else 0.5,
            place_name=source_region,
            observed_at=datetime.fromisoformat(published_at),
            time_precision=0.8,
            evidence_type=EvidenceType.TEXT,
            confidence=0.72 if candidate else 0.85,
            rationale_code="offline_fixture_rules",
        )
