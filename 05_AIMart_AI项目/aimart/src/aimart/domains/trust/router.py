from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.db.session import get_db
from aimart.domains.identity.auth import require_auth, require_certifier

from .schemas import (
    CertificationRequest,
    CertificationResponse,
    EffectReport,
    TrustScoreResponse,
)
from .service import TrustService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["trust"])

# ---------------------------------------------------------------------------
# Service dependency
# ---------------------------------------------------------------------------

_service = TrustService()


def _get_service() -> TrustService:
    return _service


# ---------------------------------------------------------------------------
# Effect report
# ---------------------------------------------------------------------------

@router.post(
    "/effect-reports",
    status_code=status.HTTP_201_CREATED,
)
async def submit_effect_report(
    report: EffectReport,
    db: AsyncSession = Depends(get_db),
    svc: TrustService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> dict:
    """Submit an effect report for a completed transaction.

    The report is processed through the trust scorer which calculates
    a score delta and updates the item's trust score accordingly.
    Requires authentication.
    """
    try:
        return await svc.submit_effect_report(report, db=db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Trust score
# ---------------------------------------------------------------------------

@router.get(
    "/scores/{target_type}/{target_id}",
    response_model=TrustScoreResponse,
)
async def get_trust_score(
    target_type: str = Path(..., pattern="^(item|provider|agent)$"),
    target_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    svc: TrustService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> TrustScoreResponse:
    """Get the trust score for a target entity.

    Target can be an item, provider, or agent. Returns the current
    trust score along with recent score delta history.
    Requires authentication.
    """
    try:
        return await svc.get_trust_score(
            target_type=target_type,
            target_id=target_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Certification
# ---------------------------------------------------------------------------

@router.post(
    "/certifications",
    response_model=CertificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_certification(
    request: CertificationRequest,
    certifier_id: UUID = Query(..., description="Certifier ID (from auth context)"),
    db: AsyncSession = Depends(get_db),
    svc: TrustService = Depends(_get_service),
    _certifier=Depends(require_certifier),
) -> CertificationResponse:
    """Submit a certification request for a catalog item.

    Requires certifier authentication. Creates a pending certification
    record with benchmark results.
    """
    try:
        return await svc.request_certification(
            request=request,
            certifier_id=certifier_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.put(
    "/certifications/{certification_id}",
    response_model=CertificationResponse,
)
async def process_certification(
    certification_id: UUID,
    approved: bool = Query(..., description="Whether the certification is approved"),
    notes: str | None = Query(None, description="Optional certifier notes"),
    db: AsyncSession = Depends(get_db),
    svc: TrustService = Depends(_get_service),
    _certifier=Depends(require_certifier),
) -> CertificationResponse:
    """Process a certification decision.

    If approved, updates the item's certification_status to 'certified'
    and recalculates the trust score. If rejected, sets status to 'rejected'.
    Requires certifier authentication.
    """
    try:
        return await svc.process_certification(
            certification_id=certification_id,
            approved=approved,
            db=db,
            notes=notes,
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
