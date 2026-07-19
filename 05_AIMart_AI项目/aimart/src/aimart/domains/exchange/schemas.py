from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class OrderCreateRequest(BaseModel):
    """Request body for creating a new order."""

    item_id: UUID
    quantity: int = Field(default=1, ge=1)
    budget_pool_id: UUID
    settlement_channel: str = Field(
        default="fiat", pattern="^(fiat|x402|acp)$"
    )


class OrderResponse(BaseModel):
    """Full representation of a marketplace order."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    item_id: UUID
    provider_id: UUID
    item_type: str
    item_name: str
    pricing_model: str
    amount: Decimal
    currency: str
    quantity: int
    status: str
    payment_transaction_id: UUID | None = None
    trial_id: UUID | None = None
    delivered_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    """Paginated list of orders."""

    items: list[OrderResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Trial
# ---------------------------------------------------------------------------

class TrialCreateRequest(BaseModel):
    """Request body for creating a sandbox trial."""

    item_id: UUID
    input_data: dict


class TrialResponse(BaseModel):
    """Full representation of a sandbox trial."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    item_id: UUID
    status: str
    input_data: dict
    output_data: dict | None = None
    performance_data: dict | None = None
    sandbox_config: dict
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------

class DeliveryConfirmRequest(BaseModel):
    """Request body for confirming delivery."""

    delivery_method: str = Field(default="api_call", pattern="^(api_call|weight_download|code_package|instance)$")
    delivery_endpoint: str | None = None
    data_sensitivity: str = Field(default="public", pattern="^(public|internal|confidential|restricted)$")


class DeliveryConfirmResponse(BaseModel):
    """Response after confirming delivery."""

    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    status: str
    delivered_at: datetime


# ---------------------------------------------------------------------------
# Effect Report
# ---------------------------------------------------------------------------

class EffectReportRequest(BaseModel):
    """Request body for reporting capability effect."""

    effect_score: int = Field(..., ge=0, le=5, description="Effect score 0-5")
    success: bool = Field(default=True)
    actual_latency_ms: int | None = None
    detail: dict | None = None


class EffectReportResponse(BaseModel):
    """Response after reporting effect."""

    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    new_status: str
    escrow_result: dict
