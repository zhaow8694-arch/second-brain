"""MCP (Model Context Protocol) Gateway for AIMart.

Provides an MCP-compatible SSE endpoint that exposes AIMart marketplace
capabilities as MCP tools.  Any MCP-compatible AI agent can discover,
search, purchase and manage orders through this gateway.

Transport: SSE (Server-Sent Events) as specified by the MCP spec.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import structlog
from mcp.server import NotificationOptions, Server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route

from aimart.config import get_settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions (MCP Tool schema with strict JSON Schema)
# ---------------------------------------------------------------------------

AIMART_TOOLS: list[Tool] = [
    Tool(
        name="aimart_search",
        description=(
            "Search the AIMart capability marketplace for AI models, skills, "
            "experts, or compute resources that match a given capability need. "
            "Returns a ranked list of matching capabilities with pricing, "
            "trust scores, and five-dimensional scoring breakdown."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "need_type": {
                    "type": "string",
                    "enum": ["model", "skill", "expert", "compute"],
                    "description": "Type of capability needed.",
                },
                "domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "Domain categories to search in (e.g. ['legal', 'nlp']).",
                },
                "task_description": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Free-text description of the task to accomplish.",
                },
                "max_price": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Maximum acceptable price per call/token/hour.",
                },
                "min_trust_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Minimum trust score (0-100).",
                },
            },
            "required": ["need_type", "domains"],
        },
    ),
    Tool(
        name="aimart_purchase",
        description=(
            "Purchase a capability from the AIMart marketplace. Creates an "
            "order, links a budget pool, and initiates the selected settlement "
            "channel. Returns the order ID and current status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the capability item to purchase.",
                },
                "budget_pool_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the budget pool to charge.",
                },
                "settlement_channel": {
                    "type": "string",
                    "enum": ["fiat", "x402", "acp"],
                    "description": "Settlement channel for the transaction.",
                    "default": "fiat",
                },
                "quantity": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Number of units to purchase (default 1).",
                    "default": 1,
                },
            },
            "required": ["item_id", "budget_pool_id"],
        },
    ),
    Tool(
        name="aimart_check_order",
        description=(
            "Check the status and full details of an existing order by its "
            "UUID. Returns order status, pricing, timestamps, and related "
            "transaction and trial IDs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "UUID of the order to check.",
                },
            },
            "required": ["order_id"],
        },
    ),
    Tool(
        name="aimart_list_skills",
        description=(
            "List all currently available skill-type catalog items from the "
            "AIMart marketplace. Skills are AI capabilities that perform "
            "specific tasks. Returns name, version, provider, pricing, and "
            "trust score for each skill."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1,
                    "description": "Page number for pagination.",
                },
                "size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 20,
                    "description": "Number of items per page.",
                },
                "min_trust_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Minimum trust score filter.",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="aimart_list_models",
        description=(
            "List all currently available model-type catalog items from the "
            "AIMart marketplace. Models are AI/ML model endpoints. Returns "
            "name, version, provider, pricing, and trust score for each model."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1,
                    "description": "Page number for pagination.",
                },
                "size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 20,
                    "description": "Number of items per page.",
                },
                "min_trust_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Minimum trust score filter.",
                },
            },
            "required": [],
        },
    ),
]

# ---------------------------------------------------------------------------
# Internal API client
# ---------------------------------------------------------------------------

_API_BASE: str = ""


async def _api_url() -> str:
    """Return the base URL for internal API calls."""
    global _API_BASE
    if not _API_BASE:
        _ = get_settings()
        _API_BASE = "http://localhost:8000/api/v1"
    return _API_BASE


async def _api_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make an internal GET request to the AIMart API."""
    url = f"{await _api_url()}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def _api_post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    """Make an internal POST request to the AIMart API."""
    url = f"{await _api_url()}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Tool handler implementations
# ---------------------------------------------------------------------------

async def _handle_search(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle aimart_search tool call."""
    logger.info("mcp.search", args=arguments)
    try:
        body = {
            "need_type": arguments["need_type"],
            "domains": arguments["domains"],
        }
        if "task_description" in arguments:
            body["task_description"] = arguments["task_description"]
        if "max_price" in arguments:
            body["budget"] = {"max_price_per_call": arguments["max_price"]}
        if "min_trust_score" in arguments:
            body["trust"] = {"min_trust_score": arguments["min_trust_score"]}

        result = await _api_post("/search/capability", body)
        return {
            "query_id": str(result.get("query_id", "")),
            "total_matches": result.get("total_matches", 0),
            "items": [
                {
                    "item_id": str(item["item_id"]),
                    "item_name": item["item_name"],
                    "item_type": item["item_type"],
                    "provider_name": item["provider_name"],
                    "trust_score": item["trust_score"],
                    "composite_score": item["scores"]["composite"],
                    "trial_available": item.get("trial_available", False),
                }
                for item in result.get("items", [])
            ],
        }
    except Exception as exc:
        logger.error("mcp.search_failed", error=str(exc))
        return {"error": str(exc), "total_matches": 0, "items": []}


