"""Audit domain models: audit log entries and hash chain checkpoints.

The primary audit log storage is in ClickHouse (for efficient analytical queries).
This module provides the PostgreSQL model for checkpoint records and a reference
to the ClickHouse DDL for the main audit_log table.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from aimart.db.base import Base

# Reference DDL for the ClickHouse audit_log table.
# This table is NOT created via SQLAlchemy/Alembic—it is managed separately
# via ClickHouse DDL execution at application startup.
AUDIT_LOG_CLICKHOUSE_DDL = """
CREATE TABLE IF NOT EXISTS aimart_audit.audit_log
(
    log_id                  String,
    log_type                String,
    timestamp               DateTime64(3),
    trace_id                String,
    span_id                 String,
    previous_hash           String,
    current_hash            String,
    actor_type              String,
    actor_id                String,
    session_id              Nullable(String),
    action_operation        String,
    action_target_type      Nullable(String),
    action_target_id        Nullable(String),
    action_result           String,
    action_error_code       Nullable(String),
    action_error_message    Nullable(String),
    data_hash               String,
    data                    String,
    context_ip_hash         Nullable(String)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, log_id)
TTL timestamp + INTERVAL 365 DAY DELETE
"""


class AuditCheckpoint(Base):
    """Hash-chain checkpoint record.

    Every N audit log entries, a checkpoint is generated and stored in
    PostgreSQL. Checkpoints allow efficient verification of log chain
    integrity without scanning the entire ClickHouse table.
    """

    __tablename__ = "audit_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    checkpoint_date: Mapped[str] = mapped_column(
        String(10), nullable=False,
        comment="Date of this checkpoint (YYYY-MM-DD)"
    )
    first_log_id: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="Log ID of the first entry in this checkpoint range"
    )
    last_log_id: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="Log ID of the last entry in this checkpoint range"
    )
    entry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    first_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    merkle_root: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="Merkle root hash of all entries in this range"
    )
    previous_checkpoint_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        comment="Hash of the previous checkpoint (for chain verification)"
    )
    current_hash: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="SHA-256 hash of this checkpoint record"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_audit_checkpoints_date", "checkpoint_date"),
        Index("ix_audit_checkpoints_last_log_id", "last_log_id"),
    )
