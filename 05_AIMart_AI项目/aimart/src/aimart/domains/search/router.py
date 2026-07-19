from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.db.session import get_db
from aimart.dependencies import AuditLoggerDep, ElasticsearchDep
from aimart.domains.identity.auth import AuthContext, require_agent, require_auth
from aimart.domains.search.matcher import MatcherConfig
from aimart.domains.search.schemas import (
    CapabilityNeed,
    SearchResponse,
    TrialRequest,
    TrialResult,
)
from aimart.domains.search.service import SearchService

logger = structlog.get_logger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Service instance (singleton, ES client injected at request time)
# ---------------------------------------------------------------------------

_matcher_config = MatcherConfig()


def _get_service(es: ElasticsearchDep) -> SearchService:
    """Create a SearchService backed by the app-level ES client."""
    # The es parameter is typed as object via dependency injection, but
    # at runtime it is always an AsyncElasticsearch instance.
    return SearchService(es_client=es, matcher_config=_matcher_config)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/capability",
    response_model=SearchResponse,
    summary="Search for capabilities matching a structured need",
)
async def search_capability(
    need: CapabilityNeed,
    ctx: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    service: SearchService = Depends(_get_service),
    audit_logger: AuditLoggerDep = None,
) -> SearchResponse:
    """Execute a capability search for the authenticated agent.

    The agent submits a ``CapabilityNeed`` describing what it requires
    (model, skill, expert, or compute) and the system returns ranked
    matching items with five-dimensional scoring.
    """
    agent_id = uuid.UUID(ctx.agent_id) if ctx.agent_id else uuid.UUID(ctx.participant_id)
    try:
        return await service.search(
            need=need,
            agent_id=agent_id,
            db=db,
            audit_logger=audit_logger,
        )
    except Exception as exc:
        logger.error("search.capability_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {exc}",
        )


@router.post(
    "/trial",
    response_model=TrialResult,
    summary="Execute a sandbox trial for a capability item",
)
async def trial_capability(
    request: TrialRequest,
    ctx: AuthContext = Depends(require_agent),
    db: AsyncSession = Depends(get_db),
    service: SearchService = Depends(_get_service),
    audit_logger: AuditLoggerDep = None,
) -> TrialResult:
    """Run a sandboxed trial of a capability item before purchase.

    Requires agent-level authentication.  Enforces a daily trial limit
    of 3 per agent per item.
    """
    agent_id = uuid.UUID(ctx.agent_id)
    try:
        return await service.trial(
            request=request,
            agent_id=agent_id,
            db=db,
            audit_logger=audit_logger,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("search.trial_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trial failed: {exc}",
        )


@router.get(
    "/suggest/domains",
    summary="Suggest domain categories matching a query",
)
async def suggest_domains(
    q: str = Query(..., min_length=1, max_length=100, description="Search prefix for domain names"),
    ctx: AuthContext = Depends(require_auth),
    es: ElasticsearchDep = None,
) -> dict[str, Any]:
    """Return domain name suggestions based on a prefix query.

    Uses the Elasticsearch completion / edge_ngram analyser to provide
    fast type-ahead suggestions for the ``domains`` field.
    """
    from aimart.domains.search.indexer import CAPABILITY_INDEX_NAME

    query_body: dict[str, Any] = {
        "size": 0,
        "query": {
            "bool": {
                "filter": [{"term": {"status": "active"}}],
                "must": [
                    {
                        "match": {
                            "domains": {
                                "query": q,
                                "analyzer": "domain_analyzer",
                            }
                        }
                    }
                ],
            }
        },
        "aggs": {
            "domain_suggestions": {
                "terms": {"field": "domains", "size": 20, "include": f".*{q}.*"}
            }
        },
    }

    try:
        resp = await es.search(index=CAPABILITY_INDEX_NAME, body=query_body)
        buckets = (
            resp.get("aggregations", {})
            .get("domain_suggestions", {})
            .get("buckets", [])
        )
        suggestions = [b["key"] for b in buckets]
        return {"query": q, "suggestions": suggestions}
    except Exception as exc:
        logger.error("search.suggest_domains_failed", error=str(exc))
        return {"query": q, "suggestions": []}


@router.get(
    "/suggest/task-types",
    summary="Suggest task types for a given domain",
)
async def suggest_task_types(
    domain: str = Query(..., min_length=1, max_length=100, description="Domain to suggest task types for"),
    ctx: AuthContext = Depends(require_auth),
    es: ElasticsearchDep = None,
) -> dict[str, Any]:
    """Return task type suggestions for items in the specified domain.

    Aggregates the ``task_types.name`` field from active items in the
    given domain.
    """
    from aimart.domains.search.indexer import CAPABILITY_INDEX_NAME

    query_body: dict[str, Any] = {
        "size": 0,
        "query": {
            "bool": {
                "filter": [
                    {"term": {"status": "active"}},
                    {"term": {"domains": domain}},
                ]
            }
        },
        "aggs": {
            "task_type_suggestions": {
                "nested": {"path": "task_types"},
                "aggs": {
                    "task_names": {
                        "terms": {"field": "task_types.name", "size": 20}
                    }
                },
            }
        },
    }

    try:
        resp = await es.search(index=CAPABILITY_INDEX_NAME, body=query_body)
        buckets = (
            resp.get("aggregations", {})
            .get("task_type_suggestions", {})
            .get("task_names", {})
            .get("buckets", [])
        )
        suggestions = [b["key"] for b in buckets]
        return {"domain": domain, "suggestions": suggestions}
    except Exception as exc:
        logger.error("search.suggest_task_types_failed", error=str(exc))
        return {"domain": domain, "suggestions": []}
