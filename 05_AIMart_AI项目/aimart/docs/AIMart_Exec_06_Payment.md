# AIMart 工程执行文件 06：支付结算服务
tags: [aimart, payment, settlement]

tags: [aimart, payment, settlement]
> Codex 执行指令：实现预算池管理、分层授权、担保交易状态机、x402/ACP 双轨结算
tags: [aimart, payment, settlement]

tags: [aimart, payment, settlement]
---
tags: [aimart, payment, settlement]

## 一、数据库模型

```python
# src/aimart/payment/models.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Numeric, Boolean, DateTime, Enum, ForeignKey,
    Integer, Text, JSON, Index, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class BudgetPool(Base):
    """预算池——每个 Owner 可创建多个预算池，每个池绑定多个 Agent"""
    __tablename__ = "budget_pools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    name = Column(String(255), nullable=False, comment="预算池名称")
    currency = Column(String(10), nullable=False, default="CNY", comment="CNY | USD | USDC")

    # 余额
    balance = Column(Numeric(18, 4), nullable=False, default=0, comment="当前余额")
    frozen_amount = Column(Numeric(18, 4), nullable=False, default=0, comment="冻结金额（担保交易中）")

    # 限额
    total_cap = Column(Numeric(18, 4), nullable=True, comment="总量上限，null=无上限")
    single_transaction_max = Column(Numeric(18, 4), nullable=False, default=500.00)
    daily_max = Column(Numeric(18, 4), nullable=False, default=2000.00)
    weekly_max = Column(Numeric(18, 4), nullable=False, default=10000.00)
    monthly_max = Column(Numeric(18, 4), nullable=False, default=30000.00)

    # 自动充值
    auto_recharge = Column(Boolean, nullable=False, default=False)
    recharge_threshold = Column(Numeric(18, 4), nullable=True)
    recharge_amount = Column(Numeric(18, 4), nullable=True)

    # 状态
    status = Column(String(20), nullable=False, default="active", comment="active | suspended | closed")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    allocations = relationship("AgentBudgetAllocation", back_populates="pool")
    transactions = relationship("PaymentTransaction", back_populates="pool")

    __table_args__ = (
        Index("ix_budget_pools_owner", "owner_id"),
        Index("ix_budget_pools_status", "status"),
        CheckConstraint("balance >= 0", name="ck_budget_balance_nonneg"),
        CheckConstraint("frozen_amount >= 0", name="ck_frozen_nonneg"),
    )


class AgentBudgetAllocation(Base):
    """Agent 预算分配——每个 Agent 在预算池中的限额"""
    __tablename__ = "agent_budget_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pool_id = Column(UUID(as_uuid=True), ForeignKey("budget_pools.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)

    daily_max = Column(Numeric(18, 4), nullable=False, default=500.00)
    per_call_max = Column(Numeric(18, 4), nullable=False, default=1.00)

    # 累计消耗（每日重置，由定时任务维护）
    daily_spent = Column(Numeric(18, 4), nullable=False, default=0)
    daily_spent_date = Column(String(10), nullable=True, comment="YYYY-MM-DD，用于判断是否需要重置")

    # 分层授权
    spending_authority_level = Column(String(2), nullable=False, default="L0", comment="L0|L1|L2|L3")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    pool = relationship("BudgetPool", back_populates="allocations")

    __table_args__ = (
        Index("ix_alloc_agent_pool", "agent_id", "pool_id", unique=True),
    )


class PaymentTransaction(Base):
    """支付交易记录"""
    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pool_id = Column(UUID(as_uuid=True), ForeignKey("budget_pools.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), nullable=False)
    provider_id = Column(UUID(as_uuid=True), nullable=False)

    amount = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(10), nullable=False, default="CNY")
    commission_rate = Column(Numeric(5, 4), nullable=False, default=0.0300, comment="平台佣金率")
    commission_amount = Column(Numeric(18, 4), nullable=False, default=0)
    provider_payout = Column(Numeric(18, 4), nullable=False, default=0, comment="卖家实收")

    # 结算通道
    settlement_channel = Column(String(20), nullable=False, comment="fiat | x402 | acp")

    # 担保交易
    escrow_status = Column(
        String(20), nullable=False, default="frozen",
        comment="frozen | partial_release | released | refunded | disputed"
    )
    escrow_frozen_at = Column(DateTime, nullable=True)
    escrow_released_at = Column(DateTime, nullable=True)

    # 授权信息
    authorization_level = Column(String(2), nullable=True, comment="L0|L1|L2|L3")
    authorization_id = Column(UUID(as_uuid=True), nullable=True, comment="授权记录 ID")
    authorized_at = Column(DateTime, nullable=True)
    authorized_by = Column(String(20), nullable=True, comment="agent | owner | system")

    # 效果回传
    effect_score = Column(Integer, nullable=True, comment="0-5，Agent 回传的效果评分")
    effect_reported_at = Column(DateTime, nullable=True)

    # 状态
    status = Column(
        String(20), nullable=False, default="pending",
        comment="pending | authorized | processing | completed | failed | cancelled | disputed"
    )
    failure_reason = Column(Text, nullable=True)

    # 外部结算 ID
    external_settlement_id = Column(String(255), nullable=True, comment="x402 tx hash / ACP payment intent id")
    settlement_confirmed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    pool = relationship("BudgetPool", back_populates="transactions")

    __table_args__ = (
        Index("ix_paytx_order", "order_id"),
        Index("ix_paytx_agent", "agent_id"),
        Index("ix_paytx_provider", "provider_id"),
        Index("ix_paytx_status", "status"),
        Index("ix_paytx_escrow", "escrow_status"),
    )


class AuthorizationRequest(Base):
    """授权请求——L2/L3 交易需要 Owner 审批"""
    __tablename__ = "authorization_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("payment_transactions.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), nullable=False)
    owner_id = Column(UUID(as_uuid=True), nullable=False)

    level = Column(String(2), nullable=False, comment="L2 | L3")
    amount = Column(Numeric(18, 4), nullable=False)
    item_name = Column(String(255), nullable=True)
    item_type = Column(String(20), nullable=True)

    status = Column(
        String(20), nullable=False, default="pending",
        comment="pending | approved | rejected | expired"
    )

    # 通知
    notification_sent_at = Column(DateTime, nullable=True)
    notification_channel = Column(String(20), nullable=True, comment="email | sms | webhook | in_app")

    # 审批
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(UUID(as_uuid=True), nullable=True)
    reject_reason = Column(Text, nullable=True)

    # 超时
    expires_at = Column(DateTime, nullable=False, comment="L2: 30min, L3: 1hour")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_authreq_owner_status", "owner_id", "status"),
        Index("ix_authreq_expires", "expires_at"),
    )


class DailyBudgetSnapshot(Base):
    """日预算快照——用于每日/周/月消耗统计"""
    __tablename__ = "daily_budget_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pool_id = Column(UUID(as_uuid=True), ForeignKey("budget_pools.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), nullable=True, comment="null=池级汇总")
    snapshot_date = Column(String(10), nullable=False, comment="YYYY-MM-DD")

    daily_spent = Column(Numeric(18, 4), nullable=False, default=0)
    transaction_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_daily_snap_unique", "pool_id", "agent_id", "snapshot_date", unique=True),
    )
```

