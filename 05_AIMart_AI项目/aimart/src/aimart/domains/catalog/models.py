"""Catalog domain models: catalog items, AgentCard versions, pricing plans."""

from __future__ import annotations

import enum
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aimart.db.base import Base, TimestampMixin

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ItemType(enum.StrEnum):
    MODEL = "model"
    SKILL = "skill"
    EXPERT = "expert"
    COMPUTE = "compute"


class CatalogItemStatus(enum.StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DELISTED = "delisted"
    SUSPENDED = "suspended"


class CertificationStatus(enum.StrEnum):
    NONE = "none"
    PENDING = "pending"
    CERTIFIED = "certified"
    REJECTED = "rejected"


class PricingModelType(enum.StrEnum):
    PER_CALL = "per_call"
    PER_TOKEN = "per_token"
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    SUBSCRIPTION = "subscription"
    FREE = "free"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CatalogItem(TimestampMixin, Base):
    """A capability offering listed on the AIMart marketplace.

    Each item is backed by a full AgentCard JSON document that describes
    identity, capabilities, performance benchmarks, pricing, delivery
    mechanism, and trust metadata.
    """

    __tablename__ = "catalog_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    item_type: Mapped[ItemType] = mapped_column(
        String(32), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agentcard: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    agentcard_hash: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="SHA-256 hash of the AgentCard JSON"
    )
    agentcard_schema_version: Mapped[str | None] = mapped_column(
        String(16), nullable=True, default="1.0"
    )
    status: Mapped[CatalogItemStatus] = mapped_column(
        String(32),
        nullable=False,
        default=CatalogItemStatus.PENDING,
    )
    certification_status: Mapped[CertificationStatus] = mapped_column(
        String(32),
        nullable=False,
        default=CertificationStatus.NONE,
    )
    trust_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=50.0
    )
    total_transactions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    total_revenue: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # relationships
    versions: Mapped[list[CatalogItemVersion]] = relationship(
        "CatalogItemVersion", back_populates="item",
        lazy="selectin",
        order_by="CatalogItemVersion.created_at.desc()",
    )
    pricing_plans: Mapped[list[PricingPlan]] = relationship(
        "PricingPlan", back_populates="item", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_catalog_items_provider_id", "provider_id"),
        Index("ix_catalog_items_item_type", "item_type"),
        Index("ix_catalog_items_status", "status"),
        Index("ix_catalog_items_trust_score", "trust_score"),
    )


class CatalogItemVersion(TimestampMixin, Base):
    """Version tracking for catalog items.

    Each update creates a new version record for audit trail and
    rollback support.
    """

    __tablename__ = "catalog_item_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    version_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="patch",
        comment="major | minor | patch"
    )
    agentcard: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False,
        comment="Snapshot of the AgentCard at this version"
    )
    agentcard_hash: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_reverification: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # relationships
    item: Mapped[CatalogItem] = relationship(
        "CatalogItem", back_populates="versions"
    )

    __table_args__ = (
        Index("ix_catalog_item_versions_item_version", "item_id", "version", unique=True),
    )


class PricingPlan(TimestampMixin, Base):
    """Pricing plan for a catalog item.

    A catalog item can have multiple pricing plans (e.g., per-call,
    subscription, bulk discount).
    """

    __tablename__ = "pricing_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pricing_model: Mapped[PricingModelType] = mapped_column(
        String(32),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    unit_price: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False
    )
    billing_unit: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
        comment="call | token | minute | hour | month"
    )
    min_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    max_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    setup_fee: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # relationships
    item: Mapped[CatalogItem] = relationship(
        "CatalogItem", back_populates="pricing_plans"
    )

    __table_args__ = (
        Index("ix_pricing_plans_item_id", "item_id"),
    )
