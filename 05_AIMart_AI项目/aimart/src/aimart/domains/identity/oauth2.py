from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.domains.identity.models import (
    ApiKey,
    RefreshToken,
    RefreshTokenStatus,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration (env-driven; override via settings in production)
# ---------------------------------------------------------------------------

_JWT_SECRET_ENV = "AIMART_JWT_SECRET"
_JWT_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 60
_REFRESH_TOKEN_EXPIRE_DAYS = 30


def _get_jwt_secret() -> str:
    secret = os.environ.get(_JWT_SECRET_ENV)
    if not secret:
        raise RuntimeError(
            f"Environment variable {_JWT_SECRET_ENV} is not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    return secret


# ---------------------------------------------------------------------------
# OAuth2AgentFlow
# ---------------------------------------------------------------------------

class OAuth2AgentFlow:
    """Implements the OAuth2 client_credentials grant tailored for AI Agents.

    In AIMart an agent authenticates with its API key and receives a JWT
    access token + refresh token in return.
    """

    # ------------------------------------------------------------------
    # client_credentials grant
    # ------------------------------------------------------------------

    async def client_credentials_grant(
        self,
        db: AsyncSession,
        *,
        api_key_info: dict[str, Any],
        requested_scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Exchange a verified API key for access + refresh tokens.

        Parameters
        ----------
        api_key_info
            The dict returned by :class:`ApiKeyManager.verify`.
        requested_scopes
            Optional subset of scopes to request; must be a subset of the
            key's scopes.
        """
        participant_id = uuid.UUID(api_key_info["participant_id"])
        agent_id = uuid.UUID(api_key_info["agent_id"]) if api_key_info.get("agent_id") else None

        # Resolve scopes
        key_scopes = set(api_key_info.get("scopes", []))
        if requested_scopes:
            granted = [s for s in requested_scopes if s in key_scopes]
            if not granted:
                raise PermissionError("Requested scopes not permitted by API key")
        else:
            granted = list(key_scopes)

        # Build access token
        access_token, expires_in = await self._create_access_token(
            participant_id=participant_id,
            agent_id=agent_id,
            scopes=granted,
            key_id=api_key_info["key_id"],
            participant_type=api_key_info.get("participant_type", ""),
        )

        # Build refresh token
        refresh_token_str = await self._create_refresh_token(
            db,
            participant_id=participant_id,
            agent_id=agent_id,
        )

        logger.info(
            "oauth2.client_credentials_grant",
            participant_id=str(participant_id),
            agent_id=str(agent_id) if agent_id else None,
            scopes=granted,
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token_str,
            "scope": " ".join(granted),
        }

    # ------------------------------------------------------------------
    # Refresh token
    # ------------------------------------------------------------------

    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token_str: str,
    ) -> dict[str, Any]:
        """Rotate a refresh token: issue a new access+refresh pair and mark the
        old refresh token as used.
        """
        token_hash = hashlib.sha512(refresh_token_str.encode()).hexdigest()

        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.status == RefreshTokenStatus.ACTIVE,
        )
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            logger.warning("oauth2.refresh_token_not_found")
            raise PermissionError("Invalid or revoked refresh token")

        now = datetime.now(UTC)
        if record.expires_at < now:
            record.status = RefreshTokenStatus.EXPIRED
            await db.flush()
            raise PermissionError("Refresh token expired")

        # Mark old token as used
        record.status = RefreshTokenStatus.USED
        await db.flush()

        # Resolve key info for scope recovery
        key_info: dict[str, Any] = {
            "participant_id": str(record.participant_id),
            "agent_id": str(record.agent_id) if record.agent_id else None,
        }
        # Recover scopes from the most recent active API key
        if record.agent_id:
            kstmt = select(ApiKey).where(
                ApiKey.agent_id == record.agent_id,
            ).order_by(ApiKey.created_at.desc()).limit(1)
        else:
            kstmt = select(ApiKey).where(
                ApiKey.participant_id == record.participant_id,
            ).order_by(ApiKey.created_at.desc()).limit(1)
        kresult = await db.execute(kstmt)
        latest_key = kresult.scalar_one_or_none()
        if latest_key:
            key_info["scopes"] = latest_key.scopes or []
            key_info["key_id"] = str(latest_key.id)
            key_info["permissions"] = latest_key.permissions or {}
        else:
            key_info["scopes"] = []
            key_info["key_id"] = ""
            key_info["permissions"] = {}

        # Resolve participant type
        from aimart.domains.identity.models import Participant
        p = await db.get(Participant, record.participant_id)
        key_info["participant_type"] = p.type.value if p else ""

        # New token pair
        access_token, expires_in = await self._create_access_token(
            participant_id=record.participant_id,
            agent_id=record.agent_id,
            scopes=key_info.get("scopes", []),
            key_id=key_info.get("key_id", ""),
            participant_type=key_info.get("participant_type", ""),
        )
        new_refresh = await self._create_refresh_token(
            db,
            participant_id=record.participant_id,
            agent_id=record.agent_id,
        )

        logger.info(
            "oauth2.refresh_token_rotated",
            participant_id=str(record.participant_id),
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": new_refresh,
            "scope": " ".join(key_info.get("scopes", [])),
        }

    # ------------------------------------------------------------------
    # JWT helpers
    # ------------------------------------------------------------------

    async def _create_access_token(
        self,
        *,
        participant_id: uuid.UUID,
        agent_id: uuid.UUID | None,
        scopes: list[str],
        key_id: str,
        participant_type: str,
    ) -> tuple[str, int]:
        """Create a signed JWT. Returns (token_string, expires_in_seconds)."""
        now = datetime.now(UTC)
        expires_delta = timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = now + expires_delta

        payload = {
            "iss": "aimart",
            "sub": str(participant_id),
            "agent_id": str(agent_id) if agent_id else None,
            "participant_type": participant_type,
            "scopes": scopes,
            "key_id": key_id,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": secrets.token_urlsafe(16),
        }

        token = jwt.encode(payload, _get_jwt_secret(), algorithm=_JWT_ALGORITHM)
        return token, int(expires_delta.total_seconds())

    # ------------------------------------------------------------------

    async def verify_access_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode a JWT access token.

        Returns the payload dict or ``None`` if the token is invalid/expired.
        """
        try:
            payload = jwt.decode(
                token,
                _get_jwt_secret(),
                algorithms=[_JWT_ALGORITHM],
                options={"require": ["iss", "sub", "exp", "iat"]},
            )
            if payload.get("iss") != "aimart":
                return None
            return payload
        except JWTError:
            logger.debug("oauth2.jwt_verify_failed")
            return None

    # ------------------------------------------------------------------

    async def _create_refresh_token(
        self,
        db: AsyncSession,
        *,
        participant_id: uuid.UUID,
        agent_id: uuid.UUID | None = None,
        oauth2_client_id: uuid.UUID | None = None,
    ) -> str:
        """Generate a random refresh token, store its hash, and return the
        raw value (shown once).
        """
        raw = secrets.token_urlsafe(48)
        token_hash = hashlib.sha512(raw.encode()).hexdigest()
        now = datetime.now(UTC)

        record = RefreshToken(
            participant_id=participant_id,
            agent_id=agent_id,
            token_hash=token_hash,
            expires_at=now + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS),
            oauth2_client_id=oauth2_client_id,
            status=RefreshTokenStatus.ACTIVE,
        )
        db.add(record)
        await db.flush()

        return raw
