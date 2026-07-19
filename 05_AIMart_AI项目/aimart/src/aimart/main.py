"""AIMart FastAPI application entry point."""

import contextlib
from collections.abc import AsyncIterator

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aimart.config import get_settings

logger = structlog.get_logger()

# Load .env file into os.environ for modules that use os.environ.get()
load_dotenv(".env", override=False)

# ---------------------------------------------------------------------------
# Domain routers (imported lazily to avoid circular imports at module level)
# ---------------------------------------------------------------------------
from aimart.domains.audit.router import router as audit_router  # noqa: E402
from aimart.domains.catalog.router import router as catalog_router  # noqa: E402
from aimart.domains.exchange.router import router as exchange_router  # noqa: E402
from aimart.domains.identity.router import router as identity_router  # noqa: E402
from aimart.domains.payment.router import router as payment_router  # noqa: E402
from aimart.domains.search.router import router as search_router  # noqa: E402
from aimart.domains.trust.router import router as trust_router  # noqa: E402
from aimart.protocols.mcp_gateway import create_sse_app  # noqa: E402


# ---------------------------------------------------------------------------
# Lifespan – startup / shutdown logic
# ---------------------------------------------------------------------------
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler: mount external services on app.state."""
    settings = get_settings()

    # ---- Startup ----
    logger.info("aimart.starting", environment=settings.environment.value)

    # Redis
    import redis.asyncio as aioredis

    redis_pool = aioredis.from_url(
        settings.redis_url,
        password=settings.redis_password,
        decode_responses=True,
    )
    app.state.redis = redis_pool
    logger.info("redis.connected", url=settings.redis_url)

    # Database
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from aimart.db.session import get_async_engine

    db_engine = get_async_engine(settings.database_url)
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    app.state.db_session_factory = session_factory
    # Set module-level factory for auth contexts
    import aimart.db.session as db_session
    db_session.async_session_factory = session_factory
    logger.info("db.session_factory_created")

    # Kafka producer
    from kafka import KafkaProducer

    kafka_producer = KafkaProducer(
        bootstrap_servers=settings.kafka_brokers.split(","),
        value_serializer=lambda v: __import__("json").dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )
    app.state.kafka_producer = kafka_producer
    logger.info("kafka.connected", brokers=settings.kafka_brokers)

    # ClickHouse
    from clickhouse_driver import Client as ClickHouseClient

    clickhouse_client = ClickHouseClient.from_url(settings.clickhouse_url)
    app.state.clickhouse = clickhouse_client
    logger.info("clickhouse.connected", url=settings.clickhouse_url)

    # Elasticsearch
    from elasticsearch import AsyncElasticsearch

    es_kwargs: dict = {"hosts": [settings.elasticsearch_url]}
    if settings.elasticsearch_api_key:
        es_kwargs["api_key"] = settings.elasticsearch_api_key
    es_client = AsyncElasticsearch(**es_kwargs)
    app.state.elasticsearch = es_client
    logger.info("elasticsearch.connected", url=settings.elasticsearch_url)

    logger.info("aimart.ready")

    yield  # ---- Application runs here ----

    # ---- Shutdown ----
    logger.info("aimart.shutting_down")

    await app.state.redis.close()
    logger.info("redis.disconnected")

    app.state.kafka_producer.close()
    logger.info("kafka.disconnected")

    await app.state.elasticsearch.close()
    logger.info("elasticsearch.disconnected")

    logger.info("aimart.stopped")


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
settings = get_settings()

app = FastAPI(
    title="AIMart",
    version="1.0.0",
    description="AI Marketplace Platform – browse, purchase and use AI capabilities",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ---- CORS middleware ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allowed_methods,
    allow_headers=settings.cors_allowed_headers,
)

# ---- Include domain routers ----
app.include_router(identity_router, prefix=f"{settings.api_prefix}/identity", tags=["Identity"])
app.include_router(catalog_router, prefix=f"{settings.api_prefix}/catalog", tags=["Catalog"])
app.include_router(search_router, prefix=f"{settings.api_prefix}/search", tags=["Search"])
app.include_router(exchange_router, prefix=f"{settings.api_prefix}/exchange", tags=["Exchange"])
app.include_router(payment_router, prefix=f"{settings.api_prefix}/payment", tags=["Payment"])
app.include_router(trust_router, prefix=f"{settings.api_prefix}/trust", tags=["Trust"])
app.include_router(audit_router, prefix=f"{settings.api_prefix}/audit", tags=["Audit"])

# ---- MCP SSE endpoint ----
mcp_app = create_sse_app()
app.mount("/mcp", mcp_app, name="mcp")


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Return service health status."""
    checks: dict = {"status": "ok", "version": "1.0.0", "service": "aimart"}

    # Redis
    try:
        pong = await app.state.redis.ping()
        checks["redis"] = "ok" if pong else "error"
    except Exception:
        checks["redis"] = "unreachable"

    # ClickHouse
    try:
        app.state.clickhouse.execute("SELECT 1")
        checks["clickhouse"] = "ok"
    except Exception:
        checks["clickhouse"] = "unreachable"

    # Kafka – best-effort: the producer doesn't expose a lightweight ping
    checks["kafka"] = "connected" if app.state.kafka_producer else "unavailable"

    # Elasticsearch
    try:
        es_info = await app.state.elasticsearch.info()
        checks["elasticsearch"] = "ok" if es_info else "error"
    except Exception:
        checks["elasticsearch"] = "unreachable"

    overall = "ok" if all(v in ("ok", "connected") for v in checks.values() if isinstance(v, str)) else "degraded"
    checks["status"] = overall
    return checks
