from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.db.session import get_db
from aimart.domains.identity.auth import require_agent, require_auth

from .schemas import (
    DeliveryConfirmRequest,
    DeliveryConfirmResponse,
    EffectReportRequest,
    EffectReportResponse,
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
    TrialCreateRequest,
    TrialResponse,
)
from .service import ExchangeService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["exchange"])

# ---------------------------------------------------------------------------
# Service dependency
# ---------------------------------------------------------------------------

_service = ExchangeService()


def _get_service() -> ExchangeService:
    return _service


# ---------------------------------------------------------------------------
# Order routes
# ---------------------------------------------------------------------------

@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    request: OrderCreateRequest,
    agent_id: UUID = Query(..., description="Agent ID (from auth context)"),
    db: AsyncSession = Depends(get_db),
    svc: ExchangeService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> OrderResponse:
    """Create a new marketplace order.

    Validates that the catalog item exists and is active, checks
    the agent's budget, creates the order, and initiates escrow.
    """
    try:
        return await svc.create_order(
            request=request,
            agent_id=agent_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/orders",
    response_model=OrderListResponse,
)
async def list_orders(
    agent_id: UUID = Query(..., description="Agent ID (from auth context)"),
    status_filter: str | None = Query(
        None, alias="status",
        pattern="^(created|pending_payment|paid|delivered|completed|cancelled|disputed)$",
    ),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    svc: ExchangeService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> OrderListResponse:
    """List orders for the authenticated agent with optional status filter."""
    return await svc.list_orders(
        agent_id=agent_id,
        db=db,
        status=status_filter,
        page=page,
        size=size,
    )


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    svc: ExchangeService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> OrderResponse:
    """Get a single order by ID."""
    try:
        return await svc.get_order(order_id, db=db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderResponse,
)
async def cancel_order(
    order_id: UUID,
    agent_id: UUID = Query(..., description="Agent ID (from auth context)"),
    cancel_reason: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    svc: ExchangeService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> OrderResponse:
    """Cancel an order and unfreeze escrowed funds.

    Only the owning agent can cancel, and only if the order is in
    a cancellable state.
    """
    try:
        return await svc.cancel_order(
            order_id=order_id,
            agent_id=agent_id,
            db=db,
            cancel_reason=cancel_reason,
        )
    except ValueError as exc:
        if "not found" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Trial routes
# ---------------------------------------------------------------------------

@router.post(
    "/trials",
    response_model=TrialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_trial(
    request: TrialCreateRequest,
    agent_id: UUID = Query(..., description="Agent ID (from auth context)"),
    db: AsyncSession = Depends(get_db),
    svc: ExchangeService = Depends(_get_service),
    _agent=Depends(require_agent),
) -> TrialResponse:
    """Create and execute a sandbox trial for a catalog item.

    Enforces a daily trial limit of 3 per agent per item.
    Requires agent authentication.
    """
    try:
        return await svc.create_trial(
            request=request,
            agent_id=agent_id,
            db=db,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/trials/{trial_id}",
    response_model=TrialResponse,
)
async def get_trial(
    trial_id: UUID,
    db: AsyncSession = Depends(get_db),
    svc: ExchangeService = Depends(_get_service),
    _agent=Depends(require_agent),
) -> TrialResponse:
    """Get a sandbox trial by ID.

    Requires agent authentication.
    """
    from sqlalchemy import select

    from .models import Trial

    stmt = select(Trial).where(Trial.id == trial_id)
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()

    if trial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trial not found: {trial_id}",
        )

    from .service import _trial_to_response
    return _trial_to_response(trial)


# ---------------------------------------------------------------------------
# Delivery & Effect
# ---------------------------------------------------------------------------

@router.post(
    "/orders/{order_id}/confirm-delivery",
    response_model=DeliveryConfirmResponse,
)
async def confirm_delivery(
    order_id: UUID,
    request: DeliveryConfirmRequest,
    db: AsyncSession = Depends(get_db),
    svc: ExchangeService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> DeliveryConfirmResponse:
    """Confirm delivery of an order.

    Marks the order as delivered. Does NOT release funds — that
    happens after the agent reports an effect.
    """
    try:
        return await svc.confirm_delivery(
            order_id=order_id,
            delivery_method=request.delivery_method,
            delivery_endpoint=request.delivery_endpoint,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/orders/{order_id}/effect",
    response_model=EffectReportResponse,
)
async def report_effect(
    order_id: UUID,
    request: EffectReportRequest,
    agent_id: UUID = Query(..., description="Agent ID (from auth context)"),
    db: AsyncSession = Depends(get_db),
    svc: ExchangeService = Depends(_get_service),
    _agent=Depends(require_agent),
) -> EffectReportResponse:
    """Report the effect of a consumed capability.

    Triggers escrow completion (release funds to provider or refund to buyer)
    and trust score update.
    """
    try:
        return await svc.report_effect(
            order_id=order_id,
            agent_id=agent_id,
            effect_score=request.effect_score,
            success=request.success,
            actual_latency_ms=request.actual_latency_ms,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
