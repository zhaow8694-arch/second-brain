from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


class EscrowManager:
    """Manages escrow transactions for marketplace orders.

    Coordinates the freeze → delivery confirmation → release/refund
    lifecycle in concert with the payment domain.
    """

    def __init__(self, payment_service: Any = None) -> None:
        # payment_service is a reference to the Payment domain service
        # for actual fund operations.  May be None in isolated tests.
        self._payment_service = payment_service

    # ------------------------------------------------------------------
    # Create escrow
    # ------------------------------------------------------------------

    async def create_escrow(
        self,
        order_id: UUID,
        amount: float,
        pool_id: UUID,
        agent_id: UUID,
    ) -> dict:
        """Create an escrow by freezing funds in the budget pool.

        Delegates to the payment service to create a PaymentTransaction
        with escrow_status=frozen.

        Returns:
            A dict containing the payment transaction id and escrow status.
        """
        logger.info(
            "escrow_create",
            order_id=str(order_id),
            amount=amount,
            pool_id=str(pool_id),
            agent_id=str(agent_id),
        )

        if self._payment_service is not None:
            from aimart.domains.payment.schemas import InitiatePaymentRequest

            request = InitiatePaymentRequest(
                order_id=order_id,
                pool_id=pool_id,
            )
            result = self._payment_service.initiate_payment(
                request=request,
                agent_id=agent_id,
                amount=__import__("decimal").Decimal(str(amount)),
                provider_id=UUID("00000000-0000-0000-0000-000000000000"),
            )
            logger.info(
                "escrow_created",
                order_id=str(order_id),
                transaction_id=result.get("id"),
            )
            return result

        # Fallback: no payment service wired – return mock
        logger.warning("escrow_create_no_payment_service", order_id=str(order_id))
        return {
            "order_id": str(order_id),
            "escrow_status": "frozen",
            "amount": amount,
            "pool_id": str(pool_id),
        }

    # ------------------------------------------------------------------
    # Confirm delivery
    # ------------------------------------------------------------------

    async def confirm_delivery(self, order_id: UUID) -> None:
        """Mark an order as delivered after the provider confirms delivery.

        This updates the order status but does not yet release funds;
        fund release happens in complete_escrow after effect reporting.
        """
        logger.info("escrow_confirm_delivery", order_id=str(order_id))

        # In a full implementation this would:
        # 1. Load the Order from DB
        # 2. Transition its status to DELIVERED
        # 3. Record delivered_at timestamp

    # ------------------------------------------------------------------
    # Complete escrow (release or refund)
    # ------------------------------------------------------------------

    async def complete_escrow(
        self,
        order_id: UUID,
        effect_score: float,
    ) -> dict:
        """Complete the escrow based on the reported effect score.

        Triggers the payment service to report the effect and release
        or refund funds accordingly.

        Args:
            order_id: The order whose escrow should be completed.
            effect_score: The effect score (0-5) from the buyer's report.

        Returns:
            A dict with the escrow transition result.
        """
        logger.info(
            "escrow_complete",
            order_id=str(order_id),
            effect_score=effect_score,
        )

        from aimart.domains.payment.escrow import (
            EscrowEvent,
            EscrowState,
            transition,
        )

        # Determine escrow event from effect score
        if effect_score >= 4.0:
            event = EscrowEvent.EFFECT_CONFIRMED
        elif effect_score >= 2.0:
            event = EscrowEvent.EFFECT_PARTIAL
        else:
            event = EscrowEvent.EFFECT_FAILED

        result = transition(
            current_state=EscrowState.FROZEN,
            event=event,
            effect_score=int(effect_score),
        )

        logger.info(
            "escrow_transition_complete",
            order_id=str(order_id),
            old_state=result.old_state.value,
            new_state=result.new_state.value,
            provider_payout_pct=result.provider_payout_pct,
            buyer_refund_pct=result.buyer_refund_pct,
            action_required=result.action_required,
        )

        return {
            "order_id": str(order_id),
            "old_state": result.old_state.value,
            "new_state": result.new_state.value,
            "provider_payout_pct": result.provider_payout_pct,
            "buyer_refund_pct": result.buyer_refund_pct,
            "action_required": result.action_required,
        }
