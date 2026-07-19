from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Authorization level definitions
# ---------------------------------------------------------------------------

AUTH_LEVELS: dict[str, dict[str, Any]] = {
    "L0": {
        "max_per_call": 0.01,
        "timeout": None,  # no approval timeout – auto-approved
        "description": "Micro-transactions, fully autonomous",
    },
    "L1": {
        "max_per_call": 1.00,
        "timeout": None,  # auto-approved within per-call limit
        "description": "Standard transactions, auto-approved",
    },
    "L2": {
        "max_per_call": 100.00,
        "timeout": timedelta(minutes=30),
        "description": "High-value transactions, owner approval required within 30 min",
    },
    "L3": {
        "max_per_call": math.inf,
        "timeout": timedelta(minutes=60),
        "description": "Unlimited transactions, owner approval required within 60 min",
    },
}

# Ordered levels for comparison
_LEVEL_ORDER = ["L0", "L1", "L2", "L3"]


def determine_auth_level(
    amount: float,
    agent_level: str,
) -> tuple[str, bool]:
    """Determine the required authorization level for a transaction.

    Args:
        amount: The transaction amount.
        agent_level: The agent's spending_authority_level (L0-L3).

    Returns:
        A tuple of (required_level, needs_approval).
        - required_level: the minimum level needed for this amount.
        - needs_approval: True if owner approval is required.
    """
    required_level = "L0"
    needs_approval = False

    # Find the minimum level that can cover this amount
    for level in _LEVEL_ORDER:
        max_per_call = AUTH_LEVELS[level]["max_per_call"]
        if amount <= max_per_call:
            required_level = level
            break
    else:
        # Amount exceeds even L3 max (shouldn't happen since L3 is inf)
        required_level = "L3"

    # If the agent's level is below the required level, they need an upgrade
    # which means owner approval
    agent_idx = _LEVEL_ORDER.index(agent_level)
    required_idx = _LEVEL_ORDER.index(required_level)

    if required_idx > agent_idx:
        needs_approval = True
        # The required level stays as-is (the approval will temporarily
        # elevate for this transaction)
    elif AUTH_LEVELS[required_level]["timeout"] is not None:
        # Even at the correct level, L2+ always requires approval
        needs_approval = True

    logger.debug(
        "determine_auth_level",
        amount=amount,
        agent_level=agent_level,
        required_level=required_level,
        needs_approval=needs_approval,
    )

    return required_level, needs_approval


def calculate_auth_expiry(level: str) -> datetime:
    """Calculate the expiration datetime for an authorization request.

    Args:
        level: The authorization level (L2 or L3).

    Returns:
        The datetime at which the request expires.
    """
    timeout: timedelta | None = AUTH_LEVELS[level]["timeout"]
    if timeout is None:
        # Should not happen – L0/L1 don't create auth requests
        raise ValueError(f"Level {level} does not require approval timeout")
    return datetime.now(UTC) + timeout


def check_authorization_status(
    auth_request_id: str,
    auth_repo: Any,
) -> tuple[str, str | None]:
    """Check the status of an authorization request, auto-expiring if needed.

    Args:
        auth_request_id: The UUID of the authorization request.
        auth_repo: A repository/object with a ``get_by_id`` method that returns
                   an AuthorizationRequest-like object.

    Returns:
        A tuple of (status, reject_reason).
        - status: one of pending/approved/rejected/expired
        - reject_reason: populated only when status is rejected or expired
    """
    auth_request = auth_repo.get_by_id(auth_request_id)

    if auth_request is None:
        return "rejected", "Authorization request not found"

    if auth_request.status in ("approved", "rejected", "expired"):
        return auth_request.status, auth_request.reject_reason

    # Still pending – check if expired
    now = datetime.now(UTC)
    if auth_request.expires_at and now > auth_request.expires_at.replace(
        tzinfo=UTC
    ):
        # Auto-expire
        auth_request.status = "expired"
        auth_request.reject_reason = "Authorization request timed out"
        auth_request.decided_at = now
        logger.info(
            "authorization_auto_expired",
            auth_request_id=str(auth_request_id),
        )
        return "expired", "Authorization request timed out"

    return "pending", None
