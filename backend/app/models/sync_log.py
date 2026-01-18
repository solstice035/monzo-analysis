"""SyncLog model for tracking sync operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SyncLog(Base, TimestampMixin):
    """Tracks sync operation history."""

    __tablename__ = "sync_log"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    transactions_synced: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
