"""Surplus service.

Computes per-period surplus (allocated - spent) with cumulative running total
across budget periods. Only monthly envelopes participate.
"""

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, BudgetGroup, BudgetPeriod, EnvelopeBalance, Transaction

logger = logging.getLogger(__name__)


class SurplusService:
    """Service for computing budget surplus/deficit over time."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_surplus(
        self,
        account_id: UUID,
        months: int = 12,
    ) -> list[dict[str, Any]]:
        """Get per-period surplus data with cumulative totals.

        Returns list of dicts ordered by period_start ascending, each containing
        total_allocated, total_spent, surplus_pence, and cumulative_surplus_pence.
        Only monthly budgets are included (sinking funds excluded).
        """
        periods = await self._get_recent_periods(account_id, months)
        if not periods:
            return []

        results: list[dict[str, Any]] = []
        cumulative = 0

        for period in periods:
            # Get envelope balances for this period
            envelopes = await self._get_envelope_balances(period.id)

            total_allocated = 0
            total_spent = 0

            for eb in envelopes:
                # Check budget is monthly and not deleted
                budget = await self._get_budget(eb.budget_id)
                if not budget:
                    continue
                if budget.period_type != "monthly" or budget.deleted_at is not None:
                    continue

                total_allocated += eb.allocated
                spent = await self._compute_spent(
                    eb.budget_id, period.period_start, period.period_end,
                )
                total_spent += spent

            surplus = total_allocated - total_spent
            cumulative += surplus

            results.append({
                "period_start": period.period_start.isoformat(),
                "period_end": period.period_end.isoformat(),
                "total_allocated": total_allocated,
                "total_spent": total_spent,
                "surplus_pence": surplus,
                "cumulative_surplus_pence": cumulative,
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
        periods.reverse()
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

    async def _compute_spent(
        self, budget_id: UUID, period_start, period_end,
    ) -> int:
        """Compute spent for a budget within period boundaries."""
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

    async def get_surplus_by_group(
        self,
        account_id: UUID,
        months: int = 12,
    ) -> list[dict[str, Any]]:
        """Get per-group, per-period surplus data.

        Returns list of groups, each containing periods with allocated/spent/surplus.
        Only monthly budgets are included (sinking funds excluded).
        Ordered by period_start asc, group display_order asc.
        """
        periods = await self._get_recent_periods(account_id, months)
        if not periods:
            return []

        # Get all budget groups for this account, ordered by display_order
        groups = await self._get_budget_groups(account_id)
        if not groups:
            return []

        # Build per-group, per-period data
        group_data: dict[UUID, dict[str, Any]] = {}
        for group in groups:
            group_data[group.id] = {
                "group_id": str(group.id),
                "group_name": group.name,
                "periods": [],
            }

        for period in periods:
            envelopes = await self._get_envelope_balances(period.id)

            # Accumulate per-group totals for this period
            group_totals: dict[UUID, dict[str, int]] = {}
            for group in groups:
                group_totals[group.id] = {"allocated": 0, "spent": 0}

            for eb in envelopes:
                budget = await self._get_budget(eb.budget_id)
                if not budget:
                    continue
                if budget.period_type != "monthly" or budget.deleted_at is not None:
                    continue
                if budget.group_id is None or budget.group_id not in group_totals:
                    continue

                group_totals[budget.group_id]["allocated"] += eb.allocated
                spent = await self._compute_spent(
                    eb.budget_id, period.period_start, period.period_end,
                )
                group_totals[budget.group_id]["spent"] += spent

            for group in groups:
                totals = group_totals[group.id]
                surplus = totals["allocated"] - totals["spent"]
                group_data[group.id]["periods"].append({
                    "period_start": period.period_start.isoformat(),
                    "allocated": totals["allocated"],
                    "spent": totals["spent"],
                    "surplus_pence": surplus,
                })

        # Filter out groups that had zero activity across all periods
        result = []
        for group in groups:
            gd = group_data[group.id]
            has_activity = any(
                p["allocated"] != 0 or p["spent"] != 0
                for p in gd["periods"]
            )
            if has_activity:
                result.append(gd)

        return result

    async def _get_budget_groups(self, account_id: UUID) -> list[BudgetGroup]:
        """Get budget groups for an account, ordered by display_order."""
        result = await self._session.execute(
            select(BudgetGroup)
            .where(BudgetGroup.account_id == account_id)
            .order_by(BudgetGroup.display_order.asc())
        )
        return list(result.scalars().all())
