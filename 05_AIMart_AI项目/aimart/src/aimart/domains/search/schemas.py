from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Constraint sub-models
# ---------------------------------------------------------------------------

class PerformanceConstraint(BaseModel):
    """Performance-related constraints for capability matching."""

    latency_p50_ms_max: int | None = Field(
        None, description="Maximum acceptable p50 latency in milliseconds"
    )
    latency_p99_ms_max: int | None = Field(
        None, description="Maximum acceptable p99 latency in milliseconds"
    )
    throughput_rps_min: int | None = Field(
        None, description="Minimum required throughput in requests per second"
    )
    availability_sla_min: float | None = Field(
        None, ge=0.0, le=1.0, description="Minimum required availability (0.0-1.0)"
    )


class BudgetConstraint(BaseModel):
    """Budget and pricing constraints for capability matching."""

    max_price_per_call: float | None = Field(
        None, ge=0.0, description="Maximum price per API call"
    )
    max_price_per_token: float | None = Field(
        None, ge=0.0, description="Maximum price per token"
    )
    max_price_per_hour: float | None = Field(
        None, ge=0.0, description="Maximum price per hour of compute"
    )
    preferred_pricing_model: str | None = Field(
        None, description="Preferred pricing model (per_call, per_token, per_hour, freemium)"
    )
    currency: str = Field(
        "CNY", max_length=8, description="Currency for price values"
    )


class TrustConstraint(BaseModel):
    """Trust and certification constraints for capability matching."""

    min_trust_score: float | None = Field(
        None, ge=0.0, le=100.0, description="Minimum trust score (0-100)"
    )
    certification_required: bool = Field(
        False, description="Whether certification is required"
    )
    min_transactions: int | None = Field(
        None, ge=0, description="Minimum number of historical transactions"
    )


# ---------------------------------------------------------------------------
# Capability need (search query input)
# ---------------------------------------------------------------------------

class CapabilityNeed(BaseModel):
    """Structured description of what an AI Agent needs from the marketplace.

    This is the primary input to the search/match pipeline.  Agents express
    their capability requirements, domain constraints, and scoring preferences
    through this model.
    """

    need_type: str = Field(
        ...,
        description="Type of capability needed: model, skill, expert, or compute",
        pattern=r"^(model|skill|expert|compute)$",
    )
    domains: list[str] = Field(
        ..., min_length=1, description="Domain categories (at least one required)"
    )
    task_description: str | None = Field(
        None, max_length=500, description="Natural language description of the task"
    )
    input_format: dict[str, Any] | None = Field(
        None, description="Expected input format specification"
    )
    output_format: dict[str, Any] | None = Field(
        None, description="Expected output format specification"
    )
    supported_languages: list[str] | None = Field(
        None, description="Required supported languages"
    )
    performance: PerformanceConstraint | None = Field(
        None, description="Performance constraints"
    )
    budget: BudgetConstraint | None = Field(
        None, description="Budget constraints"
    )
    trust: TrustConstraint | None = Field(
        None, description="Trust and certification constraints"
    )
    scoring_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "capability_match": 0.35,
            "performance": 0.20,
            "price": 0.20,
            "trust": 0.15,
            "availability": 0.10,
        },
        description="Weights for each scoring dimension; must sum to 1.0",
    )

    @field_validator("scoring_weights")
    @classmethod
    def validate_scoring_weights(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure scoring weights sum to 1.0 (within floating-point tolerance)."""
        expected_keys = {
            "capability_match", "performance", "price", "trust", "availability"
        }
        if set(v.keys()) != expected_keys:
            raise ValueError(
                f"scoring_weights must contain exactly the keys: {sorted(expected_keys)}"
            )
        total = sum(v.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"scoring_weights must sum to 1.0, got {total:.6f}"
            )
        for key, weight in v.items():
            if weight < 0.0 or weight > 1.0:
                raise ValueError(
                    f"scoring_weights['{key}'] must be between 0.0 and 1.0, got {weight}"
                )
        return v


# ---------------------------------------------------------------------------
# Match scoring
# ---------------------------------------------------------------------------

class MatchedItemScore(BaseModel):
    """Five-dimensional scoring breakdown for a matched capability item."""

    capability_match: float = Field(
        ..., ge=0.0, le=1.0, description="Domain / language / task overlap score"
    )
    performance: float = Field(
        ..., ge=0.0, le=1.0, description="Performance fit score"
    )
    price: float = Field(
        ..., ge=0.0, le=1.0, description="Price competitiveness score"
    )
    trust: float = Field(
        ..., ge=0.0, le=1.0, description="Trust and certification score"
    )
    availability: float = Field(
        ..., ge=0.0, le=1.0, description="Availability SLA score"
    )
    composite: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted composite score"
    )


# ---------------------------------------------------------------------------
# Matched item
# ---------------------------------------------------------------------------

class MatchedItem(BaseModel):
    """A single capability item matched against an agent's need."""

    item_id: uuid.UUID
    item_name: str
    item_type: str
    item_version: str | None = None
    provider_id: uuid.UUID
    provider_name: str
    matched_domains: list[str]
    matched_task_types: list[str]
    performance_summary: dict[str, Any]
    pricing_summary: dict[str, Any]
    trust_score: float
    certification_status: str | None = None
    scores: MatchedItemScore
    trial_available: bool = False
    api_endpoint: str | None = None


# ---------------------------------------------------------------------------
# Search response
# ---------------------------------------------------------------------------

class SearchResponse(BaseModel):
    """Response payload returned to the agent after a capability search."""

    query_id: uuid.UUID
    need_type: str
    total_matches: int
    returned_count: int = Field(
        ..., le=20, description="Number of items returned (max 20)"
    )
    items: list[MatchedItem] = Field(
        default_factory=list, max_length=20
    )
    query_latency_ms: int
    match_latency_ms: int


# ---------------------------------------------------------------------------
# Trial
# ---------------------------------------------------------------------------

class TrialRequest(BaseModel):
    """Request to trial a capability item in the sandbox before purchase."""

    item_id: uuid.UUID
    need_type: str = Field(
        ..., pattern=r"^(model|skill|expert|compute)$"
    )
    trial_input: dict[str, Any] = Field(
        ..., description="Input payload for the trial execution"
    )
    trial_config: dict[str, Any] | None = Field(
        None, description="Optional configuration overrides for the trial"
    )


class TrialResult(BaseModel):
    """Result of a sandbox trial execution."""

    trial_id: uuid.UUID
    item_id: uuid.UUID
    success: bool
    output: dict[str, Any] | None = None
    performance: dict[str, Any] | None = None
    errors: list[str] | None = None
    sandbox_constraints: dict[str, Any] = Field(
        default_factory=lambda: {
            "max_execution_time_ms": 30000,
            "max_memory_mb": 512,
            "network_restricted": True,
        },
        description="Constraints applied during sandbox execution",
    )
