from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Effect Report
# ---------------------------------------------------------------------------

class EffectReport(BaseModel):
    """Report submitted after an order delivery to assess item effectiveness."""

    transaction_id: UUID
    item_id: UUID
    agent_id: UUID
    effect_score: int = Field(..., ge=0, le=5)
    success: bool
    actual_latency_ms: int | None = None
    declared_latency_ms: int | None = None
    detail: dict | None = None


# ---------------------------------------------------------------------------
# Trust Score
# ---------------------------------------------------------------------------

class ScoreDelta(BaseModel):
    """A single trust-score change event."""

    event_type: str
    score_delta: float
    created_at: datetime


class TrustScoreResponse(BaseModel):
    """Current trust score for a target entity with recent history."""

    target_type: str
    target_id: UUID
    trust_score: float
    score_history: list[ScoreDelta] = Field(default_factory=list)
    updated_at: datetime


# ---------------------------------------------------------------------------
# Certification
# ---------------------------------------------------------------------------

class CertificationRequest(BaseModel):
    """Request body for submitting a certification request."""

    item_id: UUID
    benchmark_results: dict


class CertificationResponse(BaseModel):
    """Full representation of a certification record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_id: UUID
    certifier_id: UUID
    status: str
    benchmark_results: dict
    verified_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime
