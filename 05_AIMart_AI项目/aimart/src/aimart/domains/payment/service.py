from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import structlog

from .anomaly import AnomalyDetector
from .authorization import calculate_auth_expiry, determine_auth_level
from .budget import BudgetManager
from .escrow import EscrowEvent, EscrowState, transition
from .schemas import (
    AuthorizationDecisionRequest,
    EffectReportRequest,
    InitiatePaymentRequest,
)
from .settle_acp import ACPSettler
from .settle_x402 import X402Settler

logger = structlog.get_logger(__name__)


class PaymentService:
    """High-level payment orchestration service.

    Coordinates budget checks, authorization, escrow, settlement,
    anomaly detection, and audit logging.
    """

    def __init__(
        self,
        repo: Any,
        budget_manager: BudgetManager | None = None,
        anomaly_detector: AnomalyDetector | None = None,
        x402_settler: X402Settler | None = None,
        acp_settler: ACPSettler | None = None,
    ):
        self.repo = repo
        self.budget_manager = budget_manager or BudgetManager()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.x402_settler = x402_settler
        self.acp_settler = acp_settler

    # ------------------------------------------------------------------
    # Initiate Payment
    # ------------------------------------------------------------------

    def initiate_payment(
        self,
        request: InitiatePaymentRequest,
        agent_id: UUID,
        amount: Decimal,
        provider_id: UUID,
        currency: str = "CNY",
        item_name: str | None = None,
        item_type: str | None = None,
    ) -> dict:
        """Execute the full payment initiation flow.

        Steps:
        1. Rules engine check (basic validation)
        2. Budget check
        3. Auth level check
        4. Freeze funds
        5. Create transaction record
        6. Anomaly check
        7. Execute settlement if no approval needed
        8. Audit log

        Returns:
            A dict with transaction details and any alerts.
        """
        correlation_id = uuid4()
        log = logger.bind(
            correlation_id=str(correlation_id),
            order_id=str(request.order_id),
            agent_id=str(agent_id),
        )

        # Step 1: Rules engine check
        if amount <= 0:
            log.warning("payment_rejected_zero_amount")
            return {"success": False, "error": "Amount must be positive"}

        # Step 2: Budget check
        sufficient, reason = self.budget_manager.check_sufficient(
            pool_id=request.pool_id,
            agent_id=agent_id,
            amount=amount,
            repo=self.repo,
        )
        if not sufficient:
            log.warning("payment_rejected_budget", reason=reason)
            return {"success": False, "error": reason}

        # Step 3: Auth level check
        allocation = self.repo.get_allocation(request.pool_id, agent_id)
        agent_level = allocation.spending_authority_level if allocation else "L0"
        required_level, needs_approval = determine_auth_level(
            float(amount), agent_level
        )

        # Step 4: Freeze funds
        freeze_ok = self.budget_manager.freeze(
            pool_id=request.pool_id,
            agent_id=agent_id,
            amount=amount,
            order_id=request.order_id,
            reason="payment_escrow",
            repo=self.repo,
        )
        if not freeze_ok:
            log.warning("payment_rejected_freeze_failed")
            return {"success": False, "error": "Failed to freeze funds"}

        # Step 5: Create transaction record
        commission_rate = Decimal("0.03")
        commission_amount = amount * commission_rate
        provider_payout = amount - commission_amount

        tx = self.repo.create_transaction(
            pool_id=request.pool_id,
            order_id=request.order_id,
            agent_id=agent_id,
            provider_id=provider_id,
            amount=amount,
            currency=currency,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            provider_payout=provider_payout,
            settlement_channel=request.settlement_channel,
            escrow_status=EscrowState.FROZEN.value,
            escrow_frozen_at=datetime.now(UTC),
            authorization_level=required_level,
            status="pending" if needs_approval else "authorized",
        )

        # Create authorization request if needed
        auth_request_id = None
        if needs_approval:
            auth_expiry = calculate_auth_expiry(required_level)
            notification_channel = self._determine_notification_channel(
                request.pool_id
            )
            auth_req = self.repo.create_authorization_request(
                transaction_id=tx.id,
                agent_id=agent_id,
                owner_id=self.repo.get_pool(request.pool_id).owner_id,
                level=required_level,
                amount=amount,
                item_name=item_name,
                item_type=item_type,
                notification_channel=notification_channel,
                expires_at=auth_expiry,
            )
            auth_request_id = auth_req.id
            log.info(
                "authorization_required",
                auth_request_id=str(auth_request_id),
                required_level=required_level,
                expires_at=auth_expiry.isoformat(),
            )

        # Step 6: Anomaly check
        alerts = self.anomaly_detector.check_after_transaction(
            pool_id=request.pool_id,
            agent_id=agent_id,
            amount=amount,
            provider_id=provider_id,
            repo=self.repo,
        )

        # Handle critical anomalies
        for alert in alerts:
            if alert.severity == "critical":
                self._handle_critical_anomaly(alert)
                log.warning(
                    "critical_anomaly_detected",
                    anomaly_type=alert.anomaly_type.value,
                    action_taken=alert.action_taken,
                )

        # Step 7: Execute settlement if no approval needed
        settlement_result = None
        if not needs_approval:
            tx.status = "processing"
            self.repo.save_transaction(tx)
            settlement_result = self._execute_settlement(
                tx, request.settlement_channel
            )
            if settlement_result and settlement_result.get("success"):
                tx.status = "completed"
                tx.external_settlement_id = settlement_result.get("settlement_id")
                tx.settlement_confirmed_at = datetime.now(UTC)
            else:
                tx.status = "failed"
                tx.failure_reason = settlement_result.get("error") if settlement_result else "Settlement failed"
            self.repo.save_transaction(tx)

        # Step 8: Audit log
        log.info(
            "payment_initiated",
            tx_id=str(tx.id),
            amount=str(amount),
            escrow_status=tx.escrow_status,
            tx_status=tx.status,
            needs_approval=needs_approval,
            alert_count=len(alerts),
        )

        return {
            "success": True,
            "transaction_id": str(tx.id),
            "status": tx.status,
            "escrow_status": tx.escrow_status,
            "needs_approval": needs_approval,
            "authorization_request_id": (
                str(auth_request_id) if auth_request_id else None
            ),
            "alerts": [
                {
                    "type": a.anomaly_type.value,
                    "severity": a.severity,
                    "message": a.message,
                    "action_taken": a.action_taken,
                }
                for a in alerts
            ],
        }

    # ------------------------------------------------------------------
    # Report Effect
    # ------------------------------------------------------------------

    def report_effect(
        self,
        request: EffectReportRequest,
        agent_id: UUID,
    ) -> dict:
        """Process an effect report for a transaction.

        Steps:
        1. Determine escrow event from effect_score
        2. Transition escrow state
        3. Release funds according to payout percentages
        4. Audit log

        Returns:
            A dict with the updated transaction state.
        """
        tx = self.repo.get_transaction(request.transaction_id)
        if tx is None:
            return {"success": False, "error": "Transaction not found"}

        log = logger.bind(
            transaction_id=str(request.transaction_id),
            agent_id=str(agent_id),
        )

        # Step 1: Determine escrow event from effect_score
        escrow_event = self._effect_score_to_event(
            request.effect_score, request.success
        )

        # Step 2: Transition escrow state
        current_state = EscrowState(tx.escrow_status)
        try:
            result = transition(
                current_state=current_state,
                event=escrow_event,
                effect_score=request.effect_score,
            )
        except ValueError as exc:
            log.warning("escrow_transition_failed", error=str(exc))
            return {"success": False, "error": str(exc)}

        # Update transaction
        tx.escrow_status = result.new_state.value
        tx.effect_score = request.effect_score
        tx.effect_reported_at = datetime.now(UTC)

        if result.new_state in (EscrowState.RELEASED, EscrowState.PARTIAL_RELEASE):
            tx.escrow_released_at = datetime.now(UTC)

        # Step 3: Release funds according to payout percentages
        if result.provider_payout_pct > 0 or result.buyer_refund_pct > 0:
            release_ok = self.budget_manager.release(
                pool_id=tx.pool_id,
                amount=Decimal(str(tx.amount)),
                provider_id=tx.provider_id,
                order_id=tx.order_id,
                release_pct=result.provider_payout_pct,
                repo=self.repo,
            )
            if not release_ok:
                log.error("fund_release_failed")
                return {"success": False, "error": "Failed to release funds"}

        # Update provider payout based on release percentage
        if result.provider_payout_pct > 0:
            tx.provider_payout = Decimal(str(tx.amount)) * Decimal(
                str(result.provider_payout_pct)
            ) * (1 - Decimal(str(tx.commission_rate)))

        # Update transaction status
        if result.new_state == EscrowState.RELEASED:
            tx.status = "completed"
        elif result.new_state == EscrowState.REFUNDED:
            tx.status = "cancelled"
        elif result.new_state == EscrowState.DISPUTED:
            tx.status = "disputed"
        elif result.new_state == EscrowState.PARTIAL_RELEASE:
            tx.status = "processing"

        self.repo.save_transaction(tx)

        # Step 4: Audit log
        log.info(
            "effect_reported",
            effect_score=request.effect_score,
            escrow_event=escrow_event.value,
            old_state=result.old_state.value,
            new_state=result.new_state.value,
            provider_payout_pct=result.provider_payout_pct,
            buyer_refund_pct=result.buyer_refund_pct,
            action_required=result.action_required,
        )

        return {
            "success": True,
            "transaction_id": str(tx.id),
            "escrow_status": tx.escrow_status,
            "status": tx.status,
            "provider_payout_pct": result.provider_payout_pct,
            "buyer_refund_pct": result.buyer_refund_pct,
            "action_required": result.action_required,
        }

    # ------------------------------------------------------------------
    # Decide Authorization
    # ------------------------------------------------------------------

    def decide_authorization(
        self,
        auth_id: UUID,
        request: AuthorizationDecisionRequest,
        owner_id: UUID,
    ) -> dict:
        """Process an authorization decision (approve or reject).

        If approved, trigger settlement.
        If rejected, unfreeze funds and cancel the transaction.

        Returns:
            A dict with the decision outcome.
        """
        auth_req = self.repo.get_authorization_request(auth_id)
        if auth_req is None:
            return {"success": False, "error": "Authorization request not found"}

        log = logger.bind(
            auth_id=str(auth_id),
            owner_id=str(owner_id),
        )

        if auth_req.status != "pending":
            return {
                "success": False,
                "error": f"Authorization already {auth_req.status}",
            }

        # Verify owner
        if auth_req.owner_id != owner_id:
            return {"success": False, "error": "Not authorized to decide this request"}

        now = datetime.now(UTC)

        if request.approved:
            auth_req.status = "approved"
            auth_req.decided_at = now
            auth_req.decided_by = owner_id
            self.repo.save_authorization_request(auth_req)

            # Update the transaction
            tx = self.repo.get_transaction(auth_req.transaction_id)
            tx.status = "processing"
            tx.authorization_id = auth_req.id
            tx.authorized_at = now
            tx.authorized_by = str(owner_id)
            self.repo.save_transaction(tx)

            # Trigger settlement
            settlement_result = self._execute_settlement(
                tx, tx.settlement_channel
            )
            if settlement_result and settlement_result.get("success"):
                tx.status = "completed"
                tx.external_settlement_id = settlement_result.get("settlement_id")
                tx.settlement_confirmed_at = now
            else:
                tx.status = "failed"
                tx.failure_reason = (
                    settlement_result.get("error")
                    if settlement_result
                    else "Settlement failed"
                )
            self.repo.save_transaction(tx)

            log.info(
                "authorization_approved",
                tx_status=tx.status,
            )
            return {
                "success": True,
                "decision": "approved",
                "transaction_id": str(tx.id),
                "tx_status": tx.status,
            }
        else:
            auth_req.status = "rejected"
            auth_req.decided_at = now
            auth_req.decided_by = owner_id
            auth_req.reject_reason = request.reject_reason
            self.repo.save_authorization_request(auth_req)

            # Unfreeze funds and cancel transaction
            tx = self.repo.get_transaction(auth_req.transaction_id)
            # Release frozen amount back (release_pct=0 means full refund)
            self.budget_manager.release(
                pool_id=tx.pool_id,
                amount=Decimal(str(tx.amount)),
                provider_id=tx.provider_id,
                order_id=tx.order_id,
                release_pct=0.0,
                repo=self.repo,
            )
            tx.status = "cancelled"
            tx.escrow_status = EscrowState.REFUNDED.value
            tx.failure_reason = request.reject_reason or "Authorization rejected"
            self.repo.save_transaction(tx)

            log.info(
                "authorization_rejected",
                reject_reason=request.reject_reason,
            )
            return {
                "success": True,
                "decision": "rejected",
                "transaction_id": str(tx.id),
                "tx_status": tx.status,
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _effect_score_to_event(
        self, effect_score: int, success: bool
    ) -> EscrowEvent:
        """Map effect score to an escrow event."""
        if not success:
            return EscrowEvent.EFFECT_FAILED
        if effect_score >= 4:
            return EscrowEvent.EFFECT_CONFIRMED
        if effect_score >= 1:
            return EscrowEvent.EFFECT_PARTIAL
        return EscrowEvent.EFFECT_FAILED

    def _execute_settlement(self, tx: Any, channel: str) -> dict | None:
        """Execute settlement based on the channel."""
        if channel == "x402" and self.x402_settler:
            payload = self.x402_settler.prepare_payment(
                amount_usdc=float(tx.amount),
                recipient_address=str(tx.provider_id),
                agent_wallet_address=str(tx.agent_id),
            )
            result: Any = self.x402_settler.verify_and_settle(
                payment_payload=payload,
                agent_signature="TODO",
            )
            if result.success:
                return {
                    "success": True,
                    "settlement_id": result.tx_hash,
                    "block_number": result.block_number,
                }
            return {"success": False, "error": result.error}

        elif channel == "acp" and self.acp_settler:
            intent = self.acp_settler.create_payment_intent(
                agent_id=tx.agent_id,
                owner_id=self.repo.get_pool(tx.pool_id).owner_id,
                amount_cny=float(tx.amount),
                provider_id=tx.provider_id,
                order_id=tx.order_id,
            )
            result = self.acp_settler.confirm_with_spt(
                intent_id=intent.intent_id,
                spt="TODO_placeholder_spt",
            )
            if result.success:
                return {
                    "success": True,
                    "settlement_id": result.payment_intent_id,
                    "charge_id": result.charge_id,
                }
            return {"success": False, "error": result.error}

        elif channel == "fiat":
            # Fiat settlement is handled externally (bank transfer, etc.)
            logger.info("fiat_settlement_deferred", tx_id=str(tx.id))
            return {
                "success": True,
                "settlement_id": f"fiat_{tx.id}",
            }

        else:
            logger.warning(
                "unsupported_settlement_channel",
                channel=channel,
            )
            return {"success": False, "error": f"Unsupported channel: {channel}"}

    def _determine_notification_channel(self, pool_id: UUID) -> str:
        """Determine the best notification channel for the pool owner."""
        # TODO: implement based on owner preferences
        return "in_app"

    def _handle_critical_anomaly(self, alert: Any) -> None:
        """Take action on a critical anomaly alert."""
        from .anomaly import AnomalyType

        if alert.anomaly_type == AnomalyType.BURST_SPENDING:
            # Suspend the agent's allocation
            self.repo.suspend_agent(alert.pool_id, alert.agent_id)
        elif alert.anomaly_type == AnomalyType.BUDGET_DEPLETED:
            # Suspend all agents on the pool
            self.repo.suspend_pool_agents(alert.pool_id)
        # Other critical types can be handled here

        logger.warning(
            "critical_anomaly_handled",
            anomaly_type=alert.anomaly_type.value,
            action_taken=alert.action_taken,
        )