---

## 二、Pydantic Schema

```python
# src/aimart/payment/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---- 预算池 ----

class CreateBudgetPoolRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(default="CNY", pattern="^(CNY|USD|USDC)$")
    total_cap: Optional[float] = Field(None, gt=0)
    single_transaction_max: float = Field(default=500.00, gt=0)
    daily_max: float = Field(default=2000.00, gt=0)
    weekly_max: float = Field(default=10000.00, gt=0)
    monthly_max: float = Field(default=30000.00, gt=0)
    auto_recharge: bool = False
    recharge_threshold: Optional[float] = Field(None, gt=0)
    recharge_amount: Optional[float] = Field(None, gt=0)


class RechargeBudgetPoolRequest(BaseModel):
    amount: float = Field(..., gt=0, description="充值金额")


class AllocateAgentBudgetRequest(BaseModel):
    agent_id: UUID
    daily_max: float = Field(default=500.00, gt=0)
    per_call_max: float = Field(default=1.00, gt=0)
    spending_authority_level: str = Field(default="L0", pattern="^L[0-3]$")


class BudgetPoolResponse(BaseModel):
    id: UUID
    name: str
    currency: str
    balance: float
    frozen_amount: float
    available_balance: float = Field(..., description="balance - frozen_amount")
    single_transaction_max: float
    daily_max: float
    status: str
    created_at: datetime


# ---- 支付交易 ----

class InitiatePaymentRequest(BaseModel):
    order_id: UUID
    pool_id: UUID
    settlement_channel: str = Field(default="fiat", pattern="^(fiat|x402|acp)$")


class PaymentTransactionResponse(BaseModel):
    id: UUID
    order_id: UUID
    amount: float
    currency: str
    commission_amount: float
    provider_payout: float
    settlement_channel: str
    escrow_status: str
    status: str
    authorization_level: Optional[str] = None
    created_at: datetime


# ---- 授权 ----

class AuthorizationDecisionRequest(BaseModel):
    approved: bool
    reject_reason: Optional[str] = None


class AuthorizationRequestResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    agent_id: UUID
    level: str
    amount: float
    item_name: Optional[str] = None
    status: str
    expires_at: datetime


# ---- 效果回传 ----

class EffectReportRequest(BaseModel):
    transaction_id: UUID
    effect_score: int = Field(..., ge=0, le=5)
    success: bool
    actual_latency_ms: Optional[int] = None
    declared_latency_ms: Optional[int] = None
    cost_actual: Optional[float] = None
    cost_declared: Optional[float] = None
    detail: Optional[dict] = None

    @field_validator("effect_score")
    @classmethod
    def validate_effect_score(cls, v):
        if v < 0 or v > 5:
            raise ValueError("effect_score must be 0-5")
        return v
```

---

## 三、担保交易状态机

```python
# src/aimart/payment/escrow.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class EscrowState(str, Enum):
    """担保交易状态"""
    FROZEN = "frozen"                  # 资金已冻结
    PARTIAL_RELEASE = "partial_release" # 部分释放
    RELEASED = "released"              # 全额释放给卖家
    REFUNDED = "refunded"              # 退还买家
    DISPUTED = "disputed"              # 争议中


class EscrowEvent(str, Enum):
    """担保交易事件"""
    EFFECT_CONFIRMED = "effect_confirmed"        # 效果达标
    EFFECT_PARTIAL = "effect_partial"            # 效果部分达标
    EFFECT_FAILED = "effect_failed"              # 效果不达标
    DISPUTE_OPENED = "dispute_opened"            # 争议发起
    DISPUTE_RESOLVED_RELEASE = "dispute_resolved_release"  # 仲裁：释放
    DISPUTE_RESOLVED_REFUND = "dispute_resolved_refund"    # 仲裁：退款
    DISPUTE_RESOLVED_SPLIT = "dispute_resolved_split"      # 仲裁：分拆
    TIMEOUT_NO_REPORT = "timeout_no_report"      # 超时未回传（默认达标）


# 合法状态转换表
VALID_TRANSITIONS: dict[EscrowState, dict[EscrowEvent, EscrowState]] = {
    EscrowState.FROZEN: {
        EscrowEvent.EFFECT_CONFIRMED: EscrowState.RELEASED,
        EscrowEvent.EFFECT_PARTIAL: EscrowState.PARTIAL_RELEASE,
        EscrowEvent.EFFECT_FAILED: EscrowState.REFUNDED,
        EscrowEvent.DISPUTE_OPENED: EscrowState.DISPUTED,
        EscrowEvent.TIMEOUT_NO_REPORT: EscrowState.RELEASED,
    },
    EscrowState.PARTIAL_RELEASE: {
        EscrowEvent.DISPUTE_OPENED: EscrowState.DISPUTED,
    },
    EscrowState.DISPUTED: {
        EscrowEvent.DISPUTE_RESOLVED_RELEASE: EscrowState.RELEASED,
        EscrowEvent.DISPUTE_RESOLVED_REFUND: EscrowState.REFUNDED,
        EscrowEvent.DISPUTE_RESOLVED_SPLIT: EscrowState.PARTIAL_RELEASE,
    },
    # RELEASED, REFUNDED 是终态
}


@dataclass
class EscrowTransitionResult:
    """状态转换结果"""
    old_state: EscrowState
    new_state: EscrowState
    event: EscrowEvent
    provider_payout_pct: float   # 卖家获得的比例 (0.0 - 1.0)
    buyer_refund_pct: float      # 买家退还的比例 (0.0 - 1.0)
    action_required: str | None  # 需要额外执行的操作


def transition(
    current_state: EscrowState,
    event: EscrowEvent,
    effect_score: int | None = None,
) -> EscrowTransitionResult:
    """
    执行担保交易状态转换。

    Args:
        current_state: 当前状态
        event: 触发事件
        effect_score: 效果评分 (0-5)，用于计算部分达标的分配比例

    Returns:
        EscrowTransitionResult

    Raises:
        ValueError: 非法状态转换
    """
    transitions = VALID_TRANSITIONS.get(current_state, {})
    new_state = transitions.get(event)

    if new_state is None:
        raise ValueError(
            f"非法状态转换: {current_state.value} + {event.value} "
            f"(当前状态只接受: {[e.value for e in transitions.keys()]})"
        )

    # 计算分配比例
    provider_pct, buyer_pct, action = _calculate_split(new_state, event, effect_score)

    logger.info(
        "escrow_transition",
        old_state=current_state.value,
        new_state=new_state.value,
        event=event.value,
        provider_pct=provider_pct,
        buyer_pct=buyer_pct,
    )

    return EscrowTransitionResult(
        old_state=current_state,
        new_state=new_state,
        event=event,
        provider_payout_pct=provider_pct,
        buyer_refund_pct=buyer_pct,
        action_required=action,
    )


def _calculate_split(
    new_state: EscrowState,
    event: EscrowEvent,
    effect_score: int | None,
) -> tuple[float, float, str | None]:
    """根据状态和事件计算资金分配"""
    if new_state == EscrowState.RELEASED:
        return 1.0, 0.0, None
    elif new_state == EscrowState.REFUNDED:
        return 0.0, 1.0, None
    elif new_state == EscrowState.PARTIAL_RELEASE:
        if effect_score is not None and 0 <= effect_score <= 5:
            # 效果评分 0-5 映射到卖家比例 0%-100%
            provider_pct = effect_score / 5.0
        else:
            provider_pct = 0.5  # 默认 50/50
        return provider_pct, 1.0 - provider_pct, "需要仲裁确认分配比例"
    elif new_state == EscrowState.DISPUTED:
        return 0.0, 0.0, "等待仲裁结果"
    else:
        return 0.0, 0.0, None
```

