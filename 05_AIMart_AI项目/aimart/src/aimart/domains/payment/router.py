from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from .schemas import (
    AllocateAgentBudgetRequest,
    AuthorizationDecisionRequest,
    AuthorizationRequestResponse,
    BudgetPoolResponse,
    CreateBudgetPoolRequest,
    EffectReportRequest,
    InitiatePaymentRequest,
    PaymentTransactionResponse,
    RechargeBudgetPoolRequest,
)
from .service import PaymentService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["payment"])


# ---------------------------------------------------------------------------
# Dependency stubs – replace with real auth/dependency injection
# ---------------------------------------------------------------------------

def get_payment_service() -> PaymentService:
    """Placeholder dependency – override in application setup."""
    raise NotImplementedError("PaymentService dependency not configured")


class OwnerChecker:
    """Dependency that verifies the current user owns the budget pool.

    TODO: Replace with real auth logic (JWT / session).
    """

    def __call__(self, pool_id: UUID, service: PaymentService = Depends(get_payment_service)):
        # Placeholder – in production, extract user_id from auth token
        # pool = service.repo.get_pool(pool_id)
        # if pool is None:
        #     raise HTTPException(status_code=404, detail="Budget pool not found")
        # if pool.owner_id != current_user_id:
        #     raise HTTPException(status_code=403, detail="Not the pool owner")
        pass


require_owner = OwnerChecker()


def require_auth():
    """Verify the current user is authenticated.

    TODO: Replace with real auth logic.
    """
    pass


# ---------------------------------------------------------------------------
# Budget Pool endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/pools",
    response_model=BudgetPoolResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_budget_pool(
    request: CreateBudgetPoolRequest,
    service: PaymentService = Depends(get_payment_service),
    _owner=Depends(require_owner),
):
    """Create a new budget pool."""
    try:
        pool = service.repo.create_pool(
            owner_id=request.owner_id,
            name=request.name,
            currency=request.currency,
            total_cap=request.total_cap,
            single_transaction_max=request.single_transaction_max,
            daily_max=request.daily_max,
            weekly_max=request.weekly_max,
            monthly_max=request.monthly_max,
            auto_recharge=request.auto_recharge,
            recharge_threshold=request.recharge_threshold,
            recharge_amount=request.recharge_amount,
        )
        return _pool_to_response(pool)
    except Exception as exc:
        logger.exception("create_budget_pool_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/pools/{pool_id}/recharge",
    response_model=BudgetPoolResponse,
)
def recharge_budget_pool(
    pool_id: UUID,
    request: RechargeBudgetPoolRequest,
    service: PaymentService = Depends(get_payment_service),
    _owner=Depends(require_owner),
):
    """Recharge (top-up) a budget pool."""
    try:
        service.budget_manager.recharge(
            pool_id=pool_id,
            amount=request.amount,
            operator_id=request.operator_id,
            repo=service.repo,
        )
        pool = service.repo.get_pool(pool_id)
        return _pool_to_response(pool)
    except Exception as exc:
        logger.exception("recharge_budget_pool_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/pools/{pool_id}",
    response_model=BudgetPoolResponse,
)
def get_budget_pool(
    pool_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    _auth=Depends(require_auth),
):
    """Get budget pool details."""
    pool = service.repo.get_pool(pool_id)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget pool not found",
        )
    return _pool_to_response(pool)


