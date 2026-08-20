from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from .enums import AssertionType, EvidenceType, Phenomenon


class SourceDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,63}$")
    adapter: str
    enabled: bool = True
    target: str
    region: str | None = None
    language: str = "und"
    poll_interval_seconds: int = Field(default=600, ge=30)
    trust: float = Field(default=0.5, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    store_text: bool = True
    env_token: str | None = None
    options: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)


class NormalizedMessage(BaseModel):
    source_name: str
    external_id: str
    permalink: str | None = None
    author_external_id: str | None = None
    text: str
    language: str = "und"
    published_at: datetime
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    media_urls: list[str] = Field(default_factory=list)
    raw: dict[str, object] = Field(default_factory=dict)


class LLMExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_weather_candidate: bool
    assertion_type: AssertionType
    phenomenon: Phenomenon
    intensity: float = Field(ge=0, le=1)
    place_name: str | None = None
    observed_at: datetime | None = None
    time_precision: float = Field(
        ge=0,
        le=1,
        description=(
            "Confidence that observed_at is temporally precise, from 0.0 (very uncertain) "
            "to 1.0 (exact); never a duration or timestamp"
        ),
    )
    evidence_type: EvidenceType = EvidenceType.TEXT
    has_photo: bool = False
    has_video: bool = False
    confidence: float = Field(ge=0, le=1)
    is_repost_or_copy: bool = False
    rationale_code: str = Field(max_length=80)

    @field_validator("time_precision", mode="before")
    @classmethod
    def normalize_duration_like_time_precision(cls, value: object) -> object:
        """Recover when a small local model returns an uncertainty duration instead of a score."""
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 1:
            return value
        if value <= 60:
            return 0.95
        if value <= 3600:
            return 0.85
        if value <= 86400:
            return 0.65
        if value <= 604800:
            return 0.45
        return 0.25

    @model_validator(mode="after")
    def reject_impossible_candidate(self) -> "LLMExtraction":
        excluded = {
            AssertionType.FORECAST,
            AssertionType.HISTORICAL,
            AssertionType.QUESTION,
            AssertionType.NEGATION,
            AssertionType.JOKE,
            AssertionType.IRRELEVANT,
        }
        if self.assertion_type in excluded and self.is_weather_candidate:
            raise ValueError("excluded assertion type cannot be a weather candidate")
        return self


class EventEvidence(BaseModel):
    observed_at: datetime
    assertion_type: AssertionType
    evidence_type: EvidenceType
    permalink: HttpUrl | None = None
    excerpt: str | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    phenomenon: Phenomenon
    latitude: float
    longitude: float
    city_id: str | None
    starts_at: datetime
    last_seen_at: datetime
    status: str
    confidence: float
    independent_authors: int
    platform_count: int
    updated_at: datetime
