"""CrewAI tool provider that exposes AIMart search and purchase as CrewAI tools."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class AIMartCapabilityProvider:
    """CrewAI tool provider that exposes AIMart search and purchase as CrewAI tools.

    This provider wraps the AIMart REST API so that CrewAI agents can search
    for capabilities and purchase them without having to construct HTTP
    requests themselves.

    Example
    -------
    >>> provider = AIMartCapabilityProvider(base_url="http://localhost:8080")
    >>> results = provider.search_capability(need_type="model", domains=["legal"])
    >>> order = provider.purchase_capability(item_id="item-uuid-001")
    """

    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        self.base_url = base_url.rstrip("/")

    # -- Search --------------------------------------------------------------

    async def search_capability(
        self,
        need_type: str,
        domains: list[str],
        task_description: str | None = None,
        max_price: float | None = None,
        min_trust_score: int | None = None,
    ) -> str:
        """Search for capabilities on the AIMart marketplace.

        Parameters
        ----------
        need_type:
            Type of capability: ``model``, ``skill``, ``expert``, or ``compute``.
        domains:
            Domain tags to filter by.
        task_description:
            Optional free-text task description.
        max_price:
            Optional maximum price filter.
        min_trust_score:
            Optional minimum trust score filter (0-100).

        Returns
        -------
        str
            Formatted search results suitable for CrewAI agent consumption.
        """
        payload: dict[str, Any] = {
            "need_type": need_type,
            "domains": domains,
        }
        if task_description:
            payload["task_description"] = task_description
        if max_price is not None:
            payload["max_price"] = max_price
        if min_trust_score is not None:
            payload["min_trust_score"] = min_trust_score

        url = f"{self.base_url}/api/v1/search/capability"
        logger.info("crewai.search_capability", url=url, payload=payload)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("crewai.search_error", error=str(exc))
            return f"Error searching AIMart: {exc}"

        return self._format_search_results(data)

    # -- Purchase ------------------------------------------------------------

    async def purchase_capability(
        self,
        item_id: str,
        budget_pool_id: str | None = None,
        settlement_channel: str = "fiat",
    ) -> str:
        """Purchase a capability from the AIMart marketplace.

        Parameters
        ----------
        item_id:
            UUID of the capability item to purchase.
        budget_pool_id:
            UUID of the budget pool to charge.  If not provided the agent's
            default budget pool is used.
        settlement_channel:
            Settlement channel: ``fiat`` (ACP) or ``x402`` (crypto).

        Returns
        -------
        str
            Formatted order confirmation suitable for CrewAI agent consumption.
        """
        payload: dict[str, Any] = {
            "item_id": item_id,
            "settlement_channel": settlement_channel,
        }
        if budget_pool_id:
            payload["budget_pool_id"] = budget_pool_id

        url = f"{self.base_url}/api/v1/exchange/orders"
        logger.info("crewai.purchase_capability", url=url, payload=payload)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("crewai.purchase_error", error=str(exc))
            return f"Error purchasing from AIMart: {exc}"

        return self._format_purchase_confirmation(data)

    # -- Formatting helpers --------------------------------------------------

    @staticmethod
    def _format_search_results(data: dict[str, Any]) -> str:
        """Format the search API response for CrewAI agent consumption."""
        matches = data.get("matches", [])
        if not matches:
            return "No matching capabilities found on AIMart."

        lines: list[str] = [f"Found {len(matches)} matching capabilities on AIMart:\n"]
        for idx, item in enumerate(matches, 1):
            name = item.get("item_name", "Unknown")
            item_type = item.get("item_type", "unknown")
            provider = item.get("provider_name", "Unknown")
            trust = item.get("trust_score", "N/A")
            price = item.get("pricing_summary", "N/A")
            item_id = item.get("item_id", "N/A")

            lines.append(
                f"{idx}. [{item_type}] {name} by {provider}\n"
                f"   ID: {item_id} | Trust: {trust} | Price: {price}"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_purchase_confirmation(data: dict[str, Any]) -> str:
        """Format the order confirmation for CrewAI agent consumption."""
        order_id = data.get("order_id", "N/A")
        status = data.get("status", "unknown")
        item_name = data.get("item_name", "Unknown Item")
        amount = data.get("amount", "N/A")
        currency = data.get("currency", "CNY")

        return (
            f"AIMart Purchase Confirmed\n"
            f"  Order ID: {order_id}\n"
            f"  Item: {item_name}\n"
            f"  Amount: {amount} {currency}\n"
            f"  Status: {status}"
        )
