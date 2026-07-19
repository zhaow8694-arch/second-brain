from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from base64 import b64decode, b64encode
from datetime import UTC, datetime
from typing import Any

import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.domains.identity.models import (
    ApiKey,
    ApiKeyStatus,
    ParticipantType,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Key prefix constants – 6-char prefix identifies participant type at a glance
# ---------------------------------------------------------------------------

class KeyPrefix:
    OWNER = "aim_o_"
    PROVIDER = "aim_p_"
    AGENT = "aim_a_"
    FACILITATOR = "aim_f_"

    _MAP: dict[str, str] = {
        ParticipantType.OWNER.value: OWNER,
        ParticipantType.PROVIDER.value: PROVIDER,
        ParticipantType.CERTIFIER.value: OWNER,  # certifiers share owner prefix
        ParticipantType.FACILITATOR.value: FACILITATOR,
    }

    @classmethod
    def for_type(cls, participant_type: str, is_agent: bool = False) -> str:
        if is_agent:
            return cls.AGENT
        return cls._MAP.get(participant_type, cls.OWNER)


# ---------------------------------------------------------------------------
# Default scopes per participant / agent type
# ---------------------------------------------------------------------------

DEFAULT_SCOPES: dict[str, list[str]] = {
    ParticipantType.OWNER.value: [
        "agent:manage",
        "budget:manage",
        "catalog:read",
        "audit:read",
    ],
    ParticipantType.PROVIDER.value: [
        "catalog:publish",
        "catalog:read",
        "exchange:read",
        "audit:read",
    ],
    ParticipantType.CERTIFIER.value: [
        "catalog:certify",
        "catalog:read",
        "audit:read",
    ],
    ParticipantType.FACILITATOR.value: [
        "exchange:facilitate",
        "catalog:read",
        "audit:read",
        "admin:read",
    ],
    "agent": [
        "catalog:search",
        "catalog:read",
        "exchange:trade",
        "exchange:trial",
    ],
}

# ---------------------------------------------------------------------------
# AES-256-GCM encryption helpers
# ---------------------------------------------------------------------------

_AES_KEY_ENV = "AIMART_API_KEY_ENCRYPTION_KEY"


def _get_aes_key() -> bytes:
    """Load the 256-bit AES key from the environment.

    Expects the key to be stored as URL-safe base64 in the
    ``AIMART_API_KEY_ENCRYPTION_KEY`` environment variable.
    """
    b64 = os.environ.get(_AES_KEY_ENV)
    if not b64:
        gen_cmd = (
            'python -c "import os,base64; '
            'print(base64.urlsafe_b64encode(os.urandom(32)).decode())"'
        )
        raise RuntimeError(
            f"Environment variable {_AES_KEY_ENV} is not set. "
            f"Generate one with: {gen_cmd}"
        )
    key = b64decode(b64)
    if len(key) != 32:
        raise ValueError(f"{_AES_KEY_ENV} must decode to exactly 32 bytes (256 bits)")
    return key


def _encrypt_key(raw: str) -> str:
    """Encrypt *raw* with AES-256-GCM; return ``nonce:ciphertext`` base64."""
    key = _get_aes_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, raw.encode(), None)
    return b64encode(nonce + ct).decode()


def _decrypt_key(encrypted: str) -> str:
    """Decrypt an AES-256-GCM encrypted key produced by :func:`_encrypt_key`."""
    key = _get_aes_key()
    data = b64decode(encrypted)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()


# ---------------------------------------------------------------------------
# ApiKeyManager
# ---------------------------------------------------------------------------