async def _handle_purchase(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle aimart_purchase tool call."""
    logger.info("mcp.purchase", args=arguments)
    try:
        body = {
            "item_id": arguments["item_id"],
            "quantity": arguments.get("quantity", 1),
            "budget_pool_id": arguments["budget_pool_id"],
            "settlement_channel": arguments.get("settlement_channel", "fiat"),
        }
        result = await _api_post("/exchange/orders", body)
        return {
            "order_id": str(result.get("id", "")),
            "status": result.get("status", ""),
            "amount": str(result.get("amount", "")),
            "currency": result.get("currency", ""),
            "created_at": result.get("created_at", ""),
        }
    except Exception as exc:
        logger.error("mcp.purchase_failed", error=str(exc))
        return {"error": str(exc)}


async def _handle_check_order(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle aimart_check_order tool call."""
    logger.info("mcp.check_order", args=arguments)
    order_id = arguments["order_id"]
    try:
        result = await _api_get(f"/exchange/orders/{order_id}")
        return {
            "order_id": str(result.get("id", "")),
            "item_id": str(result.get("item_id", "")),
            "item_name": result.get("item_name", ""),
            "item_type": result.get("item_type", ""),
            "status": result.get("status", ""),
            "amount": str(result.get("amount", "")),
            "currency": result.get("currency", ""),
            "quantity": result.get("quantity", 0),
            "created_at": result.get("created_at", ""),
            "delivered_at": result.get("delivered_at"),
            "completed_at": result.get("completed_at"),
            "cancelled_at": result.get("cancelled_at"),
            "cancel_reason": result.get("cancel_reason"),
            "payment_transaction_id": (
                str(result["payment_transaction_id"])
                if result.get("payment_transaction_id")
                else None
            ),
            "trial_id": (
                str(result["trial_id"]) if result.get("trial_id") else None
            ),
        }
    except Exception as exc:
        logger.error("mcp.check_order_failed", error=str(exc))
        return {"error": str(exc)}


async def _handle_list_skills(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle aimart_list_skills tool call."""
    logger.info("mcp.list_skills", args=arguments)
    try:
        params: dict[str, Any] = {
            "item_type": "skill",
            "page": arguments.get("page", 1),
            "size": arguments.get("size", 20),
        }
        result = await _api_get("/catalog/items", params=params)
        items = result.get("items", [])
        if arguments.get("min_trust_score"):
            items = [
                i for i in items
                if i.get("trust_score", 0) >= arguments["min_trust_score"]
            ]
        return {
            "total": result.get("total", len(items)),
            "items": [
                {
                    "item_id": str(item["id"]),
                    "name": item["name"],
                    "version": item.get("version", ""),
                    "provider_id": str(item["provider_id"]),
                    "description": item.get("description", ""),
                    "trust_score": item.get("trust_score", 0),
                    "certification_status": item.get("certification_status", ""),
                    "total_transactions": item.get("total_transactions", 0),
                    "status": item.get("status", ""),
                }
                for item in items
            ],
        }
    except Exception as exc:
        logger.error("mcp.list_skills_failed", error=str(exc))
        return {"error": str(exc), "total": 0, "items": []}


async def _handle_list_models(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle aimart_list_models tool call."""
    logger.info("mcp.list_models", args=arguments)
    try:
        params: dict[str, Any] = {
            "item_type": "model",
            "page": arguments.get("page", 1),
            "size": arguments.get("size", 20),
        }
        result = await _api_get("/catalog/items", params=params)
        items = result.get("items", [])
        if arguments.get("min_trust_score"):
            items = [
                i for i in items
                if i.get("trust_score", 0) >= arguments["min_trust_score"]
            ]
        return {
            "total": result.get("total", len(items)),
            "items": [
                {
                    "item_id": str(item["id"]),
                    "name": item["name"],
                    "version": item.get("version", ""),
                    "provider_id": str(item["provider_id"]),
                    "description": item.get("description", ""),
                    "trust_score": item.get("trust_score", 0),
                    "certification_status": item.get("certification_status", ""),
                    "total_transactions": item.get("total_transactions", 0),
                    "status": item.get("status", ""),
                }
                for item in items
            ],
        }
    except Exception as exc:
        logger.error("mcp.list_models_failed", error=str(exc))
        return {"error": str(exc), "total": 0, "items": []}


# ---------------------------------------------------------------------------
# Handler dispatch table
# ---------------------------------------------------------------------------

_HANDLERS: dict[str, Any] = {
    "aimart_search": _handle_search,
    "aimart_purchase": _handle_purchase,
    "aimart_check_order": _handle_check_order,
    "aimart_list_skills": _handle_list_skills,
    "aimart_list_models": _handle_list_models,
}


# ---------------------------------------------------------------------------
# MCP Server creation
# ---------------------------------------------------------------------------

def create_mcp_server() -> Server:
    """Create and configure the MCP server instance.

    Returns
    -------
    Server
        The configured MCP server with all AIMart tools registered.
    """
    server = Server("aimart-mcp-server")

    @server.list_tools()
    async def list_tools() -> ListToolsResult:
        logger.info("mcp.list_tools")
        return ListToolsResult(tools=AIMART_TOOLS)

    @server.call_tool()
    async def call_tool(
        request: CallToolRequest,
    ) -> CallToolResult:
        tool_name = request.params.name
        arguments = request.params.arguments or {}

        logger.info("mcp.call_tool", tool=tool_name, args=arguments)

        handler = _HANDLERS.get(tool_name)
        if handler is None:
            return CallToolResult(
                isError=True,
                content=[
                    TextContent(
                        type="text",
                        text=f"Unknown tool: {tool_name}",
                    )
                ],
            )

        try:
            result = await handler(dict(arguments))
            return CallToolResult(
                isError=False,
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2, ensure_ascii=False),
                    )
                ],
            )
        except Exception as exc:
            logger.error("mcp.tool_error", tool=tool_name, error=str(exc))
            return CallToolResult(
                isError=True,
                content=[
                    TextContent(
                        type="text",
                        text=f"Tool execution error: {exc}",
                    )
                ],
            )

    return server


# ---------------------------------------------------------------------------
# Starlette app for SSE transport
# ---------------------------------------------------------------------------

def create_sse_app(mcp_server: Server | None = None) -> Starlette:
    """Create a Starlette application that serves the MCP SSE endpoint.

    The app exposes two endpoints (relative to mount point):

    * ``/sse`` — SSE stream endpoint (GET)
    * ``/messages/`` — Message endpoint (POST, receives tool calls)

    Parameters
    ----------
    mcp_server:
        Pre-configured MCP server.  A default one is created if not provided.

    Returns
    -------
    Starlette
        The configured Starlette application, mountable into FastAPI.
    """
    if mcp_server is None:
        mcp_server = create_mcp_server()

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(
                    notification_options=NotificationOptions(),
                ),
            )
        return Response()

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    return app
