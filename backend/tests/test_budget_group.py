"""Tests for budget group service — roll-up calculations, CRUD, status aggregation."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.budget import BudgetStatus


def _make_budget_status(
    amount: int = 10000,
    spent: int = 5000,
    status: str = "under",
    period_start: date = date(2026, 2, 1),
    period_end: date = date(2026, 2, 28),
) -> BudgetStatus:
    """Helper to create a BudgetStatus for testing."""
    return BudgetStatus(
        budget_id=uuid4(),
        category="test",
        amount=amount,
        spent=spent,
        remaining=amount - spent,
        percentage=(spent / amount) * 100 if amount > 0 else 0,
        status=status,
        period_start=period_start,
        period_end=period_end,
    )


class TestBudgetGroupStatus:
    """Tests for budget group roll-up status calculations."""

    @pytest.mark.asyncio
    async def test_group_status_aggregates_budget_totals(self) -> None:
        """Group status should sum amounts and spent from all child budgets."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        group_id = uuid4()
        budget1 = MagicMock()
        budget2 = MagicMock()

        group = MagicMock()
        group.id = group_id
        group.name = "Kids"
        group.icon = None
        group.display_order = 0
        group.budgets = [budget1, budget2]

        status1 = _make_budget_status(amount=20000, spent=10000)
        status2 = _make_budget_status(amount=30000, spent=5000)

        with patch.object(
            service._budget_service,
            "get_budget_status",
            new_callable=AsyncMock,
            side_effect=[status1, status2],
        ):
            result = await service.get_group_status(group, date(2026, 2, 15))

        assert result.total_amount == 50000
        assert result.total_spent == 15000
        assert result.total_remaining == 35000
        assert result.budget_count == 2

    @pytest.mark.asyncio
    async def test_group_status_over_when_100_percent(self) -> None:
        """Group status should be 'over' when spending >= 100%."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        group = MagicMock()
        group.id = uuid4()
        group.name = "Over Budget"
        group.icon = None
        group.display_order = 0
        group.budgets = [MagicMock()]

        over_status = _make_budget_status(amount=10000, spent=12000, status="over")

        with patch.object(
            service._budget_service,
            "get_budget_status",
            new_callable=AsyncMock,
            return_value=over_status,
        ):
            result = await service.get_group_status(group, date(2026, 2, 15))

        assert result.status == "over"
        assert result.percentage == 120.0

    @pytest.mark.asyncio
    async def test_group_status_warning_at_80_percent(self) -> None:
        """Group status should be 'warning' at 80-99%."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        group = MagicMock()
        group.id = uuid4()
        group.name = "Warning"
        group.icon = None
        group.display_order = 0
        group.budgets = [MagicMock()]

        warning_status = _make_budget_status(amount=10000, spent=8500, status="warning")

        with patch.object(
            service._budget_service,
            "get_budget_status",
            new_callable=AsyncMock,
            return_value=warning_status,
        ):
            result = await service.get_group_status(group, date(2026, 2, 15))

        assert result.status == "warning"

    @pytest.mark.asyncio
    async def test_group_status_under_below_80_percent(self) -> None:
        """Group status should be 'under' when spending < 80%."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        group = MagicMock()
        group.id = uuid4()
        group.name = "On Track"
        group.icon = None
        group.display_order = 0
        group.budgets = [MagicMock()]

        under_status = _make_budget_status(amount=10000, spent=3000, status="under")

        with patch.object(
            service._budget_service,
            "get_budget_status",
            new_callable=AsyncMock,
            return_value=under_status,
        ):
            result = await service.get_group_status(group, date(2026, 2, 15))

        assert result.status == "under"

    @pytest.mark.asyncio
    async def test_group_status_zero_budget(self) -> None:
        """Group status should handle zero total budget without division error."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        group = MagicMock()
        group.id = uuid4()
        group.name = "Empty"
        group.icon = None
        group.display_order = 0
        group.budgets = [MagicMock()]

        zero_status = _make_budget_status(amount=0, spent=0, status="under")

        with patch.object(
            service._budget_service,
            "get_budget_status",
            new_callable=AsyncMock,
            return_value=zero_status,
        ):
            result = await service.get_group_status(group, date(2026, 2, 15))

        assert result.percentage == 0
        assert result.status == "under"

    @pytest.mark.asyncio
    async def test_group_status_period_uses_min_max_dates(self) -> None:
        """Group period should span from earliest start to latest end across budgets."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        group = MagicMock()
        group.id = uuid4()
        group.name = "Multi-period"
        group.icon = None
        group.display_order = 0
        group.budgets = [MagicMock(), MagicMock()]

        status1 = _make_budget_status(
            period_start=date(2026, 2, 1), period_end=date(2026, 2, 14)
        )
        status2 = _make_budget_status(
            period_start=date(2026, 1, 15), period_end=date(2026, 2, 28)
        )

        with patch.object(
            service._budget_service,
            "get_budget_status",
            new_callable=AsyncMock,
            side_effect=[status1, status2],
        ):
            result = await service.get_group_status(group, date(2026, 2, 15))

        assert result.period_start == date(2026, 1, 15)
        assert result.period_end == date(2026, 2, 28)


class TestBudgetGroupDashboardSummary:
    """Tests for dashboard summary aggregation."""

    @pytest.mark.asyncio
    async def test_dashboard_summary_totals(self) -> None:
        """Dashboard summary should aggregate all group totals."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        account_id = str(uuid4())
        ref_date = date(2026, 2, 15)

        # Mock get_all_groups to return two groups
        group1 = MagicMock()
        group1.id = uuid4()
        group1.name = "Fixed"
        group1.icon = None
        group1.display_order = 0
        group1.budgets = [MagicMock()]

        group2 = MagicMock()
        group2.id = uuid4()
        group2.name = "Variable"
        group2.icon = None
        group2.display_order = 1
        group2.budgets = [MagicMock()]

        s1 = _make_budget_status(amount=50000, spent=40000)
        s2 = _make_budget_status(amount=30000, spent=10000)

        with patch.object(
            service, "get_all_groups", new_callable=AsyncMock, return_value=[group1, group2]
        ):
            with patch.object(
                service._budget_service,
                "get_budget_status",
                new_callable=AsyncMock,
                side_effect=[s1, s2],
            ):
                result = await service.get_dashboard_summary(account_id, ref_date)

        assert result["total_budget"] == 80000
        assert result["total_spent"] == 50000
        assert result["total_remaining"] == 30000
        assert result["overall_percentage"] == 62.5


