from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Certification,
    CertificationStatusEnum,
    TargetType,
    TrustEvent,
    TrustEventType,
)
from .schemas import (
    CertificationRequest,
    CertificationResponse,
    EffectReport,
    ScoreDelta,
    TrustScoreResponse,
)
from .scorer import TrustScorer

logger = structlog.get_logger(__name__)


def _certification_to_response(cert: Certification) -> CertificationResponse:
    """Convert a Certification ORM object to a response schema."""
    return CertificationResponse(
        id=cert.id,
        item_id=cert.item_id,
        certifier_id=cert.certifier_id,
        status=cert.status.value if isinstance(cert.status, CertificationStatusEnum) else cert.status,
        benchmark_results=cert.benchmark_results,
        verified_at=cert.verified_at,
        expires_at=cert.expires_at,
        created_at=cert.created_at,
    )


class TrustService:
    """High-level orchestration for the trust domain.

    Coordinates effect report processing, trust score queries,
    certification management, and audit logging.
    """

    def __init__(
        self,
        scorer: TrustScorer | None = None,
        catalog_service: Any = None,
        audit_logger: Any = None,
    ) -> None:
        self._scorer = scorer or TrustScorer()
        self._catalog_service = catalog_service
        self._audit = audit_logger

    # ------------------------------------------------------------------
    # Effect report
    # ------------------------------------------------------------------

    async def submit_effect_report(
        self,
        report: EffectReport,
        db: AsyncSession,
    ) -> dict:
        """Process an effect report through the trust scorer.

        Steps:
          1. Process the report through TrustScorer.
          2. Update the catalog item's trust score.
          3. Emit an audit event.

        Returns:
            A dict with the score delta and new trust score.
        """
        # Create a lightweight repo adapter for the scorer
        repo = _DBRepoAdapter(db)

        # Process through scorer
        delta = await self._scorer.process_effect_report(report, repo)

        # Update catalog item trust score
        if self._catalog_service is not None:
            try:
                new_score = await self._scorer.calculate_item_score(
                    report.item_id, repo
                )
                # Update the item's trust_score in DB
                if hasattr(self._catalog_service, '_update_trust_score'):
                    await self._catalog_service._update_trust_score(
                        report.item_id, new_score, db
                    )
            except Exception as exc:
                logger.error(
                    "effect_report_score_update_failed",
                    item_id=str(report.item_id),
                    error=str(exc),
                )

        # Audit
        self._audit_log(
            "trust.effect_report_submitted",
            item_id=str(report.item_id),
            agent_id=str(report.agent_id),
            effect_score=report.effect_score,
            success=report.success,
            score_delta=delta,
        )

        logger.info(
            "effect_report_submitted",
            item_id=str(report.item_id),
            effect_score=report.effect_score,
            score_delta=delta,
        )

        return {
            "item_id": str(report.item_id),
            "score_delta": delta,
            "effect_score": report.effect_score,
        }

    # ------------------------------------------------------------------
    # Get trust score
    # ------------------------------------------------------------------

    async def get_trust_score(
        self,
        target_type: str,
        target_id: UUID,
        db: AsyncSession,
    ) -> TrustScoreResponse:
        """Retrieve the trust score for a target entity.

        Args:
            target_type: One of 'item', 'provider', 'agent'.
            target_id: The UUID of the target entity.

        Returns:
            A TrustScoreResponse with the current score and recent history.
        """
        repo = _DBRepoAdapter(db)

        if target_type == "item":
            score = await self._scorer.calculate_item_score(target_id, repo)
        elif target_type == "provider":
            score = await self._scorer.calculate_provider_score(target_id, repo)
        else:
            # Default base score for agents
            score = 50.0

        # Fetch recent score history (last 10 deltas)
        stmt = (
            select(TrustEvent)
            .where(
                TrustEvent.target_type == TargetType(target_type),
                TrustEvent.target_id == target_id,
            )
            .order_by(TrustEvent.created_at.desc())
            .limit(10)
        )
        result = await db.execute(stmt)
        events = result.scalars().all()

        history = [
            ScoreDelta(
                event_type=e.event_type.value if isinstance(e.event_type, TrustEventType) else e.event_type,
                score_delta=e.score_delta,
                created_at=e.created_at,
            )
            for e in events
        ]

        # Determine updated_at from the latest event or now
        updated_at = events[0].created_at if events else datetime.now(UTC)

        return TrustScoreResponse(
            target_type=target_type,
            target_id=target_id,
            trust_score=score,
            score_history=list(reversed(history)),
            updated_at=updated_at,
        )

    # ------------------------------------------------------------------
    # Certification
    # ------------------------------------------------------------------

    async def request_certification(
        self,
        request: CertificationRequest,
        certifier_id: UUID,
        db: AsyncSession,
    ) -> CertificationResponse:
        """Submit a certification request for a catalog item.

        Creates a Certification record with pending status and emits
        an audit event.

        Args:
            request: The certification request containing item_id and
                     benchmark_results.
            certifier_id: The UUID of the certifier submitting the request.

        Returns:
            A CertificationResponse for the newly created certification.
        """
        cert = Certification(
            item_id=request.item_id,
            certifier_id=certifier_id,
            status=CertificationStatusEnum.PENDING,
            benchmark_results=request.benchmark_results,
        )
        db.add(cert)
        await db.flush()

        # Create trust event
        event = TrustEvent(
            target_type=TargetType.ITEM,
            target_id=request.item_id,
            event_type=TrustEventType.CERTIFICATION,
            event_data={
                "certification_id": str(cert.id),
                "certifier_id": str(certifier_id),
                "status": "pending",
            },
            score_delta=0.0,
        )
        db.add(event)
        await db.flush()

        # Audit
        self._audit_log(
            "trust.certification_requested",
            certification_id=str(cert.id),
            item_id=str(request.item_id),
            certifier_id=str(certifier_id),
        )

        logger.info(
            "certification_requested",
            certification_id=str(cert.id),
            item_id=str(request.item_id),
            certifier_id=str(certifier_id),
        )

        return _certification_to_response(cert)

    async def process_certification(
        self,
        certification_id: UUID,
        approved: bool,
        db: AsyncSession,
        notes: str | None = None,
    ) -> CertificationResponse:
        """Process a certification decision.

        If approved, updates the item's certification_status to 'certified'
        and recalculates the trust score. If rejected, sets the status to
        'rejected'.

        Args:
            certification_id: The certification to process.
            approved: Whether the certification is approved.
            db: The database session.
            notes: Optional notes from the certifier.

        Returns:
            The updated CertificationResponse.
        """
        stmt = select(Certification).where(Certification.id == certification_id)
        result = await db.execute(stmt)
        cert = result.scalar_one_or_none()

        if cert is None:
            raise ValueError(f"Certification not found: {certification_id}")

        now = datetime.now(UTC)

        if approved:
            cert.status = CertificationStatusEnum.APPROVED
            cert.verified_at = now
            cert.expires_at = now.replace(year=now.year + 1)  # 1-year expiry
        else:
            cert.status = CertificationStatusEnum.REJECTED

        await db.flush()

        # Update the catalog item's certification_status
        from aimart.domains.catalog.models import CatalogItem
        from aimart.domains.catalog.models import CertificationStatus as ItemCertStatus

        item_stmt = select(CatalogItem).where(CatalogItem.id == cert.item_id)
        item_result = await db.execute(item_stmt)
        item = item_result.scalar_one_or_none()

        if item is not None:
            if approved:
                item.certification_status = ItemCertStatus.CERTIFIED
            else:
                item.certification_status = ItemCertStatus.REJECTED
            await db.flush()

            # Recalculate trust score
            repo = _DBRepoAdapter(db)
            new_score = await self._scorer.calculate_item_score(
                cert.item_id, repo
            )
            item.trust_score = new_score
            await db.flush()

        # Create trust event
        event = TrustEvent(
            target_type=TargetType.ITEM,
            target_id=cert.item_id,
            event_type=TrustEventType.CERTIFICATION,
            event_data={
                "certification_id": str(cert.id),
                "approved": approved,
                "notes": notes,
            },
            score_delta=10.0 if approved else 0.0,
        )
        db.add(event)
        await db.flush()

        # Audit
        self._audit_log(
            "trust.certification_processed",
            certification_id=str(cert.id),
            item_id=str(cert.item_id),
            approved=approved,
        )

        logger.info(
            "certification_processed",
            certification_id=str(cert.id),
            approved=approved,
        )

        return _certification_to_response(cert)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _audit_log(self, action: str, **kwargs: Any) -> None:
        """Emit a structured audit log entry."""
        if self._audit is not None:
            self._audit.info(action, **kwargs)
        else:
            logger.info(action, **kwargs)


