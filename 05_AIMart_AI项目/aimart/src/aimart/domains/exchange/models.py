"""Exchange domain models: orders, trials, escrow, delivery."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aimart.db.base import Base

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OrderStatus(enum.StrEnum):
    CREATED = "created"
    PENDING_PAYMENT = "pending_payment"
    AUTHORIZED = "authorized"
    PAID = "paid"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class TrialStatus(enum.StrEnum):
    REQUESTED = "requested"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class DeliveryMethod(enum.StrEnum):
    API_CALL = "api_call"
    WEIGHT_DOWNLOAD = "weight_download"
    CODE_PACKAGE = "code_package"
    INSTANCE = "instance"


class EscrowAccountType(enum.StrEnum):
    PLATFORM = "platform"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Order(Base):
    """A marketplace order placed by an AI Agent for a catalog item.

    Tracks the full lifecycle from creation through payment, delivery,
    completion, cancellation, or dispute.
    """

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, comment="Owner of the agent"
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    query_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="Search query that led to this order"
    )
    trial_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="Trial session that preceded this order"
    )
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pricing_model: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[OrderStatus] = mapped_column(
        String(32),
        nullable=False,
        default=OrderStatus.CREATED,
    )
    budget_pool_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="Budget pool used for payment"
    )
    payment_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    escrow_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    effect_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Effect score reported by the agent (0-5)"
    )
    effect_reported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # relationships
    trial_info: Mapped[Trial | None] = relationship(
        "Trial", back_populates="order", foreign_keys="Trial.order_id",
        uselist=False, lazy="selectin"
    )

    __table_args__ = (
        Index("ix_orders_agent_id", "agent_id"),
        Index("ix_orders_item_id", "item_id"),
        Index("ix_orders_provider_id", "provider_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
    )


class Trial(Base):
    """A sandbox trial session initiated by an AI Agent for a catalog item.

    Captures input data, constrained output, and performance metrics
    observed during the sandboxed execution.
    """

    __tablename__ = "trials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        comment="Order created after this trial, if any"
    )
    query_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="Search query that led to this trial"
    )
    status: Mapped[TrialStatus] = mapped_column(
        String(32),
        nullable=False,
        default=TrialStatus.REQUESTED,
    )
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performance_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    sandbox_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "input_scale_pct": 10,
            "max_calls": 5,
            "timeout_ms": 30000,
        },
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # relationships
    order: Mapped[Order | None] = relationship(
        "Order", back_populates="trial_info", foreign_keys=[order_id],
        uselist=False, lazy="selectin"
    )

    __table_args__ = (
        Index("ix_trials_agent_id", "agent_id"),
        Index("ix_trials_item_id", "item_id"),
        Index("ix_trials_status", "status"),
    )


class Delivery(Base):
    """Capability delivery record.

    Tracks how and when a purchased capability was delivered to the agent.
    """

    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_method: Mapped[DeliveryMethod] = mapped_column(
        String(32),
        nullable=False,
    )
    delivery_endpoint: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    delivery_latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    input_data_size_bytes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    output_data_size_bytes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    data_sensitivity: Mapped[str | None] = mapped_column(
        String(32), nullable=True, default="public"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_deliveries_order_id", "order_id"),
    )


class Dispute(Base):
    """A dispute raised by an agent or owner regarding an order."""

    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    initiator_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="agent | owner | provider"
    )
    initiator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    dispute_type: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="quality | sla_violation | unauthorized_charge | false_declaration"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    disputed_amount: Mapped[float | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open",
        comment="open | investigating | resolved | dismissed"
    )
    resolution: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        comment="buyer_wins | seller_wins | split | dismissed"
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
        Index("ix_disputes_order_id", "order_id"),
        Index("ix_disputes_status", "status"),
    )
