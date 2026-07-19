from __future__ import annotations

from datetime import date, datetime
from typing import Any

import structlog

from aimart.domains.audit.hashchain import compute_merkle_root, verify_hash_chain
from aimart.domains.audit.schemas import (
    AuditLogEntry,
    AuditLogQuery,
    AuditLogResponse,
    HashChainVerification,
)

logger = structlog.get_logger(__name__)


class AuditQueryService:
    """Service layer for querying audit logs and verifying hash chains."""

    def __init__(self, clickhouse_client: Any) -> None:
        self._ch = clickhouse_client

    def query_logs(self, query: AuditLogQuery) -> AuditLogResponse:
        """Query audit logs from ClickHouse with pagination."""
        conditions: list[str] = []
        params: list[Any] = []

        if query.log_type is not None:
            conditions.append("log_type = %s")
            params.append(query.log_type)
        if query.actor_id is not None:
            conditions.append("actor_id = %s")
            params.append(query.actor_id)
        if query.target_id is not None:
            conditions.append("action_target_id = %s")
            params.append(query.target_id)
        if query.action is not None:
            conditions.append("action_operation = %s")
            params.append(query.action)
        if query.start_time is not None:
            conditions.append("timestamp >= %s")
            params.append(query.start_time)
        if query.end_time is not None:
            conditions.append("timestamp <= %s")
            params.append(query.end_time)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        offset = (query.page - 1) * query.size

        # Count
        count_sql = f"SELECT count() FROM audit_log {where_clause}"
        total = self._ch.execute(count_sql, params)[0][0]

        # Data
        data_sql = (
            f"SELECT * FROM audit_log {where_clause} "
            f"ORDER BY timestamp, log_id "
            f"LIMIT {query.size} OFFSET {offset}"
        )
        rows = self._ch.execute(data_sql, params)

        columns = [
            "log_id", "log_type", "timestamp", "trace_id", "span_id",
            "previous_hash", "current_hash", "actor_type", "actor_id",
            "session_id", "action_operation", "action_target_type",
            "action_target_id", "action_result", "action_error_code",
            "action_error_message", "data_hash", "data", "context_ip_hash",
        ]

        entries: list[AuditLogEntry] = []
        for row in rows:
            entry_dict = dict(zip(columns, row))
            entries.append(AuditLogEntry(**entry_dict))

        return AuditLogResponse(
            entries=entries,
            total=total,
            page=query.page,
            size=query.size,
        )

    def verify_chain(
        self,
        log_type: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> HashChainVerification:
        """Verify hash chain integrity for a given log_type and time range."""
        conditions = ["log_type = %s"]
        params: list[Any] = [log_type]

        if start_time is not None:
            conditions.append("timestamp >= %s")
            params.append(start_time)
        if end_time is not None:
            conditions.append("timestamp <= %s")
            params.append(end_time)

        where_clause = f"WHERE {' AND '.join(conditions)}"
        sql = f"SELECT * FROM audit_log {where_clause} ORDER BY timestamp, log_id"

        rows = self._ch.execute(sql, params)

        columns = [
            "log_id", "log_type", "timestamp", "trace_id", "span_id",
            "previous_hash", "current_hash", "actor_type", "actor_id",
            "session_id", "action_operation", "action_target_type",
            "action_target_id", "action_result", "action_error_code",
            "action_error_message", "data_hash", "data", "context_ip_hash",
        ]

        entries: list[dict] = [dict(zip(columns, row)) for row in rows]

        valid, message = verify_hash_chain(entries)
        merkle_root = compute_merkle_root(entries)

        return HashChainVerification(
            valid=valid,
            message=message,
            merkle_root=merkle_root,
        )

    def get_merkle_root(self, log_type: str, target_date: date) -> str:
        """Compute the Merkle root for all entries of a given log_type on a given date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        sql = (
            "SELECT * FROM audit_log "
            "WHERE log_type = %s AND timestamp >= %s AND timestamp <= %s "
            "ORDER BY timestamp, log_id"
        )
        rows = self._ch.execute(sql, [log_type, start, end])

        columns = [
            "log_id", "log_type", "timestamp", "trace_id", "span_id",
            "previous_hash", "current_hash", "actor_type", "actor_id",
            "session_id", "action_operation", "action_target_type",
            "action_target_id", "action_result", "action_error_code",
            "action_error_message", "data_hash", "data", "context_ip_hash",
        ]

        entries: list[dict] = [dict(zip(columns, row)) for row in rows]
        return compute_merkle_root(entries)
