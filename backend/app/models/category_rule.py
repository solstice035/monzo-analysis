"""CategoryRule model for auto-categorisation rules."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CategoryRule(Base, TimestampMixin):
    """Represents an auto-categorisation rule."""

    __tablename__ = "category_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    conditions: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    target_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
