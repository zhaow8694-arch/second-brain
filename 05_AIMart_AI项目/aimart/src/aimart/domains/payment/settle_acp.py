from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ACPPaymentIntent:
    """An ACP (Agent Commerce Protocol) payment intent."""

    intent_id: UUID
    agent_id: UUID
    owner_id: UUID
    amount_cny: float
    provider_id: UUID
    spt: str | None = None  # Secure Payment Token
    spt_expires_at: datetime | None = None
    stripe_payment_intent_id: str | None = None
    stripe_client_secret: str | None = None


@dataclass
class ACPSettlementResult:
    """Result of an ACP settlement attempt."""

    success: bool
    payment_intent_id: str | None = None
    charge_id: str | None = None
    error: str | None = None


class ACPSettler:
    """Settles payments via the ACP (Agent Commerce Protocol) using Stripe.

    The ACP flow:
    1. Create a Stripe PaymentIntent with the owner's payment method
    2. Return a client_secret for the frontend to confirm
    3. Agent confirms with a Secure Payment Token (SPT)
    4. Stripe processes the charge
    5. Webhook confirms completion

    Actual Stripe API calls are marked with TODO.
    """

    def __init__(self, stripe_api_key: str, webhook_secret: str):
        self.stripe_api_key = stripe_api_key
        self.webhook_secret = webhook_secret
        # TODO: initialize Stripe client
        # import stripe
        # stripe.api_key = stripe_api_key
        # self.stripe = stripe

    def create_payment_intent(
        self,
        agent_id: UUID,
        owner_id: UUID,
        amount_cny: float,
        provider_id: UUID,
        order_id: UUID,
    ) -> ACPPaymentIntent:
        """Create an ACP payment intent via Stripe.

        Args:
            agent_id: The agent initiating the payment.
            owner_id: The owner whose payment method will be charged.
            amount_cny: Amount in CNY.
            provider_id: The provider who will receive the payout.
            order_id: The associated order ID.

        Returns:
            An ACPPaymentIntent with Stripe details.
        """
        intent = ACPPaymentIntent(
            intent_id=uuid4(),
            agent_id=agent_id,
            owner_id=owner_id,
            amount_cny=amount_cny,
            provider_id=provider_id,
        )

        # TODO: create Stripe PaymentIntent
        # stripe_intent = self.stripe.PaymentIntent.create(
        #     amount=int(amount_cny * 100),  # Stripe uses cents
        #     currency="cny",
        #     metadata={
        #         "agent_id": str(agent_id),
        #         "owner_id": str(owner_id),
        #         "provider_id": str(provider_id),
        #         "order_id": str(order_id),
        #         "intent_id": str(intent.intent_id),
        #     },
        #     capture_method="manual",  # authorize first, capture after effect
        # )
        # intent.stripe_payment_intent_id = stripe_intent.id
        # intent.stripe_client_secret = stripe_intent.client_secret

        # Placeholder values
        intent.stripe_payment_intent_id = f"pi_placeholder_{intent.intent_id.hex[:8]}"
        intent.stripe_client_secret = f"cs_placeholder_{intent.intent_id.hex[:8]}"

        logger.info(
            "acp_payment_intent_created",
            intent_id=str(intent.intent_id),
            agent_id=str(agent_id),
            owner_id=str(owner_id),
            amount_cny=amount_cny,
            provider_id=str(provider_id),
            order_id=str(order_id),
        )
        return intent

    def confirm_with_spt(
        self,
        intent_id: UUID,
        spt: str,
    ) -> ACPSettlementResult:
        """Confirm a payment intent with a Secure Payment Token.

        The SPT is a short-lived token that authorizes the agent to
        confirm the payment on behalf of the owner.

        Args:
            intent_id: The ACP payment intent ID.
            spt: The Secure Payment Token.

        Returns:
            ACPSettlementResult with success status.
        """
        # TODO: validate SPT and confirm with Stripe
        # 1. Look up the intent by intent_id
        # 2. Validate the SPT (check signature, expiry, etc.)
        # 3. Confirm the Stripe PaymentIntent
        # stripe_intent = self.stripe.PaymentIntent.confirm(
        #     intent.stripe_payment_intent_id,
        #     payment_method="pm_xxx",
        # )

        logger.info(
            "acp_payment_confirmed",
            intent_id=str(intent_id),
            spt=spt[:8] + "...",  # don't log full token
        )

        return ACPSettlementResult(
            success=True,
            payment_intent_id=f"pi_placeholder_{intent_id.hex[:8]}",
            charge_id=f"ch_placeholder_{intent_id.hex[:8]}",
        )

    def handle_webhook(
        self,
        event_type: str,
        event_data: dict,
    ) -> ACPSettlementResult:
        """Handle a Stripe webhook event.

        Supported event types:
        - payment_intent.succeeded: mark as completed
        - payment_intent.payment_failed: mark as failed
        - charge.refunded: handle refund

        Args:
            event_type: The Stripe event type.
            event_data: The event payload.

        Returns:
            ACPSettlementResult reflecting the outcome.
        """
        logger.info(
            "acp_webhook_received",
            event_type=event_type,
        )

        if event_type == "payment_intent.succeeded":
            # TODO: update transaction status
            # payment_intent_id = event_data["id"]
            # charge_id = event_data["latest_charge"]
            return ACPSettlementResult(
                success=True,
                payment_intent_id=event_data.get("id"),
                charge_id=event_data.get("latest_charge"),
            )

        elif event_type == "payment_intent.payment_failed":
            return ACPSettlementResult(
                success=False,
                payment_intent_id=event_data.get("id"),
                error=event_data.get("last_payment_error", {}).get(
                    "message", "Payment failed"
                ),
            )

        elif event_type == "charge.refunded":
            return ACPSettlementResult(
                success=True,
                charge_id=event_data.get("id"),
            )

        else:
            logger.warning(
                "acp_unhandled_webhook_event",
                event_type=event_type,
            )
            return ACPSettlementResult(
                success=False,
                error=f"Unhandled event type: {event_type}",
            )
