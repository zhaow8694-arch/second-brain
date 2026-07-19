"""Tests for the payment authorization module."""

from __future__ import annotations

from datetime import UTC, datetime

from aimart.domains.payment.authorization import (
    calculate_auth_expiry,
    determine_auth_level,
)


class TestAuthorization:
    """Test the authorization level determination."""

    def test_l0_amount_auto_approved(self):
        """Amount <= 0.01 should be L0, no approval needed."""
        level, needs_approval = determine_auth_level(amount=0.005, agent_level="L0")
        assert level == "L0"
        assert needs_approval is False

    def test_l1_amount_auto_approved(self):
        """Amount <= 1.00 should be L1, auto-approved for L2+ agent."""
        level, needs_approval = determine_auth_level(amount=0.50, agent_level="L2")
        assert level == "L1"
        assert needs_approval is False

    def test_l2_amount_requires_approval(self):
        """Amount > 1.00 should require L2+ approval."""
        level, needs_approval = determine_auth_level(amount=50.0, agent_level="L0")
        assert needs_approval is True

    def test_l2_agent_is_auto_approved_for_l1_amount(self):
        """Agent with L2 level does not need approval for L1 amount."""
        level, needs_approval = determine_auth_level(amount=0.50, agent_level="L2")
        assert needs_approval is False

    def test_l3_amount_triggers_l3(self):
        """Amount > 100 requires L3."""
        level, needs_approval = determine_auth_level(amount=500.0, agent_level="L0")
        assert level == "L3"
        assert needs_approval is True

    def test_l3_agent_needs_approval_for_l3_amount(self):
        """Even L3 agent needs approval for L3 amount."""
        level, needs_approval = determine_auth_level(amount=500.0, agent_level="L3")
        assert level == "L3"
        assert needs_approval is True

    def test_low_agent_level_high_amount_requires_upgrade(self):
        """Agent with L1 level needs approval for L2 amount."""
        level, needs_approval = determine_auth_level(
            amount=50.0, agent_level="L1"
        )
        assert needs_approval is True

    def test_calculate_auth_expiry_l2(self):
        """L2 expiry should be 30 minutes."""
        expiry = calculate_auth_expiry("L2")
        now = datetime.now(UTC)
        diff = (expiry - now).total_seconds()
        assert 29 * 60 < diff < 31 * 60  # ~30 min

    def test_calculate_auth_expiry_l3(self):
        """L3 expiry should be 60 minutes."""
        expiry = calculate_auth_expiry("L3")
        now = datetime.now(UTC)
        diff = (expiry - now).total_seconds()
        assert 59 * 60 < diff < 61 * 60  # ~60 min
