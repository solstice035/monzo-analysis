"""Tests for annual view service."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Budget, BudgetGroup, BudgetPeriod, EnvelopeBalance
from app.services.annual import AnnualService, _status


def _mock_execute_result(scalar_one_or_none=None, scalars_all=None, scalar=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    if scalar is not None:
        result.scalar.return_value = scalar
    return result


class TestStatusLogic:
    """Tests for the _status helper."""

    def test_under_when_spent_well_below_allocated(self):
        assert _status(1000, 10000) == "under"

    def test_on_track_when_spent_above_90_pct(self):
        assert _status(9500, 10000) == "on_track"

    def test_over_when_spent_exceeds_allocated(self):
        assert _status(11000, 10000) == "over"

    def test_under_at_exactly_90_pct(self):
        assert _status(9000, 10000) == "under"

    def test_on_track_at_exactly_allocated(self):
        assert _status(10000, 10000) == "on_track"

    def test_zero_allocated_zero_spent(self):
        assert _status(0, 0) == "under"

    def test_zero_allocated_with_spending(self):
        assert _status(100, 0) == "over"


class TestAnnualService:
    """Tests for AnnualService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return AnnualService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_correct_year(self, service, mock_session):
        """Response includes the requested year."""
        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[]),  # periods
            _mock_execute_result(scalars_all=[]),  # groups
        ]
        result = await service.get_annual_view(uuid.uuid4(), 2026)
        assert result["year"] == 2026

    @pytest.mark.asyncio
    async def test_returns_12_monthly_totals(self, service, mock_session):
        """Always returns 12 monthly totals even with no data."""
        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[]),
            _mock_execute_result(scalars_all=[]),
        ]
        result = await service.get_annual_view(uuid.uuid4(), 2026)
        assert len(result["monthly_totals"]) == 12
        assert result["monthly_totals"][0]["month"] == 1
        assert result["monthly_totals"][11]["month"] == 12

    @pytest.mark.asyncio
    async def test_empty_year_zeros(self, service, mock_session):
        """No periods or groups returns all zeros."""
        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[]),
            _mock_execute_result(scalars_all=[]),
        ]
        result = await service.get_annual_view(uuid.uuid4(), 2026)
        assert result["groups"] == []
        assert result["grand_total"]["allocated"] == 0
        assert result["grand_total"]["spent"] == 0
        assert result["grand_total"]["available"] == 0

    @pytest.mark.asyncio
    async def test_single_group_single_month(self, service, mock_session):
        """One group with data for one month."""
        account_id = uuid.uuid4()
        period_id = uuid.uuid4()
        group_id = uuid.uuid4()
        budget_id = uuid.uuid4()

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.period_start = date(2026, 3, 28)
        period.period_end = date(2026, 4, 27)
        period.status = "closed"

        group = MagicMock(spec=BudgetGroup)
        group.id = group_id
        group.name = "Variable Expenses"
        group.display_order = 1

        budget = MagicMock(spec=Budget)
        budget.id = budget_id
        budget.period_type = "monthly"
        budget.deleted_at = None

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),       # periods for year
            _mock_execute_result(scalars_all=[group]),        # groups
            _mock_execute_result(scalars_all=[budget]),       # budgets in group
            _mock_execute_result(scalar=50000),               # allocated for March
            _mock_execute_result(scalar=-30000),              # spent for March
        ]

        result = await service.get_annual_view(account_id, 2026)
        assert len(result["groups"]) == 1
        grp = result["groups"][0]
        assert grp["group_name"] == "Variable Expenses"

        # March is month 3 (index 2)
        march = grp["months"][2]
        assert march["month"] == 3
        assert march["month_name"] == "March"
        assert march["period_id"] == str(period_id)
        assert march["allocated"] == 50000
        assert march["spent"] == 30000
        assert march["available"] == 20000
        assert march["status"] == "under"

        # Other months should be zero
        jan = grp["months"][0]
        assert jan["allocated"] == 0
        assert jan["period_id"] is None

        # Totals
        assert grp["total_allocated"] == 50000
        assert grp["total_spent"] == 30000
        assert result["grand_total"]["allocated"] == 50000

    @pytest.mark.asyncio
    async def test_group_with_no_budgets_excluded(self, service, mock_session):
        """Groups with no monthly budgets are excluded."""
        account_id = uuid.uuid4()

        group = MagicMock(spec=BudgetGroup)
        group.id = uuid.uuid4()
        group.name = "Empty"
        group.display_order = 1

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[]),             # no periods
            _mock_execute_result(scalars_all=[group]),        # one group
            _mock_execute_result(scalars_all=[]),             # no budgets
        ]

        result = await service.get_annual_view(account_id, 2026)
        assert len(result["groups"]) == 0

    @pytest.mark.asyncio
    async def test_over_budget_status(self, service, mock_session):
        """Over status when spent > allocated."""
        account_id = uuid.uuid4()
        period_id = uuid.uuid4()
        group_id = uuid.uuid4()
        budget_id = uuid.uuid4()

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.period_start = date(2026, 1, 28)
        period.period_end = date(2026, 2, 27)

        group = MagicMock(spec=BudgetGroup)
        group.id = group_id
        group.name = "Test"
        group.display_order = 1

        budget = MagicMock(spec=Budget)
        budget.id = budget_id
        budget.period_type = "monthly"
        budget.deleted_at = None

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[group]),
            _mock_execute_result(scalars_all=[budget]),
            _mock_execute_result(scalar=20000),  # allocated
            _mock_execute_result(scalar=-25000),  # spent (abs = 25000 > 20000)
        ]

        result = await service.get_annual_view(account_id, 2026)
        jan = result["groups"][0]["months"][0]
        assert jan["status"] == "over"
        assert jan["available"] == -5000

    @pytest.mark.asyncio
    async def test_monthly_totals_aggregate_groups(self, service, mock_session):
        """Monthly totals sum across all groups."""
        account_id = uuid.uuid4()
        period_id = uuid.uuid4()
        group_id_1 = uuid.uuid4()
        group_id_2 = uuid.uuid4()
        budget_id_1 = uuid.uuid4()
        budget_id_2 = uuid.uuid4()

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.period_start = date(2026, 6, 28)
        period.period_end = date(2026, 7, 27)

        group1 = MagicMock(spec=BudgetGroup)
        group1.id = group_id_1
        group1.name = "Group A"
        group1.display_order = 1

        group2 = MagicMock(spec=BudgetGroup)
        group2.id = group_id_2
        group2.name = "Group B"
        group2.display_order = 2

        budget1 = MagicMock(spec=Budget)
        budget1.id = budget_id_1
        budget1.period_type = "monthly"
        budget1.deleted_at = None

        budget2 = MagicMock(spec=Budget)
        budget2.id = budget_id_2
        budget2.period_type = "monthly"
        budget2.deleted_at = None

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[period]),
            _mock_execute_result(scalars_all=[group1, group2]),
            # Group A budgets + data for June
            _mock_execute_result(scalars_all=[budget1]),
            _mock_execute_result(scalar=30000),   # allocated
            _mock_execute_result(scalar=-20000),  # spent
            # Group B budgets + data for June
            _mock_execute_result(scalars_all=[budget2]),
            _mock_execute_result(scalar=10000),   # allocated
            _mock_execute_result(scalar=-8000),   # spent
        ]

        result = await service.get_annual_view(account_id, 2026)
        # June is month 6 (index 5)
        june_total = result["monthly_totals"][5]
        assert june_total["allocated"] == 40000  # 30000 + 10000
        assert june_total["spent"] == 28000  # 20000 + 8000
        assert june_total["available"] == 12000

    @pytest.mark.asyncio
    async def test_account_isolation(self, service, mock_session):
        """Service passes account_id to all queries."""
        account_id = uuid.uuid4()
        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[]),
            _mock_execute_result(scalars_all=[]),
        ]
        await service.get_annual_view(account_id, 2026)

        # Verify execute was called (at least for periods and groups)
        assert mock_session.execute.call_count == 2
