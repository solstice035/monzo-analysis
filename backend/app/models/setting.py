"""Setting model for key-value app settings."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Setting(Base):
    """Key-value store for app settings."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    value: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
