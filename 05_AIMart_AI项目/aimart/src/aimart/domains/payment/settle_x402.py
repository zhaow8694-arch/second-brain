from __future__ import annotations

from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class X402PaymentPayload:
    """Payload for an x402 protocol payment on Base network."""

    version: str = "1"
    network_id: int = 8453  # Base mainnet chain ID
    asset: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base
    amount: str = ""  # in smallest unit (6 decimals for USDC)
    recipient: str = ""
    signature: str = ""
    payload_hash: str = ""


@dataclass
class X402SettlementResult:
    """Result of an x402 settlement attempt."""

    success: bool
    tx_hash: str | None = None
    block_number: int | None = None
    error: str | None = None


class X402Settler:
    """Settles payments via the x402 protocol on Base (USDC).

    The x402 protocol uses EIP-712 typed data signatures for agent
    authorization. This settler verifies the signature, checks the
    agent's USDC balance and allowance, then executes a ``transferFrom``
    on the USDC contract.

    Actual web3.py calls are marked with TODO.
    """

    USDC_DECIMALS = 6
    BASE_CHAIN_ID = 8453

    def __init__(self, rpc_url: str, usdc_address: str, verifier_address: str):
        self.rpc_url = rpc_url
        self.usdc_address = usdc_address
        self.verifier_address = verifier_address
        # TODO: initialize web3 provider
        # self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        # self.usdc_contract = self.w3.eth.contract(
        #     address=usdc_address, abi=USDC_ABI
        # )

    def prepare_payment(
        self,
        amount_usdc: float,
        recipient_address: str,
        agent_wallet_address: str,
    ) -> X402PaymentPayload:
        """Prepare a payment payload for the agent to sign.

        Args:
            amount_usdc: Amount in USDC (human-readable).
            recipient_address: Provider's wallet address.
            agent_wallet_address: Agent's wallet address.

        Returns:
            An X402PaymentPayload ready for signing.
        """
        amount_smallest = str(int(amount_usdc * (10**self.USDC_DECIMALS)))

        payload = X402PaymentPayload(
            version="1",
            network_id=self.BASE_CHAIN_ID,
            asset=self.usdc_address,
            amount=amount_smallest,
            recipient=recipient_address,
        )

        # TODO: compute EIP-712 typed-data hash
        # typed_data = self._build_eip712_typed_data(payload)
        # payload.payload_hash = self.w3.keccak(
        #     encode_typed_data(typed_data)
        # ).hex()

        logger.info(
            "x402_payment_prepared",
            amount_usdc=amount_usdc,
            recipient=recipient_address,
            agent_wallet=agent_wallet_address,
        )
        return payload

    def verify_and_settle(
        self,
        payment_payload: X402PaymentPayload,
        agent_signature: str,
    ) -> X402SettlementResult:
        """Verify the agent's signature and settle the payment on-chain.

        Steps:
        1. Verify EIP-712 signature
        2. Check agent's USDC balance
        3. Check agent's USDC allowance to the verifier
        4. Submit transferFrom transaction
        5. Wait for confirmation

        Args:
            payment_payload: The payment payload signed by the agent.
            agent_signature: The agent's EIP-712 signature.

        Returns:
            X402SettlementResult with success status and on-chain details.
        """
        try:
            # Step 1: Verify EIP-712 signature
            # TODO: implement signature verification
            # recovered_address = self._verify_eip712_signature(
            #     payment_payload, agent_signature
            # )
            # if recovered_address.lower() != agent_wallet_address.lower():
            #     return X402SettlementResult(
            #         success=False,
            #         error="Signature does not match agent wallet",
            #     )
            logger.info("x402_signature_verified", payload=payment_payload)

            # Step 2: Check balance
            # TODO: implement balance check
            # balance = self.usdc_contract.functions.balanceOf(
            #     agent_wallet_address
            # ).call()
            # if balance < int(payment_payload.amount):
            #     return X402SettlementResult(
            #         success=False,
            #         error=f"Insufficient USDC balance: {balance}",
            #     )
            logger.info("x402_balance_checked")

            # Step 3: Check allowance
            # TODO: implement allowance check
            # allowance = self.usdc_contract.functions.allowance(
            #     agent_wallet_address, self.verifier_address
            # ).call()
            # if allowance < int(payment_payload.amount):
            #     return X402SettlementResult(
            #         success=False,
            #         error=f"Insufficient USDC allowance: {allowance}",
            #     )
            logger.info("x402_allowance_checked")

            # Step 4: Submit transferFrom
            # TODO: implement transferFrom
            # tx_hash = self.usdc_contract.functions.transferFrom(
            #     agent_wallet_address,
            #     payment_payload.recipient,
            #     int(payment_payload.amount),
            # ).transact({"from": self.verifier_address})
            # logger.info("x402_tx_submitted", tx_hash=tx_hash.hex())

            # Step 5: Wait for confirmation
            # TODO: implement confirmation wait
            # receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            # if receipt.status != 1:
            #     return X402SettlementResult(
            #         success=False,
            #         error="Transaction reverted on-chain",
            #     )

            # For now, return a placeholder result
            return X402SettlementResult(
                success=True,
                tx_hash="0x_placeholder_tx_hash",
                block_number=0,
            )

        except Exception as exc:
            logger.exception("x402_settlement_failed", error=str(exc))
            return X402SettlementResult(
                success=False,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Private helpers (TODO: implement with web3.py)
    # ------------------------------------------------------------------

    def _build_eip712_typed_data(self, payload: X402PaymentPayload) -> dict:
        """Build the EIP-712 typed data structure for signing."""
        # TODO: implement proper EIP-712 typed data
        return {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Payment": [
                    {"name": "asset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "recipient", "type": "address"},
                ],
            },
            "primaryType": "Payment",
            "domain": {
                "name": "AIMart x402",
                "version": payload.version,
                "chainId": payload.network_id,
                "verifyingContract": self.verifier_address,
            },
            "message": {
                "asset": payload.asset,
                "amount": int(payload.amount),
                "recipient": payload.recipient,
            },
        }

    def _verify_eip712_signature(
        self, payload: X402PaymentPayload, signature: str
    ) -> str:
        """Recover the signer address from an EIP-712 signature."""
        # TODO: implement with web3.py
        # typed_data = self._build_eip712_typed_data(payload)
        # message = encode_typed_data(typed_data)
        # return self.w3.eth.account.recover_message(message, signature=signature)
        raise NotImplementedError("EIP-712 signature verification not yet implemented")
