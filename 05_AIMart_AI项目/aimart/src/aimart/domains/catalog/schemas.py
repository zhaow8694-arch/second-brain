from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# CatalogItem
# ---------------------------------------------------------------------------

class CatalogItemCreateRequest(BaseModel):
    """Request body for creating a new catalog item."""

    item_type: str = Field(..., pattern="^(model|skill|expert|compute)$")
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=64)
    agentcard: dict
    description: str | None = None


class CatalogItemResponse(BaseModel):
    """Full representation of a catalog item including trust score."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    item_type: str
    name: str
    version: str
    description: str | None = None
    agentcard: dict
    agentcard_hash: str
    status: str
    certification_status: str
    trust_score: float
    total_transactions: int
    total_revenue: Decimal
    created_at: datetime
    updated_at: datetime


class CatalogItemListResponse(BaseModel):
    """Paginated list of catalog items."""

    items: list[CatalogItemResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# AgentCard Validation
# ---------------------------------------------------------------------------

class AgentCardValidationResult(BaseModel):
    """Result of the three-stage AgentCard validation pipeline."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    security_scan_result: str = Field(
        ..., pattern="^(clean|warning|failed)$"
    )