---

## 四、分层授权逻辑

```python
# src/aimart/payment/authorization.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import structlog

logger = structlog.get_logger()


# 授权级别阈值（CNY）
AUTH_LEVELS = {
    "L0": {"max_per_call": 0.01, "description": "全自动", "timeout": None},
    "L1": {"max_per_call": 1.00, "description": "事后通知", "timeout": None},
    "L2": {"max_per_call": 100.00, "description": "事前审批", "timeout_minutes": 30},
    "L3": {"max_per_call": float("inf"), "description": "人工确认", "timeout_minutes": 60},
}


def determine_auth_level(amount: float, agent_level: str) -> tuple[str, bool]:
    """
    判定交易需要的授权级别及是否需要审批。

    Args:
        amount: 交易金额 (CNY)
        agent_level: Agent 已配置的授权级别 (L0-L3)

    Returns:
        (required_level, needs_approval)
        - required_level: 此笔交易需要的授权级别
        - needs_approval: 是否需要 Owner 人工审批
    """
    # 根据金额确定需要什么级别
    if amount <= AUTH_LEVELS["L0"]["max_per_call"]:
        required_level = "L0"
    elif amount <= AUTH_LEVELS["L1"]["max_per_call"]:
        required_level = "L1"
    elif amount <= AUTH_LEVELS["L2"]["max_per_call"]:
        required_level = "L2"
    else:
        required_level = "L3"

    # Agent 的配置级别是否覆盖
    level_order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
    agent_can = level_order.get(agent_level, 0)
    required = level_order.get(required_level, 3)

    if agent_can >= required:
        # Agent 已被授权在此级别自主决策
        needs_approval = required_level in ("L2", "L3")
        return required_level, needs_approval
    else:
        # 交易金额超出 Agent 授权范围，需要升级审批
        return required_level, True


def calculate_auth_expiry(level: str) -> datetime:
    """计算授权请求的过期时间"""
    config = AUTH_LEVELS.get(level, AUTH_LEVELS["L3"])
    timeout_minutes = config.get("timeout_minutes") or 60
    return datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)


async def check_authorization_status(
    auth_request_id: str,
    auth_repo,  # AuthorizationRequest 的 repository
) -> tuple[str, str | None]:
    """
    检查授权请求状态。

    Returns:
        (status, reject_reason)
        - status: "approved" | "rejected" | "expired" | "pending"
    """
    auth_req = await auth_repo.get_by_id(auth_request_id)
    if auth_req is None:
        return "pending", None

    # 检查是否过期
    if auth_req.status == "pending" and datetime.now(timezone.utc) > auth_req.expires_at:
        # 自动过期 → 自动拒绝
        auth_req.status = "expired"
        await auth_repo.update(auth_req)
        logger.warning("authorization_expired", auth_request_id=auth_request_id)
        return "expired", "授权请求超时自动拒绝"

    return auth_req.status, auth_req.reject_reason
```

---

## 五、预算池管理

