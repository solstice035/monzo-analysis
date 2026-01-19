"""Tests for budget tracking service."""

from datetime import datetime, date, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


class TestBudgetPeriodCalculation:
    """Tests for calculating budget periods."""

    def test_get_current_period_monthly_default_reset(self) -> None:
        """Should calculate period with reset day 1 (default)."""
        from app.services.budget import get_current_period

        # If today is Jan 15, period is Jan 1 - Jan 31
        test_date = date(2025, 1, 15)
        start, end = get_current_period(test_date, reset_day=1, period="monthly")

        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_get_current_period_monthly_mid_month_reset(self) -> None:
        """Should calculate period with mid-month reset day."""
        from app.services.budget import get_current_period

        # If reset is 15th and today is Jan 20, period is Jan 15 - Feb 14
        test_date = date(2025, 1, 20)
        start, end = get_current_period(test_date, reset_day=15, period="monthly")

        assert start == date(2025, 1, 15)
        assert end == date(2025, 2, 14)

    def test_get_current_period_monthly_before_reset(self) -> None:
        """Should calculate period from previous month if before reset day."""
        from app.services.budget import get_current_period

        # If reset is 15th and today is Jan 10, period is Dec 15 - Jan 14
        test_date = date(2025, 1, 10)
        start, end = get_current_period(test_date, reset_day=15, period="monthly")

        assert start == date(2024, 12, 15)
        assert end == date(2025, 1, 14)

    def test_get_current_period_weekly(self) -> None:
        """Should calculate weekly period (Monday to Sunday)."""
        from app.services.budget import get_current_period

        # Jan 15 2025 is a Wednesday
        test_date = date(2025, 1, 15)
        start, end = get_current_period(test_date, reset_day=1, period="weekly")

        # Week starts Monday Jan 13, ends Sunday Jan 19
        assert start == date(2025, 1, 13)
        assert end == date(2025, 1, 19)

    def test_get_current_period_handles_february(self) -> None:
        """Should handle February correctly."""
        from app.services.budget import get_current_period

        # Reset on 28th, Feb 20 should give Feb 28 - Mar 27
        test_date = date(2025, 2, 20)
        start, end = get_current_period(test_date, reset_day=28, period="monthly")

        # Before 28th, so period is Jan 28 - Feb 27
        assert start == date(2025, 1, 28)
        assert end == date(2025, 2, 27)


class TestBudgetSpendCalculation:
    """Tests for calculating spend against budgets."""

    @pytest.mark.asyncio
    async def test_calculate_spend_sums_matching_transactions(self) -> None:
        """Should sum all transactions matching budget category."""
        from app.services.budget import BudgetService

        budget = MagicMock()
        budget.category = "Groceries"
        budget.period = "monthly"
        budget.start_day = 1
        budget.amount = 30000  # £300

        # Mock returns only transactions that match the DB query
        # (DB filters by category, code just sums)
        transactions = [
            MagicMock(custom_category="Groceries", amount=-5000),  # £50
            MagicMock(custom_category="Groceries", amount=-7500),  # £75
        ]

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = transactions
        mock_session.execute.return_value = mock_result

        service = BudgetService(mock_session)
        spend = await service.calculate_spend(budget, date(2025, 1, 15))

        # Only Groceries transactions: 5000 + 7500 = 12500
        assert spend == 12500

    @pytest.mark.asyncio
    async def test_calculate_spend_returns_zero_no_transactions(self) -> None:
        """Should return 0 when no matching transactions."""
        from app.services.budget import BudgetService

        budget = MagicMock()
        budget.category = "Groceries"
        budget.period = "monthly"
        budget.start_day = 1
        budget.amount = 30000

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = BudgetService(mock_session)
        spend = await service.calculate_spend(budget, date(2025, 1, 15))

        assert spend == 0


class TestBudgetStatus:
    """Tests for budget status calculation."""

    @pytest.mark.asyncio
    async def test_get_budget_status_under_budget(self) -> None:
        """Should return under status when spend is under budget."""
        from app.services.budget import BudgetService, BudgetStatus

        budget = MagicMock()
        budget.id = uuid4()
        budget.category = "Groceries"
        budget.amount = 30000  # £300
        budget.period = "monthly"
        budget.start_day = 1

        mock_session = AsyncMock()
        service = BudgetService(mock_session)

        # Mock calculate_spend to return 15000 (50% of budget)
        service.calculate_spend = AsyncMock(return_value=15000)

        status = await service.get_budget_status(budget, date(2025, 1, 15))

        assert status.spent == 15000
        assert status.remaining == 15000
        assert status.percentage == 50.0
        assert status.status == "under"

    @pytest.mark.asyncio
    async def test_get_budget_status_warning(self) -> None:
        """Should return warning status when spend is 80-100%."""
        from app.services.budget import BudgetService

        budget = MagicMock()
        budget.id = uuid4()
        budget.category = "Groceries"
        budget.amount = 30000  # £300
        budget.period = "monthly"
        budget.start_day = 1

        mock_session = AsyncMock()
        service = BudgetService(mock_session)

        # Mock calculate_spend to return 27000 (90% of budget)
        service.calculate_spend = AsyncMock(return_value=27000)

        status = await service.get_budget_status(budget, date(2025, 1, 15))

        assert status.percentage == 90.0
        assert status.status == "warning"

    @pytest.mark.asyncio
    async def test_get_budget_status_over(self) -> None:
        """Should return over status when spend exceeds budget."""
        from app.services.budget import BudgetService

        budget = MagicMock()
        budget.id = uuid4()
        budget.category = "Groceries"
        budget.amount = 30000  # £300
        budget.period = "monthly"
        budget.start_day = 1

        mock_session = AsyncMock()
        service = BudgetService(mock_session)

        # Mock calculate_spend to return 35000 (117% of budget)
        service.calculate_spend = AsyncMock(return_value=35000)

        status = await service.get_budget_status(budget, date(2025, 1, 15))

        assert status.spent == 35000
        assert status.remaining == -5000  # Over by £50
        assert status.percentage == pytest.approx(116.67, rel=0.1)
        assert status.status == "over"


class TestBudgetServiceCRUD:
    """Tests for budget CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_all_budgets(self) -> None:
        """Should fetch all active budgets."""
        from app.services.budget import BudgetService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(category="Groceries"),
            MagicMock(category="Transport"),
        ]
        mock_session.execute.return_value = mock_result

        service = BudgetService(mock_session)
        budgets = await service.get_all_budgets()

        assert len(budgets) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_budget(self) -> None:
        """Should create a new budget."""
        from app.services.budget import BudgetService

        mock_session = AsyncMock()

        service = BudgetService(mock_session)
        budget = await service.create_budget(
            category="Groceries",
            amount=30000,
            period="monthly",
            start_day=1,
        )

        mock_session.add.assert_called_once()
        assert budget.category == "Groceries"
        assert budget.amount == 30000

    @pytest.mark.asyncio
    async def test_update_budget(self) -> None:
        """Should update an existing budget."""
        from app.services.budget import BudgetService

        existing_budget = MagicMock()
        existing_budget.id = "budget_123"
        existing_budget.amount = 30000

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_budget

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = BudgetService(mock_session)
        updated = await service.update_budget(
            budget_id="budget_123",
            amount=40000,
        )

        assert updated.amount == 40000

    @pytest.mark.asyncio
    async def test_delete_budget(self) -> None:
        """Should delete a budget."""
        from app.services.budget import BudgetService

        existing_budget = MagicMock()
        existing_budget.id = "budget_123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_budget

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = BudgetService(mock_session)
        result = await service.delete_budget("budget_123")

        assert result is True
        mock_session.delete.assert_called_once_with(existing_budget)


class TestBudgetSummary:
    """Tests for budget summary generation."""

    @pytest.mark.asyncio
    async def test_get_all_budget_statuses(self) -> None:
        """Should return status for all budgets using optimized single query."""
        from app.services.budget import BudgetService
        from datetime import datetime

        budget1_id = uuid4()
        budget2_id = uuid4()

        budget1 = MagicMock()
        budget1.id = budget1_id
        budget1.category = "Groceries"
        budget1.amount = 30000
        budget1.period = "monthly"
        budget1.start_day = 1

        budget2 = MagicMock()
        budget2.id = budget2_id
        budget2.category = "Transport"
        budget2.amount = 10000
        budget2.period = "monthly"
        budget2.start_day = 1

        # Mock transactions returned by the optimized single query
        tx1 = MagicMock()
        tx1.custom_category = "Groceries"
        tx1.amount = -15000  # Spending is negative
        tx1.created_at = datetime(2025, 1, 10, 12, 0, 0)

        tx2 = MagicMock()
        tx2.custom_category = "Transport"
        tx2.amount = -8000  # Spending is negative
        tx2.created_at = datetime(2025, 1, 12, 9, 0, 0)

        mock_session = AsyncMock()

        # First call returns budgets, second call returns transactions
        mock_budgets_result = MagicMock()
        mock_budgets_result.scalars.return_value.all.return_value = [budget1, budget2]

        mock_transactions_result = MagicMock()
        mock_transactions_result.all.return_value = [tx1, tx2]

        mock_session.execute.side_effect = [mock_budgets_result, mock_transactions_result]

        service = BudgetService(mock_session)

        statuses = await service.get_all_budget_statuses(date(2025, 1, 15))

        assert len(statuses) == 2
        assert statuses[0].spent == 15000
        assert statuses[1].spent == 8000
        # Verify only 2 queries were made (optimized from N+1)
        assert mock_session.execute.call_count == 2
