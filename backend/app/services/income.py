"""Income tracking service.

Computes per-period income vs expense summaries.
Income = positive transactions without a budget_id and not excluded.
Expense = sum of spent across all monthly envelopes in the period.
"""

import logging
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, BudgetPeriod, EnvelopeBalance, Transaction

logger = logging.getLogger(__name__)


class IncomeService:
    """Service for income vs expense tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_income_summary(
        self,
        account_id: UUID,
        months: int = 6,
    ) -> list[dict[str, Any]]:
        """Get per-period income vs expense summary.

        Args:
            account_id: The account to query.
            months: Number of recent periods to include.

        Returns:
            List of period summaries ordered by period_start ascending.
        """
        # Get recent periods
        periods = await self._get_recent_periods(account_id, months)

        results = []
        for period in periods:
            income = await self._compute_income(
                account_id, period.period_start, period.period_end
            )
            expense = await self._compute_expense(period.id)

            results.append({
                "period_start": period.period_start.isoformat(),
                "income_total_pence": income,
                "expense_total_pence": expense,
                "net_pence": income - expense,
            })

        return results

    async def _get_recent_periods(
        self, account_id: UUID, months: int
    ) -> list[BudgetPeriod]:
        """Get the most recent N periods, ordered ascending."""
        result = await self._session.execute(
            select(BudgetPeriod)
            .where(BudgetPeriod.account_id == account_id)
            .order_by(BudgetPeriod.period_start.desc())
            .limit(months)
        )
        periods = list(result.scalars().all())
        periods.reverse()  # Return ascending
        return periods

    async def _compute_income(
        self,
        account_id: UUID,
        period_start: date,
        period_end: date,
    ) -> int:
        """Compute income for a period.

        Income = SUM(amount) WHERE amount > 0 AND budget_id IS NULL
                 AND (review_status IS NULL OR review_status != 'excluded')
        """
        next_day = period_end + timedelta(days=1)
        result = await self._session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.account_id == account_id,
                    Transaction.amount > 0,
                    Transaction.budget_id.is_(None),
                    Transaction.created_at >= period_start,
                    Transaction.created_at < next_day,
                    # Exclude explicitly excluded transactions
                    (Transaction.review_status.is_(None))
                    | (Transaction.review_status != "excluded"),
                )
            )
        )
        return result.scalar() or 0

    async def _compute_expense(self, period_id: UUID) -> int:
        """Compute total expense for a period.

        Sums allocated from envelope balances for monthly budgets only,
        but we actually want spent — however spent requires transaction sums.
        For simplicity and consistency, we sum the spent across all envelopes.

        Actually: expense = sum of spent across all monthly envelopes.
        We need to join EnvelopeBalance -> Budget (monthly, not deleted)
        and then compute spent for each. That's expensive per-envelope.

        Instead, sum all negative transactions that have a budget_id
        pointing to a monthly, non-deleted budget within the period.
        """
        # Get all monthly, non-deleted budget IDs that have envelopes in this period
        budget_ids_result = await self._session.execute(
            select(EnvelopeBalance.budget_id).where(
                EnvelopeBalance.period_id == period_id
            ).join(
                Budget, Budget.id == EnvelopeBalance.budget_id
            ).where(
                and_(
                    Budget.period_type == "monthly",
                    Budget.deleted_at.is_(None),
                )
            )
        )
        budget_ids = [row[0] for row in budget_ids_result.all()]

        if not budget_ids:
            return 0

        # Get the period boundaries for computing spent
        period_result = await self._session.execute(
            select(BudgetPeriod).where(BudgetPeriod.id == period_id)
        )
        period = period_result.scalar_one_or_none()
        if not period:
            return 0

        next_day = period.period_end + timedelta(days=1)
        spent_result = await self._session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.budget_id.in_(budget_ids),
                    Transaction.created_at >= period.period_start,
                    Transaction.created_at < next_day,
                    Transaction.amount < 0,
                )
            )
        )
        return abs(spent_result.scalar() or 0)
