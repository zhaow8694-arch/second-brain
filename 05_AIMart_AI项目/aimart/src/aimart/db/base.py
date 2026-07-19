"""SQLAlchemy declarative base and common mixins for all AIMart models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models in the AIMart project."""

    pass


class TimestampMixin:
    """Mixin that adds ``created_at`` and ``updated_at`` columns.

    Both columns use the database server's ``now()`` as the default so that
    rows get a reliable timestamp regardless of the application clock.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