# ---------------------------------------------------------------------------
# DB Repo Adapter – provides the interface expected by TrustScorer
# ---------------------------------------------------------------------------

class _DBRepoAdapter:
    """Thin adapter that provides the repository interface expected
    by TrustScorer using an AsyncSession."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_trust_events(
        self, target_type: str, target_id: UUID
    ) -> list[TrustEvent]:
        stmt = (
            select(TrustEvent)
            .where(
                TrustEvent.target_type == TargetType(target_type),
                TrustEvent.target_id == target_id,
            )
            .order_by(TrustEvent.created_at.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def create_trust_event(
        self,
        target_type: str,
        target_id: UUID,
        event_type: str,
        event_data: dict,
        score_delta: float,
    ) -> TrustEvent:
        event = TrustEvent(
            target_type=TargetType(target_type),
            target_id=target_id,
            event_type=TrustEventType(event_type),
            event_data=event_data,
            score_delta=score_delta,
        )
        self._db.add(event)
        await self._db.flush()
        return event

    async def get_provider_item_ids(self, provider_id: UUID) -> list[UUID]:
        from aimart.domains.catalog.models import CatalogItem
        stmt = select(CatalogItem.id).where(
            CatalogItem.provider_id == provider_id,
            CatalogItem.status != "delisted",
        )
        result = await self._db.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_catalog_item(self, item_id: UUID):
        from aimart.domains.catalog.models import CatalogItem
        stmt = select(CatalogItem).where(CatalogItem.id == item_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_trust_events(self) -> list[TrustEvent]:
        stmt = select(TrustEvent)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def update_trust_event_delta(
        self, event_id: UUID, new_delta: float
    ) -> None:
        stmt = select(TrustEvent).where(TrustEvent.id == event_id)
        result = await self._db.execute(stmt)
        event = result.scalar_one_or_none()
        if event is not None:
            event.score_delta = new_delta
            await self._db.flush()
