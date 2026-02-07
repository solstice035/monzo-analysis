"""Tests for dashboard API endpoints — summary, trends, recurring."""

from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _mock_get_session(mock_session):
    """Create a mock get_session context manager that yields the given session."""
    @asynccontextmanager
    async def _get_session():
        yield mock_session

    return _get_session


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return AsyncMock()


@pytest.fixture
def client(mock_session):
    """Create a test client with mocked database session."""
    with patch("app.api.dashboard.get_session", _mock_get_session(mock_session)):
        from app.main import create_app

        app = create_app()
        with TestClient(app) as client:
            yield client


class TestDashboardSummary:
    """Tests for GET /api/v1/dashboard/summary."""

    def test_summary_requires_account_id(self, client: TestClient) -> None:
        """Should return 422 without account_id query param."""
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 422

    def test_summary_returns_expected_fields(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should return balance, spend_today, spend_this_month, transaction_count, top_categories."""
        # Mock the sequence of DB queries:
        # 1. count transactions
        # 2. spend today
        # 3. spend this month
        # 4. top categories
        # 5. account lookup

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 42

        mock_today_result = MagicMock()
        mock_today_result.scalar.return_value = -1500

        mock_month_result = MagicMock()
        mock_month_result.scalar.return_value = -50000

        mock_cat_row = MagicMock()
        mock_cat_row.category = "groceries"
        mock_cat_row.total = -25000
        mock_cat_result = MagicMock()
        mock_cat_result.all.return_value = [mock_cat_row]

        mock_account = MagicMock()
        mock_account.balance = 150000
        mock_account.spend_today = -1500
        mock_account_result = MagicMock()
        mock_account_result.scalar_one_or_none.return_value = mock_account

        mock_session.execute.side_effect = [
            mock_count_result,
            mock_today_result,
            mock_month_result,
            mock_cat_result,
            mock_account_result,
        ]

        response = client.get("/api/v1/dashboard/summary?account_id=acc_123")

        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 150000
        assert data["spend_today"] == 1500
        assert data["transaction_count"] == 42
        assert data["spend_this_month"] == 50000
        assert len(data["top_categories"]) == 1
        assert data["top_categories"][0]["category"] == "groceries"

    def test_summary_handles_no_account(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should return 0 balance when account not found."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_zero_result = MagicMock()
        mock_zero_result.scalar.return_value = None

        mock_empty_cat = MagicMock()
        mock_empty_cat.all.return_value = []

        mock_no_account = MagicMock()
        mock_no_account.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            mock_count_result,
            mock_zero_result,
            mock_zero_result,
            mock_empty_cat,
            mock_no_account,
        ]

        response = client.get("/api/v1/dashboard/summary?account_id=acc_missing")

        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 0


class TestDashboardTrends:
    """Tests for GET /api/v1/dashboard/trends."""

    def test_trends_requires_account_id(self, client: TestClient) -> None:
        """Should return 422 without account_id."""
        response = client.get("/api/v1/dashboard/trends")
        assert response.status_code == 422

    def test_trends_validates_days_range(self, client: TestClient) -> None:
        """Days param should be between 7 and 90."""
        response = client.get("/api/v1/dashboard/trends?account_id=acc_123&days=3")
        assert response.status_code == 422

        response = client.get("/api/v1/dashboard/trends?account_id=acc_123&days=100")
        assert response.status_code == 422

    def test_trends_fills_missing_dates(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should fill in zero-spend days for the full range."""
        # Return empty result (no transactions)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        response = client.get("/api/v1/dashboard/trends?account_id=acc_123&days=7")

        assert response.status_code == 200
        data = response.json()
        assert len(data["daily_spend"]) == 7
        assert data["total"] == 0
        assert data["average_daily"] == 0


class TestDashboardRecurring:
    """Tests for GET /api/v1/dashboard/recurring."""

    def test_recurring_requires_account_id(self, client: TestClient) -> None:
        """Should return 422 without account_id."""
        response = client.get("/api/v1/dashboard/recurring")
        assert response.status_code == 422

    def test_recurring_returns_items_and_total(self, mock_session: AsyncMock) -> None:
        """Should return recurring items with total monthly cost."""
        from app.services.recurring import RecurringTransaction

        mock_recurring = RecurringTransaction(
            merchant_name="Netflix",
            category="entertainment",
            average_amount=1599,
            frequency_days=30,
            frequency_label="monthly",
            transaction_count=6,
            monthly_cost=1599,
            last_transaction=date(2026, 2, 1),
            next_expected=date(2026, 3, 1),
            confidence=0.95,
        )

        with patch("app.api.dashboard.get_session", _mock_get_session(mock_session)):
            with patch(
                "app.api.dashboard.detect_recurring_transactions",
                new_callable=AsyncMock,
                return_value=[mock_recurring],
            ):
                from app.main import create_app

                app = create_app()
                with TestClient(app) as client:
                    response = client.get(
                        "/api/v1/dashboard/recurring?account_id=acc_123"
                    )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["merchant_name"] == "Netflix"
        assert data["total_monthly_cost"] == 1599
