import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now_utc() -> datetime:
    return datetime.now(UTC)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    adapter: Mapped[str] = mapped_column(String(32))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    target: Mapped[str] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(16), default="und")
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=600)
    trust: Mapped[float] = mapped_column(Float, default=0.5)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    store_text: Mapped[bool] = mapped_column(Boolean, default=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor: Mapped[str | None] = mapped_column(Text)
    last_error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), default="running")
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    classified_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class RawMessage(Base):
    __tablename__ = "raw_messages"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_source_message"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(512))
    permalink: Mapped[str | None] = mapped_column(Text)
    author_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    text: Mapped[str | None] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(16))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    candidate_score: Mapped[float | None] = mapped_column(Float)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[Source] = relationship()
    attachments: Mapped[list["Attachment"]] = relationship(cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(ForeignKey("raw_messages.id", ondelete="CASCADE"), index=True)
    media_type: Mapped[str] = mapped_column(String(32), default="unknown")
    remote_url: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(200))
    prompt_version: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(String(32))
    prompt_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    __table_args__ = (UniqueConstraint("model_name", "prompt_sha256", name="uq_model_prompt"),)


class WeatherSignal(Base):
    __tablename__ = "weather_signals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str] = mapped_column(ForeignKey("raw_messages.id"), unique=True)
    model_version_id: Mapped[int | None] = mapped_column(ForeignKey("model_versions.id"))
    assertion_type: Mapped[str] = mapped_column(String(48), index=True)
    phenomenon: Mapped[str] = mapped_column(String(48), index=True)
    intensity: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    time_precision: Mapped[float] = mapped_column(Float)
    evidence_type: Mapped[str] = mapped_column(String(32))
    has_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    has_video: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_confidence: Mapped[float] = mapped_column(Float)
    is_copy: Mapped[bool] = mapped_column(Boolean, default=False)
    place_name: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    message: Mapped[RawMessage] = relationship()
    geocode: Mapped["GeocodeResult | None"] = relationship(cascade="all, delete-orphan")


class GeocodeResult(Base):
    __tablename__ = "geocode_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[str] = mapped_column(ForeignKey("weather_signals.id", ondelete="CASCADE"), unique=True)
    city_id: Mapped[str | None] = mapped_column(String(64), index=True)
    geonames_id: Mapped[int | None] = mapped_column(Integer, index=True)
    display_name: Mapped[str] = mapped_column(String(240))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    precision: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(32), default="local_gazetteer")


class WeatherEvent(Base):
    __tablename__ = "weather_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phenomenon: Mapped[str] = mapped_column(String(48), index=True)
    city_id: Mapped[str | None] = mapped_column(String(64), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    independent_authors: Mapped[int] = mapped_column(Integer, default=0)
    platform_count: Mapped[int] = mapped_column(Integer, default=0)
    official_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    links: Mapped[list["EventSignal"]] = relationship(cascade="all, delete-orphan")
    __table_args__ = (Index("ix_event_geo_time", "latitude", "longitude", "last_seen_at"),)


class EventSignal(Base):
    __tablename__ = "event_signals"
    event_id: Mapped[str] = mapped_column(
        ForeignKey("weather_events.id", ondelete="CASCADE"), primary_key=True
    )
    signal_id: Mapped[str] = mapped_column(
        ForeignKey("weather_signals.id", ondelete="CASCADE"), primary_key=True
    )
    contribution: Mapped[float] = mapped_column(Float)
    signal: Mapped[WeatherSignal] = relationship()


class ProcessingError(Base):
    __tablename__ = "processing_errors"
    id: Mapped[int] = mapped_column(primary_key=True)
    stage: Mapped[str] = mapped_column(String(48), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), index=True)
    error_type: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    retryable: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
