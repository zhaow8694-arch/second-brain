"""Tests for the payment escrow state machine."""

from __future__ import annotations

import pytest

from aimart.domains.payment.escrow import (
    EscrowEvent,
    EscrowState,
    transition,
)


class TestEscrowStateMachine:
    """Test the escrow state machine transitions."""

    def test_frozen_effect_confirmed_releases(self):
        """FROZEN + EFFECT_CONFIRMED → RELEASED (full payout)."""
        result = transition(
            current_state=EscrowState.FROZEN,
            event=EscrowEvent.EFFECT_CONFIRMED,
            effect_score=5,
        )
        assert result.new_state == EscrowState.RELEASED
        assert result.provider_payout_pct == 1.0
        assert result.buyer_refund_pct == 0.0

    def test_frozen_effect_failed_refunds(self):
        """FROZEN + EFFECT_FAILED → REFUNDED (full refund)."""
        result = transition(
            current_state=EscrowState.FROZEN,
            event=EscrowEvent.EFFECT_FAILED,
            effect_score=1,
        )
        assert result.new_state == EscrowState.REFUNDED
        assert result.provider_payout_pct == 0.0
        assert result.buyer_refund_pct == 1.0

    def test_frozen_effect_partial_partial_release(self):
        """FROZEN + EFFECT_PARTIAL → PARTIAL_RELEASE."""
        result = transition(
            current_state=EscrowState.FROZEN,
            event=EscrowEvent.EFFECT_PARTIAL,
            effect_score=3,
        )
        assert result.new_state == EscrowState.PARTIAL_RELEASE

    def test_frozen_dispute_opened_disputed(self):
        """FROZEN + DISPUTE_OPENED → DISPUTED."""
        result = transition(
            current_state=EscrowState.FROZEN,
            event=EscrowEvent.DISPUTE_OPENED,
        )
        assert result.new_state == EscrowState.DISPUTED

    def test_disputed_resolve_release(self):
        """DISPUTED + DISPUTE_RESOLVED_RELEASE → RELEASED."""
        result = transition(
            current_state=EscrowState.DISPUTED,
            event=EscrowEvent.DISPUTE_RESOLVED_RELEASE,
        )
        assert result.new_state == EscrowState.RELEASED

    def test_disputed_resolve_refund(self):
        """DISPUTED + DISPUTE_RESOLVED_REFUND → REFUNDED."""
        result = transition(
            current_state=EscrowState.DISPUTED,
            event=EscrowEvent.DISPUTE_RESOLVED_REFUND,
        )
        assert result.new_state == EscrowState.REFUNDED

    def test_disputed_resolve_split(self):
        """DISPUTED + DISPUTE_RESOLVED_SPLIT → PARTIAL_RELEASE."""
        result = transition(
            current_state=EscrowState.DISPUTED,
            event=EscrowEvent.DISPUTE_RESOLVED_SPLIT,
        )
        assert result.new_state == EscrowState.PARTIAL_RELEASE

    def test_invalid_transition_raises_error(self):
        """RELEASED + EFFECT_CONFIRMED is invalid → ValueError."""
        with pytest.raises(ValueError, match="Invalid escrow transition"):
            transition(
                current_state=EscrowState.RELEASED,
                event=EscrowEvent.EFFECT_CONFIRMED,
            )

    def test_released_to_disputed_allowed(self):
        """RELEASED + DISPUTE_OPENED → DISPUTED is valid."""
        result = transition(
            current_state=EscrowState.RELEASED,
            event=EscrowEvent.DISPUTE_OPENED,
        )
        assert result.new_state == EscrowState.DISPUTED

    def test_all_valid_transitions_from_frozen(self):
        """Verify all expected transitions from FROZEN."""
        expected_events = {
            EscrowEvent.EFFECT_CONFIRMED: EscrowState.RELEASED,
            EscrowEvent.EFFECT_PARTIAL: EscrowState.PARTIAL_RELEASE,
            EscrowEvent.EFFECT_FAILED: EscrowState.REFUNDED,
            EscrowEvent.DISPUTE_OPENED: EscrowState.DISPUTED,
            EscrowEvent.TIMEOUT_NO_REPORT: EscrowState.REFUNDED,
        }
        for event, expected_state in expected_events.items():
            result = transition(EscrowState.FROZEN, event, effect_score=3)
            assert result.new_state == expected_state, (
                f"FROZEN + {event.value} should → {expected_state.value}, "
                f"got {result.new_state.value}"
            )
