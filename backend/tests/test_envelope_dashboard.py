"""Tests for envelope dashboard service."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Budget, BudgetGroup, BudgetPeriod, EnvelopeBalance
from app.services.envelope_dashboard import EnvelopeDashboardService


def _mock_execute_result(scalar_one_or_none=None, scalars_all=None, scalar=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    if scalar is not None:
        result.scalar.return_value = scalar
    return result


class TestGetEnvelopeDashboard:
    """Tests for the envelope dashboard builder."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return EnvelopeDashboardService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_active_period(self, service, mock_session):
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=None)
        result = await service.get_envelope_dashboard(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_dashboard_structure(self, service, mock_session):
        account_id = uuid.uuid4()
        period_id = uuid.uuid4()
        budget_id = uuid.uuid4()
        group_id = uuid.uuid4()

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.account_id = account_id
        period.period_start = date(2026, 3, 28)
        period.period_end = date(2026, 4, 27)
        period.status = "active"

        eb = MagicMock(spec=EnvelopeBalance)
        eb.budget_id = budget_id
        eb.period_id = period_id
        eb.allocated = 50000
        eb.original_allocated = 50000
        eb.rollover = -2000

        group = MagicMock(spec=BudgetGroup)
        group.id = group_id
        group.name = "Variable Expenses"
        group.icon = "🛒"
        group.display_order = 1

        budget = MagicMock(spec=Budget)
        budget.id = budget_id
        budget.name = "Groceries"
        budget.category = "groceries"
        budget.group_id = group_id
        budget.period_type = "monthly"
        budget.deleted_at = None

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=period),  # Active period
            _mock_execute_result(scalars_all=[eb]),  # Envelope balances
            _mock_execute_result(scalars_all=[group]),  # Groups
            _mock_execute_result(scalar=-30000),  # Spent for groceries
            _mock_execute_result(scalars_all=[budget]),  # Budgets in group
        ]

        result = await service.get_envelope_dashboard(account_id)
        assert result is not None
        assert result["period_id"] == str(period_id)
        assert result["period_start"] == "2026-03-28"
        assert result["period_end"] == "2026-04-27"
        assert len(result["groups"]) == 1
        assert result["groups"][0]["group_name"] == "Variable Expenses"
        assert len(result["groups"][0]["envelopes"]) == 1

        envelope = result["groups"][0]["envelopes"][0]
        assert envelope["budget_name"] == "Groceries"
        assert envelope["allocated"] == 50000
        assert envelope["rollover"] == -2000
        assert envelope["spent"] == 30000
        assert envelope["available"] == 18000  # 50000 + (-2000) - 30000
        assert envelope["pct_used"] == 60.0

    @pytest.mark.asyncio
    async def test_excludes_groups_with_no_envelopes(self, service, mock_session):
        """Groups with no active envelopes are excluded from response."""
        account_id = uuid.uuid4()
        period_id = uuid.uuid4()

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.account_id = account_id
        period.period_start = date(2026, 3, 28)
        period.period_end = date(2026, 4, 27)
        period.status = "active"

        group = MagicMock(spec=BudgetGroup)
        group.id = uuid.uuid4()
        group.name = "Empty Group"
        group.icon = None
        group.display_order = 1

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=period),
            _mock_execute_result(scalars_all=[]),  # No envelope balances
            _mock_execute_result(scalars_all=[group]),  # One group
            _mock_execute_result(scalars_all=[]),  # No budgets in group
        ]

        result = await service.get_envelope_dashboard(account_id)
        assert result is not None
        assert len(result["groups"]) == 0
        assert result["total_allocated"] == 0

    @pytest.mark.asyncio
    async def test_historical_period_by_id(self, service, mock_session):
        """Can fetch dashboard for a specific historical period."""
        account_id = uuid.uuid4()
        period_id = uuid.uuid4()

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.account_id = account_id
        period.period_start = date(2026, 2, 28)
        period.period_end = date(2026, 3, 27)
        period.status = "closed"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=period),  # Get period by ID
            _mock_execute_result(scalars_all=[]),  # No envelopes
            _mock_execute_result(scalars_all=[]),  # No groups
        ]

        result = await service.get_envelope_dashboard(account_id, period_id=period_id)
        assert result is not None
        assert result["period_status"] == "closed"

    @pytest.mark.asyncio
    async def test_computes_group_totals(self, service, mock_session):
        """Group totals are sum of all envelopes in the group."""
        account_id = uuid.uuid4()
        period_id = uuid.uuid4()
        group_id = uuid.uuid4()
        budget_id_1 = uuid.uuid4()
        budget_id_2 = uuid.uuid4()

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.period_start = date(2026, 3, 28)
        period.period_end = date(2026, 4, 27)
        period.status = "active"

        eb1 = MagicMock(spec=EnvelopeBalance)
        eb1.budget_id = budget_id_1
        eb1.allocated = 50000
        eb1.original_allocated = 50000
        eb1.rollover = 0

        eb2 = MagicMock(spec=EnvelopeBalance)
        eb2.budget_id = budget_id_2
        eb2.allocated = 10000
        eb2.original_allocated = 10000
        eb2.rollover = 0

        group = MagicMock(spec=BudgetGroup)
        group.id = group_id
        group.name = "Variable Expenses"
        group.icon = None
        group.display_order = 1

        budget1 = MagicMock(spec=Budget)
        budget1.id = budget_id_1
        budget1.name = "Groceries"
        budget1.category = "groceries"

        budget2 = MagicMock(spec=Budget)
        budget2.id = budget_id_2
        budget2.name = "Petrol"
        budget2.category = "petrol"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=period),
            _mock_execute_result(scalars_all=[eb1, eb2]),
            _mock_execute_result(scalars_all=[group]),
            _mock_execute_result(scalar=-30000),  # Groceries spent
            _mock_execute_result(scalar=-5000),  # Petrol spent
            _mock_execute_result(scalars_all=[budget1, budget2]),
        ]

        result = await service.get_envelope_dashboard(account_id)
        assert result is not None
        assert len(result["groups"]) == 1
        grp = result["groups"][0]
        assert grp["total_allocated"] == 60000  # 50000 + 10000
        assert grp["total_spent"] == 35000  # 30000 + 5000
        assert grp["total_available"] == 25000  # 60000 - 35000
        assert result["total_allocated"] == 60000
