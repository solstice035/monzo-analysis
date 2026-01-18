"""Budget tracking service for spending analysis."""

from dataclasses import dataclass
from datetime import date, timedelta
from calendar import monthrange
from typing import Any
from uuid import uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, Transaction


def get_current_period(
    today: date,
    reset_day: int,
    period: str,
) -> tuple[date, date]:
    """Calculate the current budget period based on reset day.

    Args:
        today: Reference date
        reset_day: Day of month budget resets (1-28)
        period: Period type ("monthly" or "weekly")

    Returns:
        Tuple of (period_start, period_end)
    """
    if period == "weekly":
        # Week runs Monday (0) to Sunday (6)
        days_since_monday = today.weekday()
        start = today - timedelta(days=days_since_monday)
        end = start + timedelta(days=6)
        return start, end

    # Monthly period
    year = today.year
    month = today.month

    if today.day >= reset_day:
        # Period started this month
        start = date(year, month, reset_day)
        # End is reset_day - 1 of next month
        if month == 12:
            end_year = year + 1
            end_month = 1
        else:
            end_year = year
            end_month = month + 1
        end = date(end_year, end_month, reset_day) - timedelta(days=1)
    else:
        # Period started last month
        if month == 1:
            start_year = year - 1
            start_month = 12
        else:
            start_year = year
            start_month = month - 1
        start = date(start_year, start_month, reset_day)
        end = date(year, month, reset_day) - timedelta(days=1)

    return start, end


@dataclass
class BudgetStatus:
    """Status of a budget for a period."""

    budget_id: Any
    category: str
    amount: int
    spent: int
    remaining: int
    percentage: float
    status: str  # "under", "warning", "over"
    period_start: date
    period_end: date


class BudgetService:
    """Service for managing budgets and tracking spend."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_all_budgets(self) -> list[Budget]:
        """Get all budgets.

        Returns:
            List of budgets
        """
        result = await self._session.execute(select(Budget))
        return list(result.scalars().all())

    async def create_budget(
        self,
        category: str,
        amount: int,
        period: str = "monthly",
        start_day: int = 1,
    ) -> Budget:
        """Create a new budget.

        Args:
            category: Category name to track
            amount: Budget amount in pence
            period: Period type ("monthly" or "weekly")
            start_day: Day of month budget resets

        Returns:
            Created budget
        """
        budget = Budget(
            id=uuid4(),
            category=category,
            amount=amount,
            period=period,
            start_day=start_day,
        )
        self._session.add(budget)
        return budget

    async def update_budget(
        self,
        budget_id: str,
        category: str | None = None,
        amount: int | None = None,
        period: str | None = None,
        start_day: int | None = None,
    ) -> Budget | None:
        """Update an existing budget.

        Args:
            budget_id: ID of budget to update
            **kwargs: Fields to update

        Returns:
            Updated budget or None if not found
        """
        result = await self._session.execute(
            select(Budget).where(Budget.id == budget_id)
        )
        budget = result.scalar_one_or_none()

        if not budget:
            return None

        if category is not None:
            budget.category = category
        if amount is not None:
            budget.amount = amount
        if period is not None:
            budget.period = period
        if start_day is not None:
            budget.start_day = start_day

        return budget

    async def delete_budget(self, budget_id: str) -> bool:
        """Delete a budget.

        Args:
            budget_id: ID of budget to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self._session.execute(
            select(Budget).where(Budget.id == budget_id)
        )
        budget = result.scalar_one_or_none()

        if not budget:
            return False

        await self._session.delete(budget)
        return True

    async def calculate_spend(
        self,
        budget: Budget,
        reference_date: date,
    ) -> int:
        """Calculate total spend for a budget's current period.

        Args:
            budget: Budget to calculate spend for
            reference_date: Reference date for period calculation

        Returns:
            Total spend in pence (positive value)
        """
        period_start, period_end = get_current_period(
            reference_date,
            budget.start_day,
            budget.period,
        )

        result = await self._session.execute(
            select(Transaction).where(
                and_(
                    Transaction.custom_category == budget.category,
                    Transaction.created_at >= period_start,
                    Transaction.created_at <= period_end,
                )
            )
        )
        transactions = result.scalars().all()

        # Sum absolute values of negative amounts (spending)
        total = sum(abs(tx.amount) for tx in transactions if tx.amount < 0)
        return total

    async def get_budget_status(
        self,
        budget: Budget,
        reference_date: date,
    ) -> BudgetStatus:
        """Get the status of a budget for the current period.

        Args:
            budget: Budget to check
            reference_date: Reference date for period calculation

        Returns:
            BudgetStatus with spend details
        """
        period_start, period_end = get_current_period(
            reference_date,
            budget.start_day,
            budget.period,
        )

        spent = await self.calculate_spend(budget, reference_date)
        remaining = budget.amount - spent
        percentage = (spent / budget.amount) * 100 if budget.amount > 0 else 0

        if percentage >= 100:
            status = "over"
        elif percentage >= 80:
            status = "warning"
        else:
            status = "under"

        return BudgetStatus(
            budget_id=budget.id,
            category=budget.category,
            amount=budget.amount,
            spent=spent,
            remaining=remaining,
            percentage=round(percentage, 2),
            status=status,
            period_start=period_start,
            period_end=period_end,
        )

    async def get_all_budget_statuses(
        self,
        reference_date: date,
    ) -> list[BudgetStatus]:
        """Get status for all budgets.

        Args:
            reference_date: Reference date for period calculation

        Returns:
            List of BudgetStatus for all budgets
        """
        budgets = await self.get_all_budgets()
        statuses = []
        for budget in budgets:
            status = await self.get_budget_status(budget, reference_date)
            statuses.append(status)
        return statuses
