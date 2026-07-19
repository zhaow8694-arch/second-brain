"""LangChain tool for purchasing AIMart capabilities."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class AIMartPurchaseInput(BaseModel):
    """Input schema for the AIMart purchase tool."""

    item_id: str = Field(
        ...,
        description="UUID of the capability item to purchase.",
    )
    budget_pool_id: str = Field(
        ...,
        description="UUID of the budget pool to charge for this purchase.",
    )
    settlement_channel: str = Field(
        default="fiat",
        description="Settlement channel: 'fiat' for ACP/fiat or 'x402' for crypto micro-payments.",
    )


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------

class AIMartPurchaseTool(BaseTool):
    """LangChain tool that purchases a capability from the AIMart marketplace.

    Use this tool when the agent has decided to buy a capability after
    searching and evaluating it.  The tool calls the AIMart order API
    and returns a formatted confirmation string.

    Example
    -------
    >>> tool = AIMartPurchaseTool(base_url="http://localhost:8080")
    >>> result = tool.invoke({"item_id": "...", "budget_pool_id": "..."})
    """

    name: str = "aimart_purchase"
    description: str = (
        "Purchase a capability from the AIMart marketplace.  Provide the item "
        "ID (from search results), the budget pool ID to charge, and optionally "
        "the settlement channel ('fiat' or 'x402').  Returns an order confirmation "
        "with order ID and status."
    )
    args_schema: type[BaseModel] = AIMartPurchaseInput

    base_url: str = "http://localhost:8080"
    """Base URL of the AIMart API server."""

    def _run(
        self,
        item_id: str,
        budget_pool_id: str,
        settlement_channel: str = "fiat",
    ) -> str:
        """Synchronous purchase – delegates to the async implementation."""
        import asyncio

        coro = self._arun(
            item_id=item_id,
            budget_pool_id=budget_pool_id,
            settlement_channel=settlement_channel,
        )
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return asyncio.run(coro)

    async def _arun(
        self,
        item_id: str,
        budget_pool_id: str,
        settlement_channel: str = "fiat",
    ) -> str:
        """Async purchase via the AIMart /api/v1/exchange/orders endpoint."""
        payload: dict[str, Any] = {
            "item_id": item_id,
            "budget_pool_id": budget_pool_id,
            "settlement_channel": settlement_channel,
        }

        url = f"{self.base_url}/api/v1/exchange/orders"
        logger.info("langchain.purchase_tool", url=url, payload=payload)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("langchain.purchase_tool_error", error=str(exc))
            return f"Error purchasing from AIMart: {exc}"

        return self._format_confirmation(data)

    # -- Formatting ----------------------------------------------------------

    @staticmethod
    def _format_confirmation(data: dict[str, Any]) -> str:
        """Format the order response into a human/LLM-readable string."""
        order_id = data.get("order_id", "N/A")
        status = data.get("status", "unknown")
        item_name = data.get("item_name", "Unknown Item")
        amount = data.get("amount", "N/A")
        currency = data.get("currency", "CNY")

        return (
            f"Order confirmed!\n"
            f"  Order ID: {order_id}\n"
            f"  Item: {item_name}\n"
            f"  Amount: {amount} {currency}\n"
            f"  Status: {status}"
        )
