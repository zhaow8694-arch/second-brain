from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogQuery(BaseModel):
    """Query parameters for audit log retrieval."""

    log_type: str | None = None
    actor_id: str | None = None
    target_id: str | None = None
    action: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=200)


class AuditLogEntry(BaseModel):
    """Single audit log entry matching the ClickHouse table schema."""

    log_id: str
    log_type: str
    timestamp: datetime
    trace_id: str
    span_id: str
    previous_hash: str
    current_hash: str
    actor_type: str
    actor_id: str
    session_id: str | None = None
    action_operation: str
    action_target_type: str | None = None
    action_target_id: str | None = None
    action_result: str
    action_error_code: str | None = None
    action_error_message: str | None = None
    data_hash: str
    data: str
    context_ip_hash: str | None = None


class AuditLogResponse(BaseModel):
    """Paginated response for audit log queries."""

    entries: list[AuditLogEntry]
    total: int
    page: int
    size: int


class HashChainVerification(BaseModel):
    """Result of hash chain verification."""

    valid: bool
    message: str
    merkle_root: str