@router.post(
    "/pools/{pool_id}/agents",
    status_code=status.HTTP_201_CREATED,
)
def allocate_agent_budget(
    pool_id: UUID,
    request: AllocateAgentBudgetRequest,
    service: PaymentService = Depends(get_payment_service),
    _owner=Depends(require_owner),
):
    """Allocate budget for an agent within a pool."""
    try:
        allocation = service.repo.create_allocation(
            pool_id=pool_id,
            agent_id=request.agent_id,
            daily_max=request.daily_max,
            per_call_max=request.per_call_max,
            spending_authority_level=request.spending_authority_level,
        )
        return {
            "id": str(allocation.id),
            "pool_id": str(allocation.pool_id),
            "agent_id": str(allocation.agent_id),
            "daily_max": float(allocation.daily_max),
            "per_call_max": float(allocation.per_call_max),
            "spending_authority_level": allocation.spending_authority_level,
        }
    except Exception as exc:
        logger.exception("allocate_agent_budget_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Transaction endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/transactions",
    status_code=status.HTTP_201_CREATED,
)
def initiate_payment(
    request: InitiatePaymentRequest,
    agent_id: UUID = Query(..., description="The agent initiating the payment"),
    amount: Decimal = Query(..., description="Payment amount"),
    provider_id: UUID = Query(..., description="The provider receiving the payment"),
    currency: str = Query("CNY", description="Currency code"),
    item_name: str | None = Query(None, description="Item being purchased"),
    item_type: str | None = Query(None, description="Type of item"),
    service: PaymentService = Depends(get_payment_service),
    _auth=Depends(require_auth),
):
    """Initiate a new payment transaction."""
    try:
        result = service.initiate_payment(
            request=request,
            agent_id=agent_id,
            amount=amount,
            provider_id=provider_id,
            currency=currency,
            item_name=item_name,
            item_type=item_type,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Payment initiation failed"),
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("initiate_payment_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get(
    "/transactions/{transaction_id}",
    response_model=PaymentTransactionResponse,
)
def get_transaction(
    transaction_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    _auth=Depends(require_auth),
):
    """Get transaction details."""
    tx = service.repo.get_transaction(transaction_id)
    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return PaymentTransactionResponse.model_validate(tx)


# ---------------------------------------------------------------------------
# Authorization endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/authorizations",
)
def list_pending_authorizations(
    owner_id: UUID = Query(..., description="Filter by owner"),
    service: PaymentService = Depends(get_payment_service),
    _owner=Depends(require_owner),
):
    """List pending authorization requests for an owner."""
    auth_requests = service.repo.list_authorization_requests(
        owner_id=owner_id,
        status="pending",
    )
    return [
        AuthorizationRequestResponse.model_validate(ar)
        for ar in auth_requests
    ]


@router.post(
    "/authorizations/{auth_id}/decide",
)
def decide_authorization(
    auth_id: UUID,
    request: AuthorizationDecisionRequest,
    owner_id: UUID = Query(..., description="The owner making the decision"),
    service: PaymentService = Depends(get_payment_service),
    _owner=Depends(require_owner),
):
    """Approve or reject an authorization request."""
    try:
        result = service.decide_authorization(
            auth_id=auth_id,
            request=request,
            owner_id=owner_id,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Authorization decision failed"),
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("decide_authorization_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Effect Report endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/effect-reports",
)
def report_effect(
    request: EffectReportRequest,
    agent_id: UUID = Query(..., description="The agent reporting the effect"),
    service: PaymentService = Depends(get_payment_service),
    _auth=Depends(require_auth),
):
    """Report the effect (outcome) of a completed transaction."""
    try:
        result = service.report_effect(
            request=request,
            agent_id=agent_id,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Effect report failed"),
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("report_effect_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pool_to_response(pool) -> BudgetPoolResponse:
    """Convert a BudgetPool ORM object to a BudgetPoolResponse schema."""
    balance = Decimal(str(pool.balance))
    frozen = Decimal(str(pool.frozen_amount))
    return BudgetPoolResponse(
        id=pool.id,
        owner_id=pool.owner_id,
        name=pool.name,
        currency=pool.currency,
        balance=balance,
        frozen_amount=frozen,
        available_balance=balance - frozen,
        total_cap=Decimal(str(pool.total_cap)) if pool.total_cap is not None else None,
        single_transaction_max=Decimal(str(pool.single_transaction_max)),
        daily_max=Decimal(str(pool.daily_max)),
        weekly_max=Decimal(str(pool.weekly_max)),
        monthly_max=Decimal(str(pool.monthly_max)),
        auto_recharge=pool.auto_recharge,
        recharge_threshold=(
            Decimal(str(pool.recharge_threshold))
            if pool.recharge_threshold is not None
            else None
        ),
        recharge_amount=(
            Decimal(str(pool.recharge_amount))
            if pool.recharge_amount is not None
            else None
        ),
        status=pool.status,
        created_at=pool.created_at,
        updated_at=pool.updated_at,
    )
