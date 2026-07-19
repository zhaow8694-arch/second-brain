"""Tests for the budget management module."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from aimart.domains.payment.budget import BudgetManager


@dataclass
class FakePool:
    """Simulates a BudgetPool ORM object."""
    id: UUID
    owner_id: UUID
    name: str
    currency: str = "CNY"
    balance: Decimal = Decimal("1000.00")
    frozen_amount: Decimal = Decimal("0")
    total_cap: Decimal | None = Decimal("10000.00")
    single_transaction_max: Decimal = Decimal("500.00")
    daily_max: Decimal = Decimal("2000.00")
    weekly_max: Decimal = Decimal("10000.00")
    monthly_max: Decimal = Decimal("30000.00")
    status: str = "active"


@dataclass
class FakeAllocation:
    """Simulates an AgentBudgetAllocation ORM object."""
    pool_id: UUID
    agent_id: UUID
    daily_max: Decimal = Decimal("500.00")
    per_call_max: Decimal = Decimal("1.00")
    daily_spent: Decimal = Decimal("0")
    spending_authority_level: str = "L0"


@dataclass
class FakeSnapshot:
    """Simulates a DailyBudgetSnapshot ORM object."""
    pool_id: UUID
    agent_id: UUID | None
    snapshot_date: str
    daily_spent: Decimal = Decimal("0")


class FakeRepo:
    """Simulates a repository for budget operations."""

    def __init__(self):
        self.pools: dict[UUID, FakePool] = {}
        self.allocations: dict[tuple[UUID, UUID], FakeAllocation] = {}
        self.snapshots: dict[str, FakeSnapshot] = {}

    def add_pool(self, pool: FakePool):
        self.pools[pool.id] = pool

    def get_pool(self, pool_id: UUID) -> FakePool | None:
        return self.pools.get(pool_id)

    def get_allocation(self, pool_id: UUID, agent_id: UUID) -> FakeAllocation | None:
        return self.allocations.get((pool_id, agent_id))

    def get_snapshot(self, pool_id: UUID, agent_id: UUID | None, snapshot_date):
        key = f"{pool_id}|{agent_id}|{snapshot_date}"
        return self.snapshots.get(key)

    def save(self, obj):
        if isinstance(obj, FakePool):
            self.pools[obj.id] = obj
        elif isinstance(obj, FakeAllocation):
            self.allocations[(obj.pool_id, obj.agent_id)] = obj

    def create_snapshot(self, pool_id, agent_id, snapshot_date):
        snap = FakeSnapshot(
            pool_id=pool_id,
            agent_id=agent_id,
            snapshot_date=str(snapshot_date),
        )
        key = f"{pool_id}|{agent_id}|{snapshot_date}"
        self.snapshots[key] = snap
        return snap


class TestBudgetManager:
    """Test budget management operations."""

    def setup_method(self):
        self.manager = BudgetManager()
        self.repo = FakeRepo()
        self.pool_id = uuid4()
        self.agent_id = uuid4()
        self.repo.add_pool(FakePool(id=self.pool_id, owner_id=uuid4(), name="Test Pool"))
        self.repo.allocations[(self.pool_id, self.agent_id)] = FakeAllocation(
            pool_id=self.pool_id,
            agent_id=self.agent_id,
        )

    def test_check_sufficient_balance(self):
        """Should pass when balance is sufficient."""
        ok, reason = self.manager.check_sufficient(
            pool_id=self.pool_id,
            agent_id=self.agent_id,
            amount=Decimal("0.50"),
            repo=self.repo,
        )
        assert ok is True, reason
        assert reason == ""

    def test_check_insufficient_balance(self):
        """Should fail when amount exceeds balance."""
        ok, reason = self.manager.check_sufficient(
            pool_id=self.pool_id,
            agent_id=self.agent_id,
            amount=Decimal("999999.00"),
            repo=self.repo,
        )
        assert ok is False
        assert "Insufficient" in reason

    def test_check_pool_not_found(self):
        """Should fail for non-existent pool."""
        ok, reason = self.manager.check_sufficient(
            pool_id=uuid4(),
            agent_id=self.agent_id,
            amount=Decimal("10.00"),
            repo=self.repo,
        )
        assert ok is False

    def test_freeze_funds_success(self):
        """Freezing should increase frozen_amount."""
        self.manager.freeze(
            pool_id=self.pool_id,
            agent_id=self.agent_id,
            amount=Decimal("100.00"),
            order_id=uuid4(),
            reason="test",
            repo=self.repo,
        )
        pool = self.repo.get_pool(self.pool_id)
        assert pool.frozen_amount == Decimal("100.00")

    def test_freeze_insufficient_funds(self):
        """Freezing should fail when balance is too low."""
        pool = self.repo.get_pool(self.pool_id)
        pool.balance = Decimal("10.00")
        pool.frozen_amount = Decimal("5.00")

        with pytest.raises(Exception, match="Insufficient"):
            self.manager.freeze(
                pool_id=self.pool_id,
                agent_id=self.agent_id,
                amount=Decimal("100.00"),
                order_id=uuid4(),
                reason="test",
                repo=self.repo,
            )

    def test_release_full_payout(self):
        """Full release (100% to provider)."""
        pool = self.repo.get_pool(self.pool_id)
        pool.frozen_amount = Decimal("100.00")
        pool.balance = Decimal("1000.00")

        self.manager.release(
            pool_id=self.pool_id,
            amount=Decimal("100.00"),
            provider_id=uuid4(),
            order_id=uuid4(),
            release_pct=1.0,
            repo=self.repo,
        )
        assert pool.frozen_amount == Decimal("0")
        assert pool.balance == Decimal("900.00")  # 1000 - 100

    def test_release_partial_payout(self):
        """Partial release (60% to provider, 40% refund)."""
        pool = self.repo.get_pool(self.pool_id)
        pool.frozen_amount = Decimal("100.00")
        pool.balance = Decimal("1000.00")

        self.manager.release(
            pool_id=self.pool_id,
            amount=Decimal("100.00"),
            provider_id=uuid4(),
            order_id=uuid4(),
            release_pct=0.6,
            repo=self.repo,
        )
        assert pool.frozen_amount == Decimal("0")
        assert pool.balance == Decimal("940.00")  # 1000 - 60

    def test_recharge_pool(self):
        """Recharging should increase balance."""
        self.manager.recharge(
            pool_id=self.pool_id,
            amount=Decimal("500.00"),
            operator_id=uuid4(),
            repo=self.repo,
        )
        pool = self.repo.get_pool(self.pool_id)
        assert pool.balance == Decimal("1500.00")  # 1000 + 500

    def test_recharge_closed_pool_fails(self):
        """Recharging a closed pool should fail."""
        pool = self.repo.get_pool(self.pool_id)
        pool.status = "closed"

        with pytest.raises(Exception, match="Cannot recharge"):
            self.manager.recharge(
                pool_id=self.pool_id,
                amount=Decimal("500.00"),
                operator_id=uuid4(),
                repo=self.repo,
            )