class ApiKeyManager:
    """Stateless helper; each method accepts a db session explicitly so the
    manager can be reused across requests.
    """

    async def generate(
        self,
        db: AsyncSession,
        *,
        participant_id: uuid.UUID,
        participant_type: str,
        agent_id: uuid.UUID | None = None,
        scopes: list[str] | None = None,
        permissions: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
        allowed_ips: list[str] | None = None,
        allowed_origins: list[str] | None = None,
    ) -> tuple[str, ApiKey]:
        """Generate a new API key and persist its metadata.

        Returns
        -------
        (raw_key, api_key_record)
            *raw_key* is the full key string shown to the caller exactly once.
        """
        is_agent = agent_id is not None
        prefix = KeyPrefix.for_type(participant_type, is_agent=is_agent)
        token = secrets.token_urlsafe(32)
        raw_key = f"{prefix}{token}"

        key_hash = hashlib.sha512(raw_key.encode()).hexdigest()
        key_encrypted = _encrypt_key(raw_key)
        key_prefix = raw_key[:8]

        resolved_scopes = scopes or DEFAULT_SCOPES.get(
            "agent" if is_agent else participant_type,
            [],
        )
        resolved_permissions = permissions or {}

        record = ApiKey(
            participant_id=participant_id,
            agent_id=agent_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            key_encrypted=key_encrypted,
            scopes=resolved_scopes,
            permissions=resolved_permissions,
            expires_at=expires_at,
            allowed_ips=allowed_ips,
            allowed_origins=allowed_origins,
            status=ApiKeyStatus.ACTIVE,
        )
        db.add(record)
        await db.flush()

        logger.info(
            "api_key.generated",
            key_id=str(record.id),
            participant_id=str(participant_id),
            agent_id=str(agent_id) if agent_id else None,
            prefix=key_prefix,
        )
        return raw_key, record

    # ------------------------------------------------------------------

    async def verify(self, raw_key: str) -> dict[str, Any] | None:
        """Verify a raw API key against the database.

        Returns a dict with key metadata or ``None`` if the key is invalid,
        revoked, or expired.
        """
        # We need an async session; this method relies on the session
        # being injected via the db dependency in the caller context.
        # For the auth dependency we perform a lazy import to get the
        # session factory.
        from aimart.db.session import async_session_factory

        if async_session_factory is None:
            logger.error("async_session_factory_not_initialized")
            return None

        prefix = raw_key[:8]
        candidate_hash = hashlib.sha512(raw_key.encode()).hexdigest()

        async with async_session_factory() as db:
            stmt = select(ApiKey).where(
                ApiKey.key_prefix == prefix,
                ApiKey.key_hash == candidate_hash,
                ApiKey.status == ApiKeyStatus.ACTIVE,
            )
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()

        if record is None:
            logger.warning("api_key.verify_failed", prefix=prefix, reason="not_found")
            return None

        now = datetime.now(UTC)

        # Expiry check
        if record.expires_at and record.expires_at < now:
            logger.warning("api_key.verify_failed", prefix=prefix, reason="expired")
            return None

        # IP whitelist
        if record.allowed_ips:
            # IP check is done by the caller who has the request context
            pass

        # Update usage stats
        assert async_session_factory is not None
        async with async_session_factory() as db:
            db_key = await db.get(ApiKey, record.id)
            if db_key is None:
                return None
            db_key.last_used_at = now
            db_key.use_count += 1
            await db.commit()

        # Build info dict
        participant_type = ""
        if record.participant_id:
            from aimart.domains.identity.models import Participant

            assert async_session_factory is not None
            async with async_session_factory() as db:
                p = await db.get(Participant, record.participant_id)
                if p:
                    participant_type = p.type.value

        return {
            "key_id": str(record.id),
            "participant_id": str(record.participant_id),
            "participant_type": participant_type,
            "agent_id": str(record.agent_id) if record.agent_id else None,
            "scopes": record.scopes or [],
            "permissions": record.permissions or {},
            "allowed_ips": record.allowed_ips or [],
            "allowed_origins": record.allowed_origins or [],
        }

    # ------------------------------------------------------------------

    async def revoke(
        self,
        db: AsyncSession,
        key_id: uuid.UUID,
        revoked_by: uuid.UUID,
        reason: str | None = None,
    ) -> None:
        """Revoke an API key by its record id."""
        record = await db.get(ApiKey, key_id)
        if record is None:
            raise ValueError(f"API key {key_id} not found")
        if record.status != ApiKeyStatus.ACTIVE:
            raise ValueError(f"API key {key_id} is already {record.status.value}")

        record.status = ApiKeyStatus.REVOKED
        record.revoked_at = datetime.now(UTC)
        record.revoke_reason = reason
        await db.flush()

        logger.info(
            "api_key.revoked",
            key_id=str(key_id),
            revoked_by=str(revoked_by),
            reason=reason,
        )

    # ------------------------------------------------------------------

    async def revoke_all_for_agent(
        self,
        db: AsyncSession,
        agent_id: uuid.UUID,
        reason: str = "agent_terminated",
    ) -> int:
        """Revoke all active API keys belonging to an agent. Returns count."""
        stmt = select(ApiKey).where(
            ApiKey.agent_id == agent_id,
            ApiKey.status == ApiKeyStatus.ACTIVE,
        )
        result = await db.execute(stmt)
        keys = result.scalars().all()

        now = datetime.now(UTC)
        for k in keys:
            k.status = ApiKeyStatus.REVOKED
            k.revoked_at = now
            k.revoke_reason = reason
        await db.flush()

        logger.info(
            "api_key.revoke_all_for_agent",
            agent_id=str(agent_id),
            count=len(keys),
        )
        return len(keys)
