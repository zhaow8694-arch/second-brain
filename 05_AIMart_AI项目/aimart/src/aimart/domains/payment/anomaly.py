from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


class AnomalyType(StrEnum):
    BURST_SPENDING = "burst_spending"
    HIGH_FREQ_MICRO = "high_freq_micro"
    BUDGET_DEPLETED = "budget_depleted"
    CONCENTRATED_SELLER = "concentrated_seller"
    OFF_HOURS_LARGE = "off_hours_large"


@dataclass
class AnomalyAlert:
    """An anomaly alert raised after a transaction."""

    anomaly_type: AnomalyType
    pool_id: UUID
    agent_id: UUID
    severity: str  # "warning" or "critical"
    message: str
    data: dict = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    action_taken: str = ""


class AnomalyDetector:
    """Detects anomalous spending patterns after each transaction.

    Five detection rules:
    1. Burst spending: 1hr spend > 50% of daily limit → critical
    2. High-frequency micro: >100 L0 tx/min → warning
    3. Budget depleted: balance < single_transaction_max → critical
    4. Concentrated seller: 80%+ to single provider → warning
    5. Off-hours large: >100 CNY outside work hours → warning

    All methods accept a ``repo`` parameter – an object that provides
    query methods for transaction and budget data.
    """

    def check_after_transaction(
        self,
        pool_id: UUID,
        agent_id: UUID,
        amount: Decimal,
        provider_id: UUID,
        repo: Any,
    ) -> list[AnomalyAlert]:
        """Run all anomaly checks after a transaction.

        Args:
            pool_id: The budget pool ID.
            agent_id: The agent making the transaction.
            amount: The transaction amount.
            provider_id: The provider receiving the payment.
            repo: Repository for querying transaction/budget data.

        Returns:
            A list of AnomalyAlert instances (may be empty).
        """
        alerts: list[AnomalyAlert] = []

        # 1. Burst spending check
        burst_alert = self._check_burst_spending(pool_id, agent_id, amount, repo)
        if burst_alert is not None:
            alerts.append(burst_alert)

        # 2. High-frequency micro-transactions check
        freq_alert = self._check_high_freq_micro(pool_id, agent_id, repo)
        if freq_alert is not None:
            alerts.append(freq_alert)

        # 3. Budget depleted check
        depleted_alert = self._check_budget_depleted(pool_id, agent_id, repo)
        if depleted_alert is not None:
            alerts.append(depleted_alert)

        # 4. Concentrated seller check
        concentrated_alert = self._check_concentrated_seller(
            pool_id, agent_id, provider_id, repo
        )
        if concentrated_alert is not None:
            alerts.append(concentrated_alert)

        # 5. Off-hours large transaction check
        off_hours_alert = self._check_off_hours_large(pool_id, agent_id, amount)
        if off_hours_alert is not None:
            alerts.append(off_hours_alert)

        if alerts:
            logger.warning(
                "anomaly_alerts_detected",
                pool_id=str(pool_id),
                agent_id=str(agent_id),
                alert_count=len(alerts),
                alert_types=[a.anomaly_type.value for a in alerts],
            )

        return alerts

    # ------------------------------------------------------------------
    # Private check methods
    # ------------------------------------------------------------------

    def _check_burst_spending(
        self,
        pool_id: UUID,
        agent_id: UUID,
        amount: Decimal,
        repo: Any,
    ) -> AnomalyAlert | None:
        """Burst: 1hr spend > 50% of daily limit → critical, suspend agent."""
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        hourly_spent = repo.get_agent_spending_in_period(
            pool_id=pool_id,
            agent_id=agent_id,
            since=one_hour_ago,
        )

        allocation = repo.get_allocation(pool_id, agent_id)
        if allocation is None:
            return None

        daily_limit = Decimal(str(allocation.daily_max))
        threshold = daily_limit * Decimal("0.5")

        hourly_spent_dec = Decimal(str(hourly_spent))
        if hourly_spent_dec > threshold:
            return AnomalyAlert(
                anomaly_type=AnomalyType.BURST_SPENDING,
                pool_id=pool_id,
                agent_id=agent_id,
                severity="critical",
                message=(
                    f"Agent spent {hourly_spent_dec} in the last hour, "
                    f"exceeding 50% of daily limit ({daily_limit})"
                ),
                data={
                    "hourly_spent": float(hourly_spent_dec),
                    "daily_limit": float(daily_limit),
                    "threshold_pct": 0.5,
                },
                action_taken="agent_suspended",
            )
        return None

    def _check_high_freq_micro(
        self,
        pool_id: UUID,
        agent_id: UUID,
        repo: Any,
    ) -> AnomalyAlert | None:
        """High freq: >100 L0 tx/min → warning, throttle to 10/min."""
        one_minute_ago = datetime.now(UTC) - timedelta(minutes=1)
        tx_count = repo.get_transaction_count_in_period(
            pool_id=pool_id,
            agent_id=agent_id,
            since=one_minute_ago,
            level="L0",
        )

        if tx_count > 100:
            return AnomalyAlert(
                anomaly_type=AnomalyType.HIGH_FREQ_MICRO,
                pool_id=pool_id,
                agent_id=agent_id,
                severity="warning",
                message=(
                    f"Agent made {tx_count} L0 transactions in the last minute, "
                    f"exceeding threshold of 100"
                ),
                data={
                    "tx_count_last_minute": tx_count,
                    "threshold": 100,
                },
                action_taken="throttled_to_10_per_min",
            )
        return None

    def _check_budget_depleted(
        self,
        pool_id: UUID,
        agent_id: UUID,
        repo: Any,
    ) -> AnomalyAlert | None:
        """Depleted: balance < single_transaction_max → critical, suspend all."""
        pool = repo.get_pool(pool_id)
        if pool is None:
            return None

        available = Decimal(str(pool.balance)) - Decimal(str(pool.frozen_amount))
        single_max = Decimal(str(pool.single_transaction_max))

        if available < single_max:
            return AnomalyAlert(
                anomaly_type=AnomalyType.BUDGET_DEPLETED,
                pool_id=pool_id,
                agent_id=agent_id,
                severity="critical",
                message=(
                    f"Available balance ({available}) is less than "
                    f"single transaction max ({single_max})"
                ),
                data={
                    "available_balance": float(available),
                    "single_transaction_max": float(single_max),
                },
                action_taken="all_agents_suspended",
            )
        return None

    def _check_concentrated_seller(
        self,
        pool_id: UUID,
        agent_id: UUID,
        provider_id: UUID,
        repo: Any,
    ) -> AnomalyAlert | None:
        """Concentrated: 80%+ to single seller → warning, trigger review."""
        spending_by_provider = repo.get_spending_by_provider(
            pool_id=pool_id,
            agent_id=agent_id,
        )
        if not spending_by_provider:
            return None

        total_spent = sum(spending_by_provider.values())
        if total_spent <= 0:
            return None

        provider_spent = spending_by_provider.get(str(provider_id), 0)
        concentration_ratio = provider_spent / total_spent

        if concentration_ratio >= 0.8:
            return AnomalyAlert(
                anomaly_type=AnomalyType.CONCENTRATED_SELLER,
                pool_id=pool_id,
                agent_id=agent_id,
                severity="warning",
                message=(
                    f"Agent has spent {concentration_ratio:.0%} of budget "
                    f"with a single provider"
                ),
                data={
                    "provider_id": str(provider_id),
                    "provider_spent": provider_spent,
                    "total_spent": total_spent,
                    "concentration_ratio": concentration_ratio,
                },
                action_taken="review_triggered",
            )
        return None

    def _check_off_hours_large(
        self,
        pool_id: UUID,
        agent_id: UUID,
        amount: Decimal,
    ) -> AnomalyAlert | None:
        """Off hours: >100 CNY outside work hours (9-18 UTC+8 weekdays)."""
        # Current time in UTC+8
        now_utc8 = datetime.now(UTC) + timedelta(hours=8)
        hour = now_utc8.hour
        weekday = now_utc8.weekday()  # 0=Monday, 6=Sunday

        is_work_hour = (0 <= weekday <= 4) and (9 <= hour < 18)

        if not is_work_hour and amount > Decimal("100"):
            return AnomalyAlert(
                anomaly_type=AnomalyType.OFF_HOURS_LARGE,
                pool_id=pool_id,
                agent_id=agent_id,
                severity="warning",
                message=(
                    f"Large transaction ({amount} CNY) outside work hours "
                    f"(current: {now_utc8.strftime('%A %H:%M')} UTC+8)"
                ),
                data={
                    "amount": float(amount),
                    "hour_utc8": hour,
                    "weekday": weekday,
                    "weekday_name": now_utc8.strftime("%A"),
                },
                action_taken="escalated_to_higher_auth_level",
            )
        return None
