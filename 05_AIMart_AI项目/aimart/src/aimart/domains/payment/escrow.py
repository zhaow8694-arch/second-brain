from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import structlog

logger = structlog.get_logger(__name__)


class EscrowState(StrEnum):
    FROZEN = "frozen"
    PARTIAL_RELEASE = "partial_release"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class EscrowEvent(StrEnum):
    EFFECT_CONFIRMED = "effect_confirmed"
    EFFECT_PARTIAL = "effect_partial"
    EFFECT_FAILED = "effect_failed"
    DISPUTE_OPENED = "dispute_opened"
    DISPUTE_RESOLVED_RELEASE = "dispute_resolved_release"
    DISPUTE_RESOLVED_REFUND = "dispute_resolved_refund"
    DISPUTE_RESOLVED_SPLIT = "dispute_resolved_split"
    TIMEOUT_NO_REPORT = "timeout_no_report"


# (current_state) → {event → new_state}
VALID_TRANSITIONS: dict[EscrowState, dict[EscrowEvent, EscrowState]] = {
    EscrowState.FROZEN: {
        EscrowEvent.EFFECT_CONFIRMED: EscrowState.RELEASED,
        EscrowEvent.EFFECT_PARTIAL: EscrowState.PARTIAL_RELEASE,
        EscrowEvent.EFFECT_FAILED: EscrowState.REFUNDED,
        EscrowEvent.DISPUTE_OPENED: EscrowState.DISPUTED,
        EscrowEvent.TIMEOUT_NO_REPORT: EscrowState.REFUNDED,
    },
    EscrowState.PARTIAL_RELEASE: {
        EscrowEvent.EFFECT_CONFIRMED: EscrowState.RELEASED,
        EscrowEvent.EFFECT_PARTIAL: EscrowState.PARTIAL_RELEASE,
        EscrowEvent.EFFECT_FAILED: EscrowState.REFUNDED,
        EscrowEvent.DISPUTE_OPENED: EscrowState.DISPUTED,
    },
    EscrowState.RELEASED: {
        EscrowEvent.DISPUTE_OPENED: EscrowState.DISPUTED,
    },
    EscrowState.REFUNDED: {
        EscrowEvent.DISPUTE_OPENED: EscrowState.DISPUTED,
    },
    EscrowState.DISPUTED: {
        EscrowEvent.DISPUTE_RESOLVED_RELEASE: EscrowState.RELEASED,
        EscrowEvent.DISPUTE_RESOLVED_REFUND: EscrowState.REFUNDED,
        EscrowEvent.DISPUTE_RESOLVED_SPLIT: EscrowState.PARTIAL_RELEASE,
    },
}


@dataclass
class EscrowTransitionResult:
    old_state: EscrowState
    new_state: EscrowState
    event: EscrowEvent
    provider_payout_pct: float
    buyer_refund_pct: float
    action_required: str | None = None


def transition(
    current_state: EscrowState,
    event: EscrowEvent,
    effect_score: int | None = None,
) -> EscrowTransitionResult:
    """Execute a state transition on the escrow state machine.

    Returns an EscrowTransitionResult with payout percentages and any
    required follow-up action.

    Raises:
        ValueError: if the transition is invalid for the current state.
    """
    allowed = VALID_TRANSITIONS.get(current_state, {})
    if event not in allowed:
        raise ValueError(
            f"Invalid escrow transition: {current_state.value} + {event.value}"
        )

    new_state = allowed[event]

    # Determine payout / refund percentages based on resulting state
    if new_state == EscrowState.RELEASED:
        provider_payout_pct = 1.0
        buyer_refund_pct = 0.0
        action_required = "release_funds_to_provider"
    elif new_state == EscrowState.REFUNDED:
        provider_payout_pct = 0.0
        buyer_refund_pct = 1.0
        action_required = "refund_funds_to_buyer"
    elif new_state == EscrowState.PARTIAL_RELEASE:
        if effect_score is not None and 0 <= effect_score <= 5:
            provider_payout_pct = effect_score / 5.0
        else:
            provider_payout_pct = 0.5  # default 50/50 split when score unknown
        buyer_refund_pct = 1.0 - provider_payout_pct
        action_required = "split_funds_according_to_pct"
    elif new_state == EscrowState.DISPUTED:
        provider_payout_pct = 0.0
        buyer_refund_pct = 0.0
        action_required = "await_arbitration"
    else:
        provider_payout_pct = 0.0
        buyer_refund_pct = 0.0
        action_required = None

    logger.info(
        "escrow_transition",
        old_state=current_state.value,
        new_state=new_state.value,
        escrow_event=event.value,
        provider_payout_pct=provider_payout_pct,
        buyer_refund_pct=buyer_refund_pct,
    )

    return EscrowTransitionResult(
        old_state=current_state,
        new_state=new_state,
        event=event,
        provider_payout_pct=provider_payout_pct,
        buyer_refund_pct=buyer_refund_pct,
        action_required=action_required,
    )
