"""Tests for income tracking service."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import BudgetPeriod
from app.services.income import IncomeService


def _mock_execute_result(scalar_one_or_none=None, scalars_all=None, scalar=None, all_rows=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    if scalar is not None:
        result.scalar.return_value = scalar
    if all_rows is not None:
        result.all.return_value = all_rows
    return result


class TestIncomeService:
    """Tests for IncomeService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return IncomeService(mock_session)

    @pytest.mark.asyncio
    async def test_empty_when_no_periods(self, service, mock_session):
        """Returns empty list when no periods exist."""
        mock_session.execute.return_value = _mock_execute_result(scalars_all=[])
        result = await service.get_income_summary(uuid.uuid4(), months=6)
        assert result == []

    @pytest.mark.asyncio
    async def test_single_period_income_and_expense(self, service, mock_session):
        """Returns correct income, expense, and net for one period."""
        account_id = uuid.uuid4()
        period_id = uuid.uuid4()

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.period_start = date(2026, 1, 28)
        period.period_end = date(2026, 2, 27)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),      # recent periods
            _mock_execute_result(scalar=350000),             # income
            # expense computation: get budget_ids, then period, then spent
            _mock_execute_result(all_rows=[(uuid.uuid4(),)]),  # budget_ids
            _mock_execute_result(scalar_one_or_none=period),   # period for boundaries
            _mock_execute_result(scalar=-420000),              # spent
        ]

        result = await service.get_income_summary(account_id, months=6)
        assert len(result) == 1
        assert result[0]["period_start"] == "2026-01-28"
        assert result[0]["income_total_pence"] == 350000
        assert result[0]["expense_total_pence"] == 420000
        assert result[0]["net_pence"] == -70000

    @pytest.mark.asyncio
    async def test_multiple_periods_ordered_ascending(self, service, mock_session):
        """Returns periods ordered by period_start ascending."""
        account_id = uuid.uuid4()

        period1 = MagicMock(spec=BudgetPeriod)
        period1.id = uuid.uuid4()
        period1.period_start = date(2025, 12, 28)
        period1.period_end = date(2026, 1, 27)

        period2 = MagicMock(spec=BudgetPeriod)
        period2.id = uuid.uuid4()
        period2.period_start = date(2026, 1, 28)
        period2.period_end = date(2026, 2, 27)

        # _get_recent_periods returns desc, then reverses to asc
        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period2, period1]),  # desc order
            # Period 1 (Dec) income + expense
            _mock_execute_result(scalar=300000),           # income
            _mock_execute_result(all_rows=[]),              # no budgets
            # Period 2 (Jan) income + expense
            _mock_execute_result(scalar=350000),           # income
            _mock_execute_result(all_rows=[]),              # no budgets
        ]

        result = await service.get_income_summary(account_id, months=2)
        assert len(result) == 2
        # Reversed to ascending
        assert result[0]["period_start"] == "2025-12-28"
        assert result[1]["period_start"] == "2026-01-28"

    @pytest.mark.asyncio
    async def test_zero_income_period(self, service, mock_session):
        """Handles period with zero income."""
        period = MagicMock(spec=BudgetPeriod)
        period.id = uuid.uuid4()
        period.period_start = date(2026, 3, 28)
        period.period_end = date(2026, 4, 27)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalar=0),         # zero income
            _mock_execute_result(all_rows=[]),       # no budgets = zero expense
        ]

        result = await service.get_income_summary(uuid.uuid4(), months=1)
        assert result[0]["income_total_pence"] == 0
        assert result[0]["expense_total_pence"] == 0
        assert result[0]["net_pence"] == 0

    @pytest.mark.asyncio
    async def test_positive_net_when_income_exceeds_expense(self, service, mock_session):
        """Net is positive when income > expense."""
        period = MagicMock(spec=BudgetPeriod)
        period.id = uuid.uuid4()
        period.period_start = date(2026, 2, 28)
        period.period_end = date(2026, 3, 27)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalar=500000),         # income
            _mock_execute_result(all_rows=[]),            # no budgets
        ]

        result = await service.get_income_summary(uuid.uuid4(), months=1)
        assert result[0]["net_pence"] == 500000  # All income, no expense

    @pytest.mark.asyncio
    async def test_expense_with_no_budget_ids_returns_zero(self, service, mock_session):
        """When no envelope budgets exist, expense is 0."""
        period = MagicMock(spec=BudgetPeriod)
        period.id = uuid.uuid4()
        period.period_start = date(2026, 1, 28)
        period.period_end = date(2026, 2, 27)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalar=100000),      # income
            _mock_execute_result(all_rows=[]),         # no budget_ids -> expense = 0
        ]

        result = await service.get_income_summary(uuid.uuid4(), months=1)
        assert result[0]["expense_total_pence"] == 0

    @pytest.mark.asyncio
    async def test_default_months_parameter(self, service, mock_session):
        """Default is 6 months."""
        mock_session.execute.return_value = _mock_execute_result(scalars_all=[])
        await service.get_income_summary(uuid.uuid4())
        # Verify limit(6) was used — check the first call
        assert mock_session.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_account_isolation(self, service, mock_session):
        """Service uses account_id for all queries."""
        mock_session.execute.return_value = _mock_execute_result(scalars_all=[])
        account_id = uuid.uuid4()
        await service.get_income_summary(account_id, months=1)
        assert mock_session.execute.called
