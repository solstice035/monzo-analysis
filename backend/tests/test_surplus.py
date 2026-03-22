"""Tests for surplus service and API endpoints."""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Budget, BudgetGroup, BudgetPeriod, EnvelopeBalance
from app.services.surplus import SurplusService


def _mock_execute_result(scalar_one_or_none=None, scalars_all=None, scalar=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    if scalar is not None:
        result.scalar.return_value = scalar
    return result


def _make_period(account_id, period_start, period_end, status="closed"):
    p = MagicMock(spec=BudgetPeriod)
    p.id = uuid.uuid4()
    p.account_id = account_id
    p.period_start = period_start
    p.period_end = period_end
    p.status = status
    return p


def _make_budget(budget_id, name="Test", period_type="monthly", deleted_at=None):
    b = MagicMock(spec=Budget)
    b.id = budget_id
    b.name = name
    b.period_type = period_type
    b.deleted_at = deleted_at
    return b


def _make_envelope(budget_id, period_id, allocated=50000):
    eb = MagicMock(spec=EnvelopeBalance)
    eb.id = uuid.uuid4()
    eb.budget_id = budget_id
    eb.period_id = period_id
    eb.allocated = allocated
    eb.original_allocated = allocated
    eb.rollover = 0
    return eb


class TestGetSurplus:
    """Tests for SurplusService.get_surplus."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return SurplusService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_periods(self, service, mock_session):
        mock_session.execute.return_value = _mock_execute_result(scalars_all=[])
        result = await service.get_surplus(uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_single_period_surplus(self, service, mock_session):
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, name="Groceries")
        envelope = _make_envelope(budget_id, period.id, allocated=50000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[envelope]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar=-30000),  # spent 30000
        ]

        result = await service.get_surplus(account_id, months=1)
        assert len(result) == 1
        assert result[0]["period_start"] == "2026-01-28"
        assert result[0]["period_end"] == "2026-02-27"
        assert result[0]["total_allocated"] == 50000
        assert result[0]["total_spent"] == 30000
        assert result[0]["surplus_pence"] == 20000
        assert result[0]["cumulative_surplus_pence"] == 20000

    @pytest.mark.asyncio
    async def test_deficit_negative_surplus(self, service, mock_session):
        """When spent > allocated, surplus should be negative."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, name="Eating Out")
        envelope = _make_envelope(budget_id, period.id, allocated=20000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[envelope]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar=-25000),
        ]

        result = await service.get_surplus(account_id, months=1)
        assert len(result) == 1
        assert result[0]["surplus_pence"] == -5000
        assert result[0]["cumulative_surplus_pence"] == -5000

    @pytest.mark.asyncio
    async def test_cumulative_surplus_across_periods(self, service, mock_session):
        """Cumulative surplus is a running total across periods."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()

        period1 = _make_period(account_id, date(2025, 12, 28), date(2026, 1, 27))
        period2 = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))

        budget = _make_budget(budget_id)
        eb1 = _make_envelope(budget_id, period1.id, allocated=50000)
        eb2 = _make_envelope(budget_id, period2.id, allocated=50000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period1, period2]),
            # Period 1: allocated 50000, spent 30000, surplus 20000
            _mock_execute_result(scalars_all=[eb1]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar=-30000),
            # Period 2: allocated 50000, spent 60000, surplus -10000
            _mock_execute_result(scalars_all=[eb2]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar=-60000),
        ]

        result = await service.get_surplus(account_id, months=2)
        assert len(result) == 2
        assert result[0]["surplus_pence"] == 20000
        assert result[0]["cumulative_surplus_pence"] == 20000
        assert result[1]["surplus_pence"] == -10000
        assert result[1]["cumulative_surplus_pence"] == 10000  # 20000 + (-10000)

    @pytest.mark.asyncio
    async def test_excludes_sinking_funds(self, service, mock_session):
        """Non-monthly budgets (sinking funds) are excluded."""
        account_id = uuid.uuid4()
        budget_id_monthly = uuid.uuid4()
        budget_id_annual = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget_monthly = _make_budget(budget_id_monthly, name="Groceries", period_type="monthly")
        budget_annual = _make_budget(budget_id_annual, name="Car Tax", period_type="annual")
        eb1 = _make_envelope(budget_id_monthly, period.id, allocated=50000)
        eb2 = _make_envelope(budget_id_annual, period.id, allocated=10000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[eb1, eb2]),
            _mock_execute_result(scalar_one_or_none=budget_monthly),
            _mock_execute_result(scalar=-30000),
            _mock_execute_result(scalar_one_or_none=budget_annual),  # Annual - skipped
        ]

        result = await service.get_surplus(account_id, months=1)
        assert len(result) == 1
        # Only monthly budget counted
        assert result[0]["total_allocated"] == 50000
        assert result[0]["total_spent"] == 30000

    @pytest.mark.asyncio
    async def test_excludes_deleted_budgets(self, service, mock_session):
        """Soft-deleted budgets are excluded from surplus calculation."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, deleted_at=datetime.now())
        envelope = _make_envelope(budget_id, period.id, allocated=50000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[envelope]),
            _mock_execute_result(scalar_one_or_none=budget),
        ]

        result = await service.get_surplus(account_id, months=1)
        assert len(result) == 1
        assert result[0]["total_allocated"] == 0
        assert result[0]["total_spent"] == 0
        assert result[0]["surplus_pence"] == 0

    @pytest.mark.asyncio
    async def test_multiple_envelopes_summed(self, service, mock_session):
        """Multiple envelopes in the same period are summed correctly."""
        account_id = uuid.uuid4()
        budget_id_1 = uuid.uuid4()
        budget_id_2 = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget1 = _make_budget(budget_id_1, name="Groceries")
        budget2 = _make_budget(budget_id_2, name="Transport")
        eb1 = _make_envelope(budget_id_1, period.id, allocated=50000)
        eb2 = _make_envelope(budget_id_2, period.id, allocated=30000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[eb1, eb2]),
            _mock_execute_result(scalar_one_or_none=budget1),
            _mock_execute_result(scalar=-40000),
            _mock_execute_result(scalar_one_or_none=budget2),
            _mock_execute_result(scalar=-20000),
        ]

        result = await service.get_surplus(account_id, months=1)
        assert len(result) == 1
        assert result[0]["total_allocated"] == 80000  # 50000 + 30000
        assert result[0]["total_spent"] == 60000  # 40000 + 20000
        assert result[0]["surplus_pence"] == 20000

    @pytest.mark.asyncio
    async def test_no_envelopes_period_has_zero_surplus(self, service, mock_session):
        """A period with no envelopes has zero allocated, spent, and surplus."""
        account_id = uuid.uuid4()
        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[]),  # No envelopes
        ]

        result = await service.get_surplus(account_id, months=1)
        assert len(result) == 1
        assert result[0]["total_allocated"] == 0
        assert result[0]["total_spent"] == 0
        assert result[0]["surplus_pence"] == 0
        assert result[0]["cumulative_surplus_pence"] == 0

    @pytest.mark.asyncio
    async def test_zero_spent_full_surplus(self, service, mock_session):
        """When nothing is spent, surplus equals allocated."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id)
        envelope = _make_envelope(budget_id, period.id, allocated=50000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[envelope]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar=0),  # No spending
        ]

        result = await service.get_surplus(account_id, months=1)
        assert result[0]["surplus_pence"] == 50000
        assert result[0]["total_spent"] == 0
