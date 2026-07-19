"""AIMart FastAPI dependency injection providers.

Each dependency function yields a service instance that is wired up
during application startup and stored on ``app.state``.
"""

from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, Request
from kafka import KafkaProducer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from aimart.config import Settings, get_settings

# ---------------------------------------------------------------------------
# Core infrastructure dependencies
# ---------------------------------------------------------------------------

async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session from the application-level session factory.

    The session factory is expected to be initialised during startup and
    attached as ``app.state.db_session_factory``.
    """
    session_factory = request.app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_redis(request: Request) -> Redis:
    """Return the async Redis connection pool stored on app state."""
    return request.app.state.redis


def get_kafka_producer(request: Request) -> KafkaProducer:
    """Return the Kafka producer instance stored on app state."""
    return request.app.state.kafka_producer


def get_clickhouse_client(request: Request) -> Any:
    """Return the ClickHouse client instance stored on app state."""
    return request.app.state.clickhouse


def get_es_client(request: Request) -> Any:
    """Return the async Elasticsearch client stored on app state."""
    return request.app.state.elasticsearch


# ---------------------------------------------------------------------------
# Domain / cross-cutting service dependencies
# ---------------------------------------------------------------------------

def get_audit_logger(request: Request) -> Any:
    """Return the structured audit logger.

    The audit logger is initialised once during startup and stored on
    ``app.state.audit_logger``.  It uses *structlog* under the hood.
    """
    return request.app.state.audit_logger


def get_rules_engine(request: Request) -> Any:
    """Return the rules / policy engine instance.

    The rules engine evaluates access-control, pricing, and
    trust policies at runtime.
    """
    return request.app.state.rules_engine


def get_apikey_manager(request: Request) -> Any:
    """Return the API-key manager service.

    Handles creation, rotation and revocation of API keys for
    AI-agent consumers.
    """
    return request.app.state.apikey_manager


def get_oauth2_flow(request: Request) -> Any:
    """Return the OAuth2 flow handler.

    Manages the authorization-code and client-credentials flows
    used by external AI agents to obtain access tokens.
    """
    return request.app.state.oauth2_flow


# ---------------------------------------------------------------------------
# Convenience type aliases for injection
# ---------------------------------------------------------------------------

DBSession = Annotated[AsyncSession, Depends(get_db_session)]
RedisPool = Annotated[Redis, Depends(get_redis)]
KafkaProducerDep = Annotated[KafkaProducer, Depends(get_kafka_producer)]
ClickHouseDep = Annotated[object, Depends(get_clickhouse_client)]
ElasticsearchDep = Annotated[object, Depends(get_es_client)]
AuditLoggerDep = Annotated[object, Depends(get_audit_logger)]
RulesEngineDep = Annotated[object, Depends(get_rules_engine)]
ApiKeyManagerDep = Annotated[object, Depends(get_apikey_manager)]
OAuth2FlowDep = Annotated[object, Depends(get_oauth2_flow)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
