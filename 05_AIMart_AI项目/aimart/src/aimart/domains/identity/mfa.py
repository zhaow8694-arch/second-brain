from __future__ import annotations

import os
import uuid
from base64 import b64decode, b64encode
from datetime import UTC, datetime, timedelta
from typing import Any

import pyotp
import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.domains.identity.models import (
    MfaChallenge,
    MfaChallengeStatus,
    MfaChallengeType,
    MfaPurpose,
    Participant,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Encryption helpers for TOTP secrets (reuse same AES key as API keys)
# ---------------------------------------------------------------------------

_TOTP_AES_KEY_ENV = "AIMART_TOTP_ENCRYPTION_KEY"


def _get_totp_aes_key() -> bytes:
    b64 = os.environ.get(_TOTP_AES_KEY_ENV)
    if not b64:
        # Fall back to the API key encryption key if separate key not set
        b64 = os.environ.get("AIMART_API_KEY_ENCRYPTION_KEY")
    if not b64:
        raise RuntimeError(
            f"Environment variable {_TOTP_AES_KEY_ENV} (or AIMART_API_KEY_ENCRYPTION_KEY) is not set."
        )
    key = b64decode(b64)
    if len(key) != 32:
        raise ValueError("Encryption key must decode to exactly 32 bytes")
    return key


def _encrypt_totp_secret(plaintext: str) -> str:
    key = _get_totp_aes_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return b64encode(nonce + ct).decode()


def _decrypt_totp_secret(encrypted: str) -> str:
    key = _get_totp_aes_key()
    data = b64decode(encrypted)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()


# ---------------------------------------------------------------------------
# MfaService
# ---------------------------------------------------------------------------

_CHALLENGE_EXPIRY_MINUTES = 5


class MfaService:
    """Handles TOTP setup, challenge creation, and verification."""

    # ------------------------------------------------------------------
    # TOTP setup
    # ------------------------------------------------------------------

    async def setup_totp(
        self,
        db: AsyncSession,
        participant_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Generate a TOTP secret for the participant, store it encrypted,
        and return the provisioning URI plus backup codes.

        The participant must call ``verify_challenge`` with a valid TOTP code
        to confirm the setup before MFA is considered enabled.
        """
        participant = await db.get(Participant, participant_id)
        if participant is None:
            raise ValueError(f"Participant {participant_id} not found")

        # Generate TOTP secret
        secret = pyotp.random_base32()
        encrypted_secret = _encrypt_totp_secret(secret)

        # Store encrypted secret (MFA not yet enabled)
        participant.totp_secret = encrypted_secret
        await db.flush()

        # Build provisioning URI
        totp = pyotp.TOTP(secret)
        issuer = "AIMart"
        qr_url = totp.provisioning_uri(
            name=participant.email,
            issuer_name=issuer,
        )

        # Generate backup codes
        backup_codes = [os.urandom(5).hex() for _ in range(10)]

        # Store backup codes hash (for later verification)
        # TODO: store hashed backup codes in the database for one-time use
        # For now we return them and rely on the participant saving them.

        logger.info(
            "mfa.totp_setup",
            participant_id=str(participant_id),
        )

        return {
            "secret": secret,
            "qr_url": qr_url,
            "backup_codes": backup_codes,
        }

    # ------------------------------------------------------------------
    # Challenge creation
    # ------------------------------------------------------------------

    async def create_challenge(
        self,
        db: AsyncSession,
        *,
        participant_id: uuid.UUID,
        purpose: str,
        reference_id: uuid.UUID | None = None,
        challenge_type: str = "totp",
    ) -> dict[str, Any]:
        """Create an MFA challenge for a high-risk operation.

        Parameters
        ----------
        purpose
            One of: ``agent_terminate``, ``l3_confirm``, ``key_revoke``.
        challenge_type
            One of: ``totp``, ``sms``, ``email``, ``webhook``.
        """
        participant = await db.get(Participant, participant_id)
        if participant is None:
            raise ValueError(f"Participant {participant_id} not found")

        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=_CHALLENGE_EXPIRY_MINUTES)

        challenge = MfaChallenge(
            participant_id=participant_id,
            challenge_type=MfaChallengeType(challenge_type),
            purpose=MfaPurpose(purpose),
            reference_id=reference_id,
            status=MfaChallengeStatus.PENDING,
            attempts=0,
            max_attempts=3,
            expires_at=expires_at,
        )
        db.add(challenge)
        await db.flush()

        # For SMS/email/webhook, send the code out-of-band
        if challenge_type == "sms" and participant.phone:
            # TODO: integrate SMS gateway
            logger.info("mfa.sms_sent", participant_id=str(participant_id))
        elif challenge_type == "email":
            # TODO: integrate email service
            logger.info("mfa.email_sent", participant_id=str(participant_id))
        elif challenge_type == "webhook":
            # TODO: integrate webhook notification
            logger.info("mfa.webhook_sent", participant_id=str(participant_id))

        logger.info(
            "mfa.challenge_created",
            challenge_id=str(challenge.id),
            participant_id=str(participant_id),
            purpose=purpose,
            challenge_type=challenge_type,
        )

        return {
            "challenge_id": str(challenge.id),
            "expires_at": expires_at,
        }

    # ------------------------------------------------------------------
    # Challenge verification
    # ------------------------------------------------------------------

    async def verify_challenge(
        self,
        db: AsyncSession,
        challenge_id: uuid.UUID,
        code: str,
    ) -> tuple[bool, str]:
        """Verify a code against an MFA challenge.

        Returns (verified, message).
        """
        challenge = await db.get(MfaChallenge, challenge_id)
        if challenge is None:
            return False, "Challenge not found"

        now = datetime.now(UTC)

        # Already verified?
        if challenge.status == MfaChallengeStatus.VERIFIED:
            return False, "Challenge already used"

        # Expired?
        if challenge.expires_at < now:
            challenge.status = MfaChallengeStatus.EXPIRED
            await db.flush()
            return False, "Challenge expired"

        # Too many attempts?
        if challenge.attempts >= challenge.max_attempts:
            challenge.status = MfaChallengeStatus.FAILED
            await db.flush()
            return False, "Too many attempts"

        # Increment attempt counter
        challenge.attempts += 1

        # Verify code based on challenge type
        verified = False
        if challenge.challenge_type == MfaChallengeType.TOTP:
            participant = await db.get(Participant, challenge.participant_id)
            if participant and participant.totp_secret:
                verified = self.verify_totp_code(participant.totp_secret, code)
        elif challenge.challenge_type == MfaChallengeType.SMS:
            # TODO: verify against stored SMS code
            verified = False
        elif challenge.challenge_type == MfaChallengeType.EMAIL:
            # TODO: verify against stored email code
            verified = False
        elif challenge.challenge_type == MfaChallengeType.WEBHOOK:
            # TODO: verify against webhook challenge response
            verified = False

        if verified:
            challenge.status = MfaChallengeStatus.VERIFIED
            challenge.verified_at = now
            await db.flush()

            # If this was a TOTP verification for MFA setup, enable MFA
            participant = await db.get(Participant, challenge.participant_id)
            if participant and not participant.mfa_enabled and participant.totp_secret:
                participant.mfa_enabled = True
                await db.flush()

            logger.info(
                "mfa.challenge_verified",
                challenge_id=str(challenge_id),
                participant_id=str(challenge.participant_id),
            )
            return True, "MFA verification successful"
        else:
            remaining = challenge.max_attempts - challenge.attempts
            await db.flush()
            logger.warning(
                "mfa.challenge_failed",
                challenge_id=str(challenge_id),
                attempts=challenge.attempts,
            )
            return False, f"Invalid code. {remaining} attempt(s) remaining"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def verify_totp_code(self, encrypted_secret: str, code: str) -> bool:
        """Verify a 6-digit TOTP code against an encrypted secret.

        This is the stateless verification method that callers should use.
        """
        try:
            secret = _decrypt_totp_secret(encrypted_secret)
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)
        except Exception:
            logger.warning("mfa.totp_verify_error")
            return False
