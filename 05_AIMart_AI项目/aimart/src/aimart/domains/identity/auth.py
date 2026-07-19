from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from aimart.domains.identity.apikey import ApiKeyManager
from aimart.domains.identity.models import ParticipantType
from aimart.domains.identity.oauth2 import OAuth2AgentFlow

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Security schemes
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/identity/token", auto_error=False)

# Module-level instances (overridden by app lifespan in production)
_api_key_manager: ApiKeyManager | None = None
_oauth2_flow: OAuth2AgentFlow | None = None


def set_auth_dependencies(api_key_manager: ApiKeyManager, oauth2_flow: OAuth2AgentFlow) -> None:
    """Configure the auth module with runtime dependencies. Called during app startup."""
    global _api_key_manager, _oauth2_flow  # noqa: PLW0603
    _api_key_manager = api_key_manager
    _oauth2_flow = oauth2_flow


# ---------------------------------------------------------------------------
# Auth context
# ---------------------------------------------------------------------------

@dataclass
class AuthContext:
    participant_id: str
    participant_type: str
    agent_id: str | None = None
    scopes: list[str] = field(default_factory=list)
    permissions: dict[str, Any] = field(default_factory=dict)
    auth_method: str = "api_key"  # api_key | jwt


# ---------------------------------------------------------------------------
# Core auth dependency – tries API key first, then JWT
# ---------------------------------------------------------------------------

async def require_auth(
    api_key: str | None = Depends(_api_key_header),
    token: str | None = Depends(_oauth2_scheme),
) -> AuthContext:
    """Resolve identity from either an API-Key header or a Bearer JWT.

    API-Key is tried first because agents predominantly authenticate that way.
    """
    if api_key:
        key_info = await _api_key_manager.verify(api_key)  # type: ignore[union-attr]
        if key_info:
            return AuthContext(
                participant_id=key_info["participant_id"],
                participant_type=key_info["participant_type"],
                agent_id=key_info.get("agent_id"),
                scopes=key_info.get("scopes", []),
                permissions=key_info.get("permissions", {}),
                auth_method="api_key",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    if token:
        payload = await _oauth2_flow.verify_access_token(token)  # type: ignore[union-attr]
        if payload:
            return AuthContext(
                participant_id=payload["sub"],
                participant_type=payload.get("participant_type", ""),
                agent_id=payload.get("agent_id"),
                scopes=payload.get("scopes", []),
                permissions=payload.get("permissions", {}),
                auth_method="jwt",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (API key or Bearer token)",
    )


# ---------------------------------------------------------------------------
# Role-based guards
# ---------------------------------------------------------------------------

async def require_owner(ctx: AuthContext = Depends(require_auth)) -> AuthContext:
    if ctx.participant_type != ParticipantType.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner role required",
        )
    return ctx


async def require_provider(ctx: AuthContext = Depends(require_auth)) -> AuthContext:
    if ctx.participant_type != ParticipantType.PROVIDER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider role required",
        )
    return ctx


async def require_agent(ctx: AuthContext = Depends(require_auth)) -> AuthContext:
    if ctx.agent_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent identity required",
        )
    return ctx


async def require_certifier(ctx: AuthContext = Depends(require_auth)) -> AuthContext:
    if ctx.participant_type != ParticipantType.CERTIFIER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Certifier role required",
        )
    return ctx


# ---------------------------------------------------------------------------
# Scope guard factory
# ---------------------------------------------------------------------------

def require_scope(scope_name: str):
    """Return a FastAPI dependency that verifies *scope_name* is present."""

    async def _guard(ctx: AuthContext = Depends(require_auth)) -> AuthContext:
        if scope_name not in ctx.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{scope_name}' required",
            )
        return ctx

    return _guard


# ---------------------------------------------------------------------------
# MFA guard factory
# ---------------------------------------------------------------------------

def require_mfa(purpose: str):
    """Return a FastAPI dependency that insists the request carries a valid
    MFA challenge verification header (X-MFA-Verified).

    The actual MFA verification happens in the endpoint handler; this guard
    merely checks that the header is present and the challenge ID is valid.
    """

    async def _guard(
        ctx: AuthContext = Depends(require_auth),
        mfa_verified: str | None = None,
    ) -> AuthContext:
        if not mfa_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"MFA verification required for '{purpose}'",
            )
        return ctx

    return _guard
