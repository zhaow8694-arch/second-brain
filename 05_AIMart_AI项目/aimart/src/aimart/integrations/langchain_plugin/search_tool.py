"""LangChain tool for searching AIMart capabilities."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class AIMartSearchInput(BaseModel):
    """Input schema for the AIMart capability search tool."""

    need_type: str = Field(
        ...,
        description="Type of capability needed: model, skill, expert, or compute.",
    )
    domains: list[str] = Field(
        ...,
        description="Domain tags to filter by, e.g. ['legal', 'nlp', 'finance'].",
    )
    task_description: str | None = Field(
        default=None,
        description="Free-text description of the task the capability should accomplish.",
    )
    max_price: float | None = Field(
        default=None,
        description="Maximum acceptable price per call/token/hour.",
    )
    min_trust_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum trust score (0-100) for returned results.",
    )


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------

class AIMartSearchTool(BaseTool):
    """LangChain tool that searches the AIMart capability marketplace.

    Use this tool when the agent needs to find an AI capability (model, skill,
    expert, or compute) to accomplish a task.  The tool calls the AIMart
    search API and returns a formatted string suitable for LLM consumption.

    Example
    -------
    >>> tool = AIMartSearchTool(base_url="http://localhost:8080")
    >>> result = tool.invoke({"need_type": "model", "domains": ["legal"]})
    """

    name: str = "aimart_capability_search"
    description: str = (
        "Search the AIMart marketplace for AI capabilities (models, skills, "
        "experts, compute) that match a given need.  Provide the capability "
        "type, domain tags, and optionally a task description, max price, and "
        "minimum trust score.  Returns a formatted list of matching capabilities "
        "with pricing and trust information."
    )
    args_schema: type[BaseModel] = AIMartSearchInput

    base_url: str = "http://localhost:8080"
    """Base URL of the AIMart API server."""

    def _run(
        self,
        need_type: str,
        domains: list[str],
        task_description: str | None = None,
        max_price: float | None = None,
        min_trust_score: int | None = None,
    ) -> str:
        """Synchronous search – delegates to the async implementation."""
        import asyncio

        coro = self._arun(
            need_type=need_type,
            domains=domains,
            task_description=task_description,
            max_price=max_price,
            min_trust_score=min_trust_score,
        )
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an existing event loop (e.g. a Jupyter notebook).
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return asyncio.run(coro)

    async def _arun(
        self,
        need_type: str,
        domains: list[str],
        task_description: str | None = None,
        max_price: float | None = None,
        min_trust_score: int | None = None,
    ) -> str:
        """Async search against the AIMart /api/v1/search/capability endpoint."""
        payload: dict[str, Any] = {
            "need_type": need_type,
            "domains": domains,
        }
        if task_description is not None:
            payload["task_description"] = task_description
        if max_price is not None:
            payload["max_price"] = max_price
        if min_trust_score is not None:
            payload["min_trust_score"] = min_trust_score

        url = f"{self.base_url}/api/v1/search/capability"
        logger.info("langchain.search_tool", url=url, payload=payload)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("langchain.search_tool_error", error=str(exc))
            return f"Error searching AIMart: {exc}"

        return self._format_results(data)

    # -- Formatting ----------------------------------------------------------

    @staticmethod
    def _format_results(data: dict[str, Any]) -> str:
        """Format the search API response into a human/LLM-readable string."""
        matches = data.get("matches", [])
        if not matches:
            return "No matching capabilities found on AIMart."

        lines: list[str] = [f"Found {len(matches)} matching capabilities:\n"]
        for idx, item in enumerate(matches, 1):
            name = item.get("item_name", "Unknown")
            item_type = item.get("item_type", "unknown")
            provider = item.get("provider_name", "Unknown")
            trust = item.get("trust_score", "N/A")
            price = item.get("pricing_summary", "N/A")
            score = item.get("match_score", "N/A")

            lines.append(
                f"{idx}. {name} ({item_type}) by {provider}\n"
                f"   Trust: {trust} | Price: {price} | Match: {score}"
            )

        return "\n".join(lines)