```python
# src/aimart/payment/budget.py

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

import structlog

logger = structlog.get_logger()


class BudgetManager:
    """预算池管理器——扣减、冻结、释放、充值"""

    def __init__(self, pool_repo, allocation_repo, snapshot_repo, audit_logger):
        self._pool = pool_repo
        self._alloc = allocation_repo
        self._snap = snapshot_repo
        self._audit = audit_logger

    async def check_sufficient(
        self,
        pool_id: UUID,
        agent_id: UUID,
        amount: float,
    ) -> tuple[bool, str]:
        """
        检查预算是否充足（不实际扣减）。

        Returns:
            (sufficient, reason)
        """
        pool = await self._pool.get_by_id(pool_id)
        if pool is None:
            return False, "预算池不存在"
        if pool.status != "active":
            return False, f"预算池状态异常: {pool.status}"

        # 池级余额检查
        available = float(pool.balance) - float(pool.frozen_amount)
        if available < amount:
            return False, f"余额不足: 可用 {available:.2f}, 需要 {amount:.2f}"

        # 单笔上限
        if amount > float(pool.single_transaction_max):
            return False, f"超出单笔上限: {pool.single_transaction_max}"

        # 池级日限额
        today_spent = await self._get_daily_spent(pool_id, agent_id=None)
        if today_spent + amount > float(pool.daily_max):
            return False, f"超出日限额: 已用 {today_spent:.2f}, 上限 {pool.daily_max}"

        # Agent 级限额
        alloc = await self._alloc.get_by_agent_pool(agent_id, pool_id)
        if alloc:
            agent_spent = await self._get_daily_spent(pool_id, agent_id)
            if agent_spent + amount > float(alloc.daily_max):
                return False, f"Agent 日限额不足: 已用 {agent_spent:.2f}, 上限 {alloc.daily_max}"
            if amount > float(alloc.per_call_max):
                return False, f"超出 Agent 单次限额: {alloc.per_call_max}"

        return True, ""

    async def freeze(
        self,
        pool_id: UUID,
        agent_id: UUID,
        amount: float,
        order_id: UUID,
        reason: str = "escrow",
    ) -> bool:
        """冻结金额（担保交易）"""
        pool = await self._pool.get_by_id(pool_id)
        if pool is None:
            return False

        new_frozen = float(pool.frozen_amount) + amount
        available = float(pool.balance) - new_frozen
        if available < 0:
            logger.error("freeze_insufficient", pool_id=str(pool_id), amount=amount)
            return False

        pool.frozen_amount = new_frozen
        await self._pool.update(pool)

        await self._audit.log(
            log_type="PAY-FREEZE",
            actor_type="system",
            actor_id="budget_manager",
            target_type="budget_pool",
            target_id=str(pool_id),
            action="freeze",
            data={
                "pool_id": str(pool_id),
                "agent_id": str(agent_id),
                "amount": amount,
                "order_id": str(order_id),
                "reason": reason,
                "new_frozen": new_frozen,
            },
        )
        return True

    async def release(
        self,
        pool_id: UUID,
        amount: float,
        provider_id: UUID,
        order_id: UUID,
        release_pct: float = 1.0,
    ) -> bool:
        """释放冻结金额并支付给卖家"""
        pool = await self._pool.get_by_id(pool_id)
        if pool is None:
            return False

        release_amount = amount * release_pct
        refund_amount = amount * (1.0 - release_pct)

        # 解冻
        new_frozen = float(pool.frozen_amount) - amount
        if new_frozen < 0:
            logger.error("release_over_unfreeze", pool_id=str(pool_id))
            return False

        pool.frozen_amount = new_frozen
        # 扣减余额（释放给卖家的部分）
        pool.balance = float(pool.balance) - release_amount
        # 退回部分（如有）
        # refund_amount 已经在余额中（因为之前只冻结未扣减），不需要额外操作

        await self._pool.update(pool)

        await self._audit.log(
            log_type="PAY-RELEASE",
            actor_type="system",
            actor_id="budget_manager",
            target_type="budget_pool",
            target_id=str(pool_id),
            action="release",
            data={
                "pool_id": str(pool_id),
                "provider_id": str(provider_id),
                "order_id": str(order_id),
                "original_amount": amount,
                "release_to_provider": release_amount,
                "refund_to_buyer": refund_amount,
                "release_pct": release_pct,
            },
        )
        return True

    async def recharge(self, pool_id: UUID, amount: float, operator_id: str) -> bool:
        """充值预算池"""
        pool = await self._pool.get_by_id(pool_id)
        if pool is None:
            return False

        pool.balance = float(pool.balance) + amount
        # 检查总量上限
        if pool.total_cap and float(pool.balance) > float(pool.total_cap):
            logger.warning("recharge_exceeds_cap", pool_id=str(pool_id))
            # 仍然允许充值，但记录警告

        await self._pool.update(pool)

        await self._audit.log(
            log_type="PAY-RECHARGE",
            actor_type="owner",
            actor_id=operator_id,
            target_type="budget_pool",
            target_id=str(pool_id),
            action="recharge",
            data={"pool_id": str(pool_id), "amount": amount, "new_balance": float(pool.balance)},
        )
        return True

    async def _get_daily_spent(self, pool_id: UUID, agent_id: UUID | None) -> float:
        """获取当日已消耗金额"""
        today = date.today().isoformat()
        snap = await self._snap.get_by_date(pool_id, agent_id, today)
        return float(snap.daily_spent) if snap else 0.0
```

---

## 六、x402 结算适配

```python
# src/aimart/payment/settle_x402.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class X402PaymentPayload:
    """x402 协议支付载荷"""
    version: str = "1"
    network_id: str = "84532"      # Base Sepolia testnet / Base mainnet: "8453"
    asset: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA0290E"  # USDC on Base
    amount: str = ""               # 6-decimal USDC amount (e.g., "1000000" = 1.00 USDC)
    recipient: str = ""            # Seller's Ethereum address
    signature: str = ""            # Agent's EIP-712 signature
    payload_hash: str = ""         # Keccak256 of the payment payload


@datadataclass
class X402SettlementResult:
    """x402 结算结果"""
    success: bool
    tx_hash: str | None = None
    block_number: int | None = None
    error: str | None = None


class X402Settler:
    """
    x402 协议结算器。

    x402 激活 HTTP 402 状态码：
    - Agent 请求资源 → 服务端返回 402 + payment_required payload
    - Agent 构造链上微支付 → 重新请求并附带 payment proof
    - 服务端验证 proof → 返回资源

    Facilitator 角色：
    - 代付 Gas（Agent 无需持有 ETH）
    - 验证支付 proof
    - 将 USDC 从 Agent 钱包转入 Seller 钱包
    """

    def __init__(self, web3_provider_url: str, facilitator_private_key: str, contract_address: str):
        self._provider_url = web3_provider_url
        self._facilitator_key = facilitator_private_key
        self._contract_address = contract_address

    async def prepare_payment(
        self,
        amount_usdc: float,
        recipient_address: str,
        agent_wallet_address: str,
    ) -> X402PaymentPayload:
        """
        构造 x402 支付载荷（不执行链上交易，由 Agent 签名后提交）。
        """
        # USDC 使用 6 位小数
        amount_smallest_unit = str(int(amount_usdc * 1_000_000))

        payload = X402PaymentPayload(
            amount=amount_smallest_unit,
            recipient=recipient_address,
        )

        logger.info(
            "x402_payment_prepared",
            agent=agent_wallet_address,
            recipient=recipient_address,
            amount_usdc=amount_usdc,
        )
        return payload

    async def verify_and_settle(
        self,
        payment_payload: X402PaymentPayload,
        agent_signature: str,
    ) -> X402SettlementResult:
        """
        验证 Agent 签名并执行链上结算。

        流程：
        1. 验证 EIP-712 签名 → 确认 Agent 授权支付
        2. 检查 Agent USDC 余额 ≥ amount
        3. 检查 Agent 已授权 Facilitator 合约 ≥ amount (approve)
        4. Facilitator 提交 transferFrom tx
        5. 等待链上确认
        """
        try:
            # Step 1: 验证签名（伪代码，实际使用 web3.py EIP-712 验证）
            is_valid = await self._verify_eip712_signature(payment_payload, agent_signature)
            if not is_valid:
                return X402SettlementResult(success=False, error="签名验证失败")

            # Step 2-4: Facilitator 提交链上交易
            tx_hash = await self._submit_transfer(
                from_address=payment_payload.recipient,  # 实际应从签名恢复
                to_address=payment_payload.recipient,
                amount=payment_payload.amount,
            )

            # Step 5: 等待确认（1 block confirmation）
            receipt = await self._wait_for_confirmation(tx_hash)

            logger.info(
                "x402_settled",
                tx_hash=tx_hash,
                amount=payment_payload.amount,
                recipient=payment_payload.recipient,
            )

            return X402SettlementResult(
                success=True,
                tx_hash=tx_hash,
                block_number=receipt.get("blockNumber"),
            )

        except Exception as e:
            logger.error("x402_settlement_failed", error=str(e))
            return X402SettlementResult(success=False, error=str(e))

    async def _verify_eip712_signature(self, payload: X402PaymentPayload, signature: str) -> bool:
        """验证 EIP-712 签名——实际实现使用 web3.py"""
        # TODO: 实际 EIP-712 验证逻辑
        return True

    async def _submit_transfer(self, from_address: str, to_address: str, amount: str) -> str:
        """提交 USDC transferFrom 交易"""
        # TODO: 实际 web3.py 交易提交
        return "0x_placeholder_tx_hash"

    async def _wait_for_confirmation(self, tx_hash: str, timeout_seconds: int = 30) -> dict:
        """等待链上确认"""
        # TODO: 实际链上确认等待
        return {"blockNumber": 0}
```

