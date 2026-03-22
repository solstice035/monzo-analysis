"""Tests for trends service and API endpoints."""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Budget, BudgetGroup, BudgetPeriod, EnvelopeBalance
from app.services.trends import TrendsService


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


def _make_budget(budget_id, group_id, name="Test Budget", period_type="monthly", deleted_at=None):
    b = MagicMock(spec=Budget)
    b.id = budget_id
    b.group_id = group_id
    b.name = name
    b.period_type = period_type
    b.deleted_at = deleted_at
    return b


def _make_group(group_id, name="Test Group"):
    g = MagicMock(spec=BudgetGroup)
    g.id = group_id
    g.name = name
    return g


def _make_envelope(budget_id, period_id, allocated=50000, rollover=0):
    eb = MagicMock(spec=EnvelopeBalance)
    eb.id = uuid.uuid4()
    eb.budget_id = budget_id
    eb.period_id = period_id
    eb.allocated = allocated
    eb.original_allocated = allocated
    eb.rollover = rollover
    return eb


class TestGetEnvelopeTrends:
    """Tests for TrendsService.get_envelope_trends."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return TrendsService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_periods(self, service, mock_session):
        mock_session.execute.return_value = _mock_execute_result(scalars_all=[])
        result = await service.get_envelope_trends(uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_single_period_single_envelope(self, service, mock_session):
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, group_id, name="Groceries")
        group = _make_group(group_id, name="Variable Expenses")
        envelope = _make_envelope(budget_id, period.id, allocated=50000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),          # get_recent_periods
            _mock_execute_result(scalars_all=[envelope]),        # get_envelope_balances
            _mock_execute_result(scalar_one_or_none=budget),     # get_budget
            _mock_execute_result(scalar_one_or_none=group),      # get_group
            _mock_execute_result(scalar=-32000),                 # compute_spent
        ]

        result = await service.get_envelope_trends(account_id, months=1)
        assert len(result) == 1
        assert result[0]["period_start"] == "2026-01-28"
        assert result[0]["budget_name"] == "Groceries"
        assert result[0]["group_name"] == "Variable Expenses"
        assert result[0]["allocated"] == 50000
        assert result[0]["spent"] == 32000
        assert result[0]["pct_used"] == 64.0
        assert result[0]["over_budget"] is False

    @pytest.mark.asyncio
    async def test_over_budget_flag(self, service, mock_session):
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, group_id, name="Eating Out")
        group = _make_group(group_id, name="Variable Expenses")
        envelope = _make_envelope(budget_id, period.id, allocated=20000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[envelope]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar_one_or_none=group),
            _mock_execute_result(scalar=-25000),  # Over budget
        ]

        result = await service.get_envelope_trends(account_id, months=1)
        assert len(result) == 1
        assert result[0]["over_budget"] is True
        assert result[0]["pct_used"] == 125.0

    @pytest.mark.asyncio
    async def test_excludes_deleted_budgets(self, service, mock_session):
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, group_id, name="Deleted", deleted_at=datetime.now())
        envelope = _make_envelope(budget_id, period.id)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[envelope]),
            _mock_execute_result(scalar_one_or_none=budget),
        ]

        result = await service.get_envelope_trends(account_id, months=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_excludes_non_monthly_budgets(self, service, mock_session):
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, group_id, name="Annual", period_type="annual")
        envelope = _make_envelope(budget_id, period.id)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[envelope]),
            _mock_execute_result(scalar_one_or_none=budget),
        ]

        result = await service.get_envelope_trends(account_id, months=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_filter_by_budget_id(self, service, mock_session):
        account_id = uuid.uuid4()
        budget_id_1 = uuid.uuid4()
        budget_id_2 = uuid.uuid4()
        group_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget1 = _make_budget(budget_id_1, group_id, name="Groceries")
        budget2 = _make_budget(budget_id_2, group_id, name="Eating Out")
        group = _make_group(group_id)
        eb1 = _make_envelope(budget_id_1, period.id, allocated=50000)
        eb2 = _make_envelope(budget_id_2, period.id, allocated=20000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[eb1, eb2]),
            _mock_execute_result(scalar_one_or_none=budget1),  # budget for eb1
            _mock_execute_result(scalar_one_or_none=group),
            _mock_execute_result(scalar=-30000),               # spent for eb1
            _mock_execute_result(scalar_one_or_none=budget2),  # budget for eb2 - filtered out
        ]

        result = await service.get_envelope_trends(
            account_id, months=1, budget_id=budget_id_1,
        )
        assert len(result) == 1
        assert result[0]["budget_name"] == "Groceries"

    @pytest.mark.asyncio
    async def test_zero_allocated_pct_used(self, service, mock_session):
        """When allocated is 0, pct_used should be 0.0 not a division error."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, group_id, name="Zero")
        group = _make_group(group_id)
        envelope = _make_envelope(budget_id, period.id, allocated=0)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[envelope]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar_one_or_none=group),
            _mock_execute_result(scalar=0),
        ]

        result = await service.get_envelope_trends(account_id, months=1)
        assert len(result) == 1
        assert result[0]["pct_used"] == 0.0
        assert result[0]["over_budget"] is False

    @pytest.mark.asyncio
    async def test_multiple_periods_sorted(self, service, mock_session):
        """Results are sorted by period_start asc, group_name, budget_name."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        period1 = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        period2 = _make_period(account_id, date(2025, 12, 28), date(2026, 1, 27))
        budget = _make_budget(budget_id, group_id, name="Groceries")
        group = _make_group(group_id, name="Variable")
        eb1 = _make_envelope(budget_id, period1.id, allocated=50000)
        eb2 = _make_envelope(budget_id, period2.id, allocated=45000)

        # Periods returned in desc order by the query, reversed internally
        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period1, period2]),  # desc order
            # period2 (Dec) processed first after reverse
            _mock_execute_result(scalars_all=[eb2]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar_one_or_none=group),
            _mock_execute_result(scalar=-20000),
            # period1 (Jan)
            _mock_execute_result(scalars_all=[eb1]),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar_one_or_none=group),
            _mock_execute_result(scalar=-30000),
        ]

        result = await service.get_envelope_trends(account_id, months=2)
        assert len(result) == 2
        # Sorted by period_start ascending
        assert result[0]["period_start"] == "2025-12-28"
        assert result[1]["period_start"] == "2026-01-28"


class TestGetOverBudgetEnvelopes:
    """Tests for TrendsService.get_over_budget_envelopes."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return TrendsService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_periods(self, service, mock_session):
        mock_session.execute.return_value = _mock_execute_result(scalars_all=[])
        result = await service.get_over_budget_envelopes(uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_identifies_chronically_over_budget(self, service, mock_session):
        """Envelope over budget in 4/6 periods (>50%) should appear."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        budget = _make_budget(budget_id, group_id, name="Eating Out")
        group = _make_group(group_id, name="Variable Expenses")

        periods = []
        for i in range(6):
            month = 1 + i
            p = _make_period(account_id, date(2025, month + 6, 28), date(2025, month + 7, 27))
            periods.append(p)

        # Build side_effects: periods query, then per-period: envelopes, budget, group, spent
        side_effects = [_mock_execute_result(scalars_all=periods)]

        for i, period in enumerate(periods):
            eb = _make_envelope(budget_id, period.id, allocated=20000)
            # Over budget in 4 of 6 periods
            spent = -25000 if i < 4 else -15000
            side_effects.extend([
                _mock_execute_result(scalars_all=[eb]),
                _mock_execute_result(scalar_one_or_none=budget),
                _mock_execute_result(scalar_one_or_none=group),
                _mock_execute_result(scalar=spent),
            ])

        mock_session.execute.side_effect = side_effects

        result = await service.get_over_budget_envelopes(account_id, months=6)
        assert len(result) == 1
        assert result[0]["budget_name"] == "Eating Out"
        assert result[0]["over_budget_count"] == 4
        assert result[0]["total_periods"] == 6
        assert result[0]["pct_over"] == 66.7
        assert result[0]["avg_overspend_pence"] == 5000

    @pytest.mark.asyncio
    async def test_excludes_under_threshold(self, service, mock_session):
        """Envelope over budget in only 2/6 periods (<50%) should not appear."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        budget = _make_budget(budget_id, group_id, name="Transport")
        group = _make_group(group_id, name="Variable")

        periods = []
        for i in range(6):
            p = _make_period(account_id, date(2025, i + 7, 28), date(2025, i + 8, 27))
            periods.append(p)

        side_effects = [_mock_execute_result(scalars_all=periods)]

        for i, period in enumerate(periods):
            eb = _make_envelope(budget_id, period.id, allocated=30000)
            spent = -35000 if i < 2 else -20000  # Over budget only 2/6
            side_effects.extend([
                _mock_execute_result(scalars_all=[eb]),
                _mock_execute_result(scalar_one_or_none=budget),
                _mock_execute_result(scalar_one_or_none=group),
                _mock_execute_result(scalar=spent),
            ])

        mock_session.execute.side_effect = side_effects

        result = await service.get_over_budget_envelopes(account_id, months=6)
        assert result == []

    @pytest.mark.asyncio
    async def test_excludes_deleted_budgets_from_over_budget(self, service, mock_session):
        """Deleted budgets should not appear in over-budget results."""
        account_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))
        budget = _make_budget(budget_id, group_id, name="Deleted", deleted_at=datetime.now())
        eb = _make_envelope(budget_id, period.id, allocated=10000)

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[eb]),
            _mock_execute_result(scalar_one_or_none=budget),
        ]

        result = await service.get_over_budget_envelopes(account_id, months=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_no_envelopes_returns_empty(self, service, mock_session):
        """Periods with no envelopes return empty results."""
        account_id = uuid.uuid4()
        period = _make_period(account_id, date(2026, 1, 28), date(2026, 2, 27))

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[]),  # No envelopes
        ]

        result = await service.get_over_budget_envelopes(account_id, months=1)
        assert result == []
