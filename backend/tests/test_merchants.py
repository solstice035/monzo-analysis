"""Tests for the merchants endpoint (Phase 2.5a)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_app():
    """Create a test app with the merchants router."""
    from app.main import create_app
    return create_app()


class TestMerchantsEndpoint:
    """Tests for GET /api/v1/accounts/{account_id}/merchants."""

    @pytest.fixture
    def client(self):
        app = _make_app()
        return TestClient(app)

    @pytest.fixture
    def account_id(self):
        return str(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_transactions(self, client, account_id):
        """Should return empty list when account has no transactions."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch("app.api.merchants.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            response = client.get(f"/api/v1/accounts/{account_id}/merchants")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_merchants_with_null_rule_data(self, client, account_id):
        """Should return merchants with null rule data when no rules exist."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        # Simulating raw row results: (merchant_name, count, last_seen, rule_id, budget_id, budget_name, group_name)
        mock_row = MagicMock()
        mock_row._mapping = {
            "name": "Costa Coffee",
            "transaction_count": 3,
            "last_seen": datetime(2026, 3, 21, tzinfo=timezone.utc),
            "rule_id": None,
            "assigned_budget_id": None,
            "assigned_budget_name": None,
            "assigned_group_name": None,
        }
        mock_row.name = "Costa Coffee"
        mock_row.transaction_count = 3
        mock_row.last_seen = datetime(2026, 3, 21, tzinfo=timezone.utc)
        mock_row.rule_id = None
        mock_row.assigned_budget_id = None
        mock_row.assigned_budget_name = None
        mock_row.assigned_group_name = None

        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        with patch("app.api.merchants.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            response = client.get(f"/api/v1/accounts/{account_id}/merchants")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Costa Coffee"
        assert data[0]["transaction_count"] == 3
        assert data[0]["rule_id"] is None
        assert data[0]["assigned_budget_id"] is None
        assert data[0]["assigned_budget_name"] is None
        assert data[0]["assigned_group_name"] is None

    @pytest.mark.asyncio
    async def test_returns_correct_budget_assignment(self, client, account_id):
        """Should return correct budget assignment when rules exist."""
        rule_id = uuid.uuid4()
        budget_id = uuid.uuid4()

        mock_session = AsyncMock()
        mock_result = MagicMock()

        mock_row = MagicMock()
        mock_row.name = "Tesco"
        mock_row.transaction_count = 28
        mock_row.last_seen = datetime(2026, 3, 20, tzinfo=timezone.utc)
        mock_row.rule_id = rule_id
        mock_row.assigned_budget_id = budget_id
        mock_row.assigned_budget_name = "Food (groceries)"
        mock_row.assigned_group_name = "Variable Expenses"

        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        with patch("app.api.merchants.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            response = client.get(f"/api/v1/accounts/{account_id}/merchants")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Tesco"
        assert data[0]["transaction_count"] == 28
        assert data[0]["rule_id"] == str(rule_id)
        assert data[0]["assigned_budget_id"] == str(budget_id)
        assert data[0]["assigned_budget_name"] == "Food (groceries)"
        assert data[0]["assigned_group_name"] == "Variable Expenses"

    @pytest.mark.asyncio
    async def test_orders_uncategorised_first(self, client, account_id):
        """Should order uncategorised merchants first, then by transaction_count DESC."""
        mock_session = AsyncMock()
        mock_result = MagicMock()

        # Uncategorised merchant (should be first)
        uncat_row = MagicMock()
        uncat_row.name = "New Shop"
        uncat_row.transaction_count = 2
        uncat_row.last_seen = datetime(2026, 3, 21, tzinfo=timezone.utc)
        uncat_row.rule_id = None
        uncat_row.assigned_budget_id = None
        uncat_row.assigned_budget_name = None
        uncat_row.assigned_group_name = None

        # Categorised merchant (should be second despite higher count)
        cat_row = MagicMock()
        cat_row.name = "Tesco"
        cat_row.transaction_count = 28
        cat_row.last_seen = datetime(2026, 3, 20, tzinfo=timezone.utc)
        cat_row.rule_id = uuid.uuid4()
        cat_row.assigned_budget_id = uuid.uuid4()
        cat_row.assigned_budget_name = "Groceries"
        cat_row.assigned_group_name = "Variable Expenses"

        # Return in DB order (the query handles ordering)
        mock_result.all.return_value = [uncat_row, cat_row]
        mock_session.execute.return_value = mock_result

        with patch("app.api.merchants.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_session.return_value.__aexit__ = AsyncMock(return_value=False)

            response = client.get(f"/api/v1/accounts/{account_id}/merchants")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Uncategorised first
        assert data[0]["name"] == "New Shop"
        assert data[0]["rule_id"] is None
        # Categorised second
        assert data[1]["name"] == "Tesco"
        assert data[1]["rule_id"] is not None
