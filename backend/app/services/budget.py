"""Budget tracking service for spending analysis."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from calendar import monthrange
from typing import Any
from uuid import uuid4

from sqlalchemy import select, and_, or_, func
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


def calculate_sinking_fund_months(
    target_month: int,
    reference_date: date,
) -> tuple[int, int]:
    """Calculate months elapsed and remaining in a sinking fund contribution period.

    A sinking fund contributes monthly toward an annual target. The contribution
    period runs from target_month of one year to target_month of the next.

    Args:
        target_month: Month when the expense is due (1-12)
        reference_date: Date to calculate from

    Returns:
        Tuple of (months_elapsed, months_remaining), each clamped to 0-12
    """
    current_month = reference_date.month

    if current_month >= target_month:
        # Contributing for next year's target
        months_elapsed = current_month - target_month
    else:
        # Contributing for this year's target
        months_elapsed = 12 - target_month + current_month

    months_elapsed = max(1, min(months_elapsed, 12))
    months_remaining = max(0, 12 - months_elapsed)
    return months_elapsed, months_remaining


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


@dataclass
class SinkingFundStatus:
    """Status of a sinking fund budget.

    Sinking funds track contributions toward an annual target,
    optionally backed by a Monzo Pot for balance tracking.
    """

    budget_id: Any
    name: str | None
    category: str
    target_amount: int  # Total annual target in pence
    monthly_contribution: int  # Expected monthly contribution
    contributions_to_date: int  # Actual contributions so far
    expected_to_date: int  # Expected contributions by now
    variance: int  # contributions_to_date - expected_to_date
    on_track: bool  # Is the fund on track?
    target_month: int | None  # Month target is due (1-12)
    months_remaining: int  # Months until target date
    pot_balance: int | None  # Current pot balance (if linked)
    projected_balance: int  # Expected balance at target date


class BudgetService:
    """Service for managing budgets and tracking spend."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_all_budgets(self, account_id: str) -> list[Budget]:
        """Get all budgets for a specific account.

        Args:
            account_id: Account ID to filter budgets

        Returns:
            List of budgets for the account
        """
        result = await self._session.execute(
            select(Budget).where(Budget.account_id == account_id)
        )
        return list(result.scalars().all())

    async def create_budget(
        self,
        account_id: str,
        category: str,
        amount: int,
        period: str = "monthly",
        start_day: int = 1,
        name: str | None = None,
        group_id: str | None = None,
        period_type: str = "monthly",
        annual_amount: int | None = None,
        target_month: int | None = None,
        linked_pot_id: str | None = None,
    ) -> Budget:
        """Create a new budget for an account.

        Args:
            account_id: Account ID to associate the budget with
            category: Category name to track
            amount: Budget amount in pence (monthly contribution for sinking funds)
            period: Period type ("monthly" or "weekly")
            start_day: Day of month budget resets
            name: Optional display name (e.g., "Elodie Piano")
            group_id: Budget group ID (required for grouped budgets)
            period_type: "weekly", "monthly", "quarterly", "annual", "bi-annual"
            annual_amount: Total annual target for sinking funds (in pence)
            target_month: Month when annual expense is due (1-12)
            linked_pot_id: Monzo Pot ID for pot-backed budgets

        Returns:
            Created budget
        """
        budget = Budget(
            id=uuid4(),
            account_id=account_id,
            category=category,
            amount=amount,
            period=period,
            start_day=start_day,
            name=name,
            group_id=group_id,
            period_type=period_type,
            annual_amount=annual_amount,
            target_month=target_month,
            linked_pot_id=linked_pot_id,
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
        name: str | None = None,
        group_id: str | None = None,
        period_type: str | None = None,
        annual_amount: int | None = None,
        target_month: int | None = None,
        linked_pot_id: str | None = None,
    ) -> Budget | None:
        """Update an existing budget.

        Args:
            budget_id: ID of budget to update
            category: Category name to track
            amount: Budget amount in pence
            period: Period type ("monthly" or "weekly")
            start_day: Day of month budget resets
            name: Display name
            group_id: Budget group ID
            period_type: "weekly", "monthly", "quarterly", "annual", "bi-annual"
            annual_amount: Total annual target for sinking funds
            target_month: Month when annual expense is due (1-12)
            linked_pot_id: Monzo Pot ID for pot-backed budgets

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
        if name is not None:
            budget.name = name
        if group_id is not None:
            budget.group_id = group_id
        if period_type is not None:
            budget.period_type = period_type
        if annual_amount is not None:
            budget.annual_amount = annual_amount
        if target_month is not None:
            budget.target_month = target_month
        if linked_pot_id is not None:
            budget.linked_pot_id = linked_pot_id

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
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.account_id == budget.account_id,
                    Transaction.custom_category == budget.category,
                    Transaction.created_at >= period_start,
                    Transaction.created_at <= period_end,
                    Transaction.amount < 0,
                )
            )
        )
        return abs(result.scalar() or 0)

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
        account_id: str,
        reference_date: date,
    ) -> list[BudgetStatus]:
        """Get status for all budgets for a specific account.

        Optimized to use a single database query instead of N+1 queries.

        Args:
            account_id: Account ID to filter budgets
            reference_date: Reference date for period calculation

        Returns:
            List of BudgetStatus for all budgets
        """
        budgets = await self.get_all_budgets(account_id)

        if not budgets:
            return []

        # Build period ranges and collect categories for each budget
        budget_periods: dict[Any, tuple[date, date]] = {}
        categories: set[str] = set()

        for budget in budgets:
            period_start, period_end = get_current_period(
                reference_date,
                budget.start_day,
                budget.period,
            )
            budget_periods[budget.id] = (period_start, period_end)
            categories.add(budget.category)

        # Find the earliest start and latest end to bound the query
        all_starts = [p[0] for p in budget_periods.values()]
        all_ends = [p[1] for p in budget_periods.values()]
        min_start = min(all_starts)
        max_end = max(all_ends)

        # Single query: get all transactions for this account in relevant categories
        result = await self._session.execute(
            select(
                Transaction.custom_category,
                Transaction.amount,
                Transaction.created_at,
            ).where(
                and_(
                    Transaction.account_id == account_id,
                    Transaction.custom_category.in_(categories),
                    Transaction.created_at >= min_start,
                    Transaction.created_at <= max_end,
                    Transaction.amount < 0,  # Only spending
                )
            )
        )
        transactions = result.all()

        # Group spending by category and check if within each budget's specific period
        # Since budgets can have different reset days, we need to check per-budget
        category_spend_by_budget: dict[Any, int] = defaultdict(int)

        for budget in budgets:
            period_start, period_end = budget_periods[budget.id]
            for tx in transactions:
                if (
                    tx.custom_category == budget.category
                    and period_start <= tx.created_at.date() <= period_end
                ):
                    category_spend_by_budget[budget.id] += abs(tx.amount)

        # Build status objects
        statuses = []
        for budget in budgets:
            period_start, period_end = budget_periods[budget.id]
            spent = category_spend_by_budget.get(budget.id, 0)
            remaining = budget.amount - spent
            percentage = (spent / budget.amount) * 100 if budget.amount > 0 else 0

            if percentage >= 100:
                status = "over"
            elif percentage >= 80:
                status = "warning"
            else:
                status = "under"

            statuses.append(
                BudgetStatus(
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
            )

        return statuses

    async def get_sinking_fund_status(
        self,
        budget: Budget,
        reference_date: date,
        pot_balance: int | None = None,
    ) -> SinkingFundStatus:
        """Get the status of a sinking fund budget.

        Sinking funds track monthly contributions toward an annual target.
        Unlike spending budgets, they track deposits to a pot, not spending.

        Args:
            budget: Budget to check (must be a sinking fund)
            reference_date: Reference date for calculations
            pot_balance: Current pot balance (fetched from Monzo API)

        Returns:
            SinkingFundStatus with contribution progress
        """
        if not budget.is_sinking_fund:
            raise ValueError("Budget is not a sinking fund")

        target_month = budget.target_month or 12  # Default to December
        months_elapsed, months_remaining = calculate_sinking_fund_months(
            target_month, reference_date
        )

        # Monthly contribution target
        monthly_contribution = budget.monthly_contribution

        # Expected contributions to date
        expected_to_date = monthly_contribution * months_elapsed

        # Actual contributions - use pot balance if available, otherwise estimate
        # In Phase 2, we'll track actual pot deposits. For now, use pot balance.
        contributions_to_date = pot_balance if pot_balance is not None else 0

        # Variance (positive = ahead, negative = behind)
        variance = contributions_to_date - expected_to_date

        # On track if contributions >= expected
        on_track = contributions_to_date >= expected_to_date

        # Projected balance at target date
        # If on track, assume current rate continues
        if months_remaining > 0 and months_elapsed > 0:
            monthly_rate = contributions_to_date / months_elapsed
            projected_balance = contributions_to_date + int(monthly_rate * months_remaining)
        else:
            projected_balance = contributions_to_date

        return SinkingFundStatus(
            budget_id=budget.id,
            name=budget.name,
            category=budget.category,
            target_amount=budget.annual_amount or 0,
            monthly_contribution=monthly_contribution,
            contributions_to_date=contributions_to_date,
            expected_to_date=expected_to_date,
            variance=variance,
            on_track=on_track,
            target_month=target_month,
            months_remaining=months_remaining,
            pot_balance=pot_balance,
            projected_balance=projected_balance,
        )

    async def get_all_sinking_funds(self, account_id: str) -> list[Budget]:
        """Get all sinking fund budgets for an account.

        Args:
            account_id: Account ID to filter budgets

        Returns:
            List of sinking fund budgets
        """
        result = await self._session.execute(
            select(Budget).where(
                and_(
                    Budget.account_id == account_id,
                    Budget.period_type.in_(["quarterly", "annual", "bi-annual"]),
                )
            )
        )
        return list(result.scalars().all())
