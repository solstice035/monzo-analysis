"""Envelope dashboard service.

Builds the full envelope view: all budget groups with their envelopes,
including computed spent and available for each.
Excludes sinking funds and soft-deleted budgets.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Budget, BudgetGroup, BudgetPeriod, EnvelopeBalance, Transaction

logger = logging.getLogger(__name__)


class EnvelopeDashboardService:
    """Service for building the envelope dashboard view."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_envelope_dashboard(
        self,
        account_id: UUID,
        period_id: UUID | None = None,
    ) -> dict[str, Any] | None:
        """Build the full envelope dashboard for a period.

        If period_id is None, uses the current active period.

        Returns:
            Dashboard dict with groups, envelopes, and totals.
            None if no period found.
        """
        # Get period
        if period_id:
            period = await self._get_period(period_id, account_id)
        else:
            period = await self._get_active_period(account_id)

        if not period:
            return None

        # Compute next period start for spent calculation
        if period.period_start.month == 12:
            from datetime import date
            next_start = date(period.period_start.year + 1, 1, 28)
        else:
            from datetime import date
            next_start = date(period.period_start.year, period.period_start.month + 1, 28)

        # Load all envelope balances for this period with their budgets
        envelopes = await self._get_envelope_balances(period.id)

        # Load all budget groups for the account
        groups = await self._get_groups(account_id)

        # Compute spent for each envelope
        envelope_data = {}
        for eb in envelopes:
            spent = await self._compute_spent(
                eb.budget_id, period.period_start, next_start
            )
            available = eb.allocated + eb.rollover - spent
            pct_used = (spent / eb.allocated * 100) if eb.allocated > 0 else 0.0

            envelope_data[eb.budget_id] = {
                "allocated": eb.allocated,
                "original_allocated": eb.original_allocated,
                "rollover": eb.rollover,
                "spent": spent,
                "available": available,
                "pct_used": round(pct_used, 2),
            }

        # Build response grouped by BudgetGroup
        response_groups = []
        grand_allocated = 0
        grand_spent = 0
        grand_available = 0

        for group in groups:
            group_envelopes = []
            group_allocated = 0
            group_spent = 0
            group_available = 0

            # Get budgets in this group (monthly only, not deleted)
            budgets = await self._get_group_budgets(group.id)

            for budget in budgets:
                data = envelope_data.get(budget.id)
                if not data:
                    continue  # No envelope for this budget (shouldn't happen normally)

                group_envelopes.append({
                    "budget_id": str(budget.id),
                    "budget_name": budget.name,
                    "category": budget.category,
                    **data,
                })
                group_allocated += data["allocated"]
                group_spent += data["spent"]
                group_available += data["available"]

            if group_envelopes:  # Only include groups with active envelopes
                response_groups.append({
                    "group_id": str(group.id),
                    "group_name": group.name,
                    "icon": group.icon,
                    "display_order": group.display_order,
                    "total_allocated": group_allocated,
                    "total_spent": group_spent,
                    "total_available": group_available,
                    "envelopes": group_envelopes,
                })
                grand_allocated += group_allocated
                grand_spent += group_spent
                grand_available += group_available

        return {
            "period_id": str(period.id),
            "period_start": period.period_start.isoformat(),
            "period_end": period.period_end.isoformat(),
            "period_status": period.status,
            "groups": response_groups,
            "total_allocated": grand_allocated,
            "total_spent": grand_spent,
            "total_available": grand_available,
        }

    async def _get_active_period(self, account_id: UUID) -> BudgetPeriod | None:
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

    async def _get_period(self, period_id: UUID, account_id: UUID) -> BudgetPeriod | None:
        result = await self._session.execute(
            select(BudgetPeriod).where(
                and_(
                    BudgetPeriod.id == period_id,
                    BudgetPeriod.account_id == account_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_envelope_balances(self, period_id: UUID) -> list[EnvelopeBalance]:
        result = await self._session.execute(
            select(EnvelopeBalance).where(EnvelopeBalance.period_id == period_id)
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

    async def _compute_spent(
        self,
        budget_id: UUID,
        period_start,
        next_period_start,
    ) -> int:
        """Compute spent for a budget within period boundaries."""
        result = await self._session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.budget_id == budget_id,
                    Transaction.created_at >= period_start,
                    Transaction.created_at < next_period_start,
                    Transaction.amount < 0,
                )
            )
        )
        return abs(result.scalar() or 0)