---

## 七、ACP 结算适配

```python
# src/aimart/payment/settle_acp.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class ACPPaymentIntent:
    """ACP（Agent Commerce Protocol）支付意图"""
    intent_id: str
    agent_id: str
    owner_id: str
    amount_cny: float
    provider_id: str
    # Shared Payment Token
    spt: str = ""                  # 限定卖家和金额的支付令牌
    spt_expires_at: str = ""
    # Stripe Payment Intent
    stripe_payment_intent_id: str = ""
    stripe_client_secret: str = ""


@dataclass
class ACPSettlementResult:
    """ACP 结算结果"""
    success: bool
    payment_intent_id: str | None = None
    charge_id: str | None = None
    error: str | None = None


class ACPSettler:
    """
    ACP 协议结算器。

    ACP 由 OpenAI + Stripe 推动，核心机制：
    - Agent 使用 Shared Payment Token (SPT) 发起支付
    - SPT 限定：特定卖家 + 金额上限 + 有效期
    - Stripe 后台完成法币结算
    - 不暴露底层支付凭证给 Agent
    """

    def __init__(self, stripe_api_key: str, webhook_secret: str):
        self._stripe_key = stripe_api_key
        self._webhook_secret = webhook_secret

    async def create_payment_intent(
        self,
        agent_id: str,
        owner_id: str,
        amount_cny: float,
        provider_id: str,
        order_id: str,
        currency: str = "cny",
    ) -> ACPPaymentIntent:
        """
        创建 ACP 支付意图。

        流程：
        1. 创建 Stripe PaymentIntent
        2. 生成 SPT（Shared Payment Token）
        3. 返回支付意图（含 SPT 给 Agent 使用）
        """
        # Step 1: 创建 Stripe PaymentIntent（伪代码）
        stripe_intent = await self._create_stripe_intent(
            amount=amount_cny,
            currency=currency,
            metadata={
                "agent_id": agent_id,
                "owner_id": owner_id,
                "provider_id": provider_id,
                "order_id": order_id,
            },
        )

        # Step 2: 生成 SPT
        spt = await self._generate_spt(
            owner_id=owner_id,
            provider_id=provider_id,
            max_amount=amount_cny,
            expires_in_minutes=30,
        )

        intent = ACPPaymentIntent(
            intent_id=f"acp_{stripe_intent['id']}",
            agent_id=agent_id,
            owner_id=owner_id,
            amount_cny=amount_cny,
            provider_id=provider_id,
            spt=spt["token"],
            spt_expires_at=spt["expires_at"],
            stripe_payment_intent_id=stripe_intent["id"],
            stripe_client_secret=stripe_intent["client_secret"],
        )

        logger.info(
            "acp_intent_created",
            intent_id=intent.intent_id,
            agent_id=agent_id,
            amount=amount_cny,
            provider_id=provider_id,
        )

        return intent

    async def confirm_with_spt(
        self,
        intent_id: str,
        spt: str,
    ) -> ACPSettlementResult:
        """
        Agent 使用 SPT 确认支付。

        流程：
        1. 验证 SPT 有效性（卖家、金额、有效期）
        2. 调用 Stripe confirm PaymentIntent
        3. 返回结算结果
        """
        # Step 1: 验证 SPT
        spt_valid = await self._verify_spt(spt)
        if not spt_valid:
            return ACPSettlementResult(success=False, error="SPT 无效或已过期")

        # Step 2: Stripe 确认
        try:
            charge = await self._confirm_stripe_intent(intent_id)

            logger.info(
                "acp_settled",
                intent_id=intent_id,
                charge_id=charge.get("id"),
            )

            return ACPSettlementResult(
                success=True,
                payment_intent_id=intent_id,
                charge_id=charge.get("id"),
            )
        except Exception as e:
            logger.error("acp_settlement_failed", intent_id=intent_id, error=str(e))
            return ACPSettlementResult(success=False, error=str(e))

    async def handle_webhook(self, event_type: str, event_data: dict) -> None:
        """处理 Stripe Webhook 回调"""
        if event_type == "payment_intent.succeeded":
            await self._on_payment_success(event_data)
        elif event_type == "payment_intent.payment_failed":
            await self._on_payment_failure(event_data)

    async def _create_stripe_intent(self, amount: float, currency: str, metadata: dict) -> dict:
        """创建 Stripe PaymentIntent"""
        # TODO: 实际 Stripe API 调用
        return {"id": "pi_placeholder", "client_secret": "cs_placeholder"}

    async def _generate_spt(self, owner_id: str, provider_id: str, max_amount: float, expires_in_minutes: int) -> dict:
        """生成 Shared Payment Token"""
        # TODO: 实际 SPT 生成逻辑（JWT + 限制条件）
        return {"token": "spt_placeholder", "expires_at": "2026-06-07T05:00:00Z"}

    async def _verify_spt(self, spt: str) -> bool:
        """验证 SPT"""
        # TODO: 实际验证
        return True

    async def _confirm_stripe_intent(self, intent_id: str) -> dict:
        """确认 Stripe PaymentIntent"""
        # TODO: 实际 Stripe 确认
        return {"id": "ch_placeholder"}

    async def _on_payment_success(self, data: dict) -> None:
        """支付成功回调"""
        logger.info("acp_payment_succeeded", data=data)

    async def _on_payment_failure(self, data: dict) -> None:
        """支付失败回调"""
        logger.error("acp_payment_failed", data=data)
```

