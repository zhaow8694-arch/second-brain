from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from aimart.domains.audit.schemas import (
    AuditLogQuery,
    AuditLogResponse,
    HashChainVerification,
)
from aimart.domains.audit.service import AuditQueryService

router = APIRouter(tags=["audit"])


def _get_service() -> AuditQueryService:
    """Dependency injection placeholder — override in application wiring."""
    raise NotImplementedError("AuditQueryService dependency not configured")


def require_auth():
    """Placeholder for authentication dependency."""
    # Real implementation would validate JWT / session
    pass


def require_scope(scope: str):
    """Placeholder for scope/permission check dependency."""
    # Real implementation would verify the caller has the required scope
    def _check():
        pass
    return _check


@router.get("/audit/logs", response_model=AuditLogResponse)
async def query_logs(
    log_type: str | None = Query(None),
    actor_id: str | None = Query(None),
    target_id: str | None = Query(None),
    action: str | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    service: AuditQueryService = Depends(_get_service),
    _auth=Depends(require_auth),
    _scope=Depends(require_scope("audit:read")),
) -> AuditLogResponse:
    """Query audit logs with optional filters and pagination."""
    query = AuditLogQuery(
        log_type=log_type,
        actor_id=actor_id,
        target_id=target_id,
        action=action,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
    )
    return service.query_logs(query)


@router.get("/audit/verify", response_model=HashChainVerification)
async def verify_chain(
    log_type: str = Query(...),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    service: AuditQueryService = Depends(_get_service),
    _auth=Depends(require_auth),
    _scope=Depends(require_scope("audit:read")),
) -> HashChainVerification:
    """Verify hash chain integrity for a given log type and time range."""
    return service.verify_chain(log_type, start_time, end_time)


@router.get("/audit/merkle-root", response_model=str)
async def get_merkle_root(
    log_type: str = Query(...),
    target_date: date = Query(...),
    service: AuditQueryService = Depends(_get_service),
    _auth=Depends(require_auth),
    _scope=Depends(require_scope("audit:read")),
) -> str:
    """Compute the Merkle root for a given log type on a given date."""
    return service.get_merkle_root(log_type, target_date)
