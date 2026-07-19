from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

import structlog
from elasticsearch import AsyncElasticsearch
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.domains.search.matcher import CapabilityMatcher, MatcherConfig
from aimart.domains.search.models import SearchQuery
from aimart.domains.search.schemas import (
    CapabilityNeed,
    SearchResponse,
    TrialRequest,
    TrialResult,
)

logger = structlog.get_logger(__name__)

# Maximum number of trial runs per agent per item per day
_DAILY_TRIAL_LIMIT = 3


class SearchService:
    """High-level orchestration for the search domain.

    Coordinates capability matching, query recording, trial execution,
    and audit logging.
    """

    def __init__(
        self,
        es_client: AsyncElasticsearch,
        matcher_config: MatcherConfig | None = None,
    ) -> None:
        self._es = es_client
        self._matcher = CapabilityMatcher(es_client, config=matcher_config)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        need: CapabilityNeed,
        agent_id: uuid.UUID,
        db: AsyncSession,
        audit_logger: Any | None = None,
    ) -> SearchResponse:
        """Execute a capability search: record query → match → build response → audit."""
        query_start = datetime.now(UTC)

        # Record the search query
        session_id = str(uuid.uuid4())
        search_query = SearchQuery(
            agent_id=agent_id,
            session_id=session_id,
            need_type=need.need_type,
            domains=need.domains,
            task_description=need.task_description,
            constraints=need.model_dump(
                include={"performance", "budget", "trust"}
            ),
            scoring_weights=need.scoring_weights,
        )
        db.add(search_query)
        await db.flush()

        query_latency_ms = int(
            (datetime.now(UTC) - query_start).total_seconds() * 1000
        )

        # Execute matching
        match_start = datetime.now(UTC)
        matched_items = await self._matcher.match(need, agent_id)
        match_latency_ms = int(
            (datetime.now(UTC) - match_start).total_seconds() * 1000
        )

        # Update the query record with results
        search_query.result_count = len(matched_items)
        search_query.query_latency_ms = query_latency_ms
        search_query.match_latency_ms = match_latency_ms
        await db.flush()

        # Build response
        response = SearchResponse(
            query_id=search_query.id,
            need_type=need.need_type,
            total_matches=len(matched_items),
            returned_count=min(len(matched_items), 20),
            items=matched_items[:20],
            query_latency_ms=query_latency_ms,
            match_latency_ms=match_latency_ms,
        )

        # Audit log
        if audit_logger:
            audit_logger.info(
                "search.executed",
                query_id=str(search_query.id),
                agent_id=str(agent_id),
                need_type=need.need_type,
                domains=need.domains,
                total_matches=response.total_matches,
                query_latency_ms=query_latency_ms,
                match_latency_ms=match_latency_ms,
            )
        else:
            logger.info(
                "search.executed",
                query_id=str(search_query.id),
                agent_id=str(agent_id),
                need_type=need.need_type,
                total_matches=response.total_matches,
            )

        return response

    # ------------------------------------------------------------------
    # Trial
    # ------------------------------------------------------------------

    async def trial(
        self,
        request: TrialRequest,
        agent_id: uuid.UUID,
        db: AsyncSession,
        audit_logger: Any | None = None,
    ) -> TrialResult:
        """Execute a sandbox trial for a capability item.

        Enforces a daily trial limit of 3 per agent per item.
        """
        # Check daily trial limit
        today_count = await self.count_today_trials(
            db, agent_id=agent_id, item_id=request.item_id
        )
        if today_count >= _DAILY_TRIAL_LIMIT:
            raise PermissionError(
                f"Daily trial limit ({_DAILY_TRIAL_LIMIT}) reached for item "
                f"{request.item_id}"
            )

        trial_id = uuid.uuid4()

        # Execute sandbox trial (simulated — actual sandbox integration is a
        # separate concern)
        success, output, performance, errors = await self._execute_sandbox(
            request
        )

        # Update search query tracking if applicable
        stmt = (
            select(SearchQuery)
            .where(SearchQuery.agent_id == agent_id)
            .order_by(SearchQuery.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        latest_query = result.scalar_one_or_none()
        if latest_query is not None:
            latest_query.trial_initiated += 1
            latest_query.selected_item_id = request.item_id
            await db.flush()

        trial_result = TrialResult(
            trial_id=trial_id,
            item_id=request.item_id,
            success=success,
            output=output,
            performance=performance,
            errors=errors,
        )

        # Audit log
        if audit_logger:
            audit_logger.info(
                "search.trial_executed",
                trial_id=str(trial_id),
                agent_id=str(agent_id),
                item_id=str(request.item_id),
                need_type=request.need_type,
                success=success,
            )
        else:
            logger.info(
                "search.trial_executed",
                trial_id=str(trial_id),
                agent_id=str(agent_id),
                item_id=str(request.item_id),
                success=success,
            )

        return trial_result

    # ------------------------------------------------------------------
    # Trial count helper
    # ------------------------------------------------------------------

    async def count_today_trials(
        self,
        db: AsyncSession,
        agent_id: uuid.UUID,
        item_id: uuid.UUID,
    ) -> int:
        """Count today's trial records for the given agent + item.

        Currently this counts from SearchQuery rows where the agent
        trialed the specific item.  In a full implementation this would
        query a dedicated trial_audit table.
        """
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=UTC
        )
        stmt = (
            select(func.count())
            .select_from(SearchQuery)
            .where(
                SearchQuery.agent_id == agent_id,
                SearchQuery.selected_item_id == item_id,
                SearchQuery.trial_initiated > 0,
                SearchQuery.created_at >= today_start,
            )
        )
        result = await db.execute(stmt)
        count = result.scalar_one()
        return count

    # ------------------------------------------------------------------
    # Sandbox execution (placeholder for real sandbox integration)
    # ------------------------------------------------------------------

    async def _execute_sandbox(
        self, request: TrialRequest
    ) -> tuple[bool, dict[str, Any] | None, dict[str, Any] | None, list[str] | None]:
        """Execute the trial in a sandboxed environment.

        Returns (success, output, performance, errors).

        This is a placeholder that simulates a successful sandbox run.
        The real implementation would invoke the capability provider's
        endpoint in an isolated container/VM with resource limits.
        """
        # Simulated sandbox execution
        logger.info(
            "search.sandbox_executing",
            item_id=str(request.item_id),
            need_type=request.need_type,
        )

        # In production, this would:
        # 1. Provision an isolated sandbox environment
        # 2. Forward the trial_input to the capability endpoint
        # 3. Collect output and performance metrics
        # 4. Tear down the sandbox

        success = True
        output: dict[str, Any] = {
            "message": "Sandbox trial completed successfully",
            "item_id": str(request.item_id),
        }
        performance: dict[str, Any] = {
            "execution_time_ms": 150,
            "memory_used_mb": 64,
        }
        errors = None

        return success, output, performance, errors
