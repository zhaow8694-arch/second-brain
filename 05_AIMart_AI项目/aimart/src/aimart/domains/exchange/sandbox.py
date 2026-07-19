from __future__ import annotations

import copy
from uuid import UUID

import httpx
import structlog

logger = structlog.get_logger(__name__)

# Default sandbox constraints
_DEFAULT_SANDBOX_CONFIG = {
    "input_scale_pct": 10,
    "max_calls": 5,
    "timeout_ms": 30000,
}


class TrialResult:
    """Result of a sandbox trial execution."""

    def __init__(
        self,
        success: bool,
        output_data: dict | None = None,
        performance_data: dict | None = None,
        errors: list[str] | None = None,
    ) -> None:
        self.success = success
        self.output_data = output_data or {}
        self.performance_data = performance_data or {}
        self.errors = errors or []


class SandboxManager:
    """Manages sandbox trial execution for catalog items.

    Applies input constraints (scale, call limits, timeout) and then
    invokes the item's delivery API endpoint with the constrained input.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http_client = http_client or httpx.AsyncClient(timeout=30.0)

    # ------------------------------------------------------------------
    # Execute trial
    # ------------------------------------------------------------------

    async def execute_trial(
        self,
        trial_id: UUID,
        item_id: UUID,
        input_data: dict,
        config: dict | None = None,
    ) -> TrialResult:
        """Execute a sandbox trial for an item.

        Steps:
          1. Apply sandbox constraints to input data.
          2. Resolve the item's delivery API endpoint.
          3. Call the API with constrained input.
          4. Return the trial result.

        Args:
            trial_id: The trial session identifier.
            item_id: The catalog item being trialled.
            input_data: The original input from the agent.
            config: Sandbox configuration overrides.

        Returns:
            A TrialResult with success status, output, and performance data.
        """
        merged_config = {**_DEFAULT_SANDBOX_CONFIG, **(config or {})}
        constrained_input = self._apply_constraints(input_data, merged_config)

        logger.info(
            "sandbox_trial_execute",
            trial_id=str(trial_id),
            item_id=str(item_id),
            config=merged_config,
        )

        try:
            result = await self._call_item_api(item_id, constrained_input)
            logger.info(
                "sandbox_trial_success",
                trial_id=str(trial_id),
                item_id=str(item_id),
            )
            return result
        except Exception as exc:
            logger.error(
                "sandbox_trial_failed",
                trial_id=str(trial_id),
                item_id=str(item_id),
                error=str(exc),
            )
            return TrialResult(
                success=False,
                errors=[str(exc)],
            )

    # ------------------------------------------------------------------
    # Apply constraints
    # ------------------------------------------------------------------

    def _apply_constraints(self, input_data: dict, config: dict) -> dict:
        """Scale input data and enforce call limits.

        - input_scale_pct: percentage of original input to use (e.g. 10 → 10%)
        - max_calls: maximum number of API calls allowed
        - timeout_ms: per-call timeout in milliseconds
        """
        constrained = copy.deepcopy(input_data)

        scale_pct = config.get("input_scale_pct", 10)
        max_calls = config.get("max_calls", 5)
        timeout_ms = config.get("timeout_ms", 30000)

        # Scale numeric arrays in the input
        if "data" in constrained and isinstance(constrained["data"], list):
            original = constrained["data"]
            keep_count = max(1, int(len(original) * scale_pct / 100))
            constrained["data"] = original[:keep_count]

        # Attach sandbox metadata
        constrained["_sandbox"] = {
            "max_calls": max_calls,
            "timeout_ms": timeout_ms,
            "input_scale_pct": scale_pct,
            "trial_mode": True,
        }

        logger.debug(
            "sandbox_constraints_applied",
            scale_pct=scale_pct,
            max_calls=max_calls,
            timeout_ms=timeout_ms,
        )

        return constrained

    # ------------------------------------------------------------------
    # Call item API
    # ------------------------------------------------------------------

    async def _call_item_api(
        self, item_id: UUID, constrained_input: dict
    ) -> TrialResult:
        """Call the item's delivery.api_endpoint with the constrained input.

        In production this would resolve the endpoint from the catalog item's
        AgentCard.  For now it simulates the call.
        """
        # TODO: Resolve actual endpoint from CatalogItem.agentcard.delivery.api_endpoint
        # For a real implementation:
        #   from aimart.domains.catalog.service import CatalogService
        #   item = await catalog_service.get_item(item_id)
        #   endpoint = item.agentcard["delivery"]["api_endpoint"]

        logger.debug(
            "sandbox_call_item_api",
            item_id=str(item_id),
        )

        # Simulated response – replace with real HTTP call in production
        try:
            # If a real endpoint were configured:
            # response = await self._http_client.post(
            #     endpoint,
            #     json=constrained_input,
            #     timeout=constrained_input.get("_sandbox", {}).get("timeout_ms", 30000) / 1000.0,
            # )
            # return TrialResult(
            #     success=response.status_code == 200,
            #     output_data=response.json(),
            #     performance_data={"status_code": response.status_code},
            # )

            # Simulated success
            return TrialResult(
                success=True,
                output_data={"result": "sandbox_trial_completed", "item_id": str(item_id)},
                performance_data={
                    "latency_ms": 150,
                    "calls_made": 1,
                    "input_scale_pct": constrained_input.get("_sandbox", {}).get("input_scale_pct", 10),
                },
            )
        except httpx.TimeoutException as exc:
            return TrialResult(
                success=False,
                errors=[f"API call timed out: {exc}"],
            )
        except httpx.HTTPError as exc:
            return TrialResult(
                success=False,
                errors=[f"API call failed: {exc}"],
            )
