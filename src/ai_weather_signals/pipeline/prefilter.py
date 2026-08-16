import re
from dataclasses import dataclass

from .normalize import normalized_text

WEATHER_TERMS = {
    "ru": (
        "дожд",
        "ливень",
        "снег",
        "метель",
        "град",
        "гроз",
        "ветер",
        "шквал",
        "туман",
        "голол",
        "мороз",
        "жар",
        "потоп",
        "затоп",
        "пыльн",
        "мокрый снег",
        "ледяной дожд",
        "видимост",
    ),
    "en": (
        "rain",
        "downpour",
        "snow",
        "blizzard",
        "hail",
        "thunder",
        "storm",
        "wind",
        "squall",
        "fog",
        "ice",
        "freezing",
        "heat",
        "flood",
        "dust",
        "sleet",
        "freezing rain",
        "visibility",
    ),
    "other": (
        "pluie",
        "neige",
        "orage",
        "regen",
        "schnee",
        "gewitter",
        "lluvia",
        "nieve",
        "pioggia",
        "neve",
        "雨",
        "雪",
        "비",
        "눈",
    ),
}
EXCLUSION_PATTERNS = (
    re.compile(r"\b(прогноз|ожидается|будет|forecast|expected|tomorrow|завтра)\b", re.I),
    re.compile(r"\b(вопрос|кто знает|is it|will it|weather like)\b.*\?", re.I),
)
ASCII_TERM = re.compile(r"^[a-z ]+$")


@dataclass(frozen=True)
class FilterResult:
    candidate: bool
    score: float
    reasons: tuple[str, ...]


def _contains_term(value: str, term: str) -> bool:
    if ASCII_TERM.fullmatch(term):
        return re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", value) is not None
    return term in value


def prefilter(text: str, place_names: set[str] | None = None) -> FilterResult:
    value = normalized_text(text)
    hits = sum(_contains_term(value, term) for terms in WEATHER_TERMS.values() for term in terms)
    place_hit = bool(place_names and any(name in value for name in place_names))
    excluded = any(pattern.search(value) for pattern in EXCLUSION_PATTERNS)
    score = min(1.0, hits * 0.35 + (0.2 if place_hit else 0) - (0.2 if excluded else 0))
    reasons = tuple(
        filter(
            None,
            (
                "weather_term" if hits else "",
                "place" if place_hit else "",
                "possible_forecast_or_question" if excluded else "",
            ),
        )
    )
    return FilterResult(candidate=hits > 0 and score >= 0.25, score=max(0.0, score), reasons=reasons)
