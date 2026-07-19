"""Trust domain models: trust events, certifications, trust scores."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from aimart.db.base import Base, TimestampMixin

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TargetType(enum.StrEnum):
    ITEM = "item"
    PROVIDER = "provider"
    AGENT = "agent"


class TrustEventType(enum.StrEnum):
    PURCHASE = "purchase"
    EFFECT_REPORT = "effect_report"
    CERTIFICATION = "certification"
    COMPLAINT = "complaint"
    DISPUTE = "dispute"


class CertificationStatusEnum(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TrustScore(TimestampMixin, Base):
    """Current trust score for a target entity (item, provider, or agent).

    Maintains a single current score per target, updated by trust events.
    """

    __tablename__ = "trust_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_type: Mapped[TargetType] = mapped_column(
        String(32), nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    score: Mapped[float] = mapped_column(
        Float, nullable=False, default=50.0,
        comment="Current trust score (0-100)"
    )
    score_components: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="JSON breakdown: benchmark, effect_report, peer_review, certification"
    )
    total_events: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Total number of trust events processed"
    )
    last_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="ID of the most recent trust event"
    )
    last_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_trust_scores_target", "target_type", "target_id", unique=True),
        Index("ix_trust_scores_score", "score"),
    )


class TrustEvent(Base):
    """An event that influences the trust score of a target entity.

    Targets can be items, providers, or agents. Each event carries
    a score_delta that reflects its impact on the trust score.
    """

    __tablename__ = "trust_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_type: Mapped[TargetType] = mapped_column(
        String(32), nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    event_type: Mapped[TrustEventType] = mapped_column(
        String(32), nullable=False
    )
    event_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_delta: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    source: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        comment="system | agent | provider | certifier | platform"
    )
    reference_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        comment="order_id | dispute_id | cert_id | report_id"
    )
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_trust_events_target", "target_type", "target_id"),
        Index("ix_trust_events_event_type", "event_type"),
        Index("ix_trust_events_created_at", "created_at"),
    )


class Certification(Base):
    """A certification record issued by a certifier for a catalog item.

    Tracks the benchmark results, verification status, and expiration.
    """

    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    certifier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    certification_level: Mapped[str] = mapped_column(
        String(32), nullable=False, default="platform_certified",
        comment="platform_certified | premium_certified"
    )
    status: Mapped[CertificationStatusEnum] = mapped_column(
        String(32),
        nullable=False,
        default=CertificationStatusEnum.PENDING,
    )
    benchmark_results: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score_boost: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Trust score boost from this certification"
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_certifications_item_id", "item_id"),
        Index("ix_certifications_certifier_id", "certifier_id"),
        Index("ix_certifications_status", "status"),
    )


class EffectReport(TimestampMixin, Base):
    """Effect report submitted by an agent after consuming a capability.

    Structured feedback that triggers trust score updates.
    """

    __tablename__ = "effect_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    success: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    effect_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3,
        comment="Effect score 0-5"
    )
    actual_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    declared_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    declared_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    detail: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Additional structured feedback"
    )

    __table_args__ = (
        Index("ix_effect_reports_order_id", "order_id"),
        Index("ix_effect_reports_agent_id", "agent_id"),
        Index("ix_effect_reports_item_id", "item_id"),
    )
