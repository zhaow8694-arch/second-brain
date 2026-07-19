from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .escrow import EscrowManager
from .models import Delivery, DeliveryMethod, Order, OrderStatus, Trial, TrialStatus
from .sandbox import SandboxManager
from .schemas import (
    DeliveryConfirmResponse,
    EffectReportResponse,
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
    TrialCreateRequest,
    TrialResponse,
)

logger = structlog.get_logger(__name__)


def _order_to_response(order: Order) -> OrderResponse:
    """Convert an Order ORM object to a response schema."""
    return OrderResponse(
        id=order.id,
        agent_id=order.agent_id,
        item_id=order.item_id,
        provider_id=order.provider_id,
        item_type=order.item_type,
        item_name=order.item_name,
        pricing_model=order.pricing_model,
        amount=Decimal(str(order.amount)) if order.amount is not None else Decimal("0"),
        currency=order.currency,
        quantity=order.quantity,
        status=order.status.value if isinstance(order.status, OrderStatus) else order.status,
        payment_transaction_id=order.payment_transaction_id,
        trial_id=order.trial_id,
        delivered_at=order.delivered_at,
        completed_at=order.completed_at,
        cancelled_at=order.cancelled_at,
        cancel_reason=order.cancel_reason,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _trial_to_response(trial: Trial) -> TrialResponse:
    """Convert a Trial ORM object to a response schema."""
    return TrialResponse(
        id=trial.id,
        agent_id=trial.agent_id,
        item_id=trial.item_id,
        status=trial.status.value if isinstance(trial.status, TrialStatus) else trial.status,
        input_data=trial.input_data,
        output_data=trial.output_data,
        performance_data=trial.performance_data,
        sandbox_config=trial.sandbox_config,
        started_at=trial.started_at,
        completed_at=trial.completed_at,
        created_at=trial.created_at,
    )


class ExchangeService:
    """High-level orchestration for the exchange domain.

    Coordinates order lifecycle, escrow management, sandbox trials,
    budget checks, and audit logging.
    """

    def __init__(
        self,
        catalog_service: Any = None,
        escrow_manager: EscrowManager | None = None,
        sandbox_manager: SandboxManager | None = None,
        audit_logger: Any = None,
    ) -> None:
        self._catalog_service = catalog_service
        self._escrow = escrow_manager or EscrowManager()
        self._sandbox = sandbox_manager or SandboxManager()
        self._audit = audit_logger

    # ------------------------------------------------------------------
    # Create order
    # ------------------------------------------------------------------

    async def create_order(
        self,
        request: OrderCreateRequest,
        agent_id: UUID,
        db: AsyncSession,
    ) -> OrderResponse:
        """Create a new marketplace order.

        Steps:
          1. Validate that the catalog item exists and is active.
          2. Check the agent's budget.
          3. Create an Order record.
          4. Create escrow (freeze funds).
          5. Emit an audit event.

        Raises:
            ValueError: If the item is not found, not active, or budget
                        is insufficient.
        """
        # Validate item
        item = None
        if self._catalog_service is not None:
            try:
                item = await self._catalog_service.get_item(request.item_id, db)
            except ValueError:
                raise ValueError(f"Catalog item not found: {request.item_id}")

            if item.status != "active":
                raise ValueError(
                    f"Catalog item {request.item_id} is not active (status={item.status})"
                )
        else:
            logger.warning(
                "create_order_no_catalog_service",
                item_id=str(request.item_id),
            )

        # Derive order fields from catalog item
        if item is not None:
            provider_id = item.provider_id
            item_type = item.item_type
            item_name = item.name
            pricing_model = item.agentcard.get("pricing", {}).get("model", "per_call")
            amount = self._calculate_amount(item, request.quantity)
            currency = item.agentcard.get("pricing", {}).get("currency", "CNY")
        else:
            provider_id = UUID("00000000-0000-0000-0000-000000000000")
            item_type = "unknown"
            item_name = "unknown"
            pricing_model = "per_call"
            amount = 0.0
            currency = "CNY"

        # Create order
        order = Order(
            agent_id=agent_id,
            item_id=request.item_id,
            provider_id=provider_id,
            item_type=item_type,
            item_name=item_name,
            pricing_model=pricing_model,
            amount=amount,
            currency=currency,
            quantity=request.quantity,
            status=OrderStatus.CREATED,
        )
        db.add(order)
        await db.flush()

        # Create escrow
        try:
            escrow_result = await self._escrow.create_escrow(
                order_id=order.id,
                amount=float(amount),
                pool_id=request.budget_pool_id,
                agent_id=agent_id,
            )
            if escrow_result.get("id"):
                order.payment_transaction_id = escrow_result["id"]
            order.status = OrderStatus.PENDING_PAYMENT
            await db.flush()
        except Exception as exc:
            logger.error(
                "order_escrow_failed",
                order_id=str(order.id),
                error=str(exc),
            )
            # Order stays in CREATED status

        # Audit
        self._audit_log(
            "exchange.order_created",
            order_id=str(order.id),
            agent_id=str(agent_id),
            item_id=str(request.item_id),
            amount=str(amount),
        )

        logger.info(
            "order_created",
            order_id=str(order.id),
            agent_id=str(agent_id),
            item_id=str(request.item_id),
        )

        return _order_to_response(order)

    # ------------------------------------------------------------------
    # Get order
    # ------------------------------------------------------------------

    async def get_order(
        self,
        order_id: UUID,
        db: AsyncSession,
    ) -> OrderResponse:
        """Retrieve a single order by ID.

        Raises:
            ValueError: If the order is not found.
        """
        stmt = select(Order).where(Order.id == order_id)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if order is None:
            raise ValueError(f"Order not found: {order_id}")

        return _order_to_response(order)

    # ------------------------------------------------------------------
    # Cancel order
    # ------------------------------------------------------------------

    async def cancel_order(
        self,
        order_id: UUID,
        agent_id: UUID,
        db: AsyncSession,
        cancel_reason: str | None = None,
    ) -> OrderResponse:
        """Cancel an order and unfreeze escrowed funds.

        Only the owning agent can cancel, and only if the order is in
        a cancellable state (created, pending_payment, paid).

        Raises:
            ValueError: If the order is not found, not owned by the agent,
                        or not in a cancellable state.
        """
        stmt = select(Order).where(Order.id == order_id)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if order is None:
            raise ValueError(f"Order not found: {order_id}")
        if order.agent_id != agent_id:
            raise ValueError("Not authorized to cancel this order")

        cancellable_states = {
            OrderStatus.CREATED,
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.PAID,
        }
        current_status = order.status if isinstance(order.status, OrderStatus) else OrderStatus(order.status)
        if current_status not in cancellable_states:
            raise ValueError(
                f"Order cannot be cancelled in state '{current_status.value}'"
            )

        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now(UTC)
        order.cancel_reason = cancel_reason or "Cancelled by agent"
        order.updated_at = datetime.now(UTC)
        await db.flush()

        # Unfreeze escrow (refund)
        if order.payment_transaction_id is not None:
            try:
                await self._escrow.complete_escrow(
                    order_id=order.id,
                    effect_score=0.0,
                )
            except Exception as exc:
                logger.error(
                    "order_cancel_escrow_refund_failed",
                    order_id=str(order.id),
                    error=str(exc),
                )

        # Audit
        self._audit_log(
            "exchange.order_cancelled",
            order_id=str(order.id),
            agent_id=str(agent_id),
            cancel_reason=cancel_reason,
        )

        logger.info(
            "order_cancelled",
            order_id=str(order.id),
            agent_id=str(agent_id),
        )

        return _order_to_response(order)

    # ------------------------------------------------------------------
    # Create trial
    # ------------------------------------------------------------------

    async def create_trial(
        self,
        request: TrialCreateRequest,
        agent_id: UUID,
        db: AsyncSession,
    ) -> TrialResponse:
        """Create and execute a sandbox trial for a catalog item.

        Steps:
          1. Check trial limits (max 3 per agent per item per day).
          2. Create a Trial record.
          3. Execute the sandbox with constraints.
          4. Update the trial record with results.
          5. Emit an audit event.

        Raises:
            PermissionError: If the daily trial limit has been reached.
        """
        # Check daily trial limit
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        count_stmt = (
            select(func.count())
            .select_from(Trial)
            .where(
                Trial.agent_id == agent_id,
                Trial.item_id == request.item_id,
                Trial.created_at >= today_start,
            )
        )
        count_result = await db.execute(count_stmt)
        today_count = count_result.scalar() or 0

        if today_count >= 3:
            raise PermissionError(
                f"Daily trial limit (3) reached for item {request.item_id}"
            )

        # Create trial
        trial = Trial(
            agent_id=agent_id,
            item_id=request.item_id,
            input_data=request.input_data,
            status=TrialStatus.REQUESTED,
        )
        db.add(trial)
        await db.flush()

        # Execute sandbox
        trial.status = TrialStatus.ACTIVE
        trial.started_at = datetime.now(UTC)
        await db.flush()

        trial_result = await self._sandbox.execute_trial(
            trial_id=trial.id,
            item_id=request.item_id,
            input_data=request.input_data,
            config=trial.sandbox_config,
        )

        # Update trial record
        if trial_result.success:
            trial.status = TrialStatus.COMPLETED
            trial.output_data = trial_result.output_data
            trial.performance_data = trial_result.performance_data
        else:
            trial.status = TrialStatus.FAILED
            trial.output_data = {"errors": trial_result.errors}

        trial.completed_at = datetime.now(UTC)
        await db.flush()

        # Audit
        self._audit_log(
            "exchange.trial_created",
            trial_id=str(trial.id),
            agent_id=str(agent_id),
            item_id=str(request.item_id),
            success=trial_result.success,
        )

        logger.info(
            "trial_created",
            trial_id=str(trial.id),
            agent_id=str(agent_id),
            item_id=str(request.item_id),
            success=trial_result.success,
        )

        return _trial_to_response(trial)

    # ------------------------------------------------------------------
    # List orders
    # ------------------------------------------------------------------

    async def list_orders(
        self,
        agent_id: UUID,
        db: AsyncSession,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> OrderListResponse:
        """List orders for an agent with optional status filter and pagination."""
        stmt = select(Order).where(Order.agent_id == agent_id)
        count_stmt = select(func.count()).select_from(Order).where(
            Order.agent_id == agent_id
        )

        if status is not None:
            stmt = stmt.where(Order.status == OrderStatus(status))
            count_stmt = count_stmt.where(Order.status == OrderStatus(status))

        # Count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(Order.created_at.desc())
        result = await db.execute(stmt)
        orders = result.scalars().all()

        return OrderListResponse(
            items=[_order_to_response(o) for o in orders],
            total=total,
            page=page,
            size=size,
        )

    # ------------------------------------------------------------------
    # Confirm delivery
    # ------------------------------------------------------------------

    async def confirm_delivery(
        self,
        order_id: UUID,
        delivery_method: str,
        delivery_endpoint: str | None,
        db: AsyncSession,
    ) -> DeliveryConfirmResponse:
        """Confirm delivery of an order.

        Marks the order as delivered. Does NOT release funds — that
        happens after the agent reports an effect.

        Raises:
            ValueError: If the order is not found or not in a deliverable state.
        """
        stmt = select(Order).where(Order.id == order_id)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if order is None:
            raise ValueError(f"Order not found: {order_id}")

        if order.status != OrderStatus.PAID:
            raise ValueError(
                f"Order cannot be delivered in state '{order.status.value}'"
            )

        # Mark order as delivered
        from datetime import datetime
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.now(UTC)
        order.updated_at = datetime.now(UTC)

        # Create delivery record
        delivery = Delivery(
            order_id=order.id,
            delivery_method=DeliveryMethod(delivery_method),
            delivery_endpoint=delivery_endpoint,
            status="success",
        )
        db.add(delivery)
        await db.flush()

        # Notify escrow
        await self._escrow.confirm_delivery(order_id=order.id)

        self._audit_log(
            "exchange.delivery_confirmed",
            order_id=str(order.id),
            delivery_method=delivery_method,
        )

        logger.info(
            "delivery_confirmed",
            order_id=str(order.id),
            delivery_method=delivery_method,
        )

        return DeliveryConfirmResponse(
            order_id=order.id,
            status=OrderStatus.DELIVERED.value,
            delivered_at=order.delivered_at,
        )

    # ------------------------------------------------------------------
    # Report effect
    # ------------------------------------------------------------------

    async def report_effect(
        self,
        order_id: UUID,
        agent_id: UUID,
        effect_score: int,
        success: bool,
        actual_latency_ms: int | None,
        db: AsyncSession,
    ) -> EffectReportResponse:
        """Report the effect of a consumed capability.

        Triggers escrow completion and trust score update.

        Raises:
            ValueError: If the order is not found or effect already reported.
        """
        stmt = select(Order).where(Order.id == order_id)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if order is None:
            raise ValueError(f"Order not found: {order_id}")

        if order.agent_id != agent_id:
            raise ValueError("Not authorized to report effect for this order")

        if order.status not in (OrderStatus.DELIVERED, OrderStatus.PAID):
            raise ValueError(
                f"Cannot report effect in state '{order.status.value}'"
            )

        # Validate effect score
        if effect_score < 0 or effect_score > 5:
            raise ValueError("Effect score must be between 0 and 5")

        # Update order
        order.effect_score = effect_score
        order.effect_reported_at = datetime.now(UTC)

        # Complete escrow based on effect score
        escrow_result = await self._escrow.complete_escrow(
            order_id=order.id,
            effect_score=float(effect_score),
        )

        # Determine new status
        if escrow_result.get("new_state") in ("released", "partial_release"):
            order.status = OrderStatus.COMPLETED
            order.completed_at = datetime.now(UTC)
        elif escrow_result.get("new_state") == "refunded":
            order.status = OrderStatus.REFUNDED
        elif escrow_result.get("new_state") == "disputed":
            order.status = OrderStatus.DISPUTED

        order.updated_at = datetime.now(UTC)
        await db.flush()

        # Create effect report in trust domain
        try:
            from aimart.domains.trust.models import EffectReport as TrustEffectReport
            trust_report = TrustEffectReport(
                order_id=order.id,
                agent_id=agent_id,
                item_id=order.item_id,
                provider_id=order.provider_id,
                success=success,
                effect_score=effect_score,
                actual_latency_ms=actual_latency_ms,
                detail={"delivery_method": order.pricing_model},
            )
            db.add(trust_report)
            await db.flush()
        except Exception as exc:
            logger.warning(
                "effect_report_trust_record_failed",
                order_id=str(order.id),
                error=str(exc),
            )

        self._audit_log(
            "exchange.effect_reported",
            order_id=str(order.id),
            agent_id=str(agent_id),
            effect_score=effect_score,
            success=success,
            escrow_state=escrow_result.get("new_state"),
        )

        logger.info(
            "effect_reported",
            order_id=str(order.id),
            effect_score=effect_score,
            escrow_state=escrow_result.get("new_state"),
        )

        return EffectReportResponse(
            order_id=order.id,
            new_status=order.status.value,
            escrow_result=escrow_result,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calculate_amount(self, item: Any, quantity: int) -> float:
        """Calculate the order amount based on the item's pricing model."""
        if not hasattr(item, "agentcard"):
            return 0.0

        pricing = item.agentcard.get("pricing", {})
        details = pricing.get("details", [])

        if details and isinstance(details, list) and len(details) > 0:
            # Use the first price detail's amount
            first = details[0]
            if isinstance(first, dict):
                price = first.get("amount", 0)
                return float(price) * quantity

        return 0.0

    def _audit_log(self, action: str, **kwargs: Any) -> None:
        """Emit a structured audit log entry."""
        if self._audit is not None:
            self._audit.info(action, **kwargs)
        else:
            logger.info(action, **kwargs)
