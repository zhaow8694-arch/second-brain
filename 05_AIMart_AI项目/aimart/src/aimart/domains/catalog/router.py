from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.db.session import get_db
from aimart.domains.identity.auth import require_auth, require_provider

from .schemas import (
    CatalogItemCreateRequest,
    CatalogItemListResponse,
    CatalogItemResponse,
)
from .service import CatalogService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["catalog"])

# ---------------------------------------------------------------------------
# Service dependency
# ---------------------------------------------------------------------------

_service = CatalogService()


def _get_service() -> CatalogService:
    return _service


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/items",
    response_model=CatalogItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
    request: CatalogItemCreateRequest,
    provider_id: UUID = Query(..., description="Provider ID (from auth context)"),
    db: AsyncSession = Depends(get_db),
    svc: CatalogService = Depends(_get_service),
    _provider=Depends(require_provider),
) -> CatalogItemResponse:
    """Create a new catalog item.

    Requires provider authentication. The AgentCard is validated through
    a 3-stage pipeline before the item is persisted.
    """
    try:
        return await svc.create_item(request, provider_id=provider_id, db=db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/items",
    response_model=CatalogItemListResponse,
)
async def list_items(
    provider_id: UUID | None = Query(None),
    item_type: str | None = Query(None, pattern="^(model|skill|expert|compute)$"),
    status_filter: str | None = Query(None, alias="status", pattern="^(pending|active|delisted|suspended)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    svc: CatalogService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> CatalogItemListResponse:
    """List catalog items with optional filters and pagination.

    Requires authentication.
    """
    return await svc.list_items(
        db=db,
        provider_id=provider_id,
        item_type=item_type,
        status=status_filter,
        page=page,
        size=size,
    )


@router.get(
    "/items/{item_id}",
    response_model=CatalogItemResponse,
)
async def get_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    svc: CatalogService = Depends(_get_service),
    _auth=Depends(require_auth),
) -> CatalogItemResponse:
    """Get a single catalog item by ID.

    Requires authentication.
    """
    try:
        return await svc.get_item(item_id, db=db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.put(
    "/items/{item_id}",
    response_model=CatalogItemResponse,
)
async def update_item(
    item_id: UUID,
    agentcard: dict,
    provider_id: UUID = Query(..., description="Provider ID (from auth context)"),
    db: AsyncSession = Depends(get_db),
    svc: CatalogService = Depends(_get_service),
    _provider=Depends(require_provider),
) -> CatalogItemResponse:
    """Update a catalog item's AgentCard.

    Requires provider authentication and ownership of the item.
    The new AgentCard is re-validated before the update is applied.
    """
    try:
        return await svc.update_item(
            item_id=item_id,
            agentcard=agentcard,
            provider_id=provider_id,
            db=db,
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


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delist_item(
    item_id: UUID,
    provider_id: UUID = Query(..., description="Provider ID (from auth context)"),
    db: AsyncSession = Depends(get_db),
    svc: CatalogService = Depends(_get_service),
    _provider=Depends(require_provider),
) -> None:
    """Delist a catalog item.

    Marks the item as delisted and removes it from the search index.
    Requires provider authentication and ownership.
    """
    try:
        await svc.delist_item(
            item_id=item_id,
            provider_id=provider_id,
            db=db,
        )
    except ValueError as exc:
        if "not found" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
