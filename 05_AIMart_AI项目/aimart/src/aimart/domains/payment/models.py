"""Payment domain models: budget pools, transactions, authorization, escrow."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aimart.db.base import Base, TimestampMixin

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PoolStatus(str):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class CurrencyEnum(str):
    CNY = "CNY"
    USD = "USD"
    USDC = "USDC"


class AuthorityLevel(str):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class SettlementChannel(str):
    FIAT = "fiat"
    X402 = "x402"
    ACP = "acp"


class EscrowStatus(str):
    FROZEN = "frozen"
    PARTIAL_RELEASE = "partial_release"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class TransactionStatus(str):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class AuthRequestStatus(str):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class NotificationChannel(str):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class BudgetPool(TimestampMixin, Base):
    """Budget pool owned by a participant (Owner).

    Each pool has balance, frozen amount, and multi-level limits (daily/weekly/monthly).
    """

    __tablename__ = "budget_pools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="CNY")
    balance: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    frozen_amount: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    total_cap: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    single_transaction_max: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=500
    )
    daily_max: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=2000
    )
    weekly_max: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=10000
    )
    monthly_max: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=30000
    )
    auto_recharge: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    recharge_threshold: Mapped[float | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    recharge_amount: Mapped[float | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )

    # relationships
    allocations: Mapped[list[AgentBudgetAllocation]] = relationship(
        "AgentBudgetAllocation", back_populates="pool", lazy="selectin"
    )
    transactions: Mapped[list[PaymentTransaction]] = relationship(
        "PaymentTransaction", back_populates="pool", lazy="selectin"
    )
    snapshots: Mapped[list[DailyBudgetSnapshot]] = relationship(
        "DailyBudgetSnapshot", back_populates="pool", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_budget_pools_owner_id", "owner_id"),
        Index("ix_budget_pools_status", "status"),
        CheckConstraint("balance >= 0", name="ck_budget_pool_balance_nonneg"),
        CheckConstraint(
            "frozen_amount >= 0", name="ck_budget_pool_frozen_nonneg"
        ),
    )

    @property
    def available_balance(self) -> float:
        return float(self.balance) - float(self.frozen_amount)


class AgentBudgetAllocation(TimestampMixin, Base):
    """Per-agent budget allocation within a pool.

    Limits daily and per-call spending for a specific agent.
    """

    __tablename__ = "agent_budget_allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("budget_pools.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    daily_max: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=500
    )
    per_call_max: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=1
    )
    daily_spent: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    daily_spent_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    spending_authority_level: Mapped[str] = mapped_column(
        String(2), nullable=False, default="L0"
    )

    # relationships
    pool: Mapped[BudgetPool] = relationship(
        "BudgetPool", back_populates="allocations"
    )

    __table_args__ = (
        Index("ix_agent_budget_allocations_agent_pool", "agent_id", "pool_id", unique=True),
    )


class PaymentTransaction(TimestampMixin, Base):
    """Payment transaction record.

    Tracks the full lifecycle of a payment from authorization through
    escrow to settlement.
    """

    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("budget_pools.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="CNY")
    commission_rate: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.03
    )
    commission_amount: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    provider_payout: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    settlement_channel: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    escrow_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="frozen"
    )
    escrow_frozen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escrow_released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    authorization_level: Mapped[str | None] = mapped_column(
        String(2), nullable=True
    )
    authorization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    authorized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    authorized_by: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    effect_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effect_reported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    failure_reason: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    external_settlement_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    settlement_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # relationships
    pool: Mapped[BudgetPool] = relationship(
        "BudgetPool", back_populates="transactions"
    )
    authorization_requests: Mapped[list[AuthorizationRequest]] = relationship(
        "AuthorizationRequest", back_populates="transaction", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_payment_transactions_order_id", "order_id"),
        Index("ix_payment_transactions_agent_id", "agent_id"),
        Index("ix_payment_transactions_provider_id", "provider_id"),
        Index("ix_payment_transactions_status", "status"),
        Index("ix_payment_transactions_escrow_status", "escrow_status"),
        CheckConstraint(
            "effect_score IS NULL OR (effect_score >= 0 AND effect_score <= 5)",
            name="ck_payment_transaction_effect_score_range",
        ),
    )


class AuthorizationRequest(Base):
    """Authorization request for L2/L3 transactions.

    Requires Owner approval/confirmation before the transaction proceeds.
    """

    __tablename__ = "authorization_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    level: Mapped[str] = mapped_column(String(2), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    notification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notification_channel: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    reject_reason: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # relationships
    transaction: Mapped[PaymentTransaction] = relationship(
        "PaymentTransaction", back_populates="authorization_requests"
    )

    __table_args__ = (
        Index("ix_authorization_requests_owner_status", "owner_id", "status"),
        Index("ix_authorization_requests_expires_at", "expires_at"),
    )


class DailyBudgetSnapshot(Base):
    """Daily budget consumption snapshot for analytics and limit tracking."""

    __tablename__ = "daily_budget_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("budget_pools.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    daily_spent: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    transaction_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # relationships
    pool: Mapped[BudgetPool] = relationship(
        "BudgetPool", back_populates="snapshots"
    )

    __table_args__ = (
        Index("ix_daily_budget_snapshots_pool_agent_date", "pool_id", "agent_id", "snapshot_date", unique=True),
    )


class AnomalyDetectionEvent(TimestampMixin, Base):
    """Anomalous payment event detected by the anomaly detection system."""

    __tablename__ = "anomaly_detection_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    budget_pool_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    anomaly_type: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="burst_spend | high_frequency_micro | budget_depleted | single_seller_concentration | off_hours_large"
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info",
        comment="info | warning | critical"
    )
    details: Mapped[str] = mapped_column(
        String, nullable=False,
        comment="JSON with detection details"
    )
    auto_action_taken: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        comment="agent_suspended | rate_limited | notification_sent | no_action"
    )
    owner_notified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    __table_args__ = (
        Index("ix_anomaly_detection_events_agent", "agent_id"),
        Index("ix_anomaly_detection_events_type", "anomaly_type"),
    )