class TestBudgetGroupCRUD:
    """Tests for budget group create, update, delete."""

    @pytest.mark.asyncio
    async def test_create_group(self) -> None:
        """Create group should add a BudgetGroup to the session."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        group = await service.create_group(
            account_id=str(uuid4()),
            name="Kids",
            icon="👧",
            display_order=1,
        )

        assert group.name == "Kids"
        assert group.icon == "👧"
        assert group.display_order == 1
        mock_session.add.assert_called_once_with(group)

    @pytest.mark.asyncio
    async def test_update_group_returns_none_if_not_found(self) -> None:
        """Update should return None if group doesn't exist."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        with patch.object(service, "get_group", new_callable=AsyncMock, return_value=None):
            result = await service.update_group(uuid4(), name="New Name")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_group_changes_fields(self) -> None:
        """Update should modify provided fields only."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        existing = MagicMock()
        existing.name = "Old"
        existing.icon = "📦"
        existing.display_order = 0

        with patch.object(service, "get_group", new_callable=AsyncMock, return_value=existing):
            result = await service.update_group(uuid4(), name="New Name")

        assert result.name == "New Name"
        assert result.icon == "📦"  # unchanged

    @pytest.mark.asyncio
    async def test_delete_group_returns_false_if_not_found(self) -> None:
        """Delete should return False if group doesn't exist."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        with patch.object(service, "get_group", new_callable=AsyncMock, return_value=None):
            result = await service.delete_group(uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_group_calls_session_delete(self) -> None:
        """Delete should call session.delete on the group."""
        from app.services.budget_group import BudgetGroupService

        mock_session = AsyncMock()
        service = BudgetGroupService(mock_session)

        existing = MagicMock()

        with patch.object(service, "get_group", new_callable=AsyncMock, return_value=existing):
            result = await service.delete_group(uuid4())

        assert result is True
        mock_session.delete.assert_called_once_with(existing)
