"""Budget model for spending budgets."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Budget(Base, TimestampMixin):
    """Represents a spending budget for a category."""

    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    start_day: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )
