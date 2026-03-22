"""EnvelopeBalance model for tracking per-envelope state within a period."""

import uuid

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.budget_period import BudgetPeriod


class EnvelopeBalance(Base, TimestampMixin):
    """Tracks the state of each budget line item within a period.

    `spent` is NOT stored — it is computed on read via:
        ABS(SUM(amount)) for transactions where budget_id matches
        and created_at falls within the period boundaries.

    `available` is computed as: allocated + rollover - spent.

    account_id is intentionally omitted — derivable via budget_id
    and period_id joins.
    """

    __tablename__ = "envelope_balances"
    __table_args__ = (
        UniqueConstraint("budget_id", "period_id", name="uq_envelope_balances_budget_period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    budget_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("budgets.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("budget_periods.id"),
        nullable=False,
        index=True,
    )
    allocated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    original_allocated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rollover: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="envelope_balances")
    period: Mapped["BudgetPeriod"] = relationship("BudgetPeriod", back_populates="envelope_balances")
