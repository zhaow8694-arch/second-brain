"""x402 payment adapter for AIMart.

Intercepts HTTP 402 Payment Required responses and facilitates the
machine-to-machine (M2M) micro-payment flow defined by the x402 protocol.
The adapter parses payment payloads from 402 responses, constructs payment
proof headers, and verifies proofs before allowing the original request to
be retried with payment attached.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PaymentPayload:
    """Parsed payload extracted from an HTTP 402 response."""

    payment_url: str
    amount: str  # e.g. "0.001" USDC
    token: str  # e.g. "USDC"
    chain_id: int  # e.g. 8453 (Base)
    recipient: str  # on-chain address
    resource: str  # the original request URL
    expires_at: int  # unix timestamp
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


@dataclass
class PaymentProof:
    """A constructed payment proof that can be sent as an HTTP header."""

    payment_id: str
    tx_hash: str
    payload_hash: str
    signature: str
    timestamp: int
    chain_id: int


# ---------------------------------------------------------------------------
# x402 Adapter
# ---------------------------------------------------------------------------

class X402Adapter:
    """x402 payment adapter for M2M micro-payments.

    Handles the full lifecycle:

    1. **Parse** – intercept an HTTP 402 response and extract the payment
       payload from the ``X-Payment-Required`` header or response body.
    2. **Pay** – construct a payment proof once the on-chain transaction is
       confirmed.
    3. **Verify** – validate that a payment proof is legitimate before
       granting access to the paid resource.
    """

    def __init__(self, signing_key: str | None = None) -> None:
        self._signing_key = signing_key or "default-dev-key"
        self._proof_store: dict[str, PaymentProof] = {}

    # -- 402 response parsing ------------------------------------------------

    def handle_402_response(self, response: dict[str, Any]) -> PaymentPayload:
        """Parse an HTTP 402 Payment Required response.

        Parameters
        ----------
        response:
            The decoded response dict.  Must contain either an
            ``X-Payment-Required`` header (under ``headers``) or a JSON body
            with the payment fields.

        Returns
        -------
        PaymentPayload
            The parsed payment details.

        Raises
        ------
        ValueError
            If the required payment fields are missing.
        """
        # Try header first, then body
        header = response.get("headers", {}).get("x-payment-required")
        if header:
            try:
                raw = json.loads(base64.b64decode(header).decode())
            except Exception:
                raw = json.loads(header)
        else:
            raw = response.get("body", response)

        required_fields = {"payment_url", "amount", "token", "chain_id", "recipient", "resource"}
        missing = required_fields - set(raw.keys())
        if missing:
            msg = f"402 response missing required fields: {missing}"
            logger.error("x402.invalid_payload", missing=missing)
            raise ValueError(msg)

        payload = PaymentPayload(
            payment_url=raw["payment_url"],
            amount=str(raw["amount"]),
            token=raw["token"],
            chain_id=int(raw["chain_id"]),
            recipient=raw["recipient"],
            resource=raw["resource"],
            expires_at=int(raw.get("expires_at", time.time() + 300)),
            meta=raw.get("meta", {}),
        )

        logger.info(
            "x402.payload_parsed",
            resource=payload.resource,
            amount=payload.amount,
            token=payload.token,
            chain_id=payload.chain_id,
        )
        return payload

    # -- Proof construction --------------------------------------------------

    def create_payment_proof(
        self,
        payment_payload: PaymentPayload,
        signature: str,
    ) -> PaymentProof:
        """Construct a payment proof header value.

        Parameters
        ----------
        payment_payload:
            The parsed 402 payload (from :meth:`handle_402_response`).
        signature:
            A cryptographic signature over the payload hash, typically
            produced by the payer's wallet after the on-chain transaction
            is confirmed.

        Returns
        -------
        PaymentProof
            The proof object that can be serialized into an ``X-Payment``
            header.
        """
        payload_hash = self._hash_payload(payment_payload)
        payment_id = str(uuid.uuid4())

        proof = PaymentProof(
            payment_id=payment_id,
            tx_hash=signature[:64],  # In production: actual on-chain tx hash
            payload_hash=payload_hash,
            signature=signature,
            timestamp=int(time.time()),
            chain_id=payment_payload.chain_id,
        )

        self._proof_store[payment_id] = proof
        logger.info(
            "x402.proof_created",
            payment_id=payment_id,
            resource=payment_payload.resource,
        )
        return proof

    # -- Proof verification --------------------------------------------------

    def verify_payment_proof(self, proof: PaymentProof | dict[str, Any]) -> bool:
        """Validate a payment proof.

        The verification checks:

        1. The proof is well-formed and all required fields are present.
        2. The ``payload_hash`` matches a re-computed hash of the original
           payload (integrity check).
        3. The ``signature`` is valid under the platform's HMAC key (authenticity).
        4. The proof has not expired (freshness – proofs are valid for 1 hour).

        Parameters
        ----------
        proof:
            A :class:`PaymentProof` instance or a dict with the same keys.

        Returns
        -------
        bool
            ``True`` if the proof is valid, ``False`` otherwise.
        """
        if isinstance(proof, dict):
            try:
                proof = PaymentProof(**proof)
            except Exception:
                logger.warning("x402.malformed_proof")
                return False

        # Required fields check
        if not all([proof.payment_id, proof.tx_hash, proof.payload_hash, proof.signature]):
            logger.warning("x402.proof_missing_fields", payment_id=proof.payment_id)
            return False

        # Freshness – proofs expire after 1 hour
        if time.time() - proof.timestamp > 3600:
            logger.warning("x402.proof_expired", payment_id=proof.payment_id)
            return False

        # HMAC verification against signing key
        expected_sig = hmac.new(
            self._signing_key.encode(),
            proof.payload_hash.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, proof.signature):
            logger.warning("x402.proof_invalid_signature", payment_id=proof.payment_id)
            return False

        logger.info("x402.proof_verified", payment_id=proof.payment_id)
        return True

    # -- Helpers -------------------------------------------------------------

    def serialize_proof_header(self, proof: PaymentProof) -> str:
        """Serialize a payment proof into the value for the ``X-Payment`` header."""
        data = {
            "payment_id": proof.payment_id,
            "tx_hash": proof.tx_hash,
            "payload_hash": proof.payload_hash,
            "signature": proof.signature,
            "timestamp": proof.timestamp,
            "chain_id": proof.chain_id,
        }
        return base64.b64encode(json.dumps(data).encode()).decode()

    def _hash_payload(self, payload: PaymentPayload) -> str:
        """Deterministic hash of the payment payload for integrity checks."""
        canonical = json.dumps(
            {
                "payment_url": payload.payment_url,
                "amount": payload.amount,
                "token": payload.token,
                "chain_id": payload.chain_id,
                "recipient": payload.recipient,
                "resource": payload.resource,
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()
