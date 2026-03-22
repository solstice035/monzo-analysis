"""Trends service.

Provides envelope spending trends over multiple periods and
identifies chronically over-budget envelopes.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, BudgetGroup, BudgetPeriod, EnvelopeBalance, Transaction

logger = logging.getLogger(__name__)


class TrendsService:
    """Service for envelope spending trend analysis."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_envelope_trends(
        self,
        account_id: UUID,
        months: int = 6,
        budget_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Get envelope spending trends over the last N months.

        Returns a list of dicts with period/envelope data, ordered by
        period_start ascending, then group_name, then budget_name.
        """
        periods = await self._get_recent_periods(account_id, months)
        if not periods:
            return []

        results: list[dict[str, Any]] = []

        for period in periods:
            # Get envelope balances for this period
            envelopes = await self._get_envelope_balances(period.id)

            for eb in envelopes:
                # Load the budget and its group
                budget = await self._get_budget(eb.budget_id)
                if not budget:
                    continue
                # Skip non-monthly and deleted budgets
                if budget.period_type != "monthly" or budget.deleted_at is not None:
                    continue
                # Filter by budget_id if specified
                if budget_id and budget.id != budget_id:
                    continue

                group = await self._get_group(budget.group_id) if budget.group_id else None
                group_name = group.name if group else "Ungrouped"

                spent = await self._compute_spent(
                    eb.budget_id, period.period_start, period.period_end,
                )
                pct_used = round(spent / eb.allocated * 100, 1) if eb.allocated > 0 else 0.0

                results.append({
                    "period_start": period.period_start.isoformat(),
                    "budget_name": budget.name,
                    "group_name": group_name,
                    "allocated": eb.allocated,
                    "spent": spent,
                    "pct_used": pct_used,
                    "over_budget": spent > eb.allocated,
                })

        # Sort: period_start asc, group_name, budget_name
        results.sort(key=lambda r: (r["period_start"], r["group_name"], r["budget_name"] or ""))
        return results

    async def get_over_budget_envelopes(
        self,
        account_id: UUID,
        months: int = 6,
    ) -> list[dict[str, Any]]:
        """Get envelopes over budget in >50% of recent periods.

        Returns list of chronically over-budget envelopes with stats.
        """
        periods = await self._get_recent_periods(account_id, months)
        if not periods:
            return []

        total_periods = len(periods)

        # Track per-budget over-budget counts and overspend amounts
        budget_stats: dict[UUID, dict[str, Any]] = {}

        for period in periods:
            envelopes = await self._get_envelope_balances(period.id)

            for eb in envelopes:
                budget = await self._get_budget(eb.budget_id)
                if not budget:
                    continue
                if budget.period_type != "monthly" or budget.deleted_at is not None:
                    continue

                spent = await self._compute_spent(
                    eb.budget_id, period.period_start, period.period_end,
                )

                if eb.budget_id not in budget_stats:
                    group = await self._get_group(budget.group_id) if budget.group_id else None
                    budget_stats[eb.budget_id] = {
                        "budget_id": str(eb.budget_id),
                        "budget_name": budget.name,
                        "group_name": group.name if group else "Ungrouped",
                        "over_budget_count": 0,
                        "overspend_amounts": [],
                    }

                if spent > eb.allocated:
                    budget_stats[eb.budget_id]["over_budget_count"] += 1
                    budget_stats[eb.budget_id]["overspend_amounts"].append(spent - eb.allocated)

        # Filter to >50% over budget
        results = []
        for stats in budget_stats.values():
            if stats["over_budget_count"] > total_periods / 2:
                overspend_amounts = stats["overspend_amounts"]
                avg_overspend = (
                    sum(overspend_amounts) // len(overspend_amounts)
                    if overspend_amounts
                    else 0
                )
                results.append({
                    "budget_id": stats["budget_id"],
                    "budget_name": stats["budget_name"],
                    "group_name": stats["group_name"],
                    "over_budget_count": stats["over_budget_count"],
                    "total_periods": total_periods,
                    "pct_over": round(
                        stats["over_budget_count"] / total_periods * 100, 1
                    ),
                    "avg_overspend_pence": avg_overspend,
                })

        return results

    async def _get_recent_periods(
        self, account_id: UUID, months: int
    ) -> list[BudgetPeriod]:
        """Get the last N periods for an account, ordered by period_start ascending."""
        result = await self._session.execute(
            select(BudgetPeriod)
            .where(BudgetPeriod.account_id == account_id)
            .order_by(BudgetPeriod.period_start.desc())
            .limit(months)
        )
        periods = list(result.scalars().all())
        periods.reverse()  # Ascending order
        return periods

    async def _get_envelope_balances(self, period_id: UUID) -> list[EnvelopeBalance]:
        result = await self._session.execute(
            select(EnvelopeBalance).where(EnvelopeBalance.period_id == period_id)
        )
        return list(result.scalars().all())

    async def _get_budget(self, budget_id: UUID) -> Budget | None:
        result = await self._session.execute(
            select(Budget).where(Budget.id == budget_id)
        )
        return result.scalar_one_or_none()

    async def _get_group(self, group_id: UUID) -> BudgetGroup | None:
        result = await self._session.execute(
            select(BudgetGroup).where(BudgetGroup.id == group_id)
        )
        return result.scalar_one_or_none()

    async def _compute_spent(
        self, budget_id: UUID, period_start, period_end,
    ) -> int:
        """Compute spent for a budget within period boundaries.

        Uses period_end + 1 day as the upper bound (transactions on the 27th
        are included since created_at < day after period_end).
        """
        from datetime import timedelta
        upper_bound = period_end + timedelta(days=1)
        result = await self._session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.budget_id == budget_id,
                    Transaction.created_at >= period_start,
                    Transaction.created_at < upper_bound,
                    Transaction.amount < 0,
                )
            )
        )
        return abs(result.scalar() or 0)
