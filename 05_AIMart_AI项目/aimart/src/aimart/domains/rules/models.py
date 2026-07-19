"""Rules domain models: rule definitions and execution records."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from aimart.db.base import Base


class RuleDefinition(Base):
    """Persistent rule definition stored in the database.

    Rules can be dynamically enabled/disabled and configured without
    code changes.
    """

    __tablename__ = "rule_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True,
        comment="Unique rule identifier, e.g. TR-001, BUDGET-001"
    )
    rule_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Human-readable rule name"
    )
    category: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="trading | budget | security | sla | pricing"
    )
    severity: Mapped[str] = mapped_column(
        String(32), nullable=False, default="block",
        comment="info | warning | block | suspend"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Detailed rule description"
    )
    applies_to_operations: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, default=list,
        comment="List of operations this rule applies to, empty = all"
    )
    config: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict,
        comment="Rule-specific configuration (thresholds, params, etc.)"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Evaluation priority (higher = evaluated first)"
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
        Index("ix_rule_definitions_category", "category"),
        Index("ix_rule_definitions_enabled", "enabled"),
    )


class RuleExecutionRecord(Base):
    """Record of a rule evaluation during a business operation.

    Captures the context and outcome of each rule evaluation for
    audit and debugging purposes.
    """

    __tablename__ = "rule_execution_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    operation: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment="The business operation being evaluated"
    )
    actor_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    actor_id: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    context_snapshot: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Snapshot of the rule context at evaluation time"
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(32), nullable=False, default="block"
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_rule_execution_records_rule_id", "rule_id"),
        Index("ix_rule_execution_records_operation", "operation"),
        Index("ix_rule_execution_records_created_at", "created_at"),
    )