---

## 八、异常检测

```python
# src/aimart/payment/anomaly.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

import structlog

logger = structlog.get_logger()


class AnomalyType(str, Enum):
    BURST_SPENDING = "burst_spending"           # 突发性消费
    HIGH_FREQ_MICRO = "high_freq_micro"         # 高频微支付
    BUDGET_DEPLETED = "budget_depleted"         # 预算耗尽
    CONCENTRATED_SELLER = "concentrated_seller" # 异常卖家集中
    OFF_HOURS_LARGE = "off_hours_large"         # 非工作时间大额


@dataclass
class AnomalyAlert:
    """异常告警"""
    anomaly_type: AnomalyType
    pool_id: str
    agent_id: str
    severity: str              # warning | critical
    message: str
    data: dict
    detected_at: datetime
    action_taken: str          # 暂停交易 / 限速 / 仅通知


class AnomalyDetector:
    """消费异常检测器"""

    def __init__(self, transaction_repo, allocation_repo, notification_service):
        self._tx_repo = transaction_repo
        self._alloc_repo = allocation_repo
        self._notify = notification_service

    async def check_after_transaction(
        self,
        pool_id: str,
        agent_id: str,
        amount: float,
        provider_id: str,
    ) -> list[AnomalyAlert]:
        """每次交易后执行异常检查"""
        alerts = []

        # 检查1: 突发性消费 — 1小时内消费超过日限额50%
        burst = await self._check_burst_spending(pool_id, agent_id, amount)
        if burst:
            alerts.append(burst)

        # 检查2: 高频微支付 — 1分钟内超过100笔L0交易
        high_freq = await self._check_high_freq_micro(pool_id, agent_id)
        if high_freq:
            alerts.append(high_freq)

        # 检查3: 预算耗尽
        depleted = await self._check_budget_depleted(pool_id)
        if depleted:
            alerts.append(depleted)

        # 检查4: 异常卖家集中 — 同一Agent 80%+支出流向单一卖家
        concentrated = await self._check_concentrated_seller(agent_id, provider_id)
        if concentrated:
            alerts.append(concentrated)

        # 检查5: 非工作时间大额
        off_hours = await self._check_off_hours_large(amount)
        if off_hours:
            alerts.append(off_hours)

        # 处理告警
        for alert in alerts:
            await self._handle_alert(alert)

        return alerts

    async def _check_burst_spending(self, pool_id: str, agent_id: str, current_amount: float) -> AnomalyAlert | None:
        """突发性消费检测"""
        one_hour_ago = datetime.now(timezone.utc).replace(minute=0, second=0)
        recent_spent = await self._tx_repo.sum_spent_since(pool_id, agent_id, one_hour_ago)

        # 需要从 allocation 获取日限额
        alloc = await self._alloc_repo.get_by_agent(agent_id)
        daily_max = float(alloc.daily_max) if alloc else 2000.0

        if recent_spent + current_amount > daily_max * 0.5:
            return AnomalyAlert(
                anomaly_type=AnomalyType.BURST_SPENDING,
                pool_id=pool_id,
                agent_id=agent_id,
                severity="critical",
                message=f"1小时内消费 {recent_spent + current_amount:.2f} 超过日限额 {daily_max:.2f} 的50%",
                data={"recent_spent": recent_spent, "current_amount": current_amount, "daily_max": daily_max},
                detected_at=datetime.now(timezone.utc),
                action_taken="暂停该Agent交易 + 通知Owner",
            )
        return None

    async def _check_high_freq_micro(self, pool_id: str, agent_id: str) -> AnomalyAlert | None:
        """高频微支付检测"""
        one_min_ago = datetime.now(timezone.utc).replace(second=0)
        tx_count = await self._tx_repo.count_transactions_since(pool_id, agent_id, one_min_ago)

        if tx_count > 100:
            return AnomalyAlert(
                anomaly_type=AnomalyType.HIGH_FREQ_MICRO,
                pool_id=pool_id,
                agent_id=agent_id,
                severity="warning",
                message=f"1分钟内 {tx_count} 笔L0交易",
                data={"tx_count_last_minute": tx_count},
                detected_at=datetime.now(timezone.utc),
                action_taken="限速至10笔/分钟 + 通知Owner",
            )
        return None

    async def _check_budget_depleted(self, pool_id: str) -> AnomalyAlert | None:
        """预算耗尽检测"""
        pool = await self._alloc_repo.get_pool_by_id(pool_id)
        if pool and float(pool.balance) < float(pool.single_transaction_max):
            return AnomalyAlert(
                anomaly_type=AnomalyType.BUDGET_DEPLETED,
                pool_id=pool_id,
                agent_id="",
                severity="critical",
                message=f"余额 {pool.balance} 低于单笔最低限额",
                data={"balance": float(pool.balance), "min_tx": float(pool.single_transaction_max)},
                detected_at=datetime.now(timezone.utc),
                action_taken="暂停所有Agent交易 + 通知Owner",
            )
        return None

    async def _check_concentrated_seller(self, agent_id: str, provider_id: str) -> AnomalyAlert | None:
        """卖家集中度检测"""
        distribution = await self._tx_repo.get_provider_distribution(agent_id)
        if distribution:
            total_spent = sum(distribution.values())
            provider_spent = distribution.get(provider_id, 0)
            if total_spent > 0 and (provider_spent / total_spent) > 0.8:
                return AnomalyAlert(
                    anomaly_type=AnomalyType.CONCENTRATED_SELLER,
                    pool_id="",
                    agent_id=agent_id,
                    severity="warning",
                    message=f"Agent {agent_id} 80%以上支出流向卖家 {provider_id}",
                    data={"provider_id": provider_id, "concentration": provider_spent / total_spent},
                    detected_at=datetime.now(timezone.utc),
                    action_taken="触发卖家审查 + 通知Owner",
                )
        return None

    async def _check_off_hours_large(self, amount: float) -> AnomalyAlert | None:
        """非工作时间大额检测"""
        now = datetime.now(timezone.utc)
        # 工作时间：周一至周五 9:00-18:00 UTC+8
        hour_cn = (now.hour + 8) % 24
        is_work_hours = now.weekday() < 5 and 9 <= hour_cn < 18

        if not is_work_hours and amount > 100.0:
            return AnomalyAlert(
                anomaly_type=AnomalyType.OFF_HOURS_LARGE,
                pool_id="",
                agent_id="",
                severity="warning",
                message=f"非工作时间大额交易: {amount} CNY",
                data={"amount": amount, "hour_cn": hour_cn},
                detected_at=datetime.now(timezone.utc),
                action_taken="提升授权级别（L2→L3, L3→人工复核）",
            )
        return None

    async def _handle_alert(self, alert: AnomalyAlert) -> None:
        """处理异常告警：执行自动响应 + 通知"""
        logger.warning(
            "anomaly_detected",
            type=alert.anomaly_type.value,
            agent_id=alert.agent_id,
            severity=alert.severity,
            action=alert.action_taken,
        )
        # TODO: 执行自动响应（暂停Agent、限速等）
        # TODO: 通知 Owner
```

