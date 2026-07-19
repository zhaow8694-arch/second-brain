from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# BudgetPool
# ---------------------------------------------------------------------------

class CreateBudgetPoolRequest(BaseModel):
    owner_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(..., pattern="^(CNY|USD|USDC)$")
    total_cap: Decimal | None = None
    single_transaction_max: Decimal = Field(default=Decimal("500"))
    daily_max: Decimal = Field(default=Decimal("2000"))
    weekly_max: Decimal = Field(default=Decimal("10000"))
    monthly_max: Decimal = Field(default=Decimal("30000"))
    auto_recharge: bool = False
    recharge_threshold: Decimal | None = None
    recharge_amount: Decimal | None = None


class RechargeBudgetPoolRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    operator_id: UUID


class AllocateAgentBudgetRequest(BaseModel):
    agent_id: UUID
    daily_max: Decimal = Field(default=Decimal("500"))
    per_call_max: Decimal = Field(default=Decimal("1"))
    spending_authority_level: str = Field(default="L0", pattern="^L[0-3]$")


class BudgetPoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    currency: str
    balance: Decimal
    frozen_amount: Decimal
    available_balance: Decimal = Field(default=Decimal("0"))
    total_cap: Decimal | None = None
    single_transaction_max: Decimal
    daily_max: Decimal
    weekly_max: Decimal
    monthly_max: Decimal
    auto_recharge: bool
    recharge_threshold: Decimal | None = None
    recharge_amount: Decimal | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# PaymentTransaction
# ---------------------------------------------------------------------------

class InitiatePaymentRequest(BaseModel):
    order_id: UUID
    pool_id: UUID
    settlement_channel: str = Field(default="fiat", pattern="^(fiat|x402|acp)$")


class PaymentTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pool_id: UUID
    order_id: UUID
    agent_id: UUID
    provider_id: UUID
    amount: Decimal
    currency: str
    commission_rate: Decimal
    commission_amount: Decimal | None = None
    provider_payout: Decimal | None = None
    settlement_channel: str
    escrow_status: str
    authorization_level: str | None = None
    authorization_id: UUID | None = None
    status: str
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

class AuthorizationDecisionRequest(BaseModel):
    approved: bool
    reject_reason: str | None = None


class AuthorizationRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transaction_id: UUID
    agent_id: UUID
    owner_id: UUID
    level: str
    amount: Decimal
    item_name: str | None = None
    item_type: str | None = None
    status: str
    notification_channel: str
    reject_reason: str | None = None
    expires_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Effect Report
# ---------------------------------------------------------------------------

class EffectReportRequest(BaseModel):
    transaction_id: UUID
    effect_score: int = Field(..., ge=0, le=5)
    success: bool
    actual_latency_ms: int | None = None
    declared_latency_ms: int | None = None
    cost_actual: Decimal | None = None
    cost_declared: Decimal | None = None
    detail: dict | None = None
