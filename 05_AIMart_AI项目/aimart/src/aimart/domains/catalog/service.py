from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CatalogItem, CatalogItemStatus, ItemType
from .schemas import (
    CatalogItemCreateRequest,
    CatalogItemListResponse,
    CatalogItemResponse,
)
from .validator import validate_agentcard

logger = structlog.get_logger(__name__)


def _compute_agentcard_hash(agentcard: dict) -> str:
    """Compute SHA-256 hash of the AgentCard JSON for integrity checking."""
    canonical = json.dumps(agentcard, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _item_to_response(item: CatalogItem) -> CatalogItemResponse:
    """Convert a CatalogItem ORM object to a response schema."""
    return CatalogItemResponse(
        id=item.id,
        provider_id=item.provider_id,
        item_type=item.item_type.value if isinstance(item.item_type, ItemType) else item.item_type,
        name=item.name,
        version=item.version,
        description=item.description,
        agentcard=item.agentcard,
        agentcard_hash=item.agentcard_hash,
        status=item.status.value if isinstance(item.status, CatalogItemStatus) else item.status,
        certification_status=item.certification_status.value,
        trust_score=item.trust_score,
        total_transactions=item.total_transactions,
        total_revenue=Decimal(str(item.total_revenue)) if item.total_revenue is not None else Decimal("0"),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class CatalogService:
    """High-level orchestration for the catalog domain.

    Coordinates AgentCard validation, item persistence, Elasticsearch
    indexing, and audit logging.
    """

    def __init__(
        self,
        es_client: Any = None,
        audit_logger: Any = None,
    ) -> None:
        self._es = es_client
        self._audit = audit_logger

    # ------------------------------------------------------------------
    # Create item
    # ------------------------------------------------------------------

    async def create_item(
        self,
        request: CatalogItemCreateRequest,
        provider_id: UUID,
        db: AsyncSession,
    ) -> CatalogItemResponse:
        """Create a new catalog item after validating the AgentCard.

        Steps:
          1. Validate the AgentCard through the 3-stage pipeline.
          2. Create a CatalogItem record in the database.
          3. Index the item to Elasticsearch.
          4. Emit an audit event.

        Raises:
            ValueError: If the AgentCard fails validation.
        """
        # Validate agentcard
        validation = validate_agentcard(request.agentcard, request.item_type)
        if not validation.valid:
            logger.warning(
                "catalog_item_validation_failed",
                provider_id=str(provider_id),
                item_type=request.item_type,
                errors=validation.errors,
            )
            raise ValueError(
                f"AgentCard validation failed: {'; '.join(validation.errors)}"
            )

        if validation.warnings:
            logger.info(
                "catalog_item_validation_warnings",
                provider_id=str(provider_id),
                warnings=validation.warnings,
            )

        # Compute hash
        agentcard_hash = _compute_agentcard_hash(request.agentcard)

        # Create item
        item = CatalogItem(
            provider_id=provider_id,
            item_type=ItemType(request.item_type),
            name=request.name,
            version=request.version,
            description=request.description,
            agentcard=request.agentcard,
            agentcard_hash=agentcard_hash,
            status=CatalogItemStatus.PENDING,
        )
        db.add(item)
        await db.flush()

        # Index to Elasticsearch
        await self._index_to_es(item)

        # Audit
        self._audit_log(
            "catalog.item_created",
            item_id=str(item.id),
            provider_id=str(provider_id),
            item_type=request.item_type,
            name=request.name,
        )

        logger.info(
            "catalog_item_created",
            item_id=str(item.id),
            provider_id=str(provider_id),
            item_type=request.item_type,
        )

        return _item_to_response(item)

    # ------------------------------------------------------------------
    # Get item
    # ------------------------------------------------------------------

    async def get_item(
        self,
        item_id: UUID,
        db: AsyncSession,
    ) -> CatalogItemResponse:
        """Retrieve a single catalog item by ID.

        Raises:
            ValueError: If the item is not found.
        """
        stmt = select(CatalogItem).where(CatalogItem.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if item is None:
            raise ValueError(f"Catalog item not found: {item_id}")

        return _item_to_response(item)

    # ------------------------------------------------------------------
    # List items
    # ------------------------------------------------------------------

    async def list_items(
        self,
        db: AsyncSession,
        provider_id: UUID | None = None,
        item_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> CatalogItemListResponse:
        """List catalog items with optional filters and pagination."""
        stmt = select(CatalogItem)
        count_stmt = select(func.count()).select_from(CatalogItem)

        if provider_id is not None:
            stmt = stmt.where(CatalogItem.provider_id == provider_id)
            count_stmt = count_stmt.where(CatalogItem.provider_id == provider_id)

        if item_type is not None:
            stmt = stmt.where(CatalogItem.item_type == ItemType(item_type))
            count_stmt = count_stmt.where(CatalogItem.item_type == ItemType(item_type))

        if status is not None:
            stmt = stmt.where(CatalogItem.status == CatalogItemStatus(status))
            count_stmt = count_stmt.where(CatalogItem.status == CatalogItemStatus(status))

        # Count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(CatalogItem.created_at.desc())
        result = await db.execute(stmt)
        items = result.scalars().all()

        return CatalogItemListResponse(
            items=[_item_to_response(i) for i in items],
            total=total,
            page=page,
            size=size,
        )

    # ------------------------------------------------------------------
    # Update item
    # ------------------------------------------------------------------

    async def update_item(
        self,
        item_id: UUID,
        agentcard: dict,
        provider_id: UUID,
        db: AsyncSession,
    ) -> CatalogItemResponse:
        """Update a catalog item's AgentCard after re-validation.

        Steps:
          1. Load the item and verify ownership.
          2. Re-validate the new AgentCard.
          3. Update the record.
          4. Re-index to Elasticsearch.
          5. Emit an audit event.

        Raises:
            ValueError: If the item is not found, not owned by the provider,
                        or the new AgentCard fails validation.
        """
        stmt = select(CatalogItem).where(CatalogItem.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if item is None:
            raise ValueError(f"Catalog item not found: {item_id}")
        if item.provider_id != provider_id:
            raise ValueError("Not authorized to update this item")

        item_type_str = item.item_type.value if isinstance(item.item_type, ItemType) else item.item_type

        # Re-validate
        validation = validate_agentcard(agentcard, item_type_str)
        if not validation.valid:
            raise ValueError(
                f"AgentCard validation failed: {'; '.join(validation.errors)}"
            )

        # Update
        item.agentcard = agentcard
        item.agentcard_hash = _compute_agentcard_hash(agentcard)
        item.updated_at = datetime.now(UTC)
        await db.flush()

        # Re-index
        await self._index_to_es(item)

        # Audit
        self._audit_log(
            "catalog.item_updated",
            item_id=str(item.id),
            provider_id=str(provider_id),
        )

        logger.info(
            "catalog_item_updated",
            item_id=str(item.id),
            provider_id=str(provider_id),
        )

        return _item_to_response(item)

    # ------------------------------------------------------------------
    # Delist item
    # ------------------------------------------------------------------

    async def delist_item(
        self,
        item_id: UUID,
        provider_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Mark a catalog item as delisted and remove from ES index.

        Raises:
            ValueError: If the item is not found or not owned by the provider.
        """
        stmt = select(CatalogItem).where(CatalogItem.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if item is None:
            raise ValueError(f"Catalog item not found: {item_id}")
        if item.provider_id != provider_id:
            raise ValueError("Not authorized to delist this item")

        item.status = CatalogItemStatus.DELISTED
        item.updated_at = datetime.now(UTC)
        await db.flush()

        # Remove from ES
        await self._remove_from_es(item_id)

        # Audit
        self._audit_log(
            "catalog.item_delisted",
            item_id=str(item.id),
            provider_id=str(provider_id),
        )

        logger.info(
            "catalog_item_delisted",
            item_id=str(item.id),
            provider_id=str(provider_id),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _index_to_es(self, item: CatalogItem) -> None:
        """Index a catalog item into Elasticsearch."""
        if self._es is None:
            logger.debug("es_index_skipped", reason="no_es_client")
            return

        try:
            doc = {
                "item_id": str(item.id),
                "provider_id": str(item.provider_id),
                "item_type": item.item_type.value if isinstance(item.item_type, ItemType) else item.item_type,
                "name": item.name,
                "version": item.version,
                "description": item.description,
                "status": item.status.value if isinstance(item.status, CatalogItemStatus) else item.status,
                "trust_score": item.trust_score,
                "agentcard": item.agentcard,
            }
            await self._es.index(
                index="aimart-catalog",
                id=str(item.id),
                document=doc,
            )
            logger.debug("es_index_success", item_id=str(item.id))
        except Exception as exc:
            logger.error(
                "es_index_failed",
                item_id=str(item.id),
                error=str(exc),
            )

    async def _remove_from_es(self, item_id: UUID) -> None:
        """Remove a catalog item from the Elasticsearch index."""
        if self._es is None:
            logger.debug("es_remove_skipped", reason="no_es_client")
            return

        try:
            await self._es.delete(
                index="aimart-catalog",
                id=str(item_id),
                ignore=[404],
            )
            logger.debug("es_remove_success", item_id=str(item_id))
        except Exception as exc:
            logger.error(
                "es_remove_failed",
                item_id=str(item_id),
                error=str(exc),
            )

    def _audit_log(self, action: str, **kwargs: Any) -> None:
        """Emit a structured audit log entry."""
        if self._audit is not None:
            self._audit.info(action, **kwargs)
        else:
            logger.info(action, **kwargs)
