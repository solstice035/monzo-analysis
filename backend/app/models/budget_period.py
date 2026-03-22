"""BudgetPeriod model for tracking monthly budget periods."""

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.envelope_balance import EnvelopeBalance


class BudgetPeriod(Base, TimestampMixin):
    """Represents one month's budget period (28th to 27th cycle).

    All envelopes share the same period boundaries per account.
    Status transitions: 'active' -> 'closing' -> 'closed'.
    """

    __tablename__ = "budget_periods"
    __table_args__ = (
        UniqueConstraint("account_id", "period_start", name="uq_budget_periods_account_start"),
        CheckConstraint(
            "status IN ('active', 'closing', 'closed')",
            name="ck_budget_periods_status",
        ),
        Index("ix_budget_periods_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="budget_periods")
    envelope_balances: Mapped[list["EnvelopeBalance"]] = relationship(
        "EnvelopeBalance",
        back_populates="period",
        cascade="all, delete-orphan",
    )
