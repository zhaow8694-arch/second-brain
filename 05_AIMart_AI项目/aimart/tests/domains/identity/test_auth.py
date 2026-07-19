"""Tests for identity auth module."""

from __future__ import annotations

from uuid import uuid4

from aimart.domains.identity.auth import AuthContext


class TestAuthContext:
    """Test AuthContext creation."""

    def test_auth_context_creation(self):
        ctx = AuthContext(
            participant_id="test-owner",
            participant_type="owner",
            agent_id="test-agent",
        )
        assert ctx.participant_id == "test-owner"
        assert ctx.participant_type == "owner"
        assert ctx.agent_id == "test-agent"

    def test_auth_context_no_agent(self):
        ctx = AuthContext(
            participant_id="test-owner",
            participant_type="owner",
        )
        assert ctx.agent_id is None

    def test_auth_context_various_types(self):
        for ptype in ("owner", "provider", "certifier", "platform"):
            ctx = AuthContext(
                participant_id=str(uuid4()),
                participant_type=ptype,
            )
            assert ctx.participant_type == ptype
