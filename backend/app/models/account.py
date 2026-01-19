"""Account model for Monzo accounts."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.category_rule import CategoryRule
    from app.models.pot import Pot
    from app.models.transaction import Transaction


class Account(Base, TimestampMixin):
    """Represents a Monzo account (retail or joint)."""

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    monzo_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    pots: Mapped[list["Pot"]] = relationship(
        "Pot",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    budgets: Mapped[list["Budget"]] = relationship(
        "Budget",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    category_rules: Mapped[list["CategoryRule"]] = relationship(
        "CategoryRule",
        back_populates="account",
        cascade="all, delete-orphan",
    )
