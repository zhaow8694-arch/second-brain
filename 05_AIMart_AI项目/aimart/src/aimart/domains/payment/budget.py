from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


class BudgetError(Exception):
    """Raised when a budget operation fails."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class BudgetManager:
    """Manages budget pool operations: checking, freezing, releasing, recharging.

    All methods accept a ``repo`` parameter – an object that provides
    ``get_pool``, ``get_allocation``, ``get_snapshot``, ``save``,
    ``create_snapshot``, and ``update_snapshot`` methods.
    This keeps the manager decoupled from any specific ORM session.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_sufficient(
        self,
        pool_id: UUID,
        agent_id: UUID,
        amount: Decimal,
        repo: Any,
    ) -> tuple[bool, str]:
        """Check whether a payment of *amount* is allowed.

        Returns (True, "") if allowed, or (False, reason) if not.
        Checks performed (in order):
        1. Pool exists and is active
        2. Available balance (balance - frozen) >= amount
        3. Single transaction limit
        4. Pool daily limit
        5. Agent daily limit
        6. Agent per-call limit
        """
        pool = repo.get_pool(pool_id)
        if pool is None:
            return False, "Budget pool not found"

        if pool.status != "active":
            return False, f"Budget pool status is {pool.status}"

        available = Decimal(str(pool.balance)) - Decimal(str(pool.frozen_amount))
        if available < amount:
            return False, (
                f"Insufficient available balance: {available} < {amount}"
            )

        # Single transaction limit
        single_max = Decimal(str(pool.single_transaction_max))
        if amount > single_max:
            return False, (
                f"Amount {amount} exceeds single transaction max {single_max}"
            )

        # Pool daily limit
        date.today()
        pool_daily_spent = self._get_daily_spent(pool_id, agent_id=None, repo=repo)
        if pool_daily_spent + amount > Decimal(str(pool.daily_max)):
            return False, (
                f"Pool daily limit exceeded: "
                f"{pool_daily_spent}+{amount} > {pool.daily_max}"
            )

        # Agent allocation checks
        allocation = repo.get_allocation(pool_id, agent_id)
        if allocation is not None:
            # Agent per-call limit
            per_call_max = Decimal(str(allocation.per_call_max))
            if amount > per_call_max:
                return False, (
                    f"Agent per-call limit exceeded: {amount} > {per_call_max}"
                )

            # Agent daily limit
            agent_daily_spent = self._get_daily_spent(
                pool_id, agent_id, repo=repo
            )
            agent_daily_max = Decimal(str(allocation.daily_max))
            if agent_daily_spent + amount > agent_daily_max:
                return False, (
                    f"Agent daily limit exceeded: "
                    f"{agent_daily_spent}+{amount} > {agent_daily_max}"
                )

        logger.debug(
            "budget_check_passed",
            pool_id=str(pool_id),
            agent_id=str(agent_id),
            amount=str(amount),
        )
        return True, ""

    def freeze(
        self,
        pool_id: UUID,
        agent_id: UUID,
        amount: Decimal,
        order_id: UUID,
        reason: str,
        repo: Any,
    ) -> bool:
        """Freeze *amount* in the pool for an upcoming transaction.

        Increases ``frozen_amount`` by *amount*.
        Returns True on success, raises BudgetError on failure.
        """
        pool = repo.get_pool(pool_id)
        if pool is None:
            raise BudgetError("Budget pool not found")

        available = Decimal(str(pool.balance)) - Decimal(str(pool.frozen_amount))
        if available < amount:
            raise BudgetError(
                f"Insufficient available balance to freeze: {available} < {amount}"
            )

        pool.frozen_amount = Decimal(str(pool.frozen_amount)) + amount
        repo.save(pool)

        logger.info(
            "budget_frozen",
            pool_id=str(pool_id),
            agent_id=str(agent_id),
            amount=str(amount),
            order_id=str(order_id),
            reason=reason,
        )
        return True

    def release(
        self,
        pool_id: UUID,
        amount: Decimal,
        provider_id: UUID,
        order_id: UUID,
        release_pct: float = 1.0,
        repo: Any = None,
    ) -> bool:
        """Release frozen funds after escrow resolution.

        - Decreases ``frozen_amount`` by *amount*.
        - Decreases ``balance`` by ``release_pct * amount`` (paid to provider).
        - The remaining ``(1 - release_pct) * amount`` is refunded to balance.

        Returns True on success, raises BudgetError on failure.
        """
        pool = repo.get_pool(pool_id)
        if pool is None:
            raise BudgetError("Budget pool not found")

        frozen = Decimal(str(pool.frozen_amount))
        if frozen < amount:
            raise BudgetError(
                f"Frozen amount {frozen} is less than release amount {amount}"
            )

        balance = Decimal(str(pool.balance))
        release_pct_dec = Decimal(str(release_pct))
        provider_payout = amount * release_pct_dec
        buyer_refund = amount * (Decimal("1") - release_pct_dec)

        pool.frozen_amount = frozen - amount
        pool.balance = balance - provider_payout
        # buyer_refund is already implicitly in balance since we only
        # subtract provider_payout from balance

        repo.save(pool)

        logger.info(
            "budget_released",
            pool_id=str(pool_id),
            amount=str(amount),
            provider_id=str(provider_id),
            order_id=str(order_id),
            release_pct=release_pct,
            provider_payout=str(provider_payout),
            buyer_refund=str(buyer_refund),
        )
        return True

    def recharge(
        self,
        pool_id: UUID,
        amount: Decimal,
        operator_id: UUID,
        repo: Any,
    ) -> bool:
        """Recharge (top-up) a budget pool.

        Increases ``balance`` by *amount*.
        Returns True on success, raises BudgetError on failure.
        """
        if amount <= 0:
            raise BudgetError("Recharge amount must be positive")

        pool = repo.get_pool(pool_id)
        if pool is None:
            raise BudgetError("Budget pool not found")

        if pool.status == "closed":
            raise BudgetError("Cannot recharge a closed budget pool")

        pool.balance = Decimal(str(pool.balance)) + amount

        # Check total cap
        if pool.total_cap is not None:
            if Decimal(str(pool.balance)) > Decimal(str(pool.total_cap)):
                raise BudgetError(
                    f"Recharge would exceed total cap of {pool.total_cap}"
                )

        repo.save(pool)

        logger.info(
            "budget_recharged",
            pool_id=str(pool_id),
            amount=str(amount),
            operator_id=str(operator_id),
            new_balance=str(pool.balance),
        )
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_daily_spent(
        self,
        pool_id: UUID,
        agent_id: UUID | None,
        repo: Any,
    ) -> Decimal:
        """Query the DailyBudgetSnapshot for today's spending.

        If agent_id is None, returns pool-level daily spending.
        If no snapshot exists, returns 0.
        """
        today = date.today()
        snapshot = repo.get_snapshot(
            pool_id=pool_id,
            agent_id=agent_id,
            snapshot_date=today,
        )
        if snapshot is None:
            return Decimal("0")
        return Decimal(str(snapshot.daily_spent))
