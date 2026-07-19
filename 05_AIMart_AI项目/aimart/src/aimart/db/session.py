"""Async database session management for AIMart."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog
from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = structlog.get_logger()

# Module-level session factory (set by init_db for use in auth contexts)
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_engine(database_url: str, **engine_kwargs: object) -> AsyncEngine:
    """Create an :class:`AsyncEngine` backed by asyncpg.

    Parameters
    ----------
    database_url:
        A PostgreSQL connection string.  If the URL does not already include
        the ``+asyncpg`` driver, it will be injected automatically.
    **engine_kwargs:
        Extra keyword arguments forwarded to :func:`create_async_engine`
        (e.g. ``pool_size``, ``echo``).
    """
    if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    defaults: dict = {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_recycle": 3600,
    }
    defaults.update(engine_kwargs)

    engine = create_async_engine(database_url, **defaults)
    logger.info("db.engine_created", url=database_url.split("@")[-1])
    return engine


async def get_async_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an :class:`AsyncSession` from the given engine.

    The session is automatically committed on success and rolled-back on
    failure, making it suitable for use as a FastAPI dependency.
    """
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def init_db(database_url: str, **engine_kwargs: object) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Bootstrap the database layer.

    Returns
    -------
    tuple[AsyncEngine, async_sessionmaker]
        A 2-tuple of the async engine and the session factory, ready for use.
    """
    global async_session_factory  # noqa: PLW0603
    engine = get_async_engine(database_url, **engine_kwargs)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("db.initialized")
    return engine, async_session_factory


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session.

    Uses the session factory stored in ``request.app.state.db_session_factory``.
    """
    session_factory = request.app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
