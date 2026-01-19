"""Budget model for spending budgets."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account


class Budget(Base, TimestampMixin):
    """Represents a spending budget for a category, scoped to an account."""

    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
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

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="budgets")
