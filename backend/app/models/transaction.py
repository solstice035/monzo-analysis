"""Transaction model for Monzo transactions."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account


class Transaction(Base, TimestampMixin):
    """Represents a Monzo transaction."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    monzo_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    merchant_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    monzo_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    custom_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    settled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationship
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="transactions",
    )
