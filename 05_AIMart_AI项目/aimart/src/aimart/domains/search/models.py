"""Search domain models: search queries, capability indices."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from aimart.db.base import Base

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NeedType(enum.StrEnum):
    MODEL = "model"
    SKILL = "skill"
    EXPERT = "expert"
    COMPUTE = "compute"


class ItemStatus(enum.StrEnum):
    ACTIVE = "active"
    DELISTED = "delisted"
    SUSPENDED = "suspended"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class SearchQuery(Base):
    """Persistent record of every capability search performed by an AI Agent.

    Captures the full need specification, the matching latency, and any
    downstream action (trial / purchase) taken on the results.
    """

    __tablename__ = "search_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    need_type: Mapped[NeedType] = mapped_column(
        String(32), nullable=False, index=True
    )
    domains: Mapped[list] = mapped_column(JSONB, nullable=False)
    task_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scoring_weights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    selected_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    trial_initiated: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    purchased: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    query_latency_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    match_latency_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
    )

    __table_args__ = (
        Index("ix_search_queries_agent_id", "agent_id"),
        Index("ix_search_queries_need_type", "need_type"),
        Index("ix_search_queries_created_at", "created_at"),
    )


class CapabilityIndex(Base):
    """Denormalised index row for every capability item listed on the marketplace.

    Synchronised from the catalog domain and enriched with performance /
    trust metrics.  This is the primary table used by the matching engine
    and the Elasticsearch indexer.
    """

    __tablename__ = "capability_indices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True
    )
    agentcard_version: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    item_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    item_version: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    domains: Mapped[list] = mapped_column(JSONB, nullable=False)
    task_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    supported_languages: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    latency_p50_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_p99_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    throughput_rps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    availability_sla: Mapped[float | None] = mapped_column(Float, nullable=True)
    trust_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=50.0
    )
    pricing_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    price_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    status: Mapped[ItemStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ItemStatus.ACTIVE,
    )
    es_index_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    certification_status: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        Index("ix_capability_indices_item_id", "item_id", unique=True),
        Index("ix_capability_indices_item_type", "item_type"),
        Index("ix_capability_indices_status", "status"),
        Index("ix_capability_indices_trust_score", "trust_score"),
    )


class TrialLimit(Base):
    """Track trial usage limits per agent per item.

    Prevents excessive free trials.
    """

    __tablename__ = "trial_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    trial_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_trial_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="YYYY-MM-DD"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        Index("ix_trial_limits_agent_item", "agent_id", "item_id", unique=True),
    )
