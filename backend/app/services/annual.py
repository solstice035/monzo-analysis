"""Annual view service.

Builds a year-long matrix of budget groups × months,
with allocated/spent/available per cell.
Excludes sinking funds and soft-deleted budgets.
"""

import logging
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, BudgetGroup, BudgetPeriod, EnvelopeBalance, Transaction

logger = logging.getLogger(__name__)

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _status(spent: int, allocated: int) -> str:
    """Determine envelope status based on spent vs allocated."""
    if allocated <= 0:
        return "under" if spent == 0 else "over"
    if spent <= allocated * 0.9:
        return "under"
    if spent <= allocated:
        return "on_track"
    return "over"


class AnnualService:
    """Service for building the annual budget overview."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_annual_view(
        self,
        account_id: UUID,
        year: int,
    ) -> dict[str, Any]:
        """Build the annual budget matrix for a given year.

        Returns groups × months matrix with totals.
        """
        # 1. Get all periods for this account whose period_start falls in the year
        periods = await self._get_periods_for_year(account_id, year)

        # Map month -> period
        month_to_period: dict[int, Any] = {}
        for p in periods:
            month_to_period[p.period_start.month] = p

        # 2. Get all budget groups for account
        groups = await self._get_groups(account_id)

        # 3. For each group, get monthly budgets
        response_groups = []
        # monthly_totals[month] = {allocated, spent, available}
        monthly_totals: dict[int, dict[str, int]] = {
            m: {"allocated": 0, "spent": 0, "available": 0} for m in range(1, 13)
        }

        for group in groups:
            budgets = await self._get_group_budgets(group.id)
            if not budgets:
                continue

            budget_ids = [b.id for b in budgets]

            group_months = []
            group_total_allocated = 0
            group_total_spent = 0
            group_total_available = 0

            for month in range(1, 13):
                period = month_to_period.get(month)
                if not period:
                    group_months.append({
                        "month": month,
                        "month_name": MONTH_NAMES[month],
                        "period_id": None,
                        "allocated": 0,
                        "spent": 0,
                        "available": 0,
                        "status": "under",
                    })
                    continue

                # Get envelope balances for these budgets in this period
                allocated = await self._get_allocated_for_budgets(
                    budget_ids, period.id
                )
                spent = await self._get_spent_for_budgets(
                    budget_ids, period.period_start, period.period_end
                )
                available = allocated - spent
                status = _status(spent, allocated)

                group_months.append({
                    "month": month,
                    "month_name": MONTH_NAMES[month],
                    "period_id": str(period.id),
                    "allocated": allocated,
                    "spent": spent,
                    "available": available,
                    "status": status,
                })

                group_total_allocated += allocated
                group_total_spent += spent
                group_total_available += available

                monthly_totals[month]["allocated"] += allocated
                monthly_totals[month]["spent"] += spent
                monthly_totals[month]["available"] += available

            response_groups.append({
                "group_id": str(group.id),
                "group_name": group.name,
                "months": group_months,
                "total_allocated": group_total_allocated,
                "total_spent": group_total_spent,
                "total_available": group_total_available,
            })

        # Build monthly_totals list and grand total
        monthly_totals_list = []
        grand_allocated = 0
        grand_spent = 0
        grand_available = 0

        for month in range(1, 13):
            mt = monthly_totals[month]
            monthly_totals_list.append({
                "month": month,
                "allocated": mt["allocated"],
                "spent": mt["spent"],
                "available": mt["available"],
            })
            grand_allocated += mt["allocated"]
            grand_spent += mt["spent"]
            grand_available += mt["available"]

        return {
            "year": year,
            "groups": response_groups,
            "monthly_totals": monthly_totals_list,
            "grand_total": {
                "allocated": grand_allocated,
                "spent": grand_spent,
                "available": grand_available,
            },
        }

    async def _get_periods_for_year(
        self, account_id: UUID, year: int
    ) -> list[BudgetPeriod]:
        """Get all budget periods whose period_start falls within the given year."""
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        result = await self._session.execute(
            select(BudgetPeriod).where(
                and_(
                    BudgetPeriod.account_id == account_id,
                    BudgetPeriod.period_start >= start,
                    BudgetPeriod.period_start <= end,
                )
            )
        )
        return list(result.scalars().all())

    async def _get_groups(self, account_id: UUID) -> list[BudgetGroup]:
        result = await self._session.execute(
            select(BudgetGroup)
            .where(BudgetGroup.account_id == account_id)
            .order_by(BudgetGroup.display_order)
        )
        return list(result.scalars().all())

    async def _get_group_budgets(self, group_id: UUID) -> list[Budget]:
        """Get monthly, non-deleted budgets for a group."""
        result = await self._session.execute(
            select(Budget).where(
                and_(
                    Budget.group_id == group_id,
                    Budget.period_type == "monthly",
                    Budget.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def _get_allocated_for_budgets(
        self, budget_ids: list[UUID], period_id: UUID
    ) -> int:
        """Sum allocated across all budgets for a period."""
        result = await self._session.execute(
            select(func.coalesce(func.sum(EnvelopeBalance.allocated), 0)).where(
                and_(
                    EnvelopeBalance.budget_id.in_(budget_ids),
                    EnvelopeBalance.period_id == period_id,
                )
            )
        )
        return result.scalar() or 0

    async def _get_spent_for_budgets(
        self,
        budget_ids: list[UUID],
        period_start: date,
        period_end: date,
    ) -> int:
        """Compute total spent across budgets within period boundaries.

        Uses period_end + 1 day as the upper bound since periods are inclusive.
        """
        from datetime import timedelta
        next_day = period_end + timedelta(days=1)

        result = await self._session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.budget_id.in_(budget_ids),
                    Transaction.created_at >= period_start,
                    Transaction.created_at < next_day,
                    Transaction.amount < 0,
                )
            )
        )
        return abs(result.scalar() or 0)
