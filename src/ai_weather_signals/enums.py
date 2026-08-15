from enum import StrEnum


class Phenomenon(StrEnum):
    HEAT = "heat"
    EXTREME_HEAT = "extreme_heat"
    COLD = "cold"
    EXTREME_COLD = "extreme_cold"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    HEAVY_SNOW = "heavy_snow"
    SLEET = "sleet"
    HAIL = "hail"
    THUNDERSTORM = "thunderstorm"
    STRONG_WIND = "strong_wind"
    SQUALL = "squall"
    FOG = "fog"
    ICE = "ice"
    FREEZING_RAIN = "freezing_rain"
    FLOOD = "flood"
    DUST_STORM = "dust_storm"
    POOR_VISIBILITY = "poor_visibility"
    UNKNOWN = "unknown_weather"


class AssertionType(StrEnum):
    PERSONAL_CURRENT = "personal_current_observation"
    PROBABLE_PERSONAL = "probable_personal_observation"
    RETELLING = "retelling"
    OFFICIAL = "official_report"
    NEWS = "news"
    FORECAST = "forecast"
    HISTORICAL = "historical"
    QUESTION = "question"
    NEGATION = "negation"
    JOKE = "metaphor_or_joke"
    IRRELEVANT = "irrelevant"


class EventStatus(StrEnum):
    UNCONFIRMED = "unconfirmed"
    PROBABLE = "probable"
    CONFIRMED = "confirmed"
    CONFLICTING = "conflicting"
    EXPIRED = "expired"
    NEEDS_REVIEW = "needs_review"


class EvidenceType(StrEnum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    OFFICIAL_BULLETIN = "official_bulletin"
