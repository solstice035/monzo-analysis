"""Budget period service for envelope budgeting with rollover.

Core YNAB-style mechanics:
- Periods run 28th to 27th each month
- Each period has EnvelopeBalance records for all active monthly budgets
- On close: compute spent, calculate available, create next period with rollover
- Sinking funds (period_type != 'monthly') are excluded
- Soft-deleted budgets are skipped in rollover
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Budget, BudgetPeriod, EnvelopeBalance, Transaction

logger = logging.getLogger(__name__)


@dataclass
class EnvelopeStatus:
    """Computed status of an envelope within a period."""

    budget_id: UUID
    budget_name: str | None
    category: str
    allocated: int
    original_allocated: int
    rollover: int
    spent: int  # Computed on read
    available: int  # allocated + rollover - spent
    pct_used: float


def calculate_period_dates(period_start: date) -> tuple[date, date]:
    """Calculate period end from period start.

    Period runs from the 28th of one month to the 27th of the next.

    Args:
        period_start: Must be the 28th of a month.

    Returns:
        Tuple of (period_start, period_end).
    """
    # Next month's 28th minus 1 day = 27th
    if period_start.month == 12:
        next_period_start = date(period_start.year + 1, 1, 28)
    else:
        next_period_start = date(period_start.year, period_start.month + 1, 28)
    period_end = next_period_start - timedelta(days=1)
    return period_start, period_end


def get_period_start_for_date(reference_date: date) -> date:
    """Get the period start date (28th) for a given reference date.

    If reference_date.day >= 28, period started this month.
    If reference_date.day < 28, period started last month.
    """
    if reference_date.day >= 28:
        return date(reference_date.year, reference_date.month, 28)
    else:
        if reference_date.month == 1:
            return date(reference_date.year - 1, 12, 28)
        else:
            return date(reference_date.year, reference_date.month - 1, 28)


class BudgetPeriodService:
    """Service for managing budget periods and envelope balances."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_period(
        self,
        account_id: UUID,
        period_start: date,
    ) -> BudgetPeriod:
        """Create a new budget period with envelope balances for all active monthly budgets.

        Args:
            account_id: Account to create period for.
            period_start: Start date (must be the 28th).

        Returns:
            Created BudgetPeriod.

        Raises:
            ValueError: If period already exists or start date is not the 28th.
        """
        if period_start.day != 28:
            raise ValueError(f"Period must start on the 28th, got day {period_start.day}")

        # Check for existing period
        existing = await self._get_period_by_start(account_id, period_start)
        if existing:
            raise ValueError(
                f"Period already exists for account {account_id} starting {period_start}"
            )

        _, period_end = calculate_period_dates(period_start)

        period = BudgetPeriod(
            id=uuid4(),
            account_id=account_id,
            period_start=period_start,
            period_end=period_end,
            status="active",
        )
        self._session.add(period)
        await self._session.flush()

        # Create envelope balances for all active monthly budgets
        budgets = await self._get_active_monthly_budgets(account_id)
        for budget in budgets:
            eb = EnvelopeBalance(
                id=uuid4(),
                budget_id=budget.id,
                period_id=period.id,
                allocated=budget.amount,
                original_allocated=budget.amount,
                rollover=0,
            )
            self._session.add(eb)

        await self._session.flush()
        logger.info(
            f"Created period {period_start} for account {account_id} "
            f"with {len(budgets)} envelopes"
        )
        return period

    async def get_current_period(self, account_id: UUID) -> BudgetPeriod | None:
        """Get the current active period for an account.

        Returns:
            Active BudgetPeriod or None if no active period exists.
        """
        result = await self._session.execute(
            select(BudgetPeriod)
            .where(
                and_(
                    BudgetPeriod.account_id == account_id,
                    BudgetPeriod.status == "active",
                )
            )
            .order_by(BudgetPeriod.period_start.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def close_period(
        self,
        account_id: UUID,
        period_id: UUID,
    ) -> BudgetPeriod:
        """Close a period and create the next one with rollover.

        Atomically:
        1. Mark period as 'closing'
        2. Compute spent for each envelope
        3. Create next period with rollovers
        4. Mark old period as 'closed'

        All in one DB transaction — if any step fails, everything rolls back.

        Args:
            account_id: Account ID.
            period_id: Period to close.

        Returns:
            The newly created next period.

        Raises:
            ValueError: If period not found, wrong account, or not active.
        """
        # Load period with envelope balances
        period = await self._get_period_with_envelopes(period_id)
        if not period:
            raise ValueError(f"Period {period_id} not found")
        if period.account_id != account_id:
            raise ValueError(f"Period {period_id} does not belong to account {account_id}")
        if period.status != "active":
            raise ValueError(f"Period {period_id} is not active (status: {period.status})")

        # Step 1: Mark as closing
        period.status = "closing"
        await self._session.flush()

        # Step 2: Compute next period start
        if period.period_start.month == 12:
            next_start = date(period.period_start.year + 1, 1, 28)
        else:
            next_start = date(period.period_start.year, period.period_start.month + 1, 28)

        _, next_end = calculate_period_dates(next_start)

        # Step 3: Create next period
        next_period = BudgetPeriod(
            id=uuid4(),
            account_id=account_id,
            period_start=next_start,
            period_end=next_end,
            status="active",
        )
        self._session.add(next_period)
        await self._session.flush()

        # Step 4: Compute spent and create next envelopes with rollover
        active_budgets = await self._get_active_monthly_budgets(account_id)
        active_budget_ids = {b.id for b in active_budgets}

        for eb in period.envelope_balances:
            # Skip soft-deleted budgets
            if eb.budget_id not in active_budget_ids:
                continue

            # Compute spent for this envelope
            spent = await self._compute_spent(
                eb.budget_id, period.period_start, next_start
            )
            available = eb.allocated + eb.rollover - spent

            # Find the current budget amount (may have changed mid-period)
            budget = next((b for b in active_budgets if b.id == eb.budget_id), None)
            if not budget:
                continue

            # Create next period's envelope with rollover
            next_eb = EnvelopeBalance(
                id=uuid4(),
                budget_id=eb.budget_id,
                period_id=next_period.id,
                allocated=budget.amount,
                original_allocated=budget.amount,
                rollover=available,  # Carry forward: positive = underspend, negative = overspend
            )
            self._session.add(next_eb)

        # Step 5: Create envelopes for any new budgets that didn't exist in the old period
        old_budget_ids = {eb.budget_id for eb in period.envelope_balances}
        for budget in active_budgets:
            if budget.id not in old_budget_ids:
                new_eb = EnvelopeBalance(
                    id=uuid4(),
                    budget_id=budget.id,
                    period_id=next_period.id,
                    allocated=budget.amount,
                    original_allocated=budget.amount,
                    rollover=0,
                )
                self._session.add(new_eb)

        # Step 6: Mark old period as closed
        period.status = "closed"
        await self._session.flush()

        logger.info(
            f"Closed period {period.period_start} for account {account_id}, "
            f"created next period {next_start}"
        )
        return next_period

    async def get_envelope_status(
        self,
        budget_id: UUID,
        period_id: UUID,
    ) -> EnvelopeStatus | None:
        """Get the computed status of an envelope balance.

        Args:
            budget_id: Budget ID.
            period_id: Period ID.

        Returns:
            EnvelopeStatus with computed spent and available, or None.
        """
        # Load envelope balance
        result = await self._session.execute(
            select(EnvelopeBalance).where(
                and_(
                    EnvelopeBalance.budget_id == budget_id,
                    EnvelopeBalance.period_id == period_id,
                )
            )
        )
        eb = result.scalar_one_or_none()
        if not eb:
            return None

        # Load period for date boundaries
        period_result = await self._session.execute(
            select(BudgetPeriod).where(BudgetPeriod.id == period_id)
        )
        period = period_result.scalar_one_or_none()
        if not period:
            return None

        # Load budget for name/category
        budget_result = await self._session.execute(
            select(Budget).where(Budget.id == budget_id)
        )
        budget = budget_result.scalar_one_or_none()
        if not budget:
            return None

        # Compute next period start for upper bound
        if period.period_start.month == 12:
            next_start = date(period.period_start.year + 1, 1, 28)
        else:
            next_start = date(period.period_start.year, period.period_start.month + 1, 28)

        spent = await self._compute_spent(budget_id, period.period_start, next_start)
        available = eb.allocated + eb.rollover - spent
        pct_used = (spent / eb.allocated * 100) if eb.allocated > 0 else 0.0

        return EnvelopeStatus(
            budget_id=budget_id,
            budget_name=budget.name,
            category=budget.category,
            allocated=eb.allocated,
            original_allocated=eb.original_allocated,
            rollover=eb.rollover,
            spent=spent,
            available=available,
            pct_used=round(pct_used, 2),
        )

    async def ensure_envelope_for_new_budget(
        self,
        budget: Budget,
    ) -> EnvelopeBalance | None:
        """Create an EnvelopeBalance for a new budget in the current active period.

        Called when a new monthly budget is created mid-period.
        Rollover is 0 (fresh start).

        Returns:
            Created EnvelopeBalance, or None if no active period.
        """
        if budget.period_type != "monthly":
            return None

        period = await self.get_current_period(budget.account_id)
        if not period:
            return None

        # Check if one already exists
        existing = await self._session.execute(
            select(EnvelopeBalance).where(
                and_(
                    EnvelopeBalance.budget_id == budget.id,
                    EnvelopeBalance.period_id == period.id,
                )
            )
        )
        if existing.scalar_one_or_none():
            return None  # Already exists

        eb = EnvelopeBalance(
            id=uuid4(),
            budget_id=budget.id,
            period_id=period.id,
            allocated=budget.amount,
            original_allocated=budget.amount,
            rollover=0,
        )
        self._session.add(eb)
        await self._session.flush()
        return eb

    # --- Private helpers ---

    async def _get_active_monthly_budgets(self, account_id: UUID) -> list[Budget]:
        """Get all active (non-deleted) monthly budgets for an account."""
        result = await self._session.execute(
            select(Budget).where(
                and_(
                    Budget.account_id == account_id,
                    Budget.period_type == "monthly",
                    Budget.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def _get_period_by_start(
        self, account_id: UUID, period_start: date
    ) -> BudgetPeriod | None:
        """Get a period by account and start date."""
        result = await self._session.execute(
            select(BudgetPeriod).where(
                and_(
                    BudgetPeriod.account_id == account_id,
                    BudgetPeriod.period_start == period_start,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_period_with_envelopes(self, period_id: UUID) -> BudgetPeriod | None:
        """Load a period with its envelope balances eagerly loaded."""
        result = await self._session.execute(
            select(BudgetPeriod)
            .where(BudgetPeriod.id == period_id)
            .options(selectinload(BudgetPeriod.envelope_balances))
        )
        return result.scalar_one_or_none()

    async def _compute_spent(
        self,
        budget_id: UUID,
        period_start: date,
        next_period_start: date,
    ) -> int:
        """Compute total spent for a budget within a period.

        Uses ABS(SUM(amount)) so refunds (positive amounts) net out naturally.
        Only considers transactions with matching budget_id.

        Args:
            budget_id: Budget to compute spend for.
            period_start: Inclusive start (DATE, compared against created_at).
            next_period_start: Exclusive end.

        Returns:
            Spent amount in pence (positive value).
        """
        result = await self._session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.budget_id == budget_id,
                    Transaction.created_at >= period_start,
                    Transaction.created_at < next_period_start,
                    Transaction.amount < 0,  # Only debits
                )
            )
        )
        total = result.scalar() or 0
        return abs(total)