---

## 九、API 路由

```python
# src/aimart/payment/router.py

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from aimart.identity.auth import require_auth, require_owner
from aimart.payment.schemas import (
    CreateBudgetPoolRequest, RechargeBudgetPoolRequest,
    AllocateAgentBudgetRequest, BudgetPoolResponse,
    InitiatePaymentRequest, PaymentTransactionResponse,
    AuthorizationDecisionRequest, AuthorizationRequestResponse,
    EffectReportRequest,
)
from aimart.payment import service as payment_service

router = APIRouter()


# ---- 预算池 ----

@router.post("/pools", response_model=BudgetPoolResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_pool(request: CreateBudgetPoolRequest, auth=Depends(require_owner)):
    """创建预算池"""
    return await payment_service.create_budget_pool(request, owner_id=auth.participant_id)


@router.post("/pools/{pool_id}/recharge", response_model=BudgetPoolResponse)
async def recharge_budget_pool(pool_id: UUID, request: RechargeBudgetPoolRequest, auth=Depends(require_owner)):
    """充值预算池"""
    return await payment_service.recharge_budget_pool(pool_id, request, operator_id=auth.participant_id)


@router.get("/pools/{pool_id}", response_model=BudgetPoolResponse)
async def get_budget_pool(pool_id: UUID, auth=Depends(require_auth)):
    """获取预算池详情"""
    return await payment_service.get_budget_pool(pool_id)


@router.post("/pools/{pool_id}/agents", status_code=status.HTTP_201_CREATED)
async def allocate_agent_budget(pool_id: UUID, request: AllocateAgentBudgetRequest, auth=Depends(require_owner)):
    """为 Agent 分配预算"""
    return await payment_service.allocate_agent_budget(pool_id, request)


# ---- 支付交易 ----

@router.post("/transactions", response_model=PaymentTransactionResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(request: InitiatePaymentRequest, auth=Depends(require_auth)):
    """发起支付（创建交易 + 预算检查 + 授权判断 + 冻结资金）"""
    return await payment_service.initiate_payment(request, agent_id=auth.agent_id)


@router.get("/transactions/{transaction_id}", response_model=PaymentTransactionResponse)
async def get_transaction(transaction_id: UUID, auth=Depends(require_auth)):
    """获取交易详情"""
    return await payment_service.get_transaction(transaction_id)


# ---- 授权审批 ----

@router.get("/authorizations", response_model=list[AuthorizationRequestResponse])
async def list_pending_authorizations(auth=Depends(require_owner)):
    """列出待审批的授权请求"""
    return await payment_service.list_pending_authorizations(owner_id=auth.participant_id)


@router.post("/authorizations/{auth_id}/decide", response_model=AuthorizationRequestResponse)
async def decide_authorization(auth_id: UUID, request: AuthorizationDecisionRequest, auth=Depends(require_owner)):
    """审批授权请求"""
    return await payment_service.decide_authorization(auth_id, request, owner_id=auth.participant_id)


# ---- 效果回传 ----

@router.post("/effect-reports", status_code=status.HTTP_200_OK)
async def report_effect(request: EffectReportRequest, auth=Depends(require_auth)):
    """回传使用效果（触发担保交易状态转换）"""
    return await payment_service.report_effect(request, agent_id=auth.agent_id)
```

---

## 十、Service 骨架

