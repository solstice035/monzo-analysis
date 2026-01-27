"""Budget model for spending budgets and sinking funds."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.budget_group import BudgetGroup


class Budget(Base, TimestampMixin):
    """Represents a spending budget or sinking fund for a category.

    Budget Types:
    - Spending budget (period_type = weekly/monthly): "Don't exceed £X this period"
    - Sinking fund (period_type = quarterly/annual/bi-annual): "Contribute £X/month towards £Y target"

    For sinking funds, `amount` represents the monthly contribution target,
    and `annual_amount` represents the total target (e.g., £675 car tax due in October).
    """

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
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("budget_groups.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
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
    period_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="monthly",
    )
    start_day: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )
    annual_amount: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    target_month: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    linked_pot_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="budgets")
    group: Mapped["BudgetGroup"] = relationship("BudgetGroup", back_populates="budgets")

    @property
    def is_sinking_fund(self) -> bool:
        """Return True if this budget is a sinking fund (annual/quarterly/bi-annual)."""
        return self.period_type in ("quarterly", "annual", "bi-annual")

    @property
    def monthly_contribution(self) -> int:
        """Return the monthly contribution amount.

        For regular budgets, this is the amount.
        For sinking funds, this calculates from annual_amount if set.
        """
        if not self.is_sinking_fund or not self.annual_amount:
            return self.amount

        # Calculate monthly contribution from annual amount
        if self.period_type == "annual":
            return self.annual_amount // 12
        elif self.period_type == "bi-annual":
            return self.annual_amount // 6
        elif self.period_type == "quarterly":
            return self.annual_amount // 3
        return self.amount
