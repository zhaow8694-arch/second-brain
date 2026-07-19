from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from aimart.domains.audit.hashchain import compute_entry_hash

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Dual-write audit logger: Kafka + ClickHouse with hash-chain integrity.

    Each log entry is linked to the previous one via a SHA-256 hash chain,
    ensuring tamper-evident audit trails per log category.
    """

    def __init__(self, clickhouse_client: Any, kafka_producer: Any) -> None:
        self._clickhouse = clickhouse_client
        self._kafka = kafka_producer
        # Maps log_type/category → last known current_hash
        self._last_hash: dict[str, str] = {}

    async def log(
        self,
        log_type: str,
        actor_type: str,
        actor_id: str,
        target_type: str | None = None,
        target_id: str | None = None,
        action: str = "",
        result: str = "success",
        error_code: str | None = None,
        error_message: str | None = None,
        data: dict[str, Any] | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        ip_address: str | None = None,
    ) -> str:
        """Create an audit log entry and write to Kafka + ClickHouse.

        Returns:
            The generated log_id.
        """
        log_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        # --- data hash ---
        data_str = str(data) if data else ""
        data_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

        # --- hash chain ---
        previous_hash = self._last_hash.get(log_type, "0" * 64)
        current_hash = compute_entry_hash(
            log_id=log_id,
            timestamp=timestamp.isoformat(),
            actor_id=actor_id,
            action=action,
            data_hash=data_hash,
            previous_hash=previous_hash,
        )
        self._last_hash[log_type] = current_hash

        # --- ip hash (privacy) ---
        ip_hash: str | None = None
        if ip_address:
            ip_hash = hashlib.sha256(ip_address.encode("utf-8")).hexdigest()

        # --- build entry ---
        entry: dict[str, Any] = {
            "log_id": log_id,
            "log_type": log_type,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "trace_id": trace_id or "",
            "span_id": str(uuid.uuid4())[:16],
            "previous_hash": previous_hash,
            "current_hash": current_hash,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "session_id": session_id,
            "action_operation": action,
            "action_target_type": target_type,
            "action_target_id": target_id,
            "action_result": result,
            "action_error_code": error_code,
            "action_error_message": error_message,
            "data_hash": data_hash,
            "data": data_str,
            "context_ip_hash": ip_hash,
        }

        # --- dual write ---
        await self._write_to_kafka(entry)
        await self._write_to_clickhouse(entry)

        logger.debug(
            "audit_log_written",
            log_id=log_id,
            log_type=log_type,
            actor_id=actor_id,
            action=action,
        )
        return log_id

    # ------------------------------------------------------------------
    # Internal writers
    # ------------------------------------------------------------------

    async def _write_to_kafka(self, entry: dict[str, Any]) -> None:
        """Publish the audit entry to the category-specific Kafka topic."""
        topic = f"aimart.audit_{entry['log_type']}"
        try:
            import json

            self._kafka.produce(
                topic=topic,
                key=entry["log_id"],
                value=json.dumps(entry).encode("utf-8"),
            )
        except Exception:
            logger.exception(
                "kafka_write_failed",
                topic=topic,
                log_id=entry.get("log_id"),
            )

    async def _write_to_clickhouse(self, entry: dict[str, Any]) -> None:
        """Insert the audit entry into ClickHouse."""
        try:
            columns = ", ".join(entry.keys())
            placeholders = ", ".join(["%s"] * len(entry))
            sql = f"INSERT INTO audit_log ({columns}) VALUES ({placeholders})"
            self._clickhouse.execute(sql, list(entry.values()))
        except Exception:
            logger.exception(
                "clickhouse_write_failed",
                log_id=entry.get("log_id"),
            )
