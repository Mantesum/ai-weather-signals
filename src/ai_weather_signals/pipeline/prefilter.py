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
        "наводнен",
        "ураган",
        "торнадо",
        "лавин",
        "засух",
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
        "cyclone",
        "typhoon",
        "hurricane",
        "tornado",
        "landslide",
        "drought",
        "avalanche",
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
    "western_europe": (
        "inondation",
        "grêle",
        "tempête",
        "canicule",
        "überschwemmung",
        "hagel",
        "sturm",
        "hitzewelle",
        "inundación",
        "granizo",
        "tormenta",
        "huracán",
        "enchente",
        "tempestade",
        "ciclone",
    ),
    "indonesian_malay": (
        "banjir",
        "hujan",
        "badai",
        "puting beliung",
        "gelombang tinggi",
        "longsor",
        "kekeringan",
        "hujan es",
        "ribut",
        "tanah runtuh",
        "cuaca ekstrem",
    ),
    "vietnamese": (
        "lũ",
        "lụt",
        "ngập",
        "mưa",
        "bão",
        "dông",
        "lốc",
        "sạt lở",
        "nắng nóng",
        "hạn hán",
    ),
    "thai": (
        "น้ำท่วม",
        "น้ำป่า",
        "ฝน",
        "พายุ",
        "ลูกเห็บ",
        "ลมแรง",
        "ดินถล่ม",
        "ภัยแล้ง",
        "อากาศร้อน",
    ),
    "filipino": ("bagyo", "baha", "malakas na ulan"),
    "myanmar": ("ရေကြီး", "မိုးသည်းထန်", "မုန်တိုင်း"),
    "khmer": ("ទឹកជំនន់", "ភ្លៀងខ្លាំង", "ព្យុះ"),
    "lao": ("ນ້ຳຖ້ວມ", "ຖ້ວມ", "ຝົນຕົກໜັກ", "ຝົນ", "ພາຍຸ"),
    "arabic": (
        "فيضانات",
        "سيول",
        "عاصفة",
        "برد",
        "أمطار غزيرة",
        "إعصار",
        "موجة حر",
        "عاصفة ترابية",
    ),
    "south_asian": (
        "बाढ़",
        "भारी बारिश",
        "तूफान",
        "चक्रवात",
        "ओलावृष्टि",
        "लू",
        "বন্যা",
        "ভারী বৃষ্টি",
        "ঝড়",
        "ঘূর্ণিঝড়",
        "سیلاب",
        "شدید بارش",
        "طوفان",
        "ژالہ باری",
    ),
    "east_asian": (
        "洪水",
        "暴雨",
        "台风",
        "暴雪",
        "高温",
        "沙尘暴",
        "大雨",
        "台風",
        "猛暑",
        "大雪",
        "土砂災害",
        "홍수",
        "폭우",
        "태풍",
        "폭설",
        "폭염",
    ),
    "african": ("mafuriko", "mvua kubwa", "dhoruba", "ukame"),
    "middle_east": (
        "سیل",
        "باران شدید",
        "طوفان",
        "sel",
        "şiddetli yağmur",
        "fırtına",
        "dolu",
        "sıcak hava",
    ),
    "central_asian": (
        "су тасқыны",
        "нөсер",
        "дауыл",
        "боран",
        "suv toshqini",
        "kuchli yomg'ir",
        "bo'ron",
        "qurg'oqchilik",
    ),
    "eastern_europe": ("powódź", "ulewa", "burza", "upał", "повінь", "злива", "спека"),
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