```python
# src/aimart/payment/service.py

from __future__ import annotations

from uuid import UUID

import structlog

from aimart.payment.budget import BudgetManager
from aimart.payment.authorization import determine_auth_level, calculate_auth_expiry
from aimart.payment.escrow import EscrowState, EscrowEvent, transition
from aimart.payment.anomaly import AnomalyDetector
from aimart.payment.schemas import *
from aimart.rules.engine import RulesEngine, RuleContext
from aimart.audit.logger import AuditLogger

logger = structlog.get_logger()


class PaymentService:
    """支付域服务"""

    def __init__(
        self,
        budget_manager: BudgetManager,
        anomaly_detector: AnomalyDetector,
        rules_engine: RulesEngine,
        audit_logger: AuditLogger,
        pool_repo,
        transaction_repo,
        auth_repo,
    ):
        self._budget = budget_manager
        self._anomaly = anomaly_detector
        self._rules = rules_engine
        self._audit = audit_logger
        self._pools = pool_repo
        self._txs = transaction_repo
        self._auths = auth_repo

    async def initiate_payment(
        self,
        request: InitiatePaymentRequest,
        agent_id: UUID,
    ) -> PaymentTransactionResponse:
        """
        发起支付完整流程：
        1. 规则引擎评估
        2. 预算充足性检查
        3. 分层授权判断
        4. 冻结资金
        5. 创建交易记录
        6. 异常检测
        7. 执行结算（x402/ACP/fiat）
        """
        # Step 1: 规则引擎
        rule_ctx = RuleContext(
            actor_type="agent",
            actor_id=str(agent_id),
            operation="payment_settle",
            budget_pool_id=str(request.pool_id),
        )
        rule_result = await self._rules.evaluate(rule_ctx)
        if rule_result.blocked:
            raise ValueError(f"规则引擎阻止: {rule_result.blocked_by}")

        # Step 2: 预算检查
        order = await self._txs.get_order(request.order_id)
        amount = float(order.amount)
        sufficient, reason = await self._budget.check_sufficient(
            request.pool_id, agent_id, amount
        )
        if not sufficient:
            raise ValueError(f"预算不足: {reason}")

        # Step 3: 分层授权
        alloc = await self._pools.get_allocation(agent_id, request.pool_id)
        agent_level = alloc.spending_authority_level if alloc else "L0"
        required_level, needs_approval = determine_auth_level(amount, agent_level)

        if needs_approval:
            # 创建授权请求，等待审批
            auth_req = await self._create_authorization_request(
                agent_id=agent_id,
                pool_id=request.pool_id,
                order_id=request.order_id,
                amount=amount,
                level=required_level,
                item_name=getattr(order, "item_name", None),
                item_type=getattr(order, "item_type", None),
            )
            # L2/L3 交易返回 pending 状态，等待审批
            # 审批通过后由 webhook/轮询触发后续流程
            logger.info("payment_awaiting_authorization", auth_id=str(auth_req.id))

        # Step 4: 冻结资金
        frozen = await self._budget.freeze(
            pool_id=request.pool_id,
            agent_id=agent_id,
            amount=amount,
            order_id=request.order_id,
        )
        if not frozen:
            raise ValueError("资金冻结失败")

        # Step 5: 创建交易记录
        tx = await self._txs.create(
            pool_id=request.pool_id,
            order_id=request.order_id,
            agent_id=agent_id,
            provider_id=order.provider_id,
            amount=amount,
            currency="CNY",
            settlement_channel=request.settlement_channel,
            escrow_status="frozen",
            authorization_level=required_level,
            status="authorized" if not needs_approval else "pending",
        )

        # Step 6: 异常检测
        alerts = await self._anomaly.check_after_transaction(
            pool_id=str(request.pool_id),
            agent_id=str(agent_id),
            amount=amount,
            provider_id=str(order.provider_id),
        )

        # Step 7: 如果不需要审批，立即执行结算
        if not needs_approval:
            await self._execute_settlement(tx, request.settlement_channel)

        # Step 8: 审计日志
        await self._audit.log(
            log_type="PAY-INITIATE",
            actor_type="agent",
            actor_id=str(agent_id),
            target_type="payment_transaction",
            target_id=str(tx.id),
            action="initiate_payment",
            data={
                "order_id": str(request.order_id),
                "pool_id": str(request.pool_id),
                "amount": amount,
                "settlement_channel": request.settlement_channel,
                "auth_level": required_level,
                "needs_approval": needs_approval,
            },
        )

        return PaymentTransactionResponse(
            id=tx.id,
            order_id=tx.order_id,
            amount=float(tx.amount),
            currency=tx.currency,
            commission_amount=float(tx.commission_amount),
            provider_payout=float(tx.provider_payout),
            settlement_channel=tx.settlement_channel,
            escrow_status=tx.escrow_status,
            status=tx.status,
            authorization_level=tx.authorization_level,
            created_at=tx.created_at,
        )

    async def report_effect(self, request: EffectReportRequest, agent_id: UUID) -> dict:
        """
        效果回传 → 触发担保交易状态转换 → 资金分配
        """
        tx = await self._txs.get_by_id(request.transaction_id)
        if tx is None:
            raise ValueError("交易不存在")
        if tx.escrow_status not in ("frozen", "partial_release"):
            raise ValueError(f"交易状态不支持效果回传: {tx.escrow_status}")

        # 确定事件
        if request.effect_score >= 4:
            event = EscrowEvent.EFFECT_CONFIRMED
        elif request.effect_score >= 2:
            event = EscrowEvent.EFFECT_PARTIAL
        else:
            event = EscrowEvent.EFFECT_FAILED

        # 状态转换
        result = transition(
            current_state=EscrowState(tx.escrow_status),
            event=event,
            effect_score=request.effect_score,
        )

        # 更新交易
        tx.escrow_status = result.new_state.value
        tx.effect_score = request.effect_score
        tx.effect_reported_at = datetime.now(timezone.utc)

        # 资金分配
        if result.new_state in (EscrowState.RELEASED, EscrowState.PARTIAL_RELEASE, EscrowState.REFUNDED):
            await self._budget.release(
                pool_id=tx.pool_id,
                amount=float(tx.amount),
                provider_id=tx.provider_id,
                order_id=tx.order_id,
                release_pct=result.provider_payout_pct,
            )

        await self._txs.update(tx)

        await self._audit.log(
            log_type="PAY-EFFECT",
            actor_type="agent",
            actor_id=str(agent_id),
            target_type="payment_transaction",
            target_id=str(tx.id),
            action="report_effect",
            data={
                "effect_score": request.effect_score,
                "old_state": result.old_state.value,
                "new_state": result.new_state.value,
                "provider_pct": result.provider_payout_pct,
                "buyer_pct": result.buyer_refund_pct,
            },
        )

        return {
            "transaction_id": str(tx.id),
            "escrow_status": result.new_state.value,
            "provider_payout_pct": result.provider_payout_pct,
            "buyer_refund_pct": result.buyer_refund_pct,
        }

    async def _create_authorization_request(self, **kwargs):
        """创建授权请求"""
        from aimart.payment.models import AuthorizationRequest
        # ... 创建逻辑
        pass

    async def _execute_settlement(self, tx, channel: str):
        """执行结算"""
        if channel == "x402":
            from aimart.payment.settle_x402 import X402Settler
            # ... x402 结算
        elif channel == "acp":
            from aimart.payment.settle_acp import ACPSettler
            # ... ACP 结算
        else:
            # fiat: 记账即可，线下对账
            tx.status = "completed"
            tx.escrow_released_at = datetime.now(timezone.utc)
            await self._txs.update(tx)
```

---

## 十一、Codex 执行检查清单

| # | 检查项 | 预期结果 |
|---|--------|---------|
| 1 | 创建 4 张数据表 | `budget_pools`, `agent_budget_allocations`, `payment_transactions`, `authorization_requests`, `daily_budget_snapshots` |
| 2 | 预算检查逻辑 | 余额不足 → 拒绝，超限额 → 拒绝，Agent 限额不足 → 拒绝 |
| 3 | 冻结/释放操作 | freeze 后 frozen_amount 增加，release 后 balance 扣减、frozen_amount 减少 |
| 4 | 担保状态机 | frozen→released/refunded/partial_release/disputed 全部转换合法 |
| 5 | 分层授权 | ≤0.01→L0, 0.01-1→L1, 1-100→L2, >100→L3; L2/L3 创建审批请求 |
| 6 | 授权超时 | L2 30min、L3 1hour 未审批 → 自动拒绝 |
| 7 | x402 结算 | 构造 EIP-712 载荷 → Agent 签名 → Facilitator 提交链上交易 |
| 8 | ACP 结算 | 创建 Stripe PaymentIntent → 生成 SPT → Agent 用 SPT 确认 |
| 9 | 异常检测 | 5种异常类型全部覆盖，critical→暂停交易，warning→限速/通知 |
| 10 | 审计日志 | 每个资金操作都有 AUDIT 记录，含金额、双方ID、操作类型 |
